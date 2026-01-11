# Quick Deployment Guide

## 🚀 Fastest Deployment Options

### Option 1: Streamlit Cloud (5 minutes)

**Best for:** Quick deployment, free tier

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy to Streamlit Cloud"
   git push origin main
   ```

2. **Deploy:**
   - Go to https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Select repository
   - Main file: `streamlit_app.py`
   - Add secrets (API keys) in Settings
   - Deploy!

**Done!** Your app is live at `https://your-app.streamlit.app`

---

### Option 2: Docker (10 minutes)

**Best for:** Local or cloud deployment

1. **Build and run:**
   ```bash
   docker-compose up -d
   ```

2. **Set environment variables:**
   Create `.env` file or export:
   ```bash
   export ANTHROPIC_API_KEY=your_key
   export OPENAI_API_KEY=your_key
   export TAVILY_API_KEY=your_key
   ```

3. **Access:** http://localhost:8501

---

### Option 3: Local Python (5 minutes)

**Best for:** Development or internal use

1. **Install:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```
   ANTHROPIC_API_KEY=your_key
   OPENAI_API_KEY=your_key
   TAVILY_API_KEY=your_key
   ```

3. **Run:**
   ```bash
   streamlit run streamlit_app.py
   ```

---

## 📋 Pre-Deployment Checklist

- [ ] All API keys ready
- [ ] `.env` file created (for local/Docker)
- [ ] Secrets configured (for Streamlit Cloud)
- [ ] ServiceNow credentials ready (optional)
- [ ] Git repository set up
- [ ] `.gitignore` includes `.env`

---

## 🔐 Required Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
TAVILY_API_KEY=tvly-dev-...
```

Optional:
```
SN_INSTANCE=your-instance.service-now.com
SN_USER=your_username
SN_PASSWORD=your_password
```

---

## 📚 Full Documentation

See `DEPLOYMENT_GUIDE.md` for detailed deployment options including:
- AWS/Azure/GCP deployment
- Production setup
- Security best practices
- Monitoring and troubleshooting

---

## 🆘 Need Help?

1. Check `DEPLOYMENT_GUIDE.md` for detailed instructions
2. Review error messages in application logs
3. Verify all environment variables are set correctly
4. Test API connections individually
