# Deployment Checklist

## Quick Start (Development/Testing)

```bash
# 1. Run deployment script
./scripts/deploy.sh  # Linux/Mac
# OR
scripts\deploy.bat   # Windows

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Make first user superadmin
python -c "from database import get_db_connection; c = get_db_connection(); c.cursor().execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"'); c.commit()"

# 4. Start backend
uvicorn api.main:app --reload

# 5. Access application
# Backend: http://localhost:8000
# Frontend: http://localhost:3000 (if running npm run dev)
```

## Pre-Deployment Checklist

### Environment Setup
- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed (backend)
- [ ] Dependencies installed (frontend)
- [ ] .env file configured with all required keys
- [ ] Database backup created

### Configuration
- [ ] Anthropic API key configured
- [ ] Tavily API key configured (optional)
- [ ] ServiceNow credentials configured (optional)
- [ ] JWT secret set (minimum 32 characters)
- [ ] Database path configured
- [ ] Log directory created

### Code Review
- [ ] All files in multi_agent/ directory
- [ ] All admin endpoints added
- [ ] Database migration script exists
- [ ] Frontend components created
- [ ] Service functions added
- [ ] Tests exist and pass

## Database Migration Checklist

- [ ] Database backup created
- [ ] Migration script executed: `python scripts/migrate.py`
- [ ] is_superadmin column added to users table
- [ ] agent_prompts table created
- [ ] multi_agent_config table created
- [ ] agent_handoffs table created
- [ ] Indexes created
- [ ] Schema verified
- [ ] No errors in migration output

## Backend Deployment Checklist

### Local/Development
- [ ] Virtual environment activated
- [ ] Requirements installed: `pip install -r requirements.txt`
- [ ] Database migrated: `python scripts/migrate.py`
- [ ] Server starts: `uvicorn api.main:app --reload`
- [ ] Health check passes: `curl http://localhost:8000/api/health`
- [ ] Can create user
- [ ] Can login
- [ ] Can access admin endpoints

### Production
- [ ] Server configured (systemd or supervisor)
- [ ] Gunicorn installed
- [ ] Workers configured (2 * CPU + 1)
- [ ] Timeout set (120s recommended)
- [ ] Logs directory created
- [ ] Access log configured
- [ ] Error log configured
- [ ] Service starts automatically
- [ ] Service restarts on failure
- [ ] Health check endpoint monitored

## Frontend Deployment Checklist

### Build
- [ ] Dependencies installed: `npm install`
- [ ] New UI components installed (Radix UI)
- [ ] API endpoint configured (.env.production)
- [ ] Build completes: `npm run build`
- [ ] No build errors
- [ ] Dist directory created
- [ ] Assets generated

### Deployment
- [ ] Static files served (Nginx, Vercel, etc.)
- [ ] API proxy configured
- [ ] CORS configured correctly
- [ ] SSL certificate installed (production)
- [ ] Domain configured (production)
- [ ] Routing works (SPA routing)
- [ ] Assets load correctly

### UI Integration
- [ ] MultiAgentManagement component integrated
- [ ] SuperadminSettings component integrated
- [ ] Tabs added to Admin page
- [ ] Service functions imported
- [ ] Toast notifications work
- [ ] All UI components render

## Configuration Checklist

- [ ] First user created
- [ ] First user made admin: `UPDATE users SET is_admin = 1...`
- [ ] First user made superadmin: `UPDATE users SET is_superadmin = 1...`
- [ ] Multi-agent rollout initialized to 0%
- [ ] Can login as admin
- [ ] Can access admin dashboard
- [ ] Can access multi-agent management tab
- [ ] Can access superadmin settings (if superadmin)

## Testing Checklist

### Backend Tests
- [ ] Unit tests pass: `pytest tests/`
- [ ] Integration tests pass: `python test_multi_agent.py`
- [ ] Admin endpoints respond correctly
- [ ] Superadmin endpoints respond correctly
- [ ] Multi-agent graph works
- [ ] Handoffs recorded in database
- [ ] Analytics endpoints return data

### Frontend Tests
- [ ] Admin page loads
- [ ] Multi-agent tab visible
- [ ] Rollout slider works
- [ ] User table loads
- [ ] Toggle switches work
- [ ] Analytics cards display
- [ ] Handoff paths shown
- [ ] Superadmin tab visible (for superadmin)
- [ ] Prompt editor works
- [ ] Can save custom prompts
- [ ] Can reset to default
- [ ] Toast notifications appear

### End-to-End Tests
- [ ] Login as regular user
- [ ] Send query (should use single or multi-agent based on rollout)
- [ ] Login as admin
- [ ] View multi-agent management
- [ ] Change rollout percentage
- [ ] Enable multi-agent for specific user
- [ ] Disable multi-agent for specific user
- [ ] View handoff analytics
- [ ] Login as superadmin
- [ ] Edit consultant prompt
- [ ] Save custom prompt
- [ ] Verify custom prompt is used
- [ ] Reset to default
- [ ] Verify default prompt is used

