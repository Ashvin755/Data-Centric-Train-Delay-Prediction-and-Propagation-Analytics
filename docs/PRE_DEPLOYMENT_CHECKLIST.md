# Pre-Deployment Checklist

Complete these steps before deploying to Render.

## ✅ Code Implementation Status

### Core Features
- [x] Flask application with dual endpoints (`/poll/one-day`, `/poll/multi-day`)
- [x] Supabase database client wrapper
- [x] RailRadar API client (handles both response formats)
- [x] Phase 1: New journey detection
- [x] Phase 2: Ongoing journey tracking with flag-based abandonment
- [x] Health check endpoint
- [x] Comprehensive logging
- [x] Error handling and graceful degradation

### Configuration Files
- [x] `requirements.txt` - All dependencies including gunicorn
- [x] `render.yaml` - Deployment configuration for both services
- [x] `.env.example` - Template for environment variables
- [x] `.gitignore` - Excludes secrets and virtual environment
- [x] `README.md` - Setup and usage instructions
- [x] `DEPLOYMENT.md` - Step-by-step Render deployment guide

### Testing Results
- [x] ✅ `/health` endpoint - Returns 200 OK
- [x] ✅ `/poll/one-day` endpoint - Detected 1 new journey, tracking 1 ongoing
- [x] ✅ `/poll/multi-day` endpoint - Detected 6 new journeys, tracking 7 ongoing
- [x] ✅ Database operations - journey_status_flags entries created
- [x] ✅ API integration - Both RailRadar response formats handled correctly

---

## 📋 Pre-Push Checklist

### 1. Environment Variables

**Verify your `.env` file has** (DO NOT commit this file):
```bash
SUPABASE_URL=https://cnxkhvzrfjbyjsttyjam.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
RAILRADAR_API_KEY=rr_xxxxxxxxxxxxxxxxxxxxxxxx
MAX_FLAG_THRESHOLD=6
TIMEZONE=Asia/Kolkata
FLASK_ENV=production
```

**Verify `.gitignore` excludes `.env`**:
```bash
# Check if .env is ignored
git status --ignored | grep .env
# Should show: .env
```

### 2. Database Schema

**Verify Supabase tables exist**:
- [ ] `train_info` - Contains your trains with `journey_type` field
- [ ] `journey_status_flags` - Empty or has test data
- [ ] `rail_data` - Empty or has test data

**Verify train data**:
```sql
-- Should show at least 4 one_day trains and 6 multiple_day trains
SELECT journey_type, COUNT(*) 
FROM train_info 
GROUP BY journey_type;
```

### 3. Code Quality

**Run final tests**:
```bash
# Activate virtual environment
venv/scripts/activate

# Start Flask app
python main.py &

# Test endpoints
curl http://localhost:5000/health
curl http://localhost:5000/poll/one-day
curl http://localhost:5000/poll/multi-day

# Stop Flask
# Press Ctrl+C or kill the process
```

**Check for errors**:
- [ ] No Python exceptions in logs
- [ ] All API calls return 200 OK
- [ ] Database queries execute successfully
- [ ] JSON responses are valid

### 4. Git Repository

**Commit all changes**:
```bash
# Check status
git status

# Add all files (excluding .env due to .gitignore)
git add .

# Commit
git commit -m "feat: Complete rail data collection system with dual endpoints"

# Verify .env is NOT tracked
git ls-files | grep .env
# Should NOT show .env (only .env.example)
```

**Push to GitHub**:
```bash
# Create GitHub repository first, then:
git remote add origin https://github.com/YOUR_USERNAME/rail_data.git
git branch -M main
git push -u origin main
```

---

## 🚀 Render Deployment Steps

### Phase 1: Initial Deployment

1. **Go to Render**: https://dashboard.render.com
2. **Connect GitHub**: Link your repository
3. **Deploy Blueprint**: Use `render.yaml` to deploy both services
4. **Set Environment Variables** (CRITICAL):
   - `RAILRADAR_API_KEY` - Your actual API key
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_KEY` - Your Supabase anon/public key
5. **Wait for Build**: 5-10 minutes for initial deployment

### Phase 2: Verification

1. **Check Service Status**: Should show "Live" with green indicator
2. **Test Health Endpoints**:
   ```bash
   curl https://rail-data-one-day.onrender.com/health
   curl https://rail-data-multi-day.onrender.com/health
   ```
3. **Test Poll Endpoints** (takes 30-60 seconds):
   ```bash
   curl https://rail-data-one-day.onrender.com/poll/one-day
   curl https://rail-data-multi-day.onrender.com/poll/multi-day
   ```
4. **Verify Database**: Check Supabase for new `journey_status_flags` entries

### Phase 3: UptimeRobot Setup

1. **Sign up**: https://uptimerobot.com
2. **Create Monitor 1**:
   - URL: `https://rail-data-one-day.onrender.com/poll/one-day`
   - Interval: Every 5 hours (300 minutes)
