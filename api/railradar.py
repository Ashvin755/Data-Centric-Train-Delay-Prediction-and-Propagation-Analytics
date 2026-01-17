"""
RailRadar API client for fetching train data.

Provides functions to interact with RailRadar API and validate journey data.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RailRadarAPI:
    """Client for RailRadar API interactions."""
    
    BASE_URL = "https://api.railradar.in/api/v1/trains"
    
    def __init__(self, api_key: str):
        """
        Initialize RailRadar API client.
        
        Args:
            api_key: RailRadar API key
        """
        self.api_key = api_key
        self.headers = {
            "Accept": "*/*",
            "X-API-Key": api_key
        }
        # Log masked API key for debugging
        masked_key = api_key[:10] + "***" + api_key[-5:] if len(api_key) > 15 else "***"
        logger.info(f"RailRadar API client initialized with key: {masked_key}")
    
    def get_train_data(self, train_number: int, journey_date: str, 
                       data_type: str = "live") -> Optional[Dict[str, Any]]:
        """
        Fetch train data from RailRadar API.
        
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
        
        try:
            logger.debug(f"Calling RailRadar API: train={train_number}, date={journey_date}, type={data_type}")
            logger.debug(f"URL: {url}")
            logger.debug(f"Params: {params}")
            logger.debug(f"Headers: {{'Accept': '{self.headers.get('Accept')}', 'X-API-Key': '{self.headers.get('X-API-Key')[:10]}***{self.headers.get('X-API-Key')[-5:]}'}}")
            logger.info(f"Full request: requests.get('{url}', headers={{'X-API-Key': '***'}}, params={params})")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response structure
            if "data" not in data:
                logger.warning(f"Invalid API response structure for train {train_number}")
                logger.debug(f"Response keys: {data.keys() if isinstance(data, dict) else type(data)}")
                return None
            
            logger.info(f"Successfully fetched data for train {train_number}")
            inner_data = data.get("data", {})
            logger.debug(f"Response data keys: {inner_data.keys() if isinstance(inner_data, dict) else type(inner_data)}")
            return inner_data
        
        except requests.exceptions.Timeout:
            logger.error(f"API timeout for train {train_number}")
            logger.debug(f"URL: {url}, Params: {params}")
            return None
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for train {train_number}: {e}")
            logger.error(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
            logger.error(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
            logger.error(f"URL: {url}")
            logger.error(f"Params: {params}")
            logger.error(f"Headers sent: {{'Accept': '{self.headers.get('Accept')}', 'X-API-Key': '{self.headers.get('X-API-Key')[:10]}***{self.headers.get('X-API-Key')[-5:]}'}}")
            logger.error(f"Full API key length: {len(self.headers.get('X-API-Key', ''))}")
            logger.error(f"Request headers from response: {dict(response.request.headers) if 'response' in locals() else 'N/A'}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for train {train_number}: {e}")
            return None
        
        except ValueError as e:
            logger.error(f"JSON decode error for train {train_number}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error for train {train_number}: {e}")
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
