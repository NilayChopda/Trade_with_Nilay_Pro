# 🚀 Cloud Deployment Guide - True 24/7 Hosting

## Quick Summary

Your app currently runs on your laptop. To make it truly 24/7 (works even when laptop is off), you need to deploy to the cloud.

**Recommended: Streamlit Cloud (100% FREE)**

---

## Step-by-Step Deployment

### Step 1: Create GitHub Account (if you don't have one)
1. Go to https://github.com
2. Click "Sign up"
3. Create account

### Step 2: Create New Repository
1. Click "+" in top right → "New repository"
2. Name: `trade-with-nilay`
3. Set to "Public" (required for free Streamlit hosting)
4. Click "Create repository"

### Step 3: Upload Your Code
**Option A: Using GitHub Desktop (Easier)**
1. Download GitHub Desktop: https://desktop.github.com
2. Install and sign in
3. Click "Add" → "Add existing repository"
4. Select folder: `g:\My Drive\Trade_with_Nilay`
5. Click "Publish repository"

**Option B: Using Command Line**
```bash
cd "g:\My Drive\Trade_with_Nilay"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/trade-with-nilay.git
git push -u origin main
```

### Step 4: Deploy to Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Click "Sign up" and use your GitHub account
3. Click "New app"
4. Select:
   - Repository: `trade-with-nilay`
   - Branch: `main`
   - Main file path: `frontend/app.py`
5. Click "Advanced settings"
6. Add secrets:
```toml
TELEGRAM_BOT_TOKEN = "your_bot_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"
```
7. Click "Deploy"

### Step 5: Wait for Deployment (2-3 minutes)
You'll see a URL like: `https://trade-with-nilay.streamlit.app`

**This URL works 24/7, even when your laptop is off!**

---

## Mobile Access

### Immediate (While on Laptop):
Run this command to get a temporary mobile link:
```batch
cd "g:\My Drive\Trade_with_Nilay"
npx -y localtunnel --port 8501
```
Copy the URL to your phone browser.

### Permanent (After Cloud Deployment):
Your Streamlit Cloud URL works on mobile automatically!

**To Install as App on Phone:**
1. Open the Streamlit URL on your phone
2. **iPhone**: Tap Share → "Add to Home Screen"
3. **Android**: Tap Menu (⋮) → "Add to Home Screen"

Now it works like a native app!

---

## Custom Domain (Optional)

Want `www.Trade_with_Nilay.com` instead of `.streamlit.app`?

1. Buy domain from GoDaddy/Namecheap (~$10/year)
2. In domain settings, add CNAME record:
   - Name: `www`
   - Value: `your-app.streamlit.app`
3. In Streamlit Cloud dashboard:
   - Go to Settings → Custom domain
   - Enter: `www.Trade_with_Nilay.com`
   - Click "Add"

---

## Troubleshooting

**Q: App shows "Sleeping" message?**
A: Free tier sleeps after 7 days of no visits. Just visit the URL to wake it up.

**Q: Need better performance?**
A: Upgrade to Streamlit Cloud paid tier ($20/month) or use Railway.app

**Q: Scanner not working on cloud?**
A: Selenium might need adjustments. The `packages.txt` file I created should handle this.

---

## Files I Created for Cloud Deployment

✅ `.streamlit/config.toml` - Streamlit settings
✅ `packages.txt` - System dependencies (Chromium for Selenium)
✅ `.gitignore` - Exclude sensitive files
✅ `frontend/static/manifest.json` - PWA for mobile app
✅ `README.md` - GitHub documentation

**Everything is ready! Just follow the steps above.**

---

## Need Help?

If you get stuck:
1. Check Streamlit Cloud logs in the dashboard
2. Telegram me the error message
3. I can help debug!

**Once deployed, your link will be:**
`https://YOUR_APP_NAME.streamlit.app`

**Share this with anyone - it works 24/7!** 🚀
