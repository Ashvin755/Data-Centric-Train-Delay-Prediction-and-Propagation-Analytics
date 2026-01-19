"""
Supabase client wrapper for Rail Data collection system.

Handles all database operations for journey tracking and data storage.
"""

import logging
import time
import random
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Retry configuration for transient errors
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1  # Initial backoff: 1 second
MAX_BACKOFF_SECONDS = 10  # Max backoff: 10 seconds

# HTTP error codes that should trigger retry
RETRYABLE_ERROR_CODES = {429, 500, 502, 503, 504}  # Rate limit, server errors, service unavailable


class SupabaseDB:
    """Wrapper class for Supabase database operations."""
    
    def __init__(self, url: str, key: str):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL
            key: Supabase API key
        """
        self.client: Client = create_client(url, key)
        logger.info("Supabase client initialized")
    
    @staticmethod
    def _is_retryable_error(error: Exception) -> bool:
        """
        Check if an error is transient and should trigger a retry.
        
        Args:
            error: The exception to check
            
        Returns:
            True if error is retryable, False otherwise
        """
        error_str = str(error).lower()
        
        # Check for HTTP error codes
        if isinstance(error, dict) and "code" in error:
            return error["code"] in RETRYABLE_ERROR_CODES
        
        # Check for known retryable error messages
        retryable_patterns = [
            "502", "500", "503", "504",  # HTTP codes
            "bad gateway", "internal server error", "service unavailable",
            "timeout", "connection reset", "temporary failure",
            "json could not be generated"  # Supabase-specific transient error
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    @staticmethod
    def _exponential_backoff(attempt: int) -> float:
        """
        Calculate exponential backoff with jitter.
        
        Args:
            attempt: The retry attempt number (0-indexed)
            
        Returns:
            Number of seconds to wait
        """
        backoff = min(BASE_BACKOFF_SECONDS * (2 ** attempt), MAX_BACKOFF_SECONDS)
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, backoff * 0.1)
        return backoff + jitter
    
    # ==================== TRAIN INFO OPERATIONS ====================
    
    def get_trains_by_journey_type(self, journey_type: str) -> List[Dict[str, Any]]:
        """
        Fetch all trains of a specific journey type.
        
        Args:
            journey_type: 'one_day' or 'multiple_day'
            
        Returns:
            List of train records with train_no, train_name, destination_station_code
        """
        try:
            response = self.client.table("train_info").select(
                "train_no, train_name, destination_station_code, journey_type"
            ).eq("journey_type", journey_type).execute()
            
            logger.info(f"Fetched {len(response.data)} trains for journey_type={journey_type}")
            return response.data
        
        except Exception as e:
            logger.error(f"Error fetching trains by journey_type: {e}")
            raise
    
    def get_destination_station(self, train_no: int) -> Optional[str]:
        """
        Get destination station code for a train.
        
        Args:
            train_no: Train number
            
        Returns:
            Destination station code or None if not found
        """
        try:
            response = self.client.table("train_info").select(
                "destination_station_code"
            ).eq("train_no", train_no).execute()
            
            if response.data:
                return response.data[0]["destination_station_code"]
            return None
        
        except Exception as e:
            logger.error(f"Error fetching destination for train {train_no}: {e}")
            raise
    
    # ==================== JOURNEY STATUS FLAGS OPERATIONS ====================
    
    def journey_exists(self, train_no: int, journey_date: str) -> bool:
        """
        Check if a journey already exists in tracking.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
            
        Returns:
            True if journey exists, False otherwise
        """
        try:
            response = self.client.table("journey_status_flags").select(
                "id"
            ).eq("train_no", train_no).eq("journey_date", journey_date).execute()
            
            exists = len(response.data) > 0
            logger.debug(f"Journey ({train_no}, {journey_date}) exists: {exists}")
            return exists
        
        except Exception as e:
            logger.error(f"Error checking journey existence: {e}")
            raise
    
    def create_journey(self, train_no: int, journey_date: str) -> None:
        """
        Create a new journey tracking record.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
        """
        try:
            data = {
                "train_no": train_no,
                "journey_date": journey_date,
                "flag": 0,
                "is_completed": False,
                "is_abandoned": False,
                "last_checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.client.table("journey_status_flags").insert(data).execute()
            logger.info(f"Created journey tracking for ({train_no}, {journey_date})")
        
        except Exception as e:
            logger.error(f"Error creating journey ({train_no}, {journey_date}): {e}")
            raise
    
    def get_ongoing_journeys(self, journey_type: str = None) -> List[Dict[str, Any]]:
        """
        Fetch all ongoing (incomplete and not abandoned) journeys.
        
        Args:
            journey_type: Optional filter for journey type ('one_day' or 'multiple_day')
        
        Returns:
            List of journey records with train_no, journey_date, flag
        """
        try:
            query = self.client.table("journey_status_flags").select(
                "train_no, journey_date, flag, train_info!inner(journey_type)"
            ).eq("is_completed", False).eq("is_abandoned", False)
            
            # Filter by journey_type if provided
            if journey_type:
                query = query.eq("train_info.journey_type", journey_type)
            
            response = query.execute()
            
            filter_msg = f" with journey_type={journey_type}" if journey_type else ""
            logger.info(f"Fetched {len(response.data)} ongoing journeys{filter_msg}")
            return response.data
        
        except Exception as e:
            logger.error(f"Error fetching ongoing journeys: {e}")
            raise
    
    def increment_flag(self, train_no: int, journey_date: str) -> None:
        """
        Increment flag counter for a journey.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
        """
        try:
            # First, get current flag value
            response = self.client.table("journey_status_flags").select(
                "flag"
            ).eq("train_no", train_no).eq("journey_date", journey_date).execute()
            
            if not response.data:
                logger.warning(f"Journey ({train_no}, {journey_date}) not found for flag increment")
                return
            
            current_flag = response.data[0]["flag"]
            new_flag = current_flag + 1
            
            # Update flag and last_checked_at
            update_data = {
                "flag": new_flag,
                "last_checked_at": datetime.utcnow().isoformat()
            }
            
            self.client.table("journey_status_flags").update(
                update_data
            ).eq("train_no", train_no).eq("journey_date", journey_date).execute()
            
            logger.info(f"Incremented flag for ({train_no}, {journey_date}): {current_flag} -> {new_flag}")
        
        except Exception as e:
            logger.error(f"Error incrementing flag for ({train_no}, {journey_date}): {e}")
            raise
    
    def mark_abandoned(self, train_no: int, journey_date: str) -> None:
        """
        Mark a journey as abandoned.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
        """
        try:
            update_data = {
                "is_abandoned": True,
                "last_checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.client.table("journey_status_flags").update(
                update_data
            ).eq("train_no", train_no).eq("journey_date", journey_date).execute()
            
            logger.warning(f"Marked journey as abandoned: ({train_no}, {journey_date})")
        
        except Exception as e:
            logger.error(f"Error marking journey as abandoned: {e}")
            raise
    
    def mark_completed(self, train_no: int, journey_date: str) -> None:
        """
        Mark a journey as completed.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
        """
        try:
            update_data = {
                "is_completed": True,
                "last_checked_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.client.table("journey_status_flags").update(
                update_data
            ).eq("train_no", train_no).eq("journey_date", journey_date).execute()
            
            logger.info(f"Marked journey as completed: ({train_no}, {journey_date})")
        
        except Exception as e:
            logger.error(f"Error marking journey as completed: {e}")
            raise
    
    # ==================== RAIL DATA OPERATIONS ====================
    
    def insert_station_data(self, train_no: int, journey_date: str, 
                           station_data: Dict[str, Any]) -> None:
        """
        Insert a single station record into rail_data with retry mechanism.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
            station_data: Dict containing station-level data from RailRadar
            
        Raises:
            Exception: If all retries fail and error is not a duplicate
        """
        data = {
            "train_no": train_no,
            "journey_date": journey_date,
            "station_code": station_data.get("stationCode"),
            "scheduled_arrival": station_data.get("scheduledArrival"),
            "scheduled_departure": station_data.get("scheduledDeparture"),
            "actual_arrival": station_data.get("actualArrival"),
            "actual_departure": station_data.get("actualDeparture"),
            "delay_arrival_minutes": station_data.get("delayArrivalMinutes"),
            "delay_departure_minutes": station_data.get("delayDepartureMinutes"),
            "distance_from_origin_km": station_data.get("distanceFromOriginKm")
        }
        
        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                self.client.table("rail_data").insert(data).execute()
                logger.debug(f"Inserted station data: ({train_no}, {journey_date}, {data['station_code']})")
                return  # Success, exit
            
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                
                # Check if it's a duplicate key error (idempotency)
                if "duplicate" in error_str or "unique" in error_str:
                    logger.warning(f"Duplicate station data, skipping: ({train_no}, {journey_date}, {station_data.get('stationCode')})")
                    return  # Success case (idempotent)
                
                # Check if error is retryable
                if self._is_retryable_error(e):
                    if attempt < MAX_RETRIES - 1:  # Not the last attempt
                        backoff_seconds = self._exponential_backoff(attempt)
                        logger.warning(
                            f"Transient error inserting station data (attempt {attempt + 1}/{MAX_RETRIES}), "
                            f"retrying in {backoff_seconds:.2f}s: {e}"
                        )
                        time.sleep(backoff_seconds)
                        continue
                    else:
                        logger.error(
                            f"Failed to insert station data after {MAX_RETRIES} retries: "
                            f"({train_no}, {journey_date}, {station_data.get('stationCode')}). Error: {e}"
                        )
                        raise
                else:
                    # Non-retryable error, fail immediately
                    logger.error(f"Non-retryable error inserting station data: {e}")
                    raise
        
        # Fallback (should not reach here)
        logger.error(f"Unexpected error state for station insert: {last_error}")
        raise last_error
    
    def insert_journey_stations(self, train_no: int, journey_date: str, 
                               route_data: List[Dict[str, Any]]) -> int:
        """
        Insert all station records for a completed journey.
        
        Args:
            train_no: Train number
            journey_date: Journey date in YYYY-MM-DD format
            route_data: List of station data from RailRadar liveData.route
            
        Returns:
            Number of stations successfully inserted
        """
        inserted_count = 0
        
        for station in route_data:
            try:
                self.insert_station_data(train_no, journey_date, station)
                inserted_count += 1
            except Exception as e:
                logger.error(f"Failed to insert station {station.get('stationCode')}: {e}")
                # Continue with other stations
        
        logger.info(f"Inserted {inserted_count}/{len(route_data)} stations for journey ({train_no}, {journey_date})")
        return inserted_count
