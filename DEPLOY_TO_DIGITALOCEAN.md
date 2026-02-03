# Deploy to DigitalOcean - Quick Start

## Prerequisites

1. **DigitalOcean Droplet** - Ubuntu 20.04/22.04 LTS (minimum: 2GB RAM, 2 vCPU)
2. **SSH Access** - Root or sudo user access
3. **API Keys** - Anthropic API key (required), Tavily API key (optional)
4. **Domain** (optional) - For SSL certificate

## One-Command Deployment

SSH into your droplet and run:

```bash
curl -fsSL https://raw.githubusercontent.com/mailsabhi2007/SNConsultant/main/scripts/deploy_digitalocean.sh | bash
```

**That's it!** The script will:
- ✅ Install all dependencies (Python, Node.js, Nginx)
- ✅ Clone the repository
- ✅ Setup virtual environment
- ✅ Build frontend
- ✅ Configure systemd service
- ✅ Setup Nginx reverse proxy
- ✅ Start all services

## Manual Deployment (Step-by-Step)

If you prefer manual control:

### 1. SSH into Droplet

```bash
ssh root@your-droplet-ip
```

### 2. Clone Repository

```bash
cd ~
git clone https://github.com/mailsabhi2007/SNConsultant.git
cd SNConsultant
```

### 3. Run Deployment Script

```bash
chmod +x scripts/deploy_digitalocean.sh
./scripts/deploy_digitalocean.sh
```

## Post-Deployment Configuration

### 1. Add API Keys

Edit the `.env` file:

```bash
nano ~/SN-Consultant/.env
```

Add your keys:
```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
JWT_SECRET=generate-a-secure-random-string-32-chars-minimum
TAVILY_API_KEY=tvly-your-key-here  # Optional
SERVICENOW_INSTANCE=dev12345.service-now.com  # Optional
SERVICENOW_USERNAME=admin  # Optional
SERVICENOW_PASSWORD=password  # Optional
```

Save and exit (Ctrl+X, Y, Enter)

### 2. Restart Backend

```bash
sudo systemctl restart sn-consultant
```

### 3. Access Application

Open your browser:
```
http://your-droplet-ip
```

### 4. Create Admin User

Two options:

**Option A: Via UI**
- Go to `/login`
- Click "Sign Up"
- Register first user (automatically becomes admin)

**Option B: Via Database**
```bash
cd ~/SN-Consultant
source venv/bin/activate
python3 -c "
from database import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"')
    print('Admin promoted to superadmin')
"
```

## Setup SSL (Optional but Recommended)

### 1. Point Domain to Droplet

Add an A record pointing to your droplet IP:
```
@ -> your-droplet-ip
```

### 2. Update Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/sn-consultant
```

Change `server_name _;` to `server_name yourdomain.com;`

### 3. Get SSL Certificate

```bash
sudo certbot --nginx -d yourdomain.com
```

Follow prompts. Certbot will automatically configure Nginx for HTTPS.

### 4. Test

Visit `https://yourdomain.com`

## Useful Commands

### Check Service Status
```bash
sudo systemctl status sn-consultant
```

### View Logs (Live)
```bash
sudo journalctl -u sn-consultant -f
```

### View Recent Logs
```bash
sudo journalctl -u sn-consultant -n 100
```

### Restart Services
```bash
# Backend
sudo systemctl restart sn-consultant

# Nginx
sudo systemctl restart nginx
```

### Update Application
```bash
cd ~/SN-Consultant
git pull origin master
source venv/bin/activate
pip install -r requirements.txt
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..
sudo systemctl restart sn-consultant
```

### Database Backup
```bash
cp ~/SN-Consultant/data/app.db ~/SN-Consultant/data/app.db.backup.$(date +%Y%m%d)
```

### View Database
```bash
cd ~/SN-Consultant
sqlite3 data/app.db
# Inside sqlite3:
# .tables              - List tables
# SELECT * FROM users; - View users
# .exit                - Exit
```

## Troubleshooting

### Backend Not Starting

Check logs:
```bash
sudo journalctl -u sn-consultant -n 50
```

Common issues:
- Missing API keys in `.env`
- Port 8000 already in use
- Python dependencies not installed

### Frontend Shows 502 Bad Gateway

Backend is down. Check:
```bash
sudo systemctl status sn-consultant
```

Restart:
```bash
sudo systemctl restart sn-consultant
```

### Can't Access from Browser

Check firewall:
```bash
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22  # SSH
```

Check Nginx:
```bash
sudo systemctl status nginx
sudo nginx -t  # Test configuration
```

### Database Locked Error

Someone else accessing database. Restart:
```bash
sudo systemctl restart sn-consultant
```

## Performance Optimization

### For Production Droplet (4GB+ RAM)

Install Gunicorn for better performance:

```bash
cd ~/SN-Consultant
source venv/bin/activate
pip install gunicorn uvicorn[standard]
```

Update systemd service:
```bash
sudo nano /etc/systemd/system/sn-consultant.service
```

Change ExecStart to:
```ini
ExecStart=/home/YOUR_USER/SN-Consultant/venv/bin/gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart sn-consultant
```

## Monitoring

### Setup Log Rotation

Create `/etc/logrotate.d/sn-consultant`:

```bash
sudo nano /etc/logrotate.d/sn-consultant
```

Add:
```
/home/*/SN-Consultant/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
}
```

### Monitor Disk Space

```bash
df -h
du -sh ~/SN-Consultant/data/
```

### Monitor Memory

```bash
free -h
htop  # If installed: sudo apt install htop
```

## Security Checklist

- [ ] Change default SSH port
- [ ] Disable root SSH login
- [ ] Setup SSH keys (disable password auth)
- [ ] Enable UFW firewall
- [ ] Setup fail2ban
- [ ] Use strong JWT_SECRET (32+ chars)
- [ ] Enable SSL/HTTPS
- [ ] Regular database backups
- [ ] Keep system updated: `sudo apt update && sudo apt upgrade`

## Cost Optimization

**Recommended Droplet Sizes:**

- **Development/Testing**: $12/mo (2GB RAM, 2 vCPU)
- **Small Production**: $24/mo (4GB RAM, 2 vCPU)
- **Medium Production**: $48/mo (8GB RAM, 4 vCPU)

Enable weekly snapshots ($1/GB/month) for easy rollback.

## Support

For issues:
1. Check logs: `sudo journalctl -u sn-consultant -n 100`
2. Check documentation: `~/SN-Consultant/DEPLOYMENT_GUIDE.md`
3. Check status: `sudo systemctl status sn-consultant nginx`

## Quick Reference

| Task | Command |
|------|---------|
| View logs | `sudo journalctl -u sn-consultant -f` |
| Restart backend | `sudo systemctl restart sn-consultant` |
| Restart nginx | `sudo systemctl restart nginx` |
| Update app | `cd ~/SN-Consultant && git pull && ./scripts/deploy_digitalocean.sh` |
| Backup DB | `cp ~/SN-Consultant/data/app.db ~/backup.db` |
| Edit config | `nano ~/SN-Consultant/.env` |
| Check status | `sudo systemctl status sn-consultant` |

---

## Success!

If you see the login page at `http://your-droplet-ip`, you're all set! 🎉

**Next Steps:**
1. Create admin account
2. Configure ServiceNow credentials (optional)
3. Test multi-agent chat
4. Enable multi-agent for users in admin panel
5. Setup SSL with certbot (recommended)
