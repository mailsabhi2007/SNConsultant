# Getting Started

## Quick Setup (5 Minutes)

### 1. Install Dependencies

**Windows:**
```bash
# Install Python dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd frontend
npm install
cd ..
```

**Linux/Mac:**
```bash
# Install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install frontend dependencies (optional)
cd frontend
npm install
cd ..
```

### 2. Run Database Migration

```bash
python scripts/migrate.py
```

**Expected output:**
```
==================================================
Database Migration Script
==================================================

[1/4] Creating backup...
✓ Backup created: data/app.db.backup.20240131_120000

[2/4] Running migrations...
Added is_superadmin column to users table
Database initialized successfully
✓ Migrations completed

[3/4] Verifying schema...
✓ Schema verification passed

[4/4] Checking database...

Database Statistics:
  Total users: 2
  Active users: 2
  Total conversations: 12
  Total messages: 34
  Cache entries: 2

==================================================
✓ Migration successful!
==================================================
```

### 3. Configure Environment

Create `.env` file:

```bash
# Copy example
cp .env.example .env  # Linux/Mac
copy .env.example .env  # Windows

# Edit .env and add your API keys
ANTHROPIC_API_KEY=your_key_here
JWT_SECRET=your_secret_minimum_32_characters
```

### 4. Create First User & Make Superadmin

```bash
# Start the backend
uvicorn api.main:app --reload

# In another terminal, create user (via API or frontend)
# Then make them superadmin:
python -c "from database import get_db_connection; c = get_db_connection(); c.cursor().execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"'); c.commit(); print('User promoted to superadmin')"
```

### 5. Access the Application

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000 (if running `npm run dev`)

## What's Available Now

### For Admins
1. **Multi-Agent Rollout**
   - Go to Admin Dashboard
   - Navigate to "Multi-Agent" tab
   - Control rollout percentage (0-100%)
   - Enable/disable for specific users

2. **User Management**
   - View all users with multi-agent status
   - Toggle multi-agent per user
   - Remove overrides

3. **Analytics**
   - View handoff statistics
   - See most common agent transitions
   - Monitor handoff rate

### For Superadmins
1. **Prompt Customization**
   - Go to Admin Dashboard
   - Navigate to "Superadmin" tab
   - Edit prompts for any agent:
     - Consultant Agent
     - Solution Architect Agent
     - Implementation Agent
     - Orchestrator
   - Save/reset to default

2. **System Configuration**
   - Configure multi-agent settings
   - View audit trail

## Testing the Multi-Agent System

### Quick Test

```bash
python test_multi_agent.py
```

### Manual Test

1. **Test Routing**
   ```bash
   # Start backend
   uvicorn api.main:app --reload

   # Send test queries via API
   curl -X POST http://localhost:8000/api/chat/multi-agent/message \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"message": "What is best practice for incident assignment?"}'
   ```

2. **Test Admin Endpoints**
   ```bash
   # Get rollout status
   curl http://localhost:8000/api/admin/multi-agent/rollout \
     -b cookies.txt

   # Set rollout to 50%
   curl -X PUT http://localhost:8000/api/admin/multi-agent/rollout \
     -H "Content-Type: application/json" \
     -b cookies.txt \
     -d '{"percentage": 50}'
   ```

3. **Test Superadmin Endpoints**
   ```bash
   # Get all prompts
   curl http://localhost:8000/api/admin/multi-agent/prompts \
     -b cookies.txt

   # Get consultant prompt
   curl http://localhost:8000/api/admin/multi-agent/prompts/consultant \
     -b cookies.txt
   ```

## Common Commands

### Backend Management

```bash
# Start development server
uvicorn api.main:app --reload

# Start production server (with gunicorn)
gunicorn api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Database Management

```bash
# Backup database
cp data/app.db data/app.db.backup.$(date +%Y%m%d)  # Linux/Mac
copy data\app.db data\app.db.backup.%date%  # Windows

