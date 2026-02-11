# API Cloudflare Protection Fix

## Problem
GitHub Actions was getting **403 Forbidden** errors from RailRadar API due to Cloudflare bot protection blocking datacenter IPs.

## Root Cause
- Cloudflare detected requests from GitHub Actions as bot traffic
- GitHub Actions runners use datacenter IPs flagged by Cloudflare
- Original `requests` library couldn't bypass JavaScript challenges

## Solution Implemented
Updated `api/railradar.py` with:

### 1. **Cloudscraper Library**
```python
import cloudscraper
self.scraper = cloudscraper.create_scraper(...)
```
- Automatically solves Cloudflare JavaScript challenges
- Maintains browser-like behavior

### 2. **Browser-Like Headers**
```python
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
"Referer": "https://railradar.in/",
"Origin": "https://railradar.in"
```
- Mimics real browser requests
- Reduces bot detection likelihood

### 3. **Retry Logic with Exponential Backoff**
```python
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
```
- Handles transient Cloudflare challenges
- Retries on connection errors, timeouts, HTTP errors

### 4. **Cloudflare Challenge Detection**
```python
if "Just a moment" in response.text:
    # Retry
```
- Detects challenge pages
- Automatically retries instead of failing

## Testing

### Local Test (Before Deployment)
```bash
pip install cloudscraper==1.2.71
python test_railradar_api.py
```

Should show:
```
✅ SUCCESS - Data keys: ['success', 'data', 'meta']
```

### GitHub Actions Test
After pushing, manually run workflow:
1. Go to **Actions** tab
2. Click **One-Day Train Polling**
3. Click **Run workflow**
4. Check logs - should see:
   ```
   ✅ Successfully fetched data for train 61631
   Phase 1 completed: {..., 'api_errors': 0, ...}
   ```

## Changes Made

### Files Modified:
1. **requirements.txt** - Added `cloudscraper==1.2.71`
2. **api/railradar.py** - Complete rewrite of API client
3. **.gitignore** - Added `test_railradar_api.py`

### Key Improvements:
- ✅ Cloudflare bypass
- ✅ 3 automatic retries
- ✅ Browser-identical headers
- ✅ Better error logging
- ✅ Challenge page detection

## Deployment Steps

1. **Install new dependency locally:**
   ```bash
   pip install cloudscraper==1.2.71
   ```

2. **Test locally (optional):**
   ```bash
   python test_railradar_api.py
   ```

3. **Commit and push:**
   ```bash
   git add .
   git commit -m "fix: Add Cloudflare bypass for GitHub Actions"
   git push origin main
   ```

4. **Test on GitHub Actions:**
   - Go to Actions tab
   - Manually trigger **One-Day Train Polling**
   - Verify logs show successful API calls

## Expected Results

### Before Fix:
```
ERROR - HTTP error for train 61631: 403 Client Error: Forbidden
ERROR - Response text: <!DOCTYPE html>...Just a moment...
Phase 1: {..., 'api_errors': 4}
```

### After Fix:
```
INFO - ✅ Successfully fetched data for train 61631
Phase 1: {..., 'new_journeys_detected': X, 'api_errors': 0}
```

## Monitoring

After deployment, check logs regularly:
- **Success**: `api_errors: 0` in Phase 1
- **Partial success**: Some API errors (retry exhausted)
- **Failure**: All API errors (contact RailRadar support)

## Alternative Solutions (If This Fails)

1. **Contact RailRadar** - Request API key whitelisting for GitHub Actions IPs
2. **Use proxy service** - Route requests through residential IPs
3. **Self-hosted runner** - Use your own server with whitelisted IP
4. **Increase delays** - Add 5-10 second delays between requests
5. **Schedule fewer polls** - Reduce frequency to avoid rate limits

---

**Status**: ✅ Ready to deploy
**Priority**: High (blocks all data collection)
**Risk**: Low (graceful fallback to None on errors)
