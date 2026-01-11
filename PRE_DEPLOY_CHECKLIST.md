# Pre-Deployment Checklist for Streamlit Cloud

## ✅ Code Readiness

- [x] All code committed to Git
- [x] `.env` file in `.gitignore` (won't be committed)
- [x] No hardcoded API keys in code
- [x] `streamlit_app.py` is the main file
- [x] `requirements.txt` is up to date
- [x] Application tested locally

## ✅ Repository Setup

- [ ] Code pushed to GitHub
- [ ] Repository is accessible (public or private with paid plan)
- [ ] Main branch is `main` (or update in Streamlit Cloud settings)

## ✅ API Keys Ready

Have these ready before deployment:

- [ ] **Anthropic API Key** (Claude)
  - Get from: https://console.anthropic.com/
  - Format: `sk-ant-api03-...`

- [ ] **OpenAI API Key** (for embeddings)
  - Get from: https://platform.openai.com/api-keys
  - Format: `sk-proj-...`

- [ ] **Tavily API Key** (for search)
  - Get from: https://app.tavily.com/
  - Format: `tvly-dev-...`

- [ ] **ServiceNow Credentials** (optional, for live instance)
  - Instance URL: `your-instance.service-now.com`
  - Username
  - Password

## ✅ Streamlit Cloud Account

- [ ] Account created at https://share.streamlit.io
- [ ] Signed in with GitHub
- [ ] GitHub account connected

## 🚀 Ready to Deploy!

Once all items are checked, follow:
- **Quick Start:** `STREAMLIT_CLOUD_QUICKSTART.md`
- **Detailed Guide:** `STREAMLIT_CLOUD_DEPLOY.md`

## 📝 Notes

- Secrets are configured AFTER deployment (in Streamlit Cloud dashboard)
- App will fail on first run if secrets aren't set
- You can update secrets anytime without redeploying
- Code updates: just push to GitHub (auto-deploys)

---

**Status:** Ready when all items checked ✅