3. **Create Monitor 2**:
   - URL: `https://rail-data-multi-day.onrender.com/poll/multi-day`
   - Interval: Every 12 hours (720 minutes)

---

## ⚠️ Important Notes

### Render Free Tier Limitations

**Problem**: Free tier gives 750 hours/month per service. You have 2 services = 1500 hours needed.

**Solutions**:
1. **Single Service Approach** (Recommended for free tier):
   - Deploy only one service
   - Use `ENDPOINT_TYPE` environment variable to switch
   - Configure both UptimeRobot monitors to hit same service but different endpoints

2. **Dual Service Approach** (Requires paid plan):
   - Deploy both services as configured
   - Upgrade at least one service to Hobby plan ($7/month)

3. **Alternative Platforms**:
   - Railway.app - Better free tier
   - Fly.io - Free tier with good limits
   - Heroku - Paid but reliable

### API Usage Monitoring

**Your current usage estimate**:
- One-day trains: ~150 calls/month (Phase 1) + ~600 calls/month (Phase 2) = **750 calls/month**
- Multi-day trains: ~300 calls/month (Phase 1) + ~600 calls/month (Phase 2) = **900 calls/month**
- **Total**: ~1650 calls/month

⚠️ **This EXCEEDS the 1000 calls/month free limit!**

**Mitigation strategies**:
1. Use separate API keys for each endpoint (1000 calls each)
2. Reduce polling frequency (e.g., 6h instead of 5h for one-day trains)
3. Lower `MAX_FLAG_THRESHOLD` from 6 to 4 (abandon journeys faster)
4. Start with fewer trains in `train_info` table

---

## 🎯 Go-Live Decision Tree

### Option A: Free Tier Single Service
```
✅ Best for: Testing, low usage, limited budget
- Deploy only rail-data-one-day service
- Use separate API keys if possible
- Monitor API usage closely
- Accept service spin-down delays (cold starts)
```

### Option B: Paid Hobby Plan
```
✅ Best for: Production use, reliability
- Deploy both services
- Upgrade one to Hobby ($7/month)
- No spin-down delays
- Better performance
```

### Option C: Alternative Platform
```
✅ Best for: More generous free tiers
- Railway.app: $5 credit/month free
- Fly.io: Better free tier limits
- Similar deployment process
```

---

## 📊 Post-Deployment Monitoring

### Day 1-3: Initial Validation
- [ ] Check logs hourly for errors
- [ ] Verify new journeys are detected daily
- [ ] Confirm Phase 2 tracking works
- [ ] Monitor API call counts
- [ ] Check for abandoned journeys (flag > 6)

### Week 1: Stability Assessment
- [ ] Review completion rates (should be >80%)
- [ ] Check abandonment rates (should be <20%)
- [ ] Verify no database errors
- [ ] Confirm UptimeRobot monitors working
- [ ] Assess API usage vs free tier limits

### Month 1: Data Quality Review
- [ ] Analyze `rail_data` entries for completeness
- [ ] Review journey lifecycle durations
- [ ] Check for data gaps or anomalies
- [ ] Adjust `MAX_FLAG_THRESHOLD` if needed
- [ ] Plan capacity scaling (add more trains)

---

## 🆘 Troubleshooting Quick Reference

| Issue | Likely Cause | Solution |
|-------|-------------|----------|
| 401 Unauthorized | Wrong API key | Check RAILRADAR_API_KEY in Render env vars |
| Database connection error | Wrong Supabase credentials | Verify SUPABASE_URL and SUPABASE_KEY |
| Timeout (504) | Render 60s limit | Add `--timeout 120` to gunicorn command |
| No journeys detected | Trains not running today | Check train schedules, wait for next day |
| Service won't start | Missing dependencies | Check build logs, verify requirements.txt |
| Cold start delays | Free tier spin-down | Upgrade to Hobby plan or accept delays |

---

## ✅ Final Checklist Before Deploy

- [ ] `.env` file configured locally (NOT committed)
- [ ] `.gitignore` excludes `.env`
- [ ] All code committed to Git
- [ ] Pushed to GitHub repository
- [ ] Supabase tables created and populated with trains
- [ ] RailRadar API key valid and has quota
- [ ] Local testing successful (both endpoints work)
- [ ] `render.yaml` configured correctly
- [ ] Environment variables documented
- [ ] Deployment guide reviewed
- [ ] Decision made on free vs paid tier
- [ ] UptimeRobot account created

---

**Ready to deploy?** Follow the steps in `DEPLOYMENT.md`!

**Questions?** Check the troubleshooting section or review logs in Render dashboard.
