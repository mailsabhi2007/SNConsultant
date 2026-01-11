# Streamlit Cloud Deployment Configuration

## Quick Start

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Ready for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Visit: https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Repository: `your-username/your-repo`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
   - Click "Deploy"

## Environment Variables (Secrets)

In Streamlit Cloud, go to "Settings" → "Secrets" and add:

```toml
[secrets]
ANTHROPIC_API_KEY = "sk-ant-api03-..."
OPENAI_API_KEY = "sk-proj-..."
TAVILY_API_KEY = "tvly-dev-..."

# Optional - ServiceNow credentials
SN_INSTANCE = "your-instance.service-now.com"
SN_USER = "your_username"
SN_PASSWORD = "your_password"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
```

## Important Notes

- ✅ `.env` file is already in `.gitignore` - your secrets won't be committed
- ✅ Use Streamlit Cloud's secrets management (not `.env` file)
- ✅ Free tier includes 1GB RAM and 1 CPU
- ✅ Apps sleep after 7 days of inactivity (free tier)
- ✅ Automatic HTTPS included

## Resource Requirements

- **Minimum:** 1GB RAM, 1 CPU (Free tier)
- **Recommended:** 2GB+ RAM for better performance
- **Storage:** Persistent storage for `chroma_db` and `user_context_data`

## Custom Domain (Paid Plans)

If you have a paid Streamlit Cloud plan, you can:
1. Go to Settings → Custom domain
2. Add your domain
3. Follow DNS configuration instructions

## Monitoring

- View logs in Streamlit Cloud dashboard
- Check "App health" for status
- Monitor API usage in respective provider dashboards
