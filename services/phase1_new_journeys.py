"""
Phase 1: New Journey Detection

Detects trains starting their journey today and initializes tracking.
"""

import logging
from datetime import datetime
import pytz
from typing import Dict, Any

from db.supabase_client import SupabaseDB
from api.railradar import RailRadarAPI

logger = logging.getLogger(__name__)


class Phase1NewJourneys:
    """Handles detection of new journeys starting today."""
    
    def __init__(self, db: SupabaseDB, railradar: RailRadarAPI, timezone: str = "Asia/Kolkata"):
        """
        Initialize Phase 1 processor.
        
        Args:
            db: Supabase database client
            railradar: RailRadar API client
            timezone: Timezone for journey date calculation (default: IST)
        """
        self.db = db
        self.railradar = railradar
        self.timezone = pytz.timezone(timezone)
        logger.info(f"Phase 1 processor initialized with timezone: {timezone}")
    
    def get_today_date(self) -> str:
        """
        Get current date in the configured timezone.
        
        Returns:
            Date string in YYYY-MM-DD format
        """
        now = datetime.now(self.timezone)
        today = now.strftime("%Y-%m-%d")
        logger.debug(f"Today's date (IST): {today}")
        return today
    
    def execute(self, journey_type: str) -> Dict[str, Any]:
        """
        Execute Phase 1: Detect and initialize new journeys starting today.
        
        Logic:
        1. Get today's date in IST
        2. Fetch all trains of specified journey_type from train_info
        3. For each train:
           a. Check if journey exists for (train_no, today)
           b. If exists, skip
           c. If not exists, call RailRadar API
           d. If journey started today, create tracking record
        
        Args:
            journey_type: 'one_day' or 'multiple_day'
            
        Returns:
            Dict with execution statistics
        """
        logger.info(f"=== Phase 1: New Journey Detection (journey_type={journey_type}) ===")
        
        stats = {
            "trains_checked": 0,
            "new_journeys_detected": 0,
            "api_errors": 0,
            "already_tracked": 0
        }
        
        try:
            # Get today's date
            today = self.get_today_date()
            logger.info(f"Checking for new journeys starting on: {today}")
            
            # Fetch all trains of specified journey type
            trains = self.db.get_trains_by_journey_type(journey_type)
            logger.info(f"Found {len(trains)} trains with journey_type={journey_type}")
            
            # Process each train
            for train in trains:
                train_no = train["train_no"]
                stats["trains_checked"] += 1
                
                try:
                    # Check if journey already exists
                    if self.db.journey_exists(train_no, today):
                        logger.debug(f"Journey already tracked: ({train_no}, {today})")
                        stats["already_tracked"] += 1
                        continue
                    
                    # Call RailRadar API to check if journey started
                    logger.info(f"Checking if train {train_no} started today...")
                    api_response = self.railradar.get_train_data(train_no, today, "live")
                    
                    if api_response is None:
                        logger.warning(f"API call failed for train {train_no}")
                        stats["api_errors"] += 1
                        continue
                    
                    # Validate if journey actually started today
                    if self.railradar.is_journey_started(api_response, today):
                        # Create tracking record
                        self.db.create_journey(train_no, today)
                        stats["new_journeys_detected"] += 1
                        logger.info(f"✓ New journey detected and tracked: ({train_no}, {today})")
                    else:
                        logger.debug(f"Train {train_no} did not start today")
                
                except Exception as e:
                    logger.error(f"Error processing train {train_no}: {e}")
                    stats["api_errors"] += 1
                    continue
            
            logger.info(f"Phase 1 completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"Phase 1 execution failed: {e}")
            raise
