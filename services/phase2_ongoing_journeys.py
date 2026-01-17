"""
Phase 2: Ongoing Journey Tracking

Tracks incomplete journeys, detects completion, and marks abandoned journeys.
"""

import logging
from typing import Dict, Any

from db.supabase_client import SupabaseDB
from api.railradar import RailRadarAPI

logger = logging.getLogger(__name__)


class Phase2OngoingJourneys:
    """Handles tracking of ongoing journeys."""
    
    def __init__(self, db: SupabaseDB, railradar: RailRadarAPI, max_flag_threshold: int = 6):
        """
        Initialize Phase 2 processor.
        
        Args:
            db: Supabase database client
            railradar: RailRadar API client
            max_flag_threshold: Maximum flag value before abandoning journey
        """
        self.db = db
        self.railradar = railradar
        self.max_flag_threshold = max_flag_threshold
        logger.info(f"Phase 2 processor initialized with max_flag_threshold={max_flag_threshold}")
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute Phase 2: Track ongoing journeys and detect completion.
        
        Logic:
        1. Fetch all journeys with is_completed=false AND is_abandoned=false
        2. For each ongoing journey:
           a. Get destination station code from train_info
           b. Call RailRadar API with journey_date
           c. If API fails: increment flag
           d. If journey completed: extract route data, insert into rail_data, mark completed
           e. If journey ongoing: increment flag
           f. If flag > threshold: mark as abandoned
        
        Returns:
            Dict with execution statistics
        """
        logger.info("=== Phase 2: Ongoing Journey Tracking ===")
        
        stats = {
            "journeys_tracked": 0,
            "completed": 0,
            "abandoned": 0,
            "still_ongoing": 0,
            "api_errors": 0
        }
        
        try:
            # Fetch all ongoing journeys
            ongoing_journeys = self.db.get_ongoing_journeys()
            logger.info(f"Found {len(ongoing_journeys)} ongoing journeys to track")
            
            if not ongoing_journeys:
                logger.info("No ongoing journeys to track")
                return stats
            
            # Process each journey
            for journey in ongoing_journeys:
                train_no = journey["train_no"]
                journey_date = journey["journey_date"]
                current_flag = journey["flag"]
                stats["journeys_tracked"] += 1
                
                try:
                    logger.info(f"Tracking journey: ({train_no}, {journey_date}), flag={current_flag}")
                    
                    # Get destination station
                    destination_code = self.db.get_destination_station(train_no)
                    if not destination_code:
                        logger.error(f"No destination found for train {train_no}")
                        continue
                    
                    # Call RailRadar API
                    logger.debug(f"Fetching live data for ({train_no}, {journey_date})")
                    api_response = self.railradar.get_train_data(train_no, journey_date, "live")
                    
                    # Handle API failure
                    if api_response is None:
                        logger.warning(f"API call failed for ({train_no}, {journey_date})")
                        self._handle_api_failure(train_no, journey_date, current_flag, stats)
                        continue
                    
                    # Check if journey completed
                    if self.railradar.is_journey_completed(api_response, destination_code):
                        self._handle_completion(train_no, journey_date, api_response, stats)
                    else:
                        self._handle_ongoing(train_no, journey_date, current_flag, stats)
                
                except Exception as e:
                    logger.error(f"Error processing journey ({train_no}, {journey_date}): {e}")
                    stats["api_errors"] += 1
                    continue
            
            logger.info(f"Phase 2 completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Phase 2 execution failed: {e}")
            raise
    
    def _handle_api_failure(self, train_no: int, journey_date: str, 
                           current_flag: int, stats: Dict[str, Any]) -> None:
        """
        Handle API call failure by incrementing flag or abandoning.
        
        Args:
            train_no: Train number
            journey_date: Journey date
            current_flag: Current flag value
            stats: Statistics dict to update
        """
        # Increment flag
        self.db.increment_flag(train_no, journey_date)
        new_flag = current_flag + 1
        
        # Check if should abandon
        if new_flag > self.max_flag_threshold:
            self.db.mark_abandoned(train_no, journey_date)
            stats["abandoned"] += 1
            logger.warning(f"Journey abandoned due to API failures: ({train_no}, {journey_date})")
        else:
            stats["api_errors"] += 1
            logger.info(f"API failure, flag incremented: ({train_no}, {journey_date}), flag={new_flag}")
    
    def _handle_completion(self, train_no: int, journey_date: str, 
                          api_response: Dict[str, Any], stats: Dict[str, Any]) -> None:
        """
        Handle journey completion by extracting and storing data.
        
        Args:
            train_no: Train number
            journey_date: Journey date
            api_response: RailRadar API response
            stats: Statistics dict to update
        """
        logger.info(f"Journey completed: ({train_no}, {journey_date})")
        
        # Extract route data
        route_data = self.railradar.extract_route_data(api_response)
        
        if not route_data:
            logger.warning(f"Journey completed but no route data: ({train_no}, {journey_date})")
            # Mark as completed anyway (journey technically finished)
            self.db.mark_completed(train_no, journey_date)
            stats["completed"] += 1
            return
        
        # Insert station data into rail_data
        try:
            inserted_count = self.db.insert_journey_stations(train_no, journey_date, route_data)
            logger.info(f"Inserted {inserted_count} station records for ({train_no}, {journey_date})")
            
            # Mark journey as completed
            self.db.mark_completed(train_no, journey_date)
            stats["completed"] += 1
            logger.info(f"✓ Journey completed and data stored: ({train_no}, {journey_date})")
        
        except Exception as e:
            logger.error(f"Error storing journey data for ({train_no}, {journey_date}): {e}")
            # Don't mark as completed if data insertion failed
            raise
    
    def _handle_ongoing(self, train_no: int, journey_date: str, 
                       current_flag: int, stats: Dict[str, Any]) -> None:
        """
        Handle ongoing journey by incrementing flag or abandoning.
        
        Args:
            train_no: Train number
            journey_date: Journey date
            current_flag: Current flag value
            stats: Statistics dict to update
        """
        # Increment flag
        self.db.increment_flag(train_no, journey_date)
        new_flag = current_flag + 1
        
        # Check if should abandon
        if new_flag > self.max_flag_threshold:
            self.db.mark_abandoned(train_no, journey_date)
            stats["abandoned"] += 1
            logger.warning(f"Journey abandoned (threshold exceeded): ({train_no}, {journey_date})")
        else:
            stats["still_ongoing"] += 1
            logger.debug(f"Journey still ongoing: ({train_no}, {journey_date}), flag={new_flag}")
