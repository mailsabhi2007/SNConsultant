# DigitalOcean Droplet Deployment Guide

## Prerequisites
- DigitalOcean account
- Domain name (optional, can use droplet IP)
- API keys ready (Anthropic, OpenAI, Tavily)

---

## Step 1: Create Droplet

1. Go to [DigitalOcean](https://cloud.digitalocean.com/droplets/new)
2. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic, $6/month (1 GB RAM, 1 vCPU) - minimum for alpha
   - **Recommended**: $12/month (2 GB RAM) for better performance
   - **Region**: Closest to your users
   - **Authentication**: SSH keys (recommended) or password

3. Click "Create Droplet"
4. Note your droplet's IP address

---

## Step 2: Initial Server Setup

SSH into your droplet:
```bash
ssh root@YOUR_DROPLET_IP
```

Run the setup script:
```bash
# Download and run setup (or copy files manually)
apt update && apt install -y git
git clone https://github.com/YOUR_REPO/sn-consultant.git /var/www/sn-consultant
cd /var/www/sn-consultant
chmod +x deploy/*.sh
./deploy/setup-droplet.sh
```

---

## Step 3: Configure Environment

Create the `.env` file:
```bash
cd /var/www/sn-consultant
nano .env
```

Add your keys:
```env
# Required API Keys
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
TAVILY_API_KEY=tvly-xxx

# JWT Secret (generate a random string)
JWT_SECRET_KEY=your-super-secret-key-change-this

# Optional: ServiceNow defaults (users can override in settings)
SN_INSTANCE=
SN_USER=
SN_PASSWORD=
```

Save and exit (Ctrl+X, Y, Enter)

---

## Step 4: Deploy Application

```bash
cd /var/www/sn-consultant
./deploy/deploy.sh
```

This will:
- Create Python virtual environment
- Install dependencies
- Build React frontend
- Start the backend service
- Configure Nginx

---

## Step 5: Update Nginx Config

Edit the nginx config to use your domain or IP:
```bash
nano /etc/nginx/sites-available/sn-consultant
```

Replace `your-domain.com` with:
- Your domain: `example.com`
- Or droplet IP: `165.232.xxx.xxx`

Reload nginx:
```bash
nginx -t && systemctl reload nginx
```

---

## Step 6: Set Up SSL (If Using Domain)

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will:
- Obtain SSL certificate
- Configure Nginx for HTTPS
- Set up auto-renewal

---

## Step 7: Test the Application

Visit in browser:
- HTTP: `http://YOUR_DROPLET_IP`
- HTTPS: `https://your-domain.com` (if SSL configured)

---

## Useful Commands

### Service Management
```bash
# Check status
systemctl status sn-consultant

# Restart backend
systemctl restart sn-consultant

# View logs
journalctl -u sn-consultant -f

# View last 100 lines
journalctl -u sn-consultant -n 100
```

### Nginx
```bash
# Test config
nginx -t

# Reload
systemctl reload nginx

# View access logs
tail -f /var/log/nginx/access.log
```

### Updates
```bash
cd /var/www/sn-consultant
git pull
./deploy/deploy.sh
```

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
journalctl -u sn-consultant -n 50

# Test manually
cd /var/www/sn-consultant
source venv/bin/activate
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 502 Bad Gateway
- Backend might not be running: `systemctl status sn-consultant`
- Check if port 8000 is listening: `ss -tlnp | grep 8000`

### Permission errors
```bash
chown -R www-data:www-data /var/www/sn-consultant
chmod 600 /var/www/sn-consultant/.env
```

---

## Security Checklist

- [ ] SSH key authentication enabled
- [ ] Password authentication disabled
- [ ] Firewall enabled (ufw)
- [ ] SSL certificate installed
- [ ] .env file permissions set to 600
- [ ] Regular system updates scheduled

---

## Estimated Costs

| Resource | Cost/Month |
|----------|------------|
| Droplet (2GB) | $12 |
| Domain (optional) | $1-2 |
| **Total** | ~$12-14 |

For alpha testing with <10 users, the $6 droplet should suffice.
