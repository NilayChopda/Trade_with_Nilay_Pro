
# 💎 Trade With Nilay - Final Handover

Your professional stock terminal is **production-ready**. Below are the final steps to go live as per your request for Option 2.

## 📁 System Overview
- **Core Engine**: `app.py` (Real-time SocketIO Server)
- **Scanning Logic**: `scanner.py` (7 Criteria Swing Pick + FNO Autopick)
- **Database**: `database.py` (Persistence with Render disk support)
- **Visuals**: Modern Dark Theme (Bootstrap 5 + Custom CSS)

---

## 🚀 Step 1: Push Code to GitHub (CLOUD UPLOAD)
1. Open up your CMD or PowerShell.
2. Go to the project folder: 
   `cd "G:\My Drive\Trade_with_Nilay"`
3. Run these 3 commands:
   ```bash
   git init
   git add .
   git commit -m "Final Institutional Release"
   ```
4. Create a **Private Repo** on GitHub and push it using the link provided by GitHub (e.g., `git remote add...` and `git push`).

---

## 🌐 Step 2: Set Up Render.com (24/7 LIVE)
1. Login to **Render.com**.
2. New -> **Web Service**.
3. Link your GitHub repository.
4. **Environment Variables** (Add these in Render settings):
   - `TELEGRAM_BOT_TOKEN`: `8289967600:AAFSLnB1eCSYpKOdIenz398AcdJ5utcNyIs`
   - `TELEGRAM_CHAT_ID`: `810052560`
   - `KITE_API_KEY`: `927xjtvndq82vjc3`
5. **Persistent Disk (CRITICAL)**:
   - Go to the "Disk" tab in Render.
   - Click "Add Disk".
   - Name: `trade-data`, Mount Path: `/data`, Size: `1 GB`.
   - *This ensures your history and AI reports aren't deleted when the server restarts.*

---

## 🔗 Step 3: Custom Domain (DNS FIX)
1. In Render, go to **Settings** -> **Custom Domains**.
2. Add `trade-with-nilay.com`.
3. In your Domain Registrar (Godaddy/Namecheap):
   - **A Record**: Host `@`, Value: (Get the IP from Render dashboard)
   - **CNAME Record**: Host `www`, Value: `trade-with-nilay.onrender.com`

---

## 📊 Maintenance & Monitoring
- **Automatic Scans**: Runs every 5 mins.
- **EOD Reports**: Generated automatically at 3:45 PM IST.
- **Telegram Alerts**: Sent instantly to your phone.

Your system is now institutional grade. **Go ahead and push to GitHub to begin the deployment!**