# Run migration
python scripts/migrate.py

# Check database
sqlite3 data/app.db ".tables"
sqlite3 data/app.db "SELECT * FROM users"
```

### Multi-Agent Configuration

```bash
# Set rollout percentage
python -c "from user_config import set_multi_agent_rollout_percentage; set_multi_agent_rollout_percentage(50)"

# Enable for specific user
python -c "from user_config import set_multi_agent_override; set_multi_agent_override('user123', True)"

# Disable for specific user
python -c "from user_config import set_multi_agent_override; set_multi_agent_override('user123', False)"

# Check if enabled for user
python -c "from user_config import is_multi_agent_enabled; print(is_multi_agent_enabled('user123'))"

# View analytics
python -c "from api.services.multi_agent_service import get_handoff_analytics; import json; print(json.dumps(get_handoff_analytics(30), indent=2))"
```

### Prompt Management

```bash
# Set custom prompt
python -c "
from database import set_agent_prompt
set_agent_prompt(
    'consultant',
    'You are an expert ServiceNow consultant with 20 years experience...',
    'admin_user_id'
)
print('Prompt updated')
"

# Check current prompt
python -c "from database import get_agent_prompt; print(get_agent_prompt('consultant'))"

# Reset to default
python -c "from database import reset_agent_prompt; reset_agent_prompt('consultant'); print('Reset to default')"
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database errors

**Solution:**
```bash
# Run migration
python scripts/migrate.py

# If issues persist, restore from backup
cp data/app.db.backup.* data/app.db
python scripts/migrate.py
```

### Issue: "403 Forbidden" on admin endpoints

**Solution:**
```bash
# Make sure user is admin/superadmin
python -c "
from database import get_db_connection
c = get_db_connection()
c.cursor().execute('UPDATE users SET is_admin = 1, is_superadmin = 1 WHERE username = \"your_username\"')
c.commit()
print('User promoted')
"
```

### Issue: Frontend not connecting to backend

**Solution:**
```bash
# Check API endpoint in frontend/.env.local
echo "REACT_APP_API_URL=http://localhost:8000" > frontend/.env.local

# Rebuild frontend
cd frontend
npm run build
```

## Next Steps

1. **Review Documentation**
   - `DEPLOYMENT_GUIDE.md` - Full deployment guide
   - `ADMIN_MULTI_AGENT_GUIDE.md` - Admin features
   - `MULTI_AGENT_README.md` - Multi-agent system

2. **Test Locally**
   - Create users
   - Test multi-agent conversations
   - Test admin features
   - Test superadmin features

3. **Deploy to Staging**
   - Follow `DEPLOYMENT_GUIDE.md`
   - Test with real users
   - Monitor metrics

4. **Gradual Rollout**
   - Start with 0% (admin only)
   - Increase to 10% (beta)
   - Gradually expand to 100%

## Support

- **Documentation**: See all `*.md` files in root directory
- **Scripts**: See `scripts/` directory
- **Issues**: Check `DEPLOYMENT_GUIDE.md` troubleshooting section

## Quick Reference

| Task | Command |
|------|---------|
| Start backend | `uvicorn api.main:app --reload` |
| Run migration | `python scripts/migrate.py` |
| Make superadmin | `python -c "from database import get_db_connection; c = get_db_connection(); c.cursor().execute('UPDATE users SET is_superadmin = 1 WHERE username = \"admin\"'); c.commit()"` |
| Set rollout 50% | `python -c "from user_config import set_multi_agent_rollout_percentage; set_multi_agent_rollout_percentage(50)"` |
| View analytics | `python -c "from api.services.multi_agent_service import get_handoff_analytics; print(get_handoff_analytics(30))"` |
| Backup database | `cp data/app.db data/app.db.backup.$(date +%Y%m%d)` |

---

**You're all set! Start with `python scripts/migrate.py` and then `uvicorn api.main:app --reload`**
