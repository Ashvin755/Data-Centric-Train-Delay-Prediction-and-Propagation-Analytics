# Rail Data Collection System

Automated system for collecting Indian Railways train delay data using RailRadar API for ML-based delay prediction projects.

## Overview

This system periodically polls RailRadar APIs to track train journeys, detect completion, and persist station-level delay data in Supabase. It handles parallel journeys, manages journey lifecycles, and gracefully abandons unresponsive trains.

## Architecture

- **Backend**: Flask (Python)
- **Hosting**: Render (Free tier)
- **Database**: Supabase PostgreSQL
- **Scheduler**: UptimeRobot (external cron)
- **API**: RailRadar.in

## Features

✅ **Dual Journey Type Support**: Separate endpoints and API keys for one-day vs multi-day trains  
✅ **Parallel Journey Tracking**: Same train tracked across multiple dates simultaneously  
✅ **Automatic Lifecycle Management**: New detection → Ongoing tracking → Completion/Abandonment  
✅ **Idempotent Operations**: Duplicate-safe database inserts  
✅ **Flag-Based Abandonment**: Stops tracking trains after threshold exceeded  

## Project Structure

```
rail_data/
├── main.py                 # Flask application with polling endpoints
├── requirements.txt        # Python dependencies
├── render.yaml            # Deployment configuration
├── .env.example           # Environment variable template
├── api/
│   └── railradar.py       # RailRadar API client
├── db/
│   └── supabase_client.py # Database operations wrapper
├── services/
│   ├── phase1_new_journeys.py      # Detect trains starting today
│   └── phase2_ongoing_journeys.py  # Track incomplete journeys
├── supabase/
│   ├── schema.sql         # Database schema reference
│   └── migrations/        # SQL migration files
└── docs/
    ├── implementation_plan.md      # Technical specification
    └── chatgpt_plan_doc.md        # Initial requirements
```

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/arz03/rail_data.git
cd rail_data
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in credentials:

```bash
cp .env.example .env
```

Required variables:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `RAILRADAR_API_KEY` - RailRadar API key (or use separate keys)

### 4. Seed Train Data

Manually populate `train_info` table in Supabase with trains to track:

```sql
INSERT INTO train_info (train_no, train_name, journey_type, destination_station_code, journey_duration)
VALUES 
  (12137, 'Punjab Mail', 'one_day', 'NDLS', 1800),
  (12345, 'Saraighat Exp', 'multiple_day', 'HWH', 3000);
```

### 5. Run Locally

```bash
python main.py
```

Access endpoints:
- Health: http://localhost:5000/health
- One-day poll: http://localhost:5000/poll/one-day
- Multi-day poll: http://localhost:5000/poll/multi-day

## Deployment

### Deploy to Render

1. Push code to GitHub
2. Connect Render to your repository
3. Render will detect `render.yaml` and create two services automatically
4. Set secret environment variables in Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `RAILRADAR_API_KEY` (different key for each service)

### Configure UptimeRobot

Set up two HTTP monitors:

**Monitor 1: One-Day Trains**
- URL: `https://rail-data-one-day.onrender.com/poll/one-day`
- Interval: **5 hours** (300 minutes)
- Method: GET

**Monitor 2: Multi-Day Trains**
- URL: `https://rail-data-multi-day.onrender.com/poll/multi-day`
- Interval: **12 hours** (720 minutes)
- Method: GET

## Endpoints