## Security Checklist

- [ ] .env not in version control (.gitignore)
- [ ] JWT secret is secure (32+ characters)
- [ ] Database file permissions correct (644)
- [ ] SSL enabled (production)
- [ ] CORS configured correctly
- [ ] Rate limiting enabled (optional)
- [ ] Admin endpoints require authentication
- [ ] Superadmin endpoints require authentication
- [ ] SQL injection protected (using parameterized queries)
- [ ] XSS protection enabled
- [ ] CSRF protection enabled

## Monitoring Checklist

- [ ] Log files created
- [ ] Log rotation configured
- [ ] Error monitoring enabled
- [ ] Health check endpoint working
- [ ] Metrics collection enabled (optional)
- [ ] Alerts configured for:
  - [ ] High error rate
  - [ ] High handoff rate
  - [ ] Slow response times
  - [ ] Database connection failures
  - [ ] Disk space low

## Rollout Checklist

### Phase 1: Alpha (Admin Only)
- [ ] Rollout set to 0%
- [ ] Admin user override enabled
- [ ] Admin tests all features
- [ ] No critical bugs
- [ ] Analytics working
- [ ] Handoffs recorded
- [ ] Admin approval obtained

### Phase 2: Beta (10% Users)
- [ ] Rollout increased to 10%
- [ ] Monitor error rate daily
- [ ] Monitor handoff rate daily
- [ ] Collect user feedback
- [ ] Compare with baseline
- [ ] A/B test results reviewed
- [ ] Adjustments made if needed

### Phase 3: Gradual Expansion
- [ ] Week 1: 10% → Monitor
- [ ] Week 2: 25% → Monitor
- [ ] Week 3: 50% → Monitor
- [ ] Week 4: 75% → Monitor
- [ ] All metrics within acceptable range
- [ ] User satisfaction maintained

### Phase 4: Full Deployment
- [ ] Rollout increased to 100%
- [ ] Monitor for 1 week
- [ ] All metrics stable
- [ ] No critical issues
- [ ] Legacy agent kept for 1 month
- [ ] Success metrics documented

## Rollback Checklist

### Emergency Rollback
- [ ] Rollback procedure documented
- [ ] Backup database available
- [ ] Can revert to 0% rollout instantly
- [ ] Can revert code if needed
- [ ] Can restore database if needed
- [ ] Team knows rollback procedure

## Documentation Checklist

- [ ] DEPLOYMENT_GUIDE.md complete
- [ ] ADMIN_MULTI_AGENT_GUIDE.md available
- [ ] MULTI_AGENT_README.md available
- [ ] ADMIN_UI_INTEGRATION.md available
- [ ] API documentation updated
- [ ] Team trained on new features
- [ ] Troubleshooting guide available

## Sign-Off Checklist

### Technical Lead
- [ ] Code reviewed
- [ ] Tests verified
- [ ] Security reviewed
- [ ] Performance acceptable
- [ ] Documentation complete

### Admin/Product
- [ ] Features tested
- [ ] UI acceptable
- [ ] User experience good
- [ ] Ready for users

### DevOps
- [ ] Deployment tested
- [ ] Monitoring in place
- [ ] Backups configured
- [ ] Rollback tested
- [ ] SSL configured

## Post-Deployment Checklist

### Day 1
- [ ] Monitor error logs
- [ ] Check health endpoints
- [ ] Verify metrics collection
- [ ] Check user feedback
- [ ] Document any issues

### Week 1
- [ ] Review handoff analytics
- [ ] Check error rate trends
- [ ] Collect user feedback
- [ ] Make minor adjustments
- [ ] Update documentation

### Month 1
- [ ] Full metrics review
- [ ] User satisfaction survey
- [ ] Performance analysis
- [ ] Cost analysis
- [ ] Deprecate legacy agent (if stable)

## Success Criteria

Deployment is successful when:
- [ ] No critical bugs in production
- [ ] Error rate ≤ baseline
- [ ] Handoff rate <20%
- [ ] User satisfaction ≥ baseline
- [ ] All features working
- [ ] Monitoring operational
- [ ] Team trained
- [ ] Documentation complete

---

## Quick Commands Reference

```bash
# Start backend
uvicorn api.main:app --reload

# Start frontend
cd frontend && npm run dev

# Run migration
python scripts/migrate.py

# Make user superadmin
python -c "from database import get_db_connection; c = get_db_connection(); c.cursor().execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"'); c.commit()"

# Set rollout percentage
python -c "from user_config import set_multi_agent_rollout_percentage; set_multi_agent_rollout_percentage(50)"

# Check analytics
python -c "from api.services.multi_agent_service import get_handoff_analytics; print(get_handoff_analytics(7))"

# Backup database
cp data/app.db data/app.db.backup.$(date +%Y%m%d)

# Rollback to 0%
python -c "from user_config import set_multi_agent_rollout_percentage; set_multi_agent_rollout_percentage(0)"
```

---

Print this checklist and mark items as you complete them!
