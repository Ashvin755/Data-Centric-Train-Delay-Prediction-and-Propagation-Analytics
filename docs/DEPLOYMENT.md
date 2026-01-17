# Render Deployment Guide

This guide walks you through deploying the Rail Data Collection System to Render's free tier using a **single service** approach optimized for cost efficiency.

## Prerequisites

- ✅ GitHub account
- ✅ Render account (sign up at https://render.com)
- ✅ Supabase project with tables created
- ✅ Two RailRadar API keys (one for each endpoint type)
- ✅ Code pushed to GitHub repository

---

## Architecture Overview

**Single Service Design** (Free Tier Optimized):
- One Render web service hosts both endpoints
- `/poll/one-day` uses `RAILRADAR_API_KEY_ONE_DAY`
- `/poll/multi-day` uses `RAILRADAR_API_KEY_MULTI_DAY`
- Each API key gets 1000 calls/month = 2000 total calls/month
- Uses only 750 hours/month (within free tier limit)

---

## Step 1: Prepare Repository

### 1.1 Push to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Rail data collection system"

# Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/rail_data.git
git branch -M main
git push -u origin main
```

### 1.2 Verify Files

Ensure these files are in your repository:
- ✅ `main.py` - Flask application
- ✅ `requirements.txt` - Python dependencies
- ✅ `render.yaml` - Deployment configuration
- ✅ `.gitignore` - Excludes .env, venv, __pycache__
- ✅ All code in `api/`, `db/`, `services/` directories

**Important**: Never commit `.env` file with secrets!

---

## Step 2: Deploy to Render

### Using render.yaml (Blueprint) - RECOMMENDED

1. **Go to Render Dashboard**: https://dashboard.render.com

2. **Click "New +"** → **"Blueprint"**

3. **Connect GitHub Repository**:
   - Click "Connect account" if first time
   - Search for your `rail_data` repository
   - Click "Connect"

4. **Configure Blueprint**:
   - Render will detect `render.yaml`
   - It will show 1 service: `rail-data-collector`
   - Click "Apply"

5. **Set Environment Variables**:
   
   Navigate to service → Environment tab → Add variables:
   
   ```
   RAILRADAR_API_KEY_ONE_DAY=rr_lx1i9s8amh6n5fg86wb92gpvo3vjmv9i
   RAILRADAR_API_KEY_MULTI_DAY=rr_b9mavijtcqg6b47m810pop9n2k0t1lt8
   SUPABASE_URL=https://cjnceqnctjpcqinvxfwg.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

6. **Deploy**: Render will automatically build and deploy the service

---

### Alternative: Manual Service Creation

If blueprint doesn't work, create service manually:

1. **Dashboard** → **New +** → **Web Service**
2. **Connect Repository**: Select `rail_data`
3. **Configure**:
   - **Name**: `rail-data-collector`
   - **Region**: Choose closest to India (Singapore recommended)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --bind 0.0.0.0:$PORT --timeout 120`
   - **Plan**: `Free`
4. **Environment Variables**:
   ```
   RAILRADAR_API_KEY_ONE_DAY=rr_lx1i9s8amh6n5fg86wb92gpvo3vjmv9i
   RAILRADAR_API_KEY_MULTI_DAY=rr_b9mavijtcqg6b47m810pop9n2k0t1lt8
   SUPABASE_URL=https://cjnceqnctjpcqinvxfwg.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   MAX_FLAG_THRESHOLD=6
   TIMEZONE=Asia/Kolkata
   FLASK_ENV=production
   ```
5. **Health Check Path**: `/health`
6. **Create Web Service**

---

## Step 3: Verify Deployment

### 3.1 Check Service Status

Wait 5-10 minutes for build and deployment. You'll see:
- ✅ Build logs
- ✅ Deploy logs
- ✅ Service running (green indicator)

### 3.2 Test Endpoints

Get your service URL from Render dashboard (e.g., `https://rail-data-collector.onrender.com`)

**Test Health Check**:
```bash
curl https://rail-data-collector.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-17T14:30:00",
  "service": "rail-data-collector",
  "endpoints": ["one-day", "multi-day"]
}
```

**Test Both Polling Endpoints** (will take 30-60 seconds each):
```bash
# Test one-day endpoint (uses RAILRADAR_API_KEY_ONE_DAY)
curl https://rail-data-collector.onrender.com/poll/one-day

# Test multi-day endpoint (uses RAILRADAR_API_KEY_MULTI_DAY)
curl https://rail-data-collector.onrender.com/poll/multi-day
```

Expected response:
```json
{
  "status": "success",
  "timestamp": "2026-01-17T14:30:00Z",
  "execution_time_seconds": 32.5,
  "endpoint_type": "one_day",
  "phase1": {
    "trains_checked": 4,
    "new_journeys_detected": 2,
    "already_tracked": 1,
    "api_errors": 0
  },
  "phase2": {
    "journeys_tracked": 3,
    "completed": 1,
    "abandoned": 0,
    "still_ongoing": 2,
    "api_errors": 0
  }
}
```

---

## Step 4: Configure UptimeRobot Cron

### 4.1 Sign Up
Go to https://uptimerobot.com and create free account.

### 4.2 Create Monitor for One-Day Trains

1. **Dashboard** → **Add New Monitor**
2. **Monitor Type**: `HTTP(s)`
3. **Friendly Name**: `Rail Data - One Day Trains`
4. **URL**: `https://rail-data-collector.onrender.com/poll/one-day`
5. **Monitoring Interval**: `Every 5 hours (300 minutes)`
   - Free tier allows: 5, 10, 15, 30, 60 minutes... up to custom intervals
6. **HTTP Method**: `GET`
7. **Alert Contacts**: Add your email
8. **Create Monitor**

### 4.3 Create Monitor for Multi-Day Trains

1. **Add New Monitor**
2. **Monitor Type**: `HTTP(s)`
3. **Friendly Name**: `Rail Data - Multi Day Trains`
4. **URL**: `https://rail-data-collector.onrender.com/poll/multi-day`
5. **Monitoring Interval**: `Every 12 hours (720 minutes)`
6. **HTTP Method**: `GET`
7. **Create Monitor**

### 4.4 Verify Monitors

- Check "Last Check Time" updates every interval
- Verify "Status" shows "Up (200)"
- Check Supabase tables for new data

**Note**: Both monitors hit the same Render service but different endpoints. Each endpoint uses its own dedicated RailRadar API key.

---

## Step 5: Monitor & Maintain

### 5.1 View Logs

In Render dashboard:
- Select service → **Logs** tab
- Filter by date/time
- Watch for errors or API failures

### 5.2 Check Database

In Supabase dashboard:
```sql
-- Check new journeys created today
SELECT * FROM journey_status_flags 
WHERE journey_date = CURRENT_DATE 
ORDER BY created_at DESC;

-- Check completed journeys
SELECT * FROM journey_status_flags 
WHERE is_completed = true 
ORDER BY last_checked_at DESC 
LIMIT 10;

-- Check rail_data entries
SELECT train_no, journey_date, COUNT(*) as stations
FROM rail_data 
GROUP BY train_no, journey_date 
ORDER BY journey_date DESC;
```

### 5.3 Monitor API Usage

Track your RailRadar API calls:
- Free tier: 1000 calls/month per key
- View logs for API call counts
- Consider this pattern:
  - Phase 1: 1 call per train per day
  - Phase 2: Multiple calls per journey until completion

### 5.4 Render Free Tier Limits

✅ **Single Service Approach Benefits**:
- Uses only 750 hours/month (within free tier)
- No service spin-down issues when actively used
- First request after spin-down takes 30-60 seconds (cold start)
- Both endpoints available from single service URL

**No additional action needed** - your setup is optimized for free tier!

---

## Step 6: Troubleshooting

### Service Won't Start

**Check build logs** for missing dependencies:
```bash
# In Render logs, look for:
ERROR: Could not find a version that satisfies the requirement...
```

**Solution**: Verify `requirements.txt` has all dependencies with correct versions.

### 401 Unauthorized from RailRadar

**Check**:
- RAILRADAR_API_KEY is set correctly in Render environment
- API key hasn't expired
- Key has sufficient quota

### Database Connection Failed

**Check**:
- SUPABASE_URL is correct (format: `https://xxx.supabase.co`)
- SUPABASE_KEY is the `anon public` key (not service_role)
- Supabase project is not paused (free tier pauses after inactivity)

### Timeout Errors (504)

Render free tier has 60s request timeout. If your polling takes longer:

**Solution**: Add `--timeout 120` to gunicorn command in render.yaml:
```yaml
startCommand: gunicorn main:app --bind 0.0.0.0:$PORT --timeout 120
```

### No Data in Supabase

**Check**:
1. Health endpoint works: `/health` returns 200
2. Poll endpoint returns success
3. Phase 1 stats show `new_journeys_detected > 0`
4. Check logs for database errors
5. Verify train_info table has trains with correct journey_type

---

## Environment Variables Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| RAILRADAR_API_KEY_ONE_DAY | Yes | `rr_lx1i9s8amh6n5fg86wb92gpvo3vjmv9i` | RailRadar API key for one-day trains |
| RAILRADAR_API_KEY_MULTI_DAY | Yes | `rr_b9mavijtcqg6b47m810pop9n2k0t1lt8` | RailRadar API key for multi-day trains |
| SUPABASE_URL | Yes | `https://xxx.supabase.co` | Supabase project URL |
| SUPABASE_KEY | Yes | `eyJhbG...` | Supabase anon/public key |
| MAX_FLAG_THRESHOLD | No | `6` (default) | Max polls before abandoning journey |
| TIMEZONE | No | `Asia/Kolkata` (default) | Timezone for journey dates |
| FLASK_ENV | No | `production` | Flask environment |
| PORT | Auto | Set by Render | Service port (don't set manually) |

**Note**: Using separate API keys allows 2000 total calls/month (1000 per key) instead of just 1000.

---

## Production Checklist

Before going live:

- [ ] Service deployed and healthy
- [ ] Environment variables set correctly (both API keys)
- [ ] Health endpoint returns 200
- [ ] Both poll endpoints tested manually
- [ ] UptimeRobot monitors configured (same service URL, different paths)
- [ ] First poll completes successfully for both endpoints
- [ ] Data appears in Supabase tables
- [ ] Logs show no errors
- [ ] Verify correct API key used for each endpoint
- [ ] Set up email alerts in UptimeRobot
- [ ] Document service URL for reference

---

## Cost Considerations

### Render Free Tier
- ✅ 750 hours/month - Single service uses only 720 hours (within limit)
- ✅ No spin-down issues with regular UptimeRobot calls
- ✅ Optimized for free tier usage

### RailRadar API
- ✅ 2000 calls/month total (1000 per key)
- Each endpoint uses dedicated API key
- Monitor usage via application logs
- Estimated usage: ~750 calls/month (one-day) + ~900 calls/month (multi-day)

**Benefits of Dual API Keys**:
- Double the API quota (2000 vs 1000 calls/month)
- Isolates usage per endpoint type
- Better tracking and monitoring

---

## Next Steps

1. ✅ Deploy services to Render
2. ✅ Configure UptimeRobot monitors
3. ✅ Wait for first scheduled poll
4. ✅ Verify data in Supabase
5. 🔄 Monitor for 2-3 days
6. 📊 Analyze journey completion rates
7. 🎯 Adjust MAX_FLAG_THRESHOLD if needed
8. 🚀 Scale by adding more trains to train_info

---

**Need Help?**
- Render Documentation: https://render.com/docs
- UptimeRobot Support: https://uptimerobot.com/help
- Check application logs in Render dashboard
- Verify Supabase tables and RLS policies
