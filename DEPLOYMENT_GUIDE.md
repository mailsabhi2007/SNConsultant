# Complete Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the multi-agent system with admin/superadmin features to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Backend Deployment](#backend-deployment)
3. [Frontend Deployment](#frontend-deployment)
4. [Database Migration](#database-migration)
5. [Configuration](#configuration)
6. [Testing](#testing)
7. [Rollout Strategy](#rollout-strategy)
8. [Monitoring](#monitoring)
9. [Rollback Procedures](#rollback-procedures)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### Requirements

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ and npm installed
- [ ] Database backup created
- [ ] API keys configured (Anthropic, Tavily)
- [ ] ServiceNow credentials configured
- [ ] SSL certificates ready (for production)
- [ ] Domain configured (if applicable)

### Code Review

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Dependencies updated
- [ ] Environment variables documented
- [ ] Security audit completed

### Infrastructure

- [ ] Server resources adequate (CPU, RAM, Disk)
- [ ] Load balancer configured (if applicable)
- [ ] Monitoring tools ready
- [ ] Backup strategy in place

---

## Backend Deployment

### Step 1: Prepare Environment

```bash
# Clone/pull latest code
cd /path/to/deployment
git pull origin main  # or your deployment branch

# Create/activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Create/update `.env` file:

```bash
# .env
ANTHROPIC_API_KEY=your_anthropic_api_key
TAVILY_API_KEY=your_tavily_api_key
JWT_SECRET=your_jwt_secret_minimum_32_characters
SERVICENOW_INSTANCE=your_instance.service-now.com
SERVICENOW_USERNAME=your_servicenow_username
SERVICENOW_PASSWORD=your_servicenow_password

# Optional
ANTHROPIC_MODEL=claude-sonnet-4-20250514
PORT=8000
```

**Security Note:** Never commit `.env` to version control!

### Step 3: Run Database Migration

```bash
# Backup existing database first!
cp data/app.db data/app.db.backup.$(date +%Y%m%d_%H%M%S)

# Run migration
python database.py
```

**Expected Output:**
```
Added is_superadmin column to users table
Database initialized successfully

Database Statistics:
{
  "total_users": 2,
  "active_users": 2,
  ...
}
```

### Step 4: Verify Database Schema

```bash
sqlite3 data/app.db << EOF
.tables
PRAGMA table_info(users);
PRAGMA table_info(agent_prompts);
PRAGMA table_info(multi_agent_config);
PRAGMA table_info(agent_handoffs);
EOF
```

**Expected Tables:**
- users (with is_superadmin column)
- agent_prompts
- multi_agent_config
- agent_handoffs
- ... (other existing tables)

### Step 5: Start Backend Server

#### Development/Testing:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production (with Gunicorn):

```bash
# Install gunicorn
pip install gunicorn uvicorn[standard]

# Start with gunicorn
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log \
  --daemon
```

#### Production (with systemd):

Create `/etc/systemd/system/sn-consultant.service`:

```ini
[Unit]
Description=ServiceNow Consultant API
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/SN-Consultant
Environment="PATH=/path/to/SN-Consultant/venv/bin"
ExecStart=/path/to/SN-Consultant/venv/bin/gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable sn-consultant
sudo systemctl start sn-consultant
sudo systemctl status sn-consultant
```

### Step 6: Test Backend Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Login (create first user if needed)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password","email":"admin@example.com"}'

# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  -c cookies.txt

# Test admin endpoint
curl http://localhost:8000/api/admin/multi-agent/rollout \
  -b cookies.txt

# Expected: {"rollout_percentage": 0, "status": "disabled"}
```

---

## Frontend Deployment

### Step 1: Install Dependencies

```bash
cd frontend
npm install

# Install new UI dependencies
npm install @radix-ui/react-slider @radix-ui/react-switch class-variance-authority
```

### Step 2: Configure API Endpoint

Update `frontend/src/services/api.ts` to point to production API:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

Create `frontend/.env.production`:

```
REACT_APP_API_URL=https://your-domain.com/api
```

### Step 3: Build Frontend

```bash
cd frontend
npm run build
```

**Expected Output:**
```
vite v4.x.x building for production...
✓ 1234 modules transformed.
dist/index.html                  1.2 kB
dist/assets/index-abc123.js    450.3 kB
...
✓ built in 12.34s
```

### Step 4: Deploy Frontend

#### Option A: Serve with Nginx

Install Nginx:

```bash
sudo apt-get install nginx  # Ubuntu/Debian
sudo yum install nginx      # CentOS/RHEL
```

Configure Nginx (`/etc/nginx/sites-available/sn-consultant`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    root /path/to/SN-Consultant/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/sn-consultant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Option B: Serve with Python

```bash
cd frontend/dist
python -m http.server 3000
```

#### Option C: Use Vercel/Netlify

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel --prod
```

### Step 5: Configure SSL (Production)

Using Let's Encrypt:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

---

## Database Migration

### Automated Migration Script

Create `scripts/migrate.py`:

```python
#!/usr/bin/env python3
"""Database migration script for multi-agent features."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database, get_database_stats, get_db_connection

def main():
    print("Starting database migration...")

    # Backup
    print("Creating backup...")
    import shutil
    from datetime import datetime
    backup_name = f"data/app.db.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2("data/app.db", backup_name)
    print(f"Backup created: {backup_name}")

    # Migrate
    print("Running migrations...")
    init_database()

    # Verify
    print("Verifying schema...")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check is_superadmin column
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        assert 'is_superadmin' in columns, "is_superadmin column not found!"

        # Check new tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert 'agent_prompts' in tables, "agent_prompts table not found!"
        assert 'multi_agent_config' in tables, "multi_agent_config table not found!"
        assert 'agent_handoffs' in tables, "agent_handoffs table not found!"

    print("✓ Migration successful!")

    # Stats
    stats = get_database_stats()
    print(f"\nDatabase stats:")
    print(f"  Total users: {stats['total_users']}")
    print(f"  Active users: {stats['active_users']}")
    print(f"  Total conversations: {stats['total_conversations']}")

if __name__ == "__main__":
    main()
```

Run migration:

```bash
python scripts/migrate.py
```

---

## Configuration

### Step 1: Make First User Superadmin

```python
python -c "
from database import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"')
    print('Admin user promoted to superadmin')
"
```

### Step 2: Initialize Multi-Agent Rollout

```python
python -c "
from user_config import set_multi_agent_rollout_percentage
set_multi_agent_rollout_percentage(0)  # Start with 0% (disabled)
print('Multi-agent rollout initialized to 0%')
"
```

### Step 3: Test Configuration

```bash
# Test admin endpoint
curl http://localhost:8000/api/admin/multi-agent/rollout -b cookies.txt

# Expected: {"rollout_percentage": 0, "status": "disabled"}
```

---

## Testing

### Backend Tests

```bash
# Run tests
pytest tests/

# Test specific modules
pytest tests/test_admin_endpoints.py
pytest tests/test_multi_agent.py
```

### Integration Tests

```bash
# Test end-to-end flow
python test_multi_agent.py
```

### Manual Testing Checklist

#### Admin Features
- [ ] Login as admin
- [ ] View multi-agent rollout page
- [ ] Change rollout percentage
- [ ] Enable multi-agent for specific user
- [ ] Disable multi-agent for specific user
- [ ] Remove user override
- [ ] View handoff analytics

#### Superadmin Features
- [ ] Login as superadmin
- [ ] View agent prompts page
- [ ] Edit consultant prompt
- [ ] Save custom prompt
- [ ] View default prompt
- [ ] Reset to default prompt
- [ ] Verify custom prompt is used

#### Multi-Agent Functionality
- [ ] Send query (should route to consultant)
- [ ] Verify correct agent handles query
- [ ] Test agent handoff
- [ ] Check handoff in database
- [ ] Verify analytics update

---

## Rollout Strategy

### Phase 1: Alpha (Week 1) - Admin Only

```python
from user_config import set_multi_agent_rollout_percentage, set_multi_agent_override

# Disable for all
set_multi_agent_rollout_percentage(0)

# Enable for admins
set_multi_agent_override("admin_user_id", True)
```

**Checklist:**
- [ ] Deploy to staging
- [ ] Test all admin features
- [ ] Test multi-agent flows
- [ ] Monitor errors
- [ ] Fix bugs
- [ ] Admin approval

### Phase 2: Beta (Weeks 2-3) - 10% Users

```python
# Gradual rollout
set_multi_agent_rollout_percentage(10)
```

**Checklist:**
- [ ] Monitor handoff rate (target: <20%)
- [ ] Monitor error rate
- [ ] Collect user feedback
- [ ] Compare with single-agent baseline
- [ ] A/B test results
- [ ] Adjust based on feedback

### Phase 3: Gradual Expansion (Weeks 4-6)

```python
# Week 4
set_multi_agent_rollout_percentage(25)

# Week 5
set_multi_agent_rollout_percentage(50)

# Week 6
set_multi_agent_rollout_percentage(75)
```

**Monitor each week:**
- [ ] Error rate ≤ baseline
- [ ] Handoff rate <20%
- [ ] User satisfaction ≥ baseline
- [ ] Performance acceptable

### Phase 4: Full Deployment (Week 7+)

```python
# Full rollout
set_multi_agent_rollout_percentage(100)
```

**Post-deployment:**
- [ ] Monitor for 1 week
- [ ] Keep legacy agent for 1 month
- [ ] Collect success metrics
- [ ] Document lessons learned

---

## Monitoring

### Key Metrics to Track

```python
from api.services.multi_agent_service import get_handoff_analytics

# Daily monitoring
analytics = get_handoff_analytics(days=1)
print(f"Handoff rate: {analytics['handoff_rate_percentage']}%")
print(f"Total handoffs: {analytics['total_handoffs']}")
```

### Database Queries

```sql
-- Users with multi-agent enabled
SELECT
    COUNT(CASE WHEN uc.config_value = 'true' THEN 1 END) as enabled_count,
    COUNT(*) as total_users
FROM users u
LEFT JOIN user_configs uc ON u.user_id = uc.user_id
    AND uc.config_key = 'multi_agent_enabled';

-- Recent handoffs
SELECT from_agent, to_agent, COUNT(*) as count
FROM agent_handoffs
WHERE timestamp >= datetime('now', '-24 hours')
GROUP BY from_agent, to_agent;

-- Error rate
SELECT COUNT(*) FROM messages
WHERE role = 'assistant'
  AND content LIKE '%error%'
  AND created_at >= datetime('now', '-24 hours');
```

### Log Monitoring

```bash
# Monitor application logs
tail -f logs/error.log

# Monitor Nginx access logs
tail -f /var/log/nginx/access.log

# Monitor systemd service
journalctl -u sn-consultant -f
```

### Alerting

Set up alerts for:
- Error rate spikes (>5% of requests)
- Handoff rate >30%
- API response time >5s
- Database connection failures
- Disk space <20%

---

## Rollback Procedures

### Emergency Rollback (Critical Issue)

```python
# IMMEDIATE: Disable multi-agent for all users
from user_config import set_multi_agent_rollout_percentage
set_multi_agent_rollout_percentage(0)
print("✓ Multi-agent disabled for all users")
```

**Takes effect immediately - no restart needed!**

### Partial Rollback (Specific Users)

```python
# Disable for specific users
from user_config import set_multi_agent_override
set_multi_agent_override("problem_user_id", False)
```

### Database Rollback

If migration causes issues:

```bash
# Stop services
sudo systemctl stop sn-consultant
sudo systemctl stop nginx

# Restore backup
cp data/app.db.backup.20240131_120000 data/app.db

# Restart services
sudo systemctl start sn-consultant
sudo systemctl start nginx

# Verify
curl http://localhost:8000/api/health
```

### Code Rollback

```bash
# Revert to previous version
git log --oneline  # Find commit before deployment
git reset --hard abc123  # Commit hash before multi-agent
pip install -r requirements.txt
sudo systemctl restart sn-consultant
```

---

## Troubleshooting

### Common Issues

#### Issue: "is_superadmin column not found"

**Cause:** Migration didn't run
**Fix:**
```bash
python database.py
```

#### Issue: "403 Forbidden" on admin endpoints

**Cause:** User not admin
**Fix:**
```python
from database import get_db_connection
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = 1, is_superadmin = 1 WHERE username = 'your_username'")
```

#### Issue: Custom prompts not being used

**Cause:** Prompt not active or doesn't exist
**Fix:**
```python
from database import get_agent_prompt, set_agent_prompt
prompt = get_agent_prompt("consultant")
if not prompt:
    set_agent_prompt("consultant", "Your custom prompt...", "admin_user_id")
```

#### Issue: Frontend not loading

**Cause:** API endpoint misconfigured
**Fix:**
Check `frontend/.env.production` and rebuild:
```bash
cd frontend
npm run build
```

#### Issue: High handoff rate

**Cause:** Poor routing accuracy
**Fix:**
1. Review orchestrator prompt
2. Check query examples
3. Consider adjusting routing logic

### Debug Commands

```bash
# Check database schema
sqlite3 data/app.db ".schema users"
sqlite3 data/app.db ".schema agent_prompts"

# Check user roles
sqlite3 data/app.db "SELECT username, is_admin, is_superadmin FROM users"

# Check rollout percentage
sqlite3 data/app.db "SELECT * FROM user_configs WHERE config_key = 'multi_agent_rollout_percentage'"

# Check custom prompts
sqlite3 data/app.db "SELECT agent_name, is_active FROM agent_prompts"

# Check recent handoffs
sqlite3 data/app.db "SELECT * FROM agent_handoffs ORDER BY timestamp DESC LIMIT 10"
```

### Getting Help

1. Check documentation:
   - `ADMIN_MULTI_AGENT_GUIDE.md`
   - `MULTI_AGENT_README.md`
   - `IMPLEMENTATION_SUMMARY.md`

2. Check logs:
   - Application logs: `logs/error.log`
   - System logs: `journalctl -u sn-consultant`
   - Nginx logs: `/var/log/nginx/error.log`

3. Enable debug mode:
   ```python
   # In api/main.py
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

---

## Success Criteria

### Deployment Complete When:

- [ ] Backend running without errors
- [ ] Frontend accessible
- [ ] Database migrated successfully
- [ ] Admin can login
- [ ] Superadmin can edit prompts
- [ ] Multi-agent rollout controllable
- [ ] Handoff analytics visible
- [ ] All tests passing
- [ ] Monitoring in place
- [ ] Rollback plan tested

### Production Ready When:

- [ ] SSL configured
- [ ] Domain configured
- [ ] Logs rotating
- [ ] Backups automated
- [ ] Monitoring alerts set
- [ ] Documentation complete
- [ ] Team trained
- [ ] Rollout plan approved

---

## Quick Reference

### Start/Stop Services

```bash
# Backend
sudo systemctl start sn-consultant
sudo systemctl stop sn-consultant
sudo systemctl restart sn-consultant
sudo systemctl status sn-consultant

# Nginx
sudo systemctl restart nginx
sudo nginx -t  # Test configuration
```

### Common Admin Tasks

```python
# Set rollout percentage
from user_config import set_multi_agent_rollout_percentage
set_multi_agent_rollout_percentage(50)

# Enable for user
from user_config import set_multi_agent_override
set_multi_agent_override("user123", True)

# View analytics
from api.services.multi_agent_service import get_handoff_analytics
print(get_handoff_analytics(7))  # Last 7 days
```

### Backup & Restore

```bash
# Backup
cp data/app.db data/app.db.backup.$(date +%Y%m%d)

# Restore
cp data/app.db.backup.20240131 data/app.db
sudo systemctl restart sn-consultant
```

---

## Appendix

### A. Full Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=minimum-32-character-secret

# Optional
TAVILY_API_KEY=tvly-...
SERVICENOW_INSTANCE=dev12345.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=password
ANTHROPIC_MODEL=claude-sonnet-4-20250514
PORT=8000
DATABASE_PATH=./data/app.db
LOG_LEVEL=INFO
```

### B. File Permissions

```bash
# Application files
chmod 644 *.py
chmod 755 scripts/*.py

# Configuration
chmod 600 .env

# Database
chmod 644 data/app.db
chmod 755 data/

# Logs
chmod 755 logs/
chmod 644 logs/*.log
```

### C. Performance Tuning

```python
# Gunicorn workers
workers = (2 * CPU_CORES) + 1

# Database connections
# For SQLite, use single connection
# For PostgreSQL, use connection pool:
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
```

---

## Summary

This deployment guide covers:

✅ Pre-deployment checklist
✅ Backend deployment (systemd, gunicorn)
✅ Frontend deployment (Nginx, SSL)
✅ Database migration scripts
✅ Configuration steps
✅ Testing procedures
✅ Gradual rollout strategy (0% → 10% → 100%)
✅ Monitoring and alerting
✅ Rollback procedures
✅ Troubleshooting guide

Follow the steps in order for a successful deployment!
