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
    level=logging.INFO,  # INFO for production, DEBUG for development
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
# Separate API keys for different endpoint types
RAILRADAR_API_KEY_ONE_DAY = os.getenv("RAILRADAR_API_KEY_ONE_DAY") or os.getenv("RAILRADAR_API_KEY")
RAILRADAR_API_KEY_MULTI_DAY = os.getenv("RAILRADAR_API_KEY_MULTI_DAY") or os.getenv("RAILRADAR_API_KEY")
MAX_FLAG_THRESHOLD = int(os.getenv("MAX_FLAG_THRESHOLD") or "6")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")
SERVICE_NAME = os.getenv("RENDER_SERVICE_NAME", "rail-data-collector")

# Validate required environment variables
if not all([SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY_ONE_DAY, RAILRADAR_API_KEY_MULTI_DAY]):
    logger.error("Missing required environment variables!")
    logger.error("Please set: SUPABASE_URL, SUPABASE_KEY, RAILRADAR_API_KEY_ONE_DAY, RAILRADAR_API_KEY_MULTI_DAY")
    raise ValueError("Missing required environment variables")

# Initialize clients
logger.info("Initializing clients...")
db = SupabaseDB(SUPABASE_URL, SUPABASE_KEY)
# Separate RailRadar API clients for different endpoint types
railradar_one_day = RailRadarAPI(RAILRADAR_API_KEY_ONE_DAY)
railradar_multi_day = RailRadarAPI(RAILRADAR_API_KEY_MULTI_DAY)

# Initialize service processors for one-day endpoint
phase1_processor_one_day = Phase1NewJourneys(db, railradar_one_day, TIMEZONE)
phase2_processor_one_day = Phase2OngoingJourneys(db, railradar_one_day, MAX_FLAG_THRESHOLD)

# Initialize service processors for multi-day endpoint
phase1_processor_multi_day = Phase1NewJourneys(db, railradar_multi_day, TIMEZONE)
phase2_processor_multi_day = Phase2OngoingJourneys(db, railradar_multi_day, MAX_FLAG_THRESHOLD)

logger.info(f"Application initialized - Rail Data Collector")
logger.info(f"Endpoints available: /poll/one-day, /poll/multi-day")
logger.info(f"Health check: /health")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "rail-data-collector",
        "endpoints": ["one-day", "multi-day"]
    }), 200


@app.route("/health2", methods=["GET"])
def health_check2():
    """Health check endpoint for monitoring."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "rail-data-collector",
        "endpoints": ["one-day", "multi-day"]
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
        
        # Phase 1: Detect new journeys starting today (using one-day API key)
        logger.info("Starting Phase 1 with one-day API key...")
        phase1_stats = phase1_processor_one_day.execute("one_day")
        
        # Phase 2: Track ongoing journeys of one_day type (using one-day API key)
        logger.info("Starting Phase 2 for one_day journeys with one-day API key...")
        phase2_stats = phase2_processor_one_day.execute(journey_type="one_day")
        
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
        
        # Phase 1: Detect new journeys starting today (using multi-day API key)
        logger.info("Starting Phase 1 with multi-day API key...")
        phase1_stats = phase1_processor_multi_day.execute("multiple_day")
        
        # Phase 2: Track ongoing journeys of multiple_day type (using multi-day API key)
        logger.info("Starting Phase 2 for multiple_day journeys with multi-day API key...")
        phase2_stats = phase2_processor_multi_day.execute(journey_type="multiple_day")
        
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
        "deployment": "Single service (free tier optimized)"
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
