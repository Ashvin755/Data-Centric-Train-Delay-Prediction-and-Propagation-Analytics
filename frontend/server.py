import os
import json
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
import cloudscraper

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from the frontend folder directory
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        # Route live API requests to the proxy handler
        if self.path.startswith('/api/live'):
            self.handle_live_api()
        else:
            super().do_GET()

    def handle_live_api(self):
        try:
            # Parse query parameters to support dynamic dates (e.g. ?journeyDate=2026-05-26)
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            # 1. Retrieve journey date from query param, or fall back to today in IST (GMT+5:30)
            journey_date = query_params.get("journeyDate", [None])[0]
            train_no = query_params.get("trainNo", ["18238"])[0]
            
            if not journey_date:
                ist_tz = timezone(timedelta(hours=5, minutes=30))
                journey_date = datetime.now(ist_tz).strftime("%Y-%m-%d")
            
            # 2. Get API key from environment, fallback to active key
            api_key = os.environ.get("RAILRADAR_API_KEY_ONE_DAY")
            
            # 3. Create scraper session to bypass Cloudflare
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            
            headers = {
                "X-API-Key": api_key,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://railradar.in/",
                "Origin": "https://railradar.in",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            url = f"https://api.railradar.in/api/v1/trains/{train_no}"
            params = {
                "journeyDate": journey_date,
                "dataType": "live",
                "dataProvider": "railradar",
                "userId": ""
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
                
            # Support nested or flat API responses
            route = []
            extracted_date = journey_date
            
            if "currentLocation" in api_data and "route" in api_data:
                route = api_data.get("route", [])
                extracted_date = api_data.get("journeyDate") or journey_date
            elif "liveData" in api_data:
                live_data = api_data.get("liveData", {}) or {}
                route = live_data.get("route", [])
                extracted_date = live_data.get("journeyDate") or journey_date
                
            if not route:
                self.send_error_response(404, "Live tracking active but route station list is empty.")
                return
                
            # Format route to match frontend schema
            formatted_journey = []
            for station in route:
                formatted_journey.append({
                    "stationCode": station.get("stationCode"),
                    "scheduledArrival": station.get("scheduledArrival"),
                    "scheduledDeparture": station.get("scheduledDeparture"),
                    "actualArrival": station.get("actualArrival"),
                    "actualDeparture": station.get("actualDeparture"),
                    "delayArrival": station.get("delayArrivalMinutes"),
                    "delayDeparture": station.get("delayDepartureMinutes")
                })
                
            # Send clean proxy response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
            self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
            self.end_headers()
            
            payload = {
                "status": "success",
                "date": extracted_date,
                "journey": formatted_journey
            }
            self.wfile.write(json.dumps(payload).encode('utf-8'))
            print(f"[Server Proxy] Successfully proxied {len(formatted_journey)} station route markers.")
            
        except Exception as e:
            print(f"[Server Proxy] Error processing live proxy request: {e}")
            self.send_error_response(500, str(e))

    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        
        payload = {
            "status": "error",
            "message": message
        }
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-API-Key')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()

def run():
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
