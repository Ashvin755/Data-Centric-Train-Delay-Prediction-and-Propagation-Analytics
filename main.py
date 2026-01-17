"""
Rail Data Collection System - Main Flask Application

Provides endpoints for polling RailRadar API and collecting train delay data.
"""

import os
import logging
from datetime import datetime, timezone
from flask import Flask, jsonify
from dotenv import load_dotenv

from db.supabase_client import SupabaseDB
from api.railradar import RailRadarAPI
from services.phase1_new_journeys import Phase1NewJourneys
from services.phase2_ongoing_journeys import Phase2OngoingJourneys

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
RAILRADAR_API_KEY = os.getenv("RAILRADAR_API_KEY")
MAX_FLAG_THRESHOLD = int(os.getenv("MAX_FLAG_THRESHOLD", "6"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
ENDPOINT_TYPE = os.getenv("ENDPOINT_TYPE", "one_day")

# Validate required environment variables
if not all([SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY]):
    logger.error("Missing required environment variables!")
    logger.error("Please set: SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY")
    raise ValueError("Missing required environment variables")

# Initialize clients
logger.info("Initializing clients...")
db = SupabaseDB(SUPABASE_URL, SUPABASE_KEY)
railradar = RailRadarAPI(RAILRADAR_API_KEY)

# Initialize service processors
phase1_processor = Phase1NewJourneys(db, railradar, TIMEZONE)
phase2_processor = Phase2OngoingJourneys(db, railradar, MAX_FLAG_THRESHOLD)

logger.info(f"Application initialized for endpoint_type={ENDPOINT_TYPE}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoint_type": ENDPOINT_TYPE
    }), 200


@app.route("/poll/one-day", methods=["GET"])
def poll_one_day_trains():
    """
    Poll endpoint for one-day journey trains.
    
    Executes both Phase 1 (new journeys) and Phase 2 (ongoing journeys).
    """
    logger.info("=" * 70)
    logger.info("POLL ENDPOINT CALLED: /poll/one-day")
    logger.info("=" * 70)
    
    try:
        start_time = datetime.now(timezone.utc)
        
        # Phase 1: Detect new journeys starting today
        logger.info("Starting Phase 1...")
        phase1_stats = phase1_processor.execute("one_day")
        
        # Phase 2: Track ongoing journeys
        logger.info("Starting Phase 2...")
        phase2_stats = phase2_processor.execute()
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        response = {
            "status": "success",
            "timestamp": end_time.isoformat(),
            "execution_time_seconds": duration,
            "endpoint_type": "one_day",
            "phase1": phase1_stats,
            "phase2": phase2_stats
        }
        
        logger.info(f"Poll completed successfully in {duration:.2f}s")
        logger.info("=" * 70)
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Poll execution failed: {e}", exc_info=True)
        
        return jsonify({
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint_type": "one_day",
            "error": str(e)
        }), 500


@app.route("/poll/multi-day", methods=["GET"])
def poll_multi_day_trains():
    """
    Poll endpoint for multi-day journey trains.
    
    Executes both Phase 1 (new journeys) and Phase 2 (ongoing journeys).
    """
    logger.info("=" * 70)
    logger.info("POLL ENDPOINT CALLED: /poll/multi-day")
    logger.info("=" * 70)
    
    try:
        start_time = datetime.now(timezone.utc)
        
        # Phase 1: Detect new journeys starting today
        logger.info("Starting Phase 1...")
        phase1_stats = phase1_processor.execute("multiple_day")
        
        # Phase 2: Track ongoing journeys
        logger.info("Starting Phase 2...")
        phase2_stats = phase2_processor.execute()
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        response = {
            "status": "success",
            "timestamp": end_time.isoformat(),
            "execution_time_seconds": duration,
            "endpoint_type": "multiple_day",
            "phase1": phase1_stats,
            "phase2": phase2_stats
        }
        
        logger.info(f"Poll completed successfully in {duration:.2f}s")
        logger.info("=" * 70)
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Poll execution failed: {e}", exc_info=True)
        
        return jsonify({
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoint_type": "multiple_day",
            "error": str(e)
        }), 500


@app.route("/", methods=["GET"])
def index():
    """Root endpoint with API information."""
    return jsonify({
        "service": "Rail Data Collection System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "poll_one_day": "/poll/one-day",
            "poll_multi_day": "/poll/multi-day"
        },
        "endpoint_type": ENDPOINT_TYPE
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
