"""
Multi-Day Train Polling Script
Runs Phase 1 and Phase 2 for multi-day journey trains
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

from db.supabase_client import SupabaseDB
from api.railradar import RailRadarAPI
from services.phase1_new_journeys import Phase1NewJourneys
from services.phase2_ongoing_journeys import Phase2OngoingJourneys

# Load environment variables
load_dotenv()

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_file = log_dir / f"multi_day_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Execute multi-day train polling"""
    logger.info("=" * 70)
    logger.info("MULTI-DAY TRAIN POLLING STARTED")
    logger.info("=" * 70)
    
    start_time = datetime.now(timezone.utc)
    
    try:
        # Load configuration
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY_MULTI_DAY")
        MAX_FLAG_THRESHOLD = int(os.getenv("MAX_FLAG_THRESHOLD") or "8")
        TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
        
        # Validate environment variables
        if not all([SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY]):
            logger.error("Missing required environment variables!")
            logger.error("Required: SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY_MULTI_DAY")
            sys.exit(1)
        
        logger.info(f"Configuration loaded - Threshold: {MAX_FLAG_THRESHOLD}, Timezone: {TIMEZONE}")
        
        # Initialize clients
        logger.info("Initializing clients...")
        db = SupabaseDB(SUPABASE_URL, SUPABASE_KEY)
        railradar = RailRadarAPI(RAILRADAR_API_KEY)
        
        # Initialize processors
        phase1_processor = Phase1NewJourneys(db, railradar, TIMEZONE)
        phase2_processor = Phase2OngoingJourneys(db, railradar, MAX_FLAG_THRESHOLD)
        
        # Execute Phase 1: New Journey Detection
        logger.info("Starting Phase 1 - New Journey Detection...")
        phase1_stats = phase1_processor.execute("multiple_day")
        logger.info(f"Phase 1 completed: {phase1_stats}")
        
        # Execute Phase 2: Ongoing Journey Tracking
        logger.info("Starting Phase 2 - Ongoing Journey Tracking...")
        phase2_stats = phase2_processor.execute(journey_type="multiple_day")
        logger.info(f"Phase 2 completed: {phase2_stats}")
        
        # Calculate execution time
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # Summary
        logger.info("=" * 70)
        logger.info("MULTI-DAY TRAIN POLLING COMPLETED SUCCESSFULLY")
        logger.info(f"Execution Time: {duration:.2f} seconds")
        logger.info(f"Phase 1: {phase1_stats}")
        logger.info(f"Phase 2: {phase2_stats}")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"Polling failed: {e}", exc_info=True)
        logger.info("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