### `GET /health`
Health check for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-17T10:30:00Z",
  "endpoint_type": "one_day"
}
```

### `GET /poll/one-day`
Execute polling for one-day journey trains.

**Response:**
```json
{
  "status": "success",
  "timestamp": "2026-01-17T10:30:15Z",
  "execution_time_seconds": 12.5,
  "endpoint_type": "one_day",
  "phase1": {
    "trains_checked": 5,
    "new_journeys_detected": 2,
    "api_errors": 0,
    "already_tracked": 3
  },
  "phase2": {
    "journeys_tracked": 8,
    "completed": 2,
    "abandoned": 1,
    "still_ongoing": 5,
    "api_errors": 0
  }
}
```

### `GET /poll/multi-day`
Execute polling for multi-day journey trains.

## How It Works

### Phase 1: New Journey Detection

1. Get today's date (IST timezone)
2. Fetch all trains with matching `journey_type` from `train_info`
3. For each train:
   - Check if `(train_no, today)` exists in `journey_status_flags`
   - If not, call RailRadar API with `journeyDate=today`
   - If journey confirmed started, create tracking record with `flag=0`

### Phase 2: Ongoing Journey Tracking

1. Fetch all journeys where `is_completed=false AND is_abandoned=false`
2. For each ongoing journey:
   - Call RailRadar API with original `journey_date`
   - Compare `currentLocation.stationCode` with `destination_station_code`
   - **If completed**: Extract route data, insert into `rail_data`, mark `is_completed=true`
   - **If ongoing**: Increment `flag`, update `last_checked_at`
   - **If `flag > 6`**: Mark `is_abandoned=true` (no data stored)

### Parallel Journey Handling

Same train can have multiple active journeys:

| train_no | journey_date | flag | is_completed | Status |
|----------|-------------|------|--------------|---------|
| 12345 | 2026-01-15 | 3 | false | Multi-day journey from Jan 15 |
| 12345 | 2026-01-16 | 2 | false | Started yesterday |
| 12345 | 2026-01-17 | 0 | false | Just detected today |

Each journey tracked independently via composite key `(train_no, journey_date)`.

## Database Schema

### `train_info`
Static train metadata (manually seeded).

| Column | Type | Description |
|--------|------|-------------|
| train_no | integer | Unique train number |
| train_name | varchar | Train name |
| journey_type | varchar | 'one_day' or 'multiple_day' |
| destination_station_code | varchar | Final destination code |

### `journey_status_flags`
Journey lifecycle tracking.

| Column | Type | Description |
|--------|------|-------------|
| train_no | integer | Train number |
| journey_date | date | Journey start date |
| flag | integer | Poll attempt counter |
| is_completed | boolean | Journey finished successfully |
| is_abandoned | boolean | Exceeded threshold, stopped tracking |
| last_checked_at | timestamp | Last API poll time |

### `rail_data`
Final immutable dataset (one row per station).

| Column | Type | Description |
|--------|------|-------------|
| train_no | integer | Train number |
| journey_date | date | Journey start date |
| station_code | varchar | Station code |
| scheduled_arrival/departure | integer | Unix timestamps |
| actual_arrival/departure | integer | Unix timestamps |
| delay_arrival/departure_minutes | integer | Delay in minutes |
| distance_from_origin_km | numeric | Distance from source |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Supabase project URL | Required |
| `SUPABASE_KEY` | Supabase API key | Required |
| `RAILRADAR_API_KEY` | RailRadar API key | Required |
| `MAX_FLAG_THRESHOLD` | Max polls before abandoning | 6 |
| `TIMEZONE` | Journey date timezone | Asia/Kolkata |
| `ENDPOINT_TYPE` | 'one_day' or 'multiple_day' | one_day |

### API Rate Limits

- RailRadar: **1000 calls/month per API key**
- Strategy: Separate keys for one-day vs multi-day endpoints
- Estimated usage: ~750-900 calls/month per endpoint

## Monitoring

### Logs

All operations logged with timestamps:
- Journey detection/creation
- API call successes/failures
- Flag increments
- Completion/abandonment events
- Database operations

### Health Checks

- Render's built-in health check pings `/health` every 5 minutes
- UptimeRobot monitors track endpoint availability

## Known Limitations

⚠️ **Selection Bias**: Abandoned journeys (severely delayed trains) not included in dataset  
⚠️ **No Backfill**: Cannot collect historical data before deployment  
⚠️ **API Dependency**: RailRadar downtime affects data collection  
⚠️ **Timezone Assumption**: All dates use IST (Indian Standard Time)  

See [docs/implementation_plan.md](docs/implementation_plan.md) for detailed technical specification.

## Development

### Run Tests

```bash
# (TODO: Add tests)
pytest tests/
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SUPABASE_URL=https://xxxxx.supabase.co
export SUPABASE_KEY=your_key_here
export RAILRADAR_API_KEY=rr_xxxxxxxx

# Run Flask app
python main.py
```

### Database Migrations

Migrations are in `supabase/migrations/`. Apply via Supabase dashboard or CLI:

```bash
supabase db push
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is for educational/research purposes.

## Acknowledgments

- RailRadar.in for providing train tracking API
- Supabase for database hosting
- Render for free tier hosting

---

**Maintained by**: [@arz03](https://github.com/arz03)  
**Last Updated**: January 17, 2026
