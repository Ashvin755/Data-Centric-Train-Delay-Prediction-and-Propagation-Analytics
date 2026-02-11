"""
RailRadar API client for fetching train data.

Provides functions to interact with RailRadar API and validate journey data.
Uses cloudscraper to bypass Cloudflare protection on GitHub Actions.
"""

import logging
import time
import cloudscraper
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RailRadarAPI:
    """Client for RailRadar API interactions with Cloudflare bypass."""
    
    BASE_URL = "https://api.railradar.in/api/v1/trains"
    MAX_RETRIES = 3
    RETRY_BASE_DELAY = 3  # seconds
    REQUEST_DELAY = 1.5  # seconds between requests to avoid rate limiting
    
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
        
        # Browser-like headers to avoid bot detection
        self.scraper.headers.update({
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
    
    def get_train_data(self, train_number: int, journey_date: str, 
                       data_type: str = "live") -> Optional[Dict[str, Any]]:
        """
        Fetch train data from RailRadar API with retry logic.
        
        Args:
            train_number: 5-digit train number
            journey_date: Journey date in YYYY-MM-DD format
            data_type: Type of data to fetch ('full', 'static', 'live')
            
        Returns:
            API response data dict or None on error
        """
        url = f"{self.BASE_URL}/{train_number}"
        params = {
            "journeyDate": journey_date,
            "dataType": data_type,
            "dataProvider": "railradar",
            "userId": ""  # Required parameter (can be empty string)
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
                
                data = response.json()
                
                # Validate response structure
                if "data" not in data:
                    logger.warning(f"Invalid API response structure for train {train_number}")
                    logger.debug(f"Response keys: {data.keys() if isinstance(data, dict) else type(data)}")
                    return None
                
                logger.info(f"✅ Successfully fetched data for train {train_number}")
                inner_data = data.get("data", {})
                return inner_data
            
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
                
                # Retry on transient errors
                if attempt < self.MAX_RETRIES and error_type in ['Timeout', 'ConnectionError', 'HTTPError']:
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
            
            # API returns TWO formats:
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
            # Handle Format 2 (live data at root)
            if 'currentLocation' in api_response:
                current_station = api_response.get("currentLocation", {}).get("stationCode")
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
