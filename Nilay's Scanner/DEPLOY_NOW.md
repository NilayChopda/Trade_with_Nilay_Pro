# 🚀 Quick Deploy to Streamlit Cloud

## Step 1: Install GitHub Desktop (Easiest Way)

1. Download: https://desktop.github.com
2. Install and sign in with GitHub (create account if needed)

## Step 2: Push Your Code to GitHub

1. Open GitHub Desktop
2. Click **File** → **Add Local Repository**
3. Select folder: `g:\My Drive\Trade_with_Nilay`
4. Click **Publish repository**
5. Name: `trade-with-nilay`
6. ✅ Make it **Public** (required for free hosting)
7. Click **Publish**

## Step 3: Deploy to Streamlit Cloud

1. Go to: https://share.streamlit.io
2. Click **Sign up** (use your GitHub account)
3. Click **New app**
4. Select:
   - **Repository**: `trade-with-nilay`
   - **Branch**: `main`
   - **Main file path**: `frontend/app.py`
5. Click **Advanced settings**
6. Add your secrets:
```toml
TELEGRAM_BOT_TOKEN = "your_token_here"
TELEGRAM_CHAT_ID = "your_chat_id_here"
```
7. Click **Deploy!**

## Step 4: Wait 2-3 Minutes

Your app will be live at:
**https://trade-with-nilay.streamlit.app**

(Or whatever name you choose)

---

## ✨ What You Get:

✅ **24/7 Live Website** - Works even when laptop is off
✅ **Free SSL (HTTPS)** - Secure connection
✅ **Mobile Access** - Works on any device
✅ **Auto-Updates** - Push to GitHub = auto-deploy
✅ **Custom Domain** - Can add www.Trade_with_Nilay.com later

---

## 🎯 Alternative: Deploy via Command Line

If you prefer terminal:

```bash
# 1. Initialize git
cd "g:\My Drive\Trade_with_Nilay"
git init
git add .
git commit -m "Initial deployment"

# 2. Create GitHub repo (via website)
# Then connect:
git remote add origin https://github.com/YOUR_USERNAME/trade-with-nilay.git
git push -u origin main
```

Then follow Step 3 above.

---

## 📱 Mobile Access

Once deployed, just open the URL on your phone:
- **https://your-app.streamlit.app**
- Add to home screen for app-like experience!

---

**Total Time: 10 minutes** ⏱️

Let me know when you're ready to start!
