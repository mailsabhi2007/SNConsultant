# 🚀 Streamlit Cloud Quick Start

## 5-Minute Deployment Guide

### Step 1: Push to GitHub ✅

```bash
git add .
git commit -m "Ready for Streamlit Cloud"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to: **https://share.streamlit.io**
2. Sign in with **GitHub**
3. Click **"New app"**
4. Fill in:
   - **Repository:** Your repo name
   - **Branch:** `main`
   - **Main file path:** `streamlit_app.py`
   - **App URL:** Choose a name (e.g., `servicenow-consultant`)
5. Click **"Deploy"**

### Step 3: Add Secrets (CRITICAL!)

**⚠️ Do this BEFORE using the app!**

1. In your app dashboard, click **Settings** (⚙️)
2. Click **"Secrets"** in sidebar
3. Paste this template and fill in your keys:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_KEY"
OPENAI_API_KEY = "sk-proj-YOUR_KEY"
TAVILY_API_KEY = "tvly-dev-YOUR_KEY"
```

**Optional (for ServiceNow connection):**
```toml
SN_INSTANCE = "your-instance.service-now.com"
SN_USER = "your_username"
SN_PASSWORD = "your_password"
```

4. Click **"Save"**

### Step 4: Test Your App

1. Wait for build to complete (2-5 minutes)
2. Visit: `https://your-app-name.streamlit.app`
3. Test the chat interface
4. Verify all features work

## ✅ That's It!

Your app is now live! 🎉

## 📋 Checklist

- [ ] Code pushed to GitHub
- [ ] App deployed on Streamlit Cloud
- [ ] Secrets configured (all 3 API keys)
- [ ] App is running (green status)
- [ ] Tested chat interface
- [ ] Verified API connections

## 🔄 Updating Your App

Just push to GitHub:
```bash
git push origin main
```
Streamlit Cloud auto-deploys in 1-2 minutes!

## 🐛 Troubleshooting

**App won't start?**
- Check logs: Dashboard → Manage app → Logs
- Verify all secrets are set correctly

**API errors?**
- Double-check secret names (case-sensitive!)
- Verify API keys are valid
- Check API provider dashboards for rate limits

**Need help?**
- See `STREAMLIT_CLOUD_DEPLOY.md` for detailed guide
- Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-community-cloud

---

**Your app URL:** `https://your-app-name.streamlit.app`
