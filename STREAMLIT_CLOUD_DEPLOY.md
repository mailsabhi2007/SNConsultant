# Streamlit Cloud Deployment - Step by Step Guide

## 🚀 Quick Deployment Steps

### Step 1: Prepare Your Repository

1. **Verify your code is committed:**
   ```bash
   git status
   ```

2. **Add and commit all files (if needed):**
   ```bash
   git add .
   git commit -m "Ready for Streamlit Cloud deployment"
   ```

3. **Push to GitHub:**
   ```bash
   git push origin main
   ```
   > **Note:** Your repository must be on GitHub (public or private with paid Streamlit Cloud plan)

### Step 2: Deploy on Streamlit Cloud

1. **Go to Streamlit Cloud:**
   - Visit: https://share.streamlit.io
   - Sign in with your GitHub account

2. **Create New App:**
   - Click **"New app"** button
   - Fill in the details:
     - **Repository:** Select your repository
     - **Branch:** `main` (or your default branch)
     - **Main file path:** `streamlit_app.py`
     - **App URL:** Choose a unique name (e.g., `servicenow-consultant`)

3. **Click "Deploy"**
   - Wait for the build to complete (usually 2-5 minutes)

### Step 3: Configure Secrets (API Keys)

**IMPORTANT:** Do this BEFORE your first run, or the app will fail.

1. **In Streamlit Cloud Dashboard:**
   - Click on your app
   - Go to **"Settings"** (⚙️ icon in top right)
   - Click **"Secrets"** in the left sidebar

2. **Add your secrets:**
   Copy and paste this template, then fill in your actual keys:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_KEY_HERE"
   OPENAI_API_KEY = "sk-proj-YOUR_KEY_HERE"
   TAVILY_API_KEY = "tvly-dev-YOUR_KEY_HERE"
   ```

   **Optional (for live ServiceNow instance):**
   ```toml
   SN_INSTANCE = "your-instance.service-now.com"
   SN_USER = "your_username"
   SN_PASSWORD = "your_password"
   ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
   ```

3. **Click "Save"**

### Step 4: Verify Deployment

1. **Check App Status:**
   - Your app URL will be: `https://your-app-name.streamlit.app`
   - Wait for "Running" status (green indicator)

2. **Test the Application:**
   - Open your app URL
   - Try asking a question
   - Verify all features work:
     - ✅ Chat interface
     - ✅ Public docs search
     - ✅ Knowledge base (if configured)
     - ✅ ServiceNow connection (if configured)

## 📋 Pre-Deployment Checklist

Before deploying, ensure:

- [ ] All code is committed to Git
- [ ] `.env` file is in `.gitignore` (✅ already done)
- [ ] No hardcoded API keys in code
- [ ] `streamlit_app.py` is the main file
- [ ] Repository is on GitHub
- [ ] All API keys are ready:
  - [ ] Anthropic API key
  - [ ] OpenAI API key
  - [ ] Tavily API key
  - [ ] ServiceNow credentials (optional)

## 🔐 Secrets Configuration

### Required Secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `TAVILY_API_KEY` | Tavily search API key | `tvly-dev-...` |

### Optional Secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SN_INSTANCE` | ServiceNow instance | `dev12345.service-now.com` |
| `SN_USER` | ServiceNow username | `admin` |
| `SN_PASSWORD` | ServiceNow password | `your_password` |
| `ANTHROPIC_MODEL` | Claude model | `claude-sonnet-4-20250514` |

## ⚙️ Streamlit Cloud Settings

### Recommended Settings:

1. **Python Version:** 3.11 (default)
2. **Memory:** 1GB (free tier) or upgrade for more
3. **Auto-restart:** Enabled (default)
4. **Always rerun:** Disabled (default)

### Resource Limits (Free Tier):

- **RAM:** 1GB
- **CPU:** 1 core
- **Storage:** 1GB
- **Sleep:** Apps sleep after 7 days of inactivity

## 🔄 Updating Your App

To update your deployed app:

1. **Make changes locally**
2. **Commit and push:**
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. **Streamlit Cloud auto-deploys** (usually within 1-2 minutes)

## 🐛 Troubleshooting

### App Won't Start

1. **Check logs:**
   - In Streamlit Cloud dashboard, click "Manage app" → "Logs"
   - Look for error messages

2. **Common issues:**
   - ❌ Missing API keys → Add secrets
   - ❌ Import errors → Check `requirements.txt`
   - ❌ Port conflicts → Not applicable (handled by Streamlit Cloud)

### API Connection Errors

1. **Verify secrets are set correctly:**
   - Go to Settings → Secrets
   - Check for typos in key names
   - Ensure no extra spaces

2. **Test API keys individually:**
   - Use the Admin Console in your app
   - Test each API connection

### Build Failures

1. **Check `requirements.txt`:**
   - All dependencies listed?
   - Version conflicts?
   - Test packages removed? (Use `requirements-dev.txt` for local dev)

2. **Check Python version:**
   - Streamlit Cloud uses Python 3.11 by default
   - Ensure your code is compatible

3. **Package loading issues:**
   - See `STREAMLIT_PACKAGE_TROUBLESHOOTING.md` for detailed fixes
   - Common: Remove test packages from `requirements.txt`
   - Pin versions if conflicts occur

### App is Slow

1. **Check resource usage:**
   - Free tier has 1GB RAM limit
   - Consider upgrading if needed

2. **Optimize:**
   - Reduce knowledge base size
   - Cache frequently used data

## 📊 Monitoring

### View Analytics:

1. **In Streamlit Cloud Dashboard:**
   - Click on your app
   - View "Analytics" tab
   - See usage stats, errors, etc.

### View Logs:

1. **Real-time logs:**
   - Click "Manage app" → "Logs"
   - See live application output

## 🔒 Security Best Practices

1. **Never commit secrets:**
   - ✅ `.env` is in `.gitignore`
   - ✅ Use Streamlit Cloud secrets management

2. **Rotate keys regularly:**
   - Update secrets in Streamlit Cloud dashboard
   - Old keys will stop working after rotation

3. **Limit access:**
   - Use private repositories for sensitive apps
   - Control who can access your Streamlit Cloud account

## 🎯 Next Steps After Deployment

1. **Test all features:**
   - Chat interface
   - Knowledge base
   - ServiceNow connection (if configured)

2. **Share with users:**
   - Share the app URL
   - Provide user guide if needed

3. **Monitor usage:**
   - Check analytics regularly
   - Monitor API costs
   - Set up alerts if needed

## 📞 Support

- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Streamlit Community:** https://discuss.streamlit.io
- **Check app logs** for specific errors

---

**Your app will be live at:** `https://your-app-name.streamlit.app`

**Status:** Ready to deploy! 🚀
