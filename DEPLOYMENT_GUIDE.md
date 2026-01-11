# Deployment Guide - ServiceNow Consultant

This guide covers multiple deployment options for the ServiceNow Consultant application.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Option 1: Streamlit Cloud (Recommended for Quick Deployment)](#option-1-streamlit-cloud)
3. [Option 2: Docker Deployment](#option-2-docker-deployment)
4. [Option 3: Cloud Platforms](#option-3-cloud-platforms)
5. [Option 4: Local/On-Premise Deployment](#option-4-localon-premise-deployment)
6. [Environment Variables](#environment-variables)
7. [Security Considerations](#security-considerations)
8. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Prerequisites

Before deploying, ensure you have:
- ✅ All API keys ready (Anthropic, OpenAI, Tavily)
- ✅ ServiceNow instance credentials (if using live instance features)
- ✅ Python 3.10+ installed (for local deployment)
- ✅ Git repository set up (for cloud deployments)

---

## Option 1: Streamlit Cloud (Recommended for Quick Deployment)

**Best for:** Quick deployment, free tier available, automatic HTTPS

### Steps:

1. **Prepare your repository:**
   ```bash
   # Ensure .env is in .gitignore (already done)
   # Commit your code
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file path: `streamlit_app.py`
   - Add environment variables (see [Environment Variables](#environment-variables))

3. **Configure Environment Variables:**
   In Streamlit Cloud dashboard, add these secrets:
   ```
   ANTHROPIC_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   TAVILY_API_KEY=your_key_here
   SN_INSTANCE=your-instance.service-now.com (optional)
   SN_USER=your_username (optional)
   SN_PASSWORD=your_password (optional)
   ```

4. **Deploy:**
   - Click "Deploy"
   - Wait for build to complete
   - Your app will be live at: `https://your-app-name.streamlit.app`

### Advantages:
- ✅ Free tier available
- ✅ Automatic HTTPS
- ✅ Easy updates (just push to GitHub)
- ✅ Built-in analytics
- ✅ No server management

### Limitations:
- ⚠️ Free tier has resource limits
- ⚠️ Public repository required (or paid plan for private)
- ⚠️ Limited customization

---

## Option 2: Docker Deployment

**Best for:** Consistent deployment across environments, containerization

### Create Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p chroma_db user_context_data .cursor

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Create .dockerignore:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.env
.git
.gitignore
.chroma_db
*.log
.coverage
.pytest_cache
tests/
*.md
!README.md
```

### Build and Run:

```bash
# Build image
docker build -t servicenow-consultant:latest .

# Run container
docker run -d \
  -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your_key \
  -e OPENAI_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  -e SN_INSTANCE=your-instance.service-now.com \
  -e SN_USER=your_username \
  -e SN_PASSWORD=your_password \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/user_context_data:/app/user_context_data \
  --name sn-consultant \
  servicenow-consultant:latest
```

### Docker Compose (Recommended):

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  servicenow-consultant:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - SN_INSTANCE=${SN_INSTANCE}
      - SN_USER=${SN_USER}
      - SN_PASSWORD=${SN_PASSWORD}
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./user_context_data:/app/user_context_data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Run with:
```bash
docker-compose up -d
```

---

## Option 3: Cloud Platforms

### 3.1 AWS (EC2 + Elastic Beanstalk)

**Best for:** Enterprise deployments, AWS ecosystem integration

#### Using EC2:

1. **Launch EC2 instance:**
   - AMI: Ubuntu 22.04 LTS
   - Instance type: t3.medium or larger
   - Security group: Allow port 8501 (or use reverse proxy)

2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv nginx
   ```

3. **Deploy application:**
   ```bash
   git clone your-repo
   cd SN\ Consultant
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Set up systemd service:**
   Create `/etc/systemd/system/sn-consultant.service`:
   ```ini
   [Unit]
   Description=ServiceNow Consultant Streamlit App
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/SN Consultant
   Environment="PATH=/home/ubuntu/SN Consultant/venv/bin"
   EnvironmentFile=/home/ubuntu/SN Consultant/.env
   ExecStart=/home/ubuntu/SN Consultant/venv/bin/streamlit run streamlit_app.py --server.port=8501
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

5. **Start service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sn-consultant
   sudo systemctl start sn-consultant
   ```

6. **Set up Nginx reverse proxy:**
   Create `/etc/nginx/sites-available/sn-consultant`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 86400;
       }
   }
   ```

7. **Enable site and restart:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/sn-consultant /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### 3.2 Azure App Service

**Best for:** Microsoft ecosystem, easy scaling

1. **Install Azure CLI:**
   ```bash
   az login
   ```

2. **Create App Service:**
   ```bash
   az webapp create \
     --resource-group your-resource-group \
     --plan your-app-service-plan \
     --name your-app-name \
     --runtime "PYTHON:3.11"
   ```

3. **Configure environment variables:**
   ```bash
   az webapp config appsettings set \
     --resource-group your-resource-group \
     --name your-app-name \
     --settings \
       ANTHROPIC_API_KEY=your_key \
       OPENAI_API_KEY=your_key \
       TAVILY_API_KEY=your_key
   ```

4. **Deploy:**
   ```bash
   az webapp up \
     --resource-group your-resource-group \
     --name your-app-name \
     --runtime "PYTHON:3.11"
   ```

### 3.3 Google Cloud Run

**Best for:** Serverless, pay-per-use, auto-scaling

1. **Build and push container:**
   ```bash
   gcloud builds submit --tag gcr.io/your-project/sn-consultant
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy sn-consultant \
     --image gcr.io/your-project/sn-consultant \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ANTHROPIC_API_KEY=your_key,OPENAI_API_KEY=your_key,TAVILY_API_KEY=your_key
   ```

---

## Option 4: Local/On-Premise Deployment

**Best for:** Internal use, air-gapped environments, maximum control

### Steps:

1. **Install Python 3.10+:**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create `.env` file:
   ```
   ANTHROPIC_API_KEY=your_key
   OPENAI_API_KEY=your_key
   TAVILY_API_KEY=your_key
   SN_INSTANCE=your-instance.service-now.com
   SN_USER=your_username
   SN_PASSWORD=your_password
   ```

5. **Run application:**
   ```bash
   streamlit run streamlit_app.py
   ```

6. **Access at:** `http://localhost:8501`

### Production Setup (with systemd):

Follow the AWS EC2 systemd setup instructions above, but run on your local server.

---

## Environment Variables

### Required Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-api03-...` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings | `sk-proj-...` |
| `TAVILY_API_KEY` | Tavily search API key | `tvly-dev-...` |

### Optional Variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SN_INSTANCE` | ServiceNow instance URL | `dev12345.service-now.com` |
| `SN_USER` | ServiceNow username | `admin` |
| `SN_PASSWORD` | ServiceNow password | `your_password` |
| `ANTHROPIC_MODEL` | Claude model to use | `claude-sonnet-4-20250514` |

---

## Security Considerations

### 1. **API Keys Security:**
   - ✅ Never commit `.env` file to Git
   - ✅ Use environment variables or secrets management
   - ✅ Rotate keys regularly
   - ✅ Use least-privilege API keys

### 2. **ServiceNow Credentials:**
   - ✅ Use dedicated ServiceNow user with minimal required permissions
   - ✅ Consider using OAuth instead of username/password
   - ✅ Store credentials securely (use secrets manager)

### 3. **Network Security:**
   - ✅ Use HTTPS in production
   - ✅ Set up firewall rules
   - ✅ Consider VPN for internal deployments
   - ✅ Use reverse proxy (Nginx/Traefik) for additional security

### 4. **Data Protection:**
   - ✅ Encrypt sensitive data at rest
   - ✅ Use secure connections (HTTPS/TLS)
   - ✅ Implement access controls
   - ✅ Regular security audits

### 5. **Rate Limiting:**
   - ✅ Monitor API usage
   - ✅ Implement request throttling
   - ✅ Set up alerts for rate limit errors

---

## Post-Deployment Checklist

### Initial Setup:
- [ ] All environment variables configured
- [ ] Application starts without errors
- [ ] All API connections working
- [ ] ServiceNow connection tested (if applicable)
- [ ] Knowledge base initialized (if needed)

### Security:
- [ ] HTTPS enabled
- [ ] API keys secured
- [ ] Firewall rules configured
- [ ] Access controls in place
- [ ] Regular backups scheduled

### Monitoring:
- [ ] Application logs configured
- [ ] Error tracking set up
- [ ] Performance monitoring enabled
- [ ] Rate limit alerts configured
- [ ] Health checks working

### Documentation:
- [ ] Deployment documentation updated
- [ ] Runbook created for operations team
- [ ] Incident response plan documented
- [ ] User guide available

---

## Recommended Deployment Strategy

### For Quick Start:
1. **Streamlit Cloud** - Easiest, free tier, automatic HTTPS

### For Production:
1. **Docker + Cloud Platform** - Most flexible, scalable
2. **AWS/Azure/GCP** - Enterprise-grade, full control

### For Internal Use:
1. **Local/On-Premise** - Maximum control, air-gapped friendly

---

## Troubleshooting

### Common Issues:

1. **Port already in use:**
   ```bash
   # Find process using port 8501
   lsof -i :8501  # Linux/Mac
   netstat -ano | findstr :8501  # Windows
   ```

2. **Environment variables not loading:**
   - Check `.env` file location
   - Verify variable names match exactly
   - Restart application after changes

3. **ChromaDB errors:**
   - Ensure `chroma_db` directory has write permissions
   - Check disk space

4. **API connection failures:**
   - Verify API keys are correct
   - Check network connectivity
   - Review rate limit status

---

## Support

For deployment issues:
1. Check application logs
2. Review error messages in UI
3. Verify environment variables
4. Test API connections individually

---

**Last Updated:** Based on current application version
**Status:** Ready for deployment
