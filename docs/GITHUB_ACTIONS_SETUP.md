# GitHub Actions Setup Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Push Code to GitHub

```bash
# Remove old check files
rm check_fk.py check_existing_fk.py

# Add all changes
git add .
git commit -m "feat: Convert to GitHub Actions with automated polling"
git push origin main
```

### Step 2: Configure GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add each:

| Secret Name | Value |
|------------|-------|
| `SUPABASE_URL` | `https://c********g.supabase.co` |
| `SUPABASE_KEY` | Your Supabase anon key |
| `RAILRADAR_API_KEY_ONE_DAY` | `rr_l*******************i` |
| `RAILRADAR_API_KEY_MULTI_DAY` | `rr_b*******************8` |

### Step 3: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. You should see two workflows:
   - ✅ **One-Day Train Polling** (runs every 5 hours)
   - ✅ **Multi-Day Train Polling** (runs every 12 hours)
3. Click **Enable workflow** if prompted

### Step 4: Test Manual Run

1. Go to **Actions** tab
2. Click **One-Day Train Polling** workflow
3. Click **Run workflow** → **Run workflow** button
4. Wait ~2 minutes for completion
5. Click the run to see logs

---

## 📋 What's Changed

### Removed:
- ❌ Flask web server (`main.py` no longer needed)
- ❌ `gunicorn` dependency
- ❌ `render.yaml` deployment config
- ❌ UptimeRobot requirement

### Added:
- ✅ `run_one_day_poll.py` - Standalone script for one-day trains
- ✅ `run_multi_day_poll.py` - Standalone script for multi-day trains
- ✅ `.github/workflows/one-day-poll.yml` - Scheduled workflow (every 5h)
- ✅ `.github/workflows/multi-day-poll.yml` - Scheduled workflow (every 12h)
- ✅ File logging to `logs/` directory

---

## 📊 Workflow Schedules

### One-Day Train Polling
- **Frequency**: Every 5 hours
- **Cron**: `0 */5 * * *`
- **Times (UTC)**: 00:00, 05:00, 10:00, 15:00, 20:00
- **Times (IST)**: 05:30, 10:30, 15:30, 20:30, 01:30

### Multi-Day Train Polling
- **Frequency**: Every 12 hours
- **Cron**: `0 */12 * * *`
- **Times (UTC)**: 00:00, 12:00
- **Times (IST)**: 05:30, 17:30

---

## 📁 Log Files

Logs are stored as GitHub Actions artifacts:
- **Location**: Actions → Workflow Run → Artifacts
- **Retention**: 30 days
- **Format**: `one_day_YYYYMMDD.log` or `multi_day_YYYYMMDD.log`
- **Download**: Click artifact name to download ZIP

Each log file contains:
- Timestamp of execution
- Phase 1 statistics (new journeys detected)
- Phase 2 statistics (ongoing journeys tracked)
- Execution time
- Any errors with stack traces

---

## 🔍 Monitoring

### View Workflow Status
1. Go to **Actions** tab
2. See all runs with status (✅ success, ❌ failed)
3. Click any run to see detailed logs

### Check Logs
1. Click on a workflow run
2. Click **poll-one-day-trains** or **poll-multi-day-trains** job
3. Expand steps to see output
4. Download artifact for full log file

### Email Notifications
GitHub will email you if workflows fail. Configure in:
- **Settings** → **Notifications** → **Actions**

---

## 🧪 Testing Locally

Before pushing, test locally:

```bash
# Activate virtual environment
venv/scripts/activate

# Test one-day polling
python run_one_day_poll.py

# Test multi-day polling
python run_multi_day_poll.py

# Check logs
cat logs/one_day_20260121.log
```

---

## 💰 Cost Analysis

### GitHub Actions Free Tier:
- **2000 minutes/month** for private repos
- **Unlimited** for public repos

### Your Usage:
- One-day: ~144 runs/month × 2 min = **288 minutes**
- Multi-day: ~60 runs/month × 3 min = **180 minutes**
- **Total: ~470 minutes/month** ✅ Well under limit

---

## ⚙️ Configuration

### Change Polling Frequency

Edit `.github/workflows/*.yml` files:

```yaml
schedule:
  # Every 3 hours instead of 5
  - cron: '0 */3 * * *'
  
  # Every 6 hours instead of 12
  - cron: '0 */6 * * *'
  
  # Specific times (e.g., 06:00 and 18:00 UTC)
  - cron: '0 6,18 * * *'
```

### Change MAX_FLAG_THRESHOLD

Edit workflow YAML files:
```yaml
env:
  MAX_FLAG_THRESHOLD: 5  # Change this value
```

---

## 🐛 Troubleshooting

### Workflow not running?
- Check if Actions are enabled in repo settings
- Verify cron syntax at https://crontab.guru/
- GitHub Actions have ~5 minute delay tolerance

### Secrets not working?
- Ensure secret names match exactly (case-sensitive)
- Re-create secrets if needed
- Check workflow logs for "variable not set" errors

### Python errors?
- Check requirements.txt is up to date
- Verify Python version matches (3.12)
- Test locally first

---

## 📦 Migration Checklist

- [ ] Push code to GitHub
- [ ] Add all 4 secrets in GitHub
- [ ] Enable workflows in Actions tab
- [ ] Test manual run of both workflows
- [ ] Verify logs are uploaded as artifacts
- [ ] Check Supabase for new journey entries
- [ ] Monitor for 24 hours
- [ ] Delete Render service (if deployed)
- [ ] Remove UptimeRobot monitors

---

## ✅ Benefits of GitHub Actions

1. **100% Free** - No hosting costs
2. **Native Scheduling** - No external cron service
3. **Built-in Logs** - Persistent for 30 days
4. **Version Control** - Workflow changes tracked in git
5. **Simple Architecture** - Just Python scripts
6. **Manual Triggers** - Run anytime from UI
7. **Email Alerts** - Automatic failure notifications

---

**Ready to deploy!** Push your code and configure secrets to start automated polling. 🚀
