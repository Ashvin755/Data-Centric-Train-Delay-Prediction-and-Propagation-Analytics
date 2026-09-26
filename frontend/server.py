import os
import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
import cloudscraper
import requests
from dotenv import load_dotenv

# Load environment variables from the root .env (one level up from frontend/)
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_ENV_PATH)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def supabase_headers():
    """Return HTTP headers required for Supabase REST API calls."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json",
    }


class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from the frontend folder directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path.startswith('/api/live'):
            self.handle_live_api()
        elif self.path.startswith('/api/supabase/journey/'):
            self.handle_supabase_journey()
        elif self.path.startswith('/api/supabase/train/'):
            self.handle_supabase_train()
        else:
            super().do_GET()

    # ──────────────────────────────────────────────────────────────────────────
    # Supabase: Train metadata + available journey dates
    # GET /api/supabase/train/<trainNo>
    # ──────────────────────────────────────────────────────────────────────────
    def handle_supabase_train(self):
        try:
            # Extract trainNo from path  e.g. /api/supabase/train/12137
            match = re.search(r'/api/supabase/train/(\d+)', self.path)
            if not match:
                self.send_error_response(400, "Missing train number in path.")
                return

            train_no = match.group(1)
            print(f"[Supabase] Fetching train info for train {train_no}")

            # 1. Fetch train_info row
            train_resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/train_info",
                headers={**supabase_headers(), "Accept": "application/json"},
                params={
                    "train_no": f"eq.{train_no}",
                    "select": "train_no,train_name,destination_station_code,journey_type",
                    "limit": "1",
                },
                timeout=10,
            )
            train_resp.raise_for_status()
            train_rows = train_resp.json()

            if not train_rows:
                self.send_error_response(404, f"No train_info found for train {train_no}.")
                return

            train_info = train_rows[0]

            # 2. Fetch distinct journey_dates from journey_status_flags for this train
            dates_resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/journey_status_flags",
                headers={**supabase_headers(), "Accept": "application/json"},
                params={
                    "train_no": f"eq.{train_no}",
                    "select": "journey_date",
                },
                timeout=10,
            )
            dates_resp.raise_for_status()
            date_rows = dates_resp.json()

            # Deduplicate and sort dates
            journey_dates = sorted(set(row["journey_date"] for row in date_rows))

            payload = {
                "status": "success",
                "trainNumber": str(train_info["train_no"]),
                "trainName": train_info["train_name"],
                "destinationStationCode": train_info["destination_station_code"],
                "journeyType": train_info["journey_type"],
                "journeyDates": journey_dates,
            }

            print(f"[Supabase] Train {train_no}: '{train_info['train_name']}', {len(journey_dates)} journey dates")
            self.send_json_response(payload)

        except requests.HTTPError as e:
            print(f"[Supabase] HTTP error fetching train info: {e}")
            self.send_error_response(502, f"Supabase API error: {e}")
        except Exception as e:
            print(f"[Supabase] Error in handle_supabase_train: {e}")
            self.send_error_response(500, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # Supabase: Station journey data for a specific train + date
    # GET /api/supabase/journey/<trainNo>/<date>
    # ──────────────────────────────────────────────────────────────────────────
    def handle_supabase_journey(self):
        try:
            # Extract trainNo and date from path  e.g. /api/supabase/journey/12137/2026-01-17
            match = re.search(r'/api/supabase/journey/(\d+)/([\d-]+)', self.path)
            if not match:
                self.send_error_response(400, "Invalid path. Expected /api/supabase/journey/<trainNo>/<YYYY-MM-DD>.")
                return

            train_no = match.group(1)
            journey_date = match.group(2)
            print(f"[Supabase] Fetching journey for train {train_no} on {journey_date}")

            ist_tz = timezone(timedelta(hours=5, minutes=30))
            today_date_obj = datetime.now(ist_tz).date()
            requested_date_obj = datetime.strptime(journey_date, "%Y-%m-%d").date()

            # If date is within the last 4 days (or future), fetch from RailRadar directly
            if (today_date_obj - requested_date_obj).days <= 4:
                print(f"[Server Proxy] {journey_date} is within 4 days. Forwarding to Live API...")
                self.path = f"/api/live?trainNo={train_no}&journeyDate={journey_date}"
                self.handle_live_api()
                return

            # Fetch all station rows for this train+date, ordered by id (= insertion/route order)
            resp = requests.get(
                f"{SUPABASE_URL}/rest/v1/rail_data",
                headers={
                    **supabase_headers(),
                    "Accept": "application/json",
                    "Range-Unit": "items",
                    "Prefer": "count=none",
                },
                params={
                    "train_no": f"eq.{train_no}",
                    "journey_date": f"eq.{journey_date}",
                    "select": (
                        "station_code,scheduled_arrival,scheduled_departure,"
                        "actual_arrival,actual_departure,"
                        "delay_arrival_minutes,delay_departure_minutes"
                    ),
                    "order": "id.asc",
                },
                timeout=15,
            )
            resp.raise_for_status()
            rows = resp.json()

            if not rows:
                self.send_error_response(404, f"No rail_data found for train {train_no} on {journey_date}.")
                return

            formatted_journey = [
                {
                    "stationCode": row["station_code"],
                    "scheduledArrival": row["scheduled_arrival"],
                    "scheduledDeparture": row["scheduled_departure"],
                    "actualArrival": row["actual_arrival"],
                    "actualDeparture": row["actual_departure"],
                    "delayArrival": row["delay_arrival_minutes"],
                    "delayDeparture": row["delay_departure_minutes"],
                }
                for row in rows
            ]

            payload = {
                "status": "success",
                "date": journey_date,
                "journey": formatted_journey,
            }

            print(f"[Supabase] Journey {train_no}/{journey_date}: {len(formatted_journey)} stations returned")
            self.send_json_response(payload)

        except requests.HTTPError as e:
            print(f"[Supabase] HTTP error fetching journey: {e}")
            self.send_error_response(502, f"Supabase API error: {e}")
        except Exception as e:
            print(f"[Supabase] Error in handle_supabase_journey: {e}")
            self.send_error_response(500, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # RailRadar live proxy
    # ──────────────────────────────────────────────────────────────────────────
    def handle_live_api(self):
        try:
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            journey_date = query_params.get("journeyDate", [None])[0]
            train_no = query_params.get("trainNo", ["18238"])[0]

            if not journey_date:
                ist_tz = timezone(timedelta(hours=5, minutes=30))
                journey_date = datetime.now(ist_tz).strftime("%Y-%m-%d")

            api_key = os.environ.get("RAILRADAR_API_KEY_ONE_DAY")

            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )

            headers = {
                "Authorization": f"Bearer {api_key}",
                "X-API-Key": api_key,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://railradar.in/",
                "Origin": "https://railradar.in",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            url = f"https://api.railradar.in/v1/trains/{train_no}/live"
            params = {
                "date": journey_date,
                "haltsOnly": "true",
            }

            print(f"[Server Proxy] Fetching live data for train {train_no} on date: {journey_date}")
            response = scraper.get(url, headers=headers, params=params, timeout=20)

            if response.status_code != 200:
                print(f"[Server Proxy] External API returned status: {response.status_code}")
                self.send_error_response(response.status_code, f"External API returned status {response.status_code}.")
                return

            res_data = response.json()
            api_data = res_data.get("data")

            if not api_data:
                self.send_error_response(404, "No live tracking data active today. Train might not have started yet.")
                return

            route = []
            extracted_date = journey_date

            if isinstance(api_data, dict):
                if "route" in api_data:
                    # Current shape: {startDate, status, currentLocation, route}
                    route = api_data.get("route", []) or []
                    extracted_date = api_data.get("startDate") or api_data.get("journeyDate") or journey_date
                elif "liveData" in api_data:
                    live_data = api_data.get("liveData", {}) or {}
                    route = live_data.get("route", [])
                    extracted_date = live_data.get("journeyDate") or journey_date

            if not route:
                self.send_error_response(404, "Live tracking active but route station list is empty.")
                return

            def _to_unix(value):
                # Frontend time helpers expect unix seconds; the new API
                # returns ISO-8601 strings, legacy payloads used unix ints.
                # Naive datetimes (no offset) are IST wall-times.
                if value is None or value == "":
                    return None
                if isinstance(value, bool):
                    return None
                if isinstance(value, (int, float)):
                    return int(value)
                if isinstance(value, str):
                    text = value.strip()
                    if not text:
                        return None
                    if text.lstrip("+-").isdigit():
                        return int(text)
                    try:
                        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                        return int(parsed.timestamp())
                    except ValueError:
                        return None
                return None

            def _to_int(value):
                if value is None or value == "":
                    return None
                if isinstance(value, bool):
                    return None
                try:
                    return int(value)
                except (TypeError, ValueError):
                    try:
                        return int(float(value))
                    except (TypeError, ValueError):
                        return None

            formatted_journey = []
            for station in route:
                if not isinstance(station, dict):
                    continue
                formatted_journey.append({
                    "stationCode": station.get("stationCode"),
                    "scheduledArrival": _to_unix(station.get("scheduledArrival")),
                    "scheduledDeparture": _to_unix(station.get("scheduledDeparture")),
                    "actualArrival": _to_unix(station.get("actualArrival")),
                    "actualDeparture": _to_unix(station.get("actualDeparture")),
                    # New API uses delayArrival/delayDeparture (minutes);
                    # legacy shape used delayArrivalMinutes/delayDepartureMinutes.
                    "delayArrival": _to_int(station.get("delayArrivalMinutes", station.get("delayArrival"))),
                    "delayDeparture": _to_int(station.get("delayDepartureMinutes", station.get("delayDeparture")))
                })

            payload = {
                "status": "success",
                "date": extracted_date,
                "journey": formatted_journey
            }
            self.send_json_response(payload)
            print(f"[Server Proxy] Successfully proxied {len(formatted_journey)} station route markers.")

        except Exception as e:
            print(f"[Server Proxy] Error processing live proxy request: {e}")
            self.send_error_response(500, str(e))

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────
    def send_json_response(self, payload, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def send_error_response(self, status_code, message):
        self.send_json_response({"status": "error", "message": message}, status_code=status_code)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()


def run():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[Server Proxy] WARNING: SUPABASE_URL or SUPABASE_KEY not set. Supabase endpoints will fail.")
    print(f"[Server Proxy] Starting HTTP server in {DIRECTORY} on port {PORT}...")
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, CustomHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server Proxy] Shutting down HTTP server.")
        httpd.server_close()


if __name__ == '__main__':
    run()
