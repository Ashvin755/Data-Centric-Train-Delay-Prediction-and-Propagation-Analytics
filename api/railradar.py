"""
RailRadar API client for fetching train data.

Uses the current RailRadar v1 API:
  GET https://api.railradar.in/v1/trains/{number}/live?date=YYYY-MM-DD&haltsOnly=true
with `Authorization: Bearer <key>` auth (X-API-Key also sent for compatibility).

Responses are normalized to the legacy DB-friendly shape so downstream
code (Phase 1/2, Supabase inserts, frontend proxy) keeps working:
  {
    "trainNumber": ...,
    "journeyDate": ...,   # mirrored from startDate
    "startDate": ...,
    "status": ...,
    "currentLocation": {"stationCode": ...},
    "route": [
      {
        "stationCode": ...,
        "scheduledArrival": <unix int|None>,
        "scheduledDeparture": <unix int|None>,
        "actualArrival": <unix int|None>,
        "actualDeparture": <unix int|None>,
        "delayArrivalMinutes": <int|None>,
        "delayDepartureMinutes": <int|None>,
        "distanceFromOriginKm": <float|None>,
      }, ...
    ]
  }
"""

import logging
import time
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import cloudscraper
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class RailRadarAPI:
    """Client for RailRadar API interactions with Cloudflare bypass."""

    BASE_URL = "https://api.railradar.in/v1/trains"
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 3  # seconds
    # The API hard-limits 10 requests/minute (429 TOO_MANY_REQUESTS beyond that).
    # 7s spacing guarantees at most 9 requests in any rolling 60s window, which
    # also covers a worst-case multi-day run (6 Phase 1 + 6 Phase 2 = 12 calls).
    REQUEST_DELAY = 7.0
    RATE_LIMIT_WAIT_SECONDS = 61  # outlast the 1-minute rate-limit window
    # Same-run response cache: Phase 1 fetches (train, today) to decide whether
    # a journey started, then Phase 2 immediately re-fetches the same key for
    # every journey Phase 1 just created. TTL covers one poll run (phases take
    # ~1-2 min together) but expires far before the next cron (5h/12h).
    RESPONSE_CACHE_TTL = 1200  # seconds
    RESPONSE_CACHE_MAX_ENTRIES = 128
    
    def __init__(self, api_key: str):
        """
        Initialize RailRadar API client.
        
        Args:
            api_key: RailRadar API key
        """
        self.api_key = api_key
        
        # Create cloudscraper session (bypasses Cloudflare)
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        
        # Browser-like headers to avoid bot detection.
        # Current docs use `Authorization: Bearer <key>`; keep X-API-Key too
        # since the new endpoint still accepts it.
        self.scraper.headers.update({
            "Authorization": f"Bearer {api_key}",
            "X-API-Key": api_key,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://railradar.in/",
            "Origin": "https://railradar.in",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Log masked API key for debugging
        masked_key = api_key[:10] + "***" + api_key[-5:] if len(api_key) > 15 else "***"
        logger.info(f"RailRadar API client initialized with key: {masked_key}")
        logger.info("Using cloudscraper for Cloudflare bypass")
        
        # Track last request time for rate limiting
        self._last_request_time = 0

        # Same-run response cache: (train_number, journey_date) -> (fetched_at, payload).
        # OrderedDict so stale/evicted entries are cheap to drop.
        self._response_cache: "OrderedDict[Tuple[int, str], Tuple[float, Dict[str, Any]]]" = OrderedDict()

    def _cache_get(self, train_number: int, journey_date: str) -> Optional[Dict[str, Any]]:
        """
        Return a fresh cached response for (train, date), or None if absent/expired.

        Returns a deep copy so callers can never mutate the cached payload.
        """
        key = (int(train_number), str(journey_date))
        entry = self._response_cache.get(key)
        if entry is None:
            return None
        fetched_at, payload = entry
        if time.time() - fetched_at > self.RESPONSE_CACHE_TTL:
            self._response_cache.pop(key, None)
            logger.debug(f"Cache entry expired for ({train_number}, {journey_date})")
            return None
        self._response_cache.move_to_end(key)
        logger.info(
            f"Cache hit for train {train_number} on {journey_date} "
            f"(skipping API call, age={time.time() - fetched_at:.0f}s)"
        )
        return deepcopy(payload)

    def _cache_put(self, train_number: int, journey_date: str, payload: Dict[str, Any]) -> None:
        """Store a successful response (deep copy) with FIFO size bound."""
        key = (int(train_number), str(journey_date))
        self._response_cache[key] = (time.time(), deepcopy(payload))
        self._response_cache.move_to_end(key)
        while len(self._response_cache) > self.RESPONSE_CACHE_MAX_ENTRIES:
            self._response_cache.popitem(last=False)
    
    @staticmethod
    def _to_unix(value: Any) -> Optional[int]:
        """Convert an API time value (unix int or ISO-8601 string) to unix seconds."""
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
                normalized = text.replace("Z", "+00:00")
                parsed = datetime.fromisoformat(normalized)
                if parsed.tzinfo is None:
                    # API times without an offset are IST wall-times.
                    # dateutil-less fallback: assume Asia/Kolkata (+05:30).
                    parsed = parsed.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                return int(parsed.timestamp())
            except ValueError:
                logger.debug(f"Unparseable time value from API: {value!r}")
                return None
        return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
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

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _normalize_station(cls, station: Dict[str, Any]) -> Dict[str, Any]:
        """Map one new-API route stop to the legacy DB-friendly shape."""
        return {
            "stationCode": station.get("stationCode"),
            "stationName": station.get("stationName"),
            "sequence": cls._to_int(station.get("sequence")),
            "scheduledArrival": cls._to_unix(station.get("scheduledArrival")),
            "scheduledDeparture": cls._to_unix(station.get("scheduledDeparture")),
            "actualArrival": cls._to_unix(station.get("actualArrival")),
            "actualDeparture": cls._to_unix(station.get("actualDeparture")),
            "delayArrivalMinutes": cls._to_int(
                station.get("delayArrivalMinutes", station.get("delayArrival"))
            ),
            "delayDepartureMinutes": cls._to_int(
                station.get("delayDepartureMinutes", station.get("delayDeparture"))
            ),
            "distanceFromOriginKm": cls._to_float(
                station.get("distanceFromOriginKm", station.get("distance"))
            ),
            "platform": station.get("platform"),
            "status": station.get("status"),
        }

    @classmethod
    def _normalize_live_payload(
        cls, data: Dict[str, Any], train_number: int, journey_date: str
    ) -> Dict[str, Any]:
        """Normalize a `/live` response envelope to the legacy flat shape."""
        current = data.get("currentLocation") or {}
        route = data.get("route") or []
        start_date = data.get("startDate") or data.get("journeyDate") or journey_date
        return {
            "trainNumber": str(data.get("trainNumber", train_number)),
            "trainName": data.get("trainName"),
            "journeyDate": start_date,
            "startDate": start_date,
            "status": data.get("status"),
            "lastUpdatedAt": data.get("lastUpdatedAt"),
            "currentLocation": {
                "stationCode": current.get("stationCode"),
                "stationName": current.get("stationName"),
                "sequence": cls._to_int(current.get("sequence")),
                "status": current.get("status"),
            },
            "route": [cls._normalize_station(s) for s in route if isinstance(s, dict)],
        }

    @classmethod
    def _not_found_payload(cls, train_number: int, journey_date: str) -> Dict[str, Any]:
        """Sentinel payload for 'no journey on this date' so callers treat it
        as 'not started / still ongoing' instead of a transient API error."""
        return {
            "trainNumber": str(train_number),
            "journeyDate": journey_date,
            "startDate": journey_date,
            "status": "not_found",
            "currentLocation": {},
            "route": [],
        }
    
    def get_train_data(self, train_number: int, journey_date: str, 
                       data_type: str = "live") -> Optional[Dict[str, Any]]:
        """
        Fetch train data from RailRadar API with retry logic.

        Uses the current endpoint:
            GET /v1/trains/{number}/live?date=YYYY-MM-DD&haltsOnly=true

        The `data_type` argument is kept for backward compatibility and ignored.

        Args:
            train_number: 5-digit train number
            journey_date: Journey date in YYYY-MM-DD format
            data_type: Ignored (kept for compatibility)
            
        Returns:
            Normalized response dict (legacy flat shape) or None on error.
            A 404 (no journey on this date) returns a `status="not_found"`
            payload rather than None so Phase 1 counts it as "not started".
        """
        # Serve from the same-run cache when Phase 2 re-checks a journey that
        # Phase 1 already fetched (same train + date => identical response).
        cached = self._cache_get(train_number, journey_date)
        if cached is not None:
            return cached

        url = f"{self.BASE_URL}/{train_number}/live"
        params = {
            "date": journey_date,
            "haltsOnly": "true",
        }
        
        # Retry loop for transient failures with exponential backoff
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                # Rate limiting: wait between requests to avoid Cloudflare triggers
                current_time = time.time()
                time_since_last = current_time - self._last_request_time
                if time_since_last < self.REQUEST_DELAY:
                    wait_time = self.REQUEST_DELAY - time_since_last
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s before request")
                    time.sleep(wait_time)
                
                logger.debug(f"Calling RailRadar API (attempt {attempt}/{self.MAX_RETRIES}): train={train_number}, date={journey_date}")
                logger.info(f"Request: GET {url} with params={params}")
                
                response = self.scraper.get(url, params=params, timeout=20)
                self._last_request_time = time.time()
                logger.debug(f"Response status: {response.status_code}")

                # No journey for this (train, date): not an error and not
                # worth retrying. Return a sentinel payload so Phase 1 counts
                # it as "checked, not started" instead of "api_errors".
                # NOTE: must come BEFORE raise_for_status(), which would turn
                # the 404 into an HTTPError and skip the sentinel path.
                if response.status_code == 404:
                    try:
                        err = (response.json().get("error", {}) or {})
                        code = str(err.get("code", "")).upper()
                        message = err.get("message", "")
                    except ValueError:
                        code, message = "", response.text[:200]
                    logger.info(
                        f"No journey for train {train_number} on {journey_date}: "
                        f"{code} {message}"
                    )
                    return self._not_found_payload(train_number, journey_date)

                # Rate limit (10 req/min). The exponential backoff (3s/6s)
                # stays INSIDE the same minute window and would fail every
                # attempt, so wait out the full window before retrying.
                if response.status_code == 429:
                    if attempt < self.MAX_RETRIES:
                        logger.warning(
                            f"Rate limited (429) for train {train_number}; "
                            f"waiting {self.RATE_LIMIT_WAIT_SECONDS}s for the window to reset "
                            f"(attempt {attempt}/{self.MAX_RETRIES})"
                        )
                        time.sleep(self.RATE_LIMIT_WAIT_SECONDS)
                        continue
                    logger.error(
                        f"Rate limited (429) for train {train_number} after "
                        f"{self.MAX_RETRIES} attempts; giving up"
                    )
                    return None

                # Check for Cloudflare challenge page
                if "Just a moment" in response.text or "cloudflare" in response.text.lower():
                    retry_delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))  # Exponential: 3s, 6s, 12s
                    logger.warning(f"Cloudflare challenge detected on attempt {attempt}")
                    if attempt < self.MAX_RETRIES:
                        logger.info(f"Retrying in {retry_delay} seconds (exponential backoff)...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error("Max retries reached, Cloudflare still blocking")
                        return None
                
                response.raise_for_status()

                try:
                    data = response.json()
                except ValueError:
                    # Non-JSON body (proxy page, truncated response, HTML error).
                    # Retry transient ones; fail otherwise.
                    retry_delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        f"Non-JSON response for train {train_number} on attempt {attempt} "
                        f"(status={response.status_code}, len={len(response.text)}). "
                        f"Body head: {response.text[:200]!r}"
                    )
                    if attempt < self.MAX_RETRIES:
                        logger.info(f"Retrying in {retry_delay} seconds (exponential backoff)...")
                        time.sleep(retry_delay)
                        continue
                    logger.error("Max retries reached with non-JSON responses")
                    return None

                # Standard envelope: {success, data, meta}
                if isinstance(data, dict) and "success" in data:
                    if not data.get("success"):
                        err = data.get("error", {}) or {}
                        code = str(err.get("code", "")).upper()
                        message = err.get("message", "")
                        logger.warning(
                            f"API error for train {train_number} on {journey_date}: "
                            f"{code} {message}"
                        )
                        return None
                    inner = data.get("data", {})
                elif "data" not in data:
                    logger.warning(f"Invalid API response structure for train {train_number}")
                    logger.debug(f"Response keys: {data.keys() if isinstance(data, dict) else type(data)}")
                    return None
                else:
                    inner = data.get("data", {})
                
                normalized = self._normalize_live_payload(inner, train_number, journey_date)
                logger.info(f"✅ Successfully fetched data for train {train_number}")
                # Cache only successes: Phase 2 re-requests exactly the keys
                # Phase 1 succeeded on (journeys it created). Failures must
                # stay retryable; not_found never reaches Phase 2.
                self._cache_put(train_number, journey_date, normalized)
                return normalized
            
            except cloudscraper.exceptions.CloudflareChallengeError as e:
                retry_delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.error(f"Cloudflare challenge failed on attempt {attempt}: {e}")
                if attempt < self.MAX_RETRIES:
                    logger.info(f"Retrying in {retry_delay} seconds (exponential backoff)...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached for Cloudflare challenge")
                    return None
            
            except Exception as e:
                error_type = type(e).__name__
                retry_delay = self.RETRY_BASE_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.error(f"{error_type} for train {train_number} on attempt {attempt}: {e}")

                # Log response details if available
                if 'response' in locals():
                    logger.error(f"Response status: {response.status_code}")
                    logger.error(f"Response text (first 500 chars): {response.text[:500]}")

                # Retry on transient errors. Match broadly: requests names them
                # ConnectTimeout/ReadTimeout (not literally "Timeout"), and
                # cloudscraper/HTTPError hierarchy varies by transport.
                transient_markers = ('timeout', 'connectionerror', 'httperror',
                                     'remotedisconnected', 'connectionaborted',
                                     'connectionreset', 'chunkedencoding')
                is_transient = (
                    error_type in ['Timeout', 'ConnectionError', 'HTTPError']
                    or any(m in error_type.lower() for m in transient_markers)
                    or any(m in str(e).lower() for m in transient_markers)
                )
                if attempt < self.MAX_RETRIES and is_transient:
                    logger.info(f"Retrying in {retry_delay} seconds (exponential backoff)...")
                    time.sleep(retry_delay)
                else:
                    logger.error(f"Max retries reached or non-retryable error ({error_type})")
                    return None
        
        return None
    
    def is_journey_started(self, api_response: Dict[str, Any], 
                          expected_date: str) -> bool:
        """
        Check if RailRadar confirms journey started on expected date.
        
        Used in Phase 1 to validate if a train actually started today.
        
        Args:
            api_response: Response from get_train_data()
            expected_date: Expected journey date in YYYY-MM-DD format
            
        Returns:
            True if journey is confirmed active for expected_date
        """
        try:
            logger.debug(f"Validating journey start for date: {expected_date}")

            status = str(api_response.get("status") or "").lower()
            # Only a physically running train counts as "started" for Phase 1.
            # The API returns status="not-started" for scheduled/future journeys
            # (with a plausible-looking origin currentLocation), so the status
            # check — not currentLocation alone — is the discriminator.
            if status in {"not_found", "notfound", "not-found", "cancelled", "canceled",
                          "not-started", "notstarted", "scheduled", "upcoming"}:
                logger.debug(f"Journey not active (status={status})")
                return False
            if status and status not in {"running", "active", "in-progress", "inprogress",
                                         "delayed", "ontime", "on-time", "completed",
                                         "arrived", "reached"}:
                # Unknown future status: fail closed but LOUD — a silent miss here
                # means a journey is never tracked and the data is lost forever.
                logger.warning(f"Unknown journey status={status!r}; treating as not started")
                return False

            # Normalized flat shape: {journeyDate/startDate, currentLocation, route}
            # (legacy liveData / Format 1/2 inputs are still accepted below)
            journey_date = api_response.get("journeyDate") or api_response.get("startDate")
            if journey_date is not None:
                logger.debug(f"Journey date from API: {journey_date}, Expected: {expected_date}")
                if str(journey_date) != str(expected_date):
                    logger.debug(f"Journey date mismatch: got {journey_date}, expected {expected_date}")
                    return False
                current_location = api_response.get("currentLocation") or {}
                station_code = current_location.get("stationCode")
                if not station_code:
                    logger.debug("No stationCode in currentLocation")
                    return False
                logger.info(f"✓ Journey confirmed started on {expected_date} at station {station_code}")
                return True

            # API returns TWO legacy formats:
            # Format 1: {train, route, liveData, metadata} - nested structure
            # Format 2: {trainNumber, journeyDate, currentLocation, route, ...} - flat structure
            
            # Check Format 2 first (live data at root level)
            if 'currentLocation' in api_response and 'journeyDate' in api_response:
                journey_date = api_response.get("journeyDate")
                logger.debug(f"Format 2 detected. Journey date: {journey_date}, Expected: {expected_date}")
                
                if journey_date != expected_date:
                    logger.debug(f"Journey date mismatch: got {journey_date}, expected {expected_date}")
                    return False
                
                current_location = api_response.get("currentLocation")
                station_code = current_location.get("stationCode") if current_location else None
                
                if not station_code:
                    logger.debug("No stationCode in currentLocation")
                    return False
                
                logger.info(f"✓ Journey confirmed started (Format 2) on {expected_date} at station {station_code}")
                return True
            
            # Check Format 1 (nested liveData)
            live_data = api_response.get("liveData", {})
            logger.debug(f"Format 1 check - has liveData: {bool(live_data)}")
            
            if not live_data:
                logger.debug("No liveData in response - journey not started")
                return False
            
            # Journey date must match expected date
            journey_date = live_data.get("journeyDate")
            logger.debug(f"Journey date from API: {journey_date}, Expected: {expected_date}")
            
            if journey_date != expected_date:
                logger.debug(f"Journey date mismatch: got {journey_date}, expected {expected_date}")
                return False
            
            # Must have current location data
            current_location = live_data.get("currentLocation")
            if not current_location:
                logger.debug("No currentLocation in liveData")
                return False
            
            station_code = current_location.get("stationCode")
            if not station_code:
                logger.debug("No stationCode in currentLocation")
                return False
            
            logger.info(f"✓ Journey confirmed started (Format 1) on {expected_date} at station {station_code}")
            return True
        
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Error validating journey start: {e}")
            return False
    
    def is_journey_completed(self, api_response: Dict[str, Any], 
                            destination_code: str) -> bool:
        """
        Check if train reached destination station.
        
        Used in Phase 2 to detect journey completion.
        
        Args:
            api_response: Response from get_train_data()
            destination_code: Expected destination station code
            
        Returns:
            True if train arrived at destination
        """
        try:
            status = str(api_response.get("status") or "").lower()
            if status == "completed":
                logger.info(f"Journey completed! API status=completed, destination: {destination_code}")
                return True
            if status in {"not_found", "notfound", "not-found", "not-started",
                          "notstarted", "scheduled", "upcoming",
                          "cancelled", "canceled"}:
                return False

            # Handle normalized flat shape (live data at root)
            if 'currentLocation' in api_response:
                current = api_response.get("currentLocation") or {}
                current_station = current.get("stationCode")
                if current_station and current_station == destination_code:
                    logger.info(f"Journey completed! Current: {current_station} == Destination: {destination_code}")
                    return True
                # Check the destination stop's own status. NOTE: the API
                # pre-fills actualArrival/actualDeparture with the scheduled
                # times for upcoming stops, so actuals alone can NOT signal
                # completion — only the per-stop `status` field can.
                route = api_response.get("route") or []
                for stop in route:
                    if not isinstance(stop, dict):
                        continue
                    if stop.get("stationCode") == destination_code:
                        stop_status = str(stop.get("status") or "").lower()
                        if stop_status in {"arrived", "at-station", "departed"}:
                            logger.info(f"Journey completed! Destination stop {destination_code} status={stop_status}")
                            return True
                        break
                if current_station:
                    logger.debug(f"Journey ongoing. Current: {current_station}, Destination: {destination_code}")
                    return False

            # Handle legacy Format 2 (live data at root)
            # NOTE: unreachable for normalized payloads (handled above), kept
            # only for raw legacy-shape inputs passed directly by callers.
            if 'currentLocation' in api_response and 'journeyDate' in api_response and 'startDate' not in api_response:
                current_station = (api_response.get("currentLocation") or {}).get("stationCode")
                if current_station:
                    is_completed = current_station == destination_code
                    if is_completed:
                        logger.info(f"Journey completed (Format 2)! Current: {current_station} == Destination: {destination_code}")
                    else:
                        logger.debug(f"Journey ongoing (Format 2). Current: {current_station}, Destination: {destination_code}")
                    return is_completed
            
            # Handle Format 1 (nested liveData)
            current_station = (
                api_response
                .get("liveData", {})
                .get("currentLocation", {})
                .get("stationCode")
            )
            
            if not current_station:
                logger.debug("No current station found in response")
                return False
            
            is_completed = current_station == destination_code
            
            if is_completed:
                logger.info(f"Journey completed (Format 1)! Current: {current_station} == Destination: {destination_code}")
            else:
                logger.debug(f"Journey ongoing (Format 1). Current: {current_station}, Destination: {destination_code}")
            
            return is_completed
        
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Error checking journey completion: {e}")
            return False
    
    def extract_route_data(self, api_response: Dict[str, Any]) -> list:
        """
        Extract station-level route data from API response.
        
        Used in Phase 2 when journey is completed.
        
        Args:
            api_response: Response from get_train_data()
            
        Returns:
            List of station data dicts, empty list if no data
        """
        try:
            # Handle Format 2 (route at root level)
            if 'currentLocation' in api_response and 'route' in api_response:
                route = api_response.get("route", [])
                if route:
                    logger.info(f"Extracted {len(route)} stations from route data (Format 2)")
                    return route
            
            # Handle Format 1 (nested in liveData)
            route = api_response.get("liveData", {}).get("route", [])
            
            if not route:
                logger.warning("No route data found in response")
                return []
            
            logger.info(f"Extracted {len(route)} stations from route data (Format 1)")
            return route
        
        except (KeyError, AttributeError, TypeError) as e:
            logger.error(f"Error extracting route data: {e}")
            return []
