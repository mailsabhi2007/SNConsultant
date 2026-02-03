# Admin & Superadmin Quick Reference

## Role Assignment

| Username | Auto-Assigned Roles |
|----------|-------------------|
| First user created | Admin + Superadmin |
| "admin" | Admin |
| "superadmin" | Admin + Superadmin |

**Manual assignment:**
```sql
UPDATE users SET is_admin = 1 WHERE user_id = 'user_id';
UPDATE users SET is_superadmin = 1 WHERE user_id = 'user_id';
```

## Admin Endpoints (Requires is_admin = true)

### Rollout Management
```
GET    /api/admin/multi-agent/rollout
PUT    /api/admin/multi-agent/rollout           {"percentage": 50}
```

### User Management
```
GET    /api/admin/multi-agent/users
PUT    /api/admin/multi-agent/users/{user_id}   {"enabled": true}
DELETE /api/admin/multi-agent/users/{user_id}/override
```

### Analytics
```
GET    /api/admin/multi-agent/analytics?days=30
```

## Superadmin Endpoints (Requires is_superadmin = true)

### Prompt Management
```
GET    /api/admin/multi-agent/prompts
GET    /api/admin/multi-agent/prompts/{agent_name}
PUT    /api/admin/multi-agent/prompts/{agent_name}   {"system_prompt": "..."}
POST   /api/admin/multi-agent/prompts/{agent_name}/reset
```

**Agent names:** `consultant`, `solution_architect`, `implementation`, `orchestrator`

### Configuration
```
GET    /api/admin/multi-agent/config
PUT    /api/admin/multi-agent/config/{key}   {"config_value": "...", "config_type": "string"}
```

## Python Quick Functions

### Admin Functions
```python
from user_config import *

# Rollout
set_multi_agent_rollout_percentage(50)  # 0-100
rollout = get_system_config('multi_agent_rollout_percentage', 0)

# User overrides
set_multi_agent_override("user_id", True)   # Enable
set_multi_agent_override("user_id", False)  # Disable
is_enabled = is_multi_agent_enabled("user_id")
```

### Superadmin Functions
```python
from database import *

# Prompts
set_agent_prompt("consultant", "Custom prompt...", "superadmin_id")
custom = get_agent_prompt("consultant")  # Returns None if default
reset_agent_prompt("consultant")

# Config
set_multi_agent_config("key", "value", "string", "Description", "superadmin_id")
value = get_multi_agent_config("key")
```

## Frontend Service Functions

### Admin
```typescript
import {
  getMultiAgentRollout,
  updateMultiAgentRollout,
  getMultiAgentUsers,
  toggleMultiAgentForUser,
  removeMultiAgentOverride,
  getMultiAgentAnalytics
} from '@/services/admin';

// Usage
const rollout = await getMultiAgentRollout();
await updateMultiAgentRollout(50);
const {users} = await getMultiAgentUsers();
await toggleMultiAgentForUser("user123", true);
const analytics = await getMultiAgentAnalytics(30);
```

### Superadmin
```typescript
import {
  getAllAgentPrompts,
  getAgentPrompt,
  updateAgentPrompt,
  resetAgentPrompt
} from '@/services/admin';

// Usage
const {prompts} = await getAllAgentPrompts();
const detail = await getAgentPrompt("consultant");
await updateAgentPrompt("consultant", "New prompt...");
await resetAgentPrompt("consultant");
```

## Common Tasks

### Enable Multi-Agent for Beta Testing
```python
# 1. Set rollout to 0% (disabled)
set_multi_agent_rollout_percentage(0)

# 2. Enable for specific beta testers
set_multi_agent_override("beta1", True)
set_multi_agent_override("beta2", True)

# 3. Test and monitor
# ...

# 4. Gradual rollout
set_multi_agent_rollout_percentage(10)   # 10%
set_multi_agent_rollout_percentage(25)   # 25%
set_multi_agent_rollout_percentage(100)  # All
```

### Customize Agent Behavior
```python
# Get current prompt
from database import get_agent_prompt
current = get_agent_prompt("consultant")

# Set custom prompt
set_agent_prompt(
    "consultant",
    "You are an expert ServiceNow consultant...",
    "superadmin_id"
)

# Reset if needed
reset_agent_prompt("consultant")
```

### Emergency Rollback
```python
# Instant disable for all users
set_multi_agent_rollout_percentage(0)
```

## Database Tables

### agent_prompts
| Column | Type | Description |
|--------|------|-------------|
| prompt_id | INT | Primary key |
| agent_name | TEXT | Agent identifier |
| system_prompt | TEXT | Custom prompt |
| is_active | BOOL | Active flag |
| updated_by | TEXT | User ID |

### multi_agent_config
| Column | Type | Description |
|--------|------|-------------|
| config_id | INT | Primary key |
| config_key | TEXT | Config key |
| config_value | TEXT | Value |
| config_type | TEXT | Type (string/int/bool/json) |
| description | TEXT | Description |
| updated_by | TEXT | User ID |

## Useful SQL Queries

```sql
-- Users with overrides
SELECT u.username, uc.config_value
FROM users u
JOIN user_configs uc ON u.user_id = uc.user_id
WHERE uc.config_key = 'multi_agent_enabled';

-- Active custom prompts
SELECT agent_name, updated_by, updated_at
FROM agent_prompts
WHERE is_active = 1;

-- Recent handoffs
SELECT from_agent, to_agent, COUNT(*) as count
FROM agent_handoffs
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY from_agent, to_agent;
```

## Testing Checklist

- [ ] Database migration ran successfully
- [ ] First user has superadmin access
- [ ] Admin can access admin endpoints
- [ ] Superadmin can access superadmin endpoints
- [ ] Rollout percentage updates correctly
- [ ] User toggles work
- [ ] Custom prompts are used by agents
- [ ] Reset to default works
- [ ] Analytics returns data

## Troubleshooting

**"403 Forbidden" on admin endpoint:**
```sql
UPDATE users SET is_admin = 1 WHERE username = 'your_username';
```

**"403 Forbidden" on superadmin endpoint:**
```sql
UPDATE users SET is_superadmin = 1 WHERE username = 'your_username';
```

**Custom prompts not being used:**
```python
# Check if prompt exists and is active
from database import get_agent_prompt
prompt = get_agent_prompt("consultant")
print(f"Has custom: {prompt is not None}")
```

**Rollout not working:**
```python
# Check system config
from user_config import get_system_config
rollout = get_system_config('multi_agent_rollout_percentage', 0)
print(f"Current rollout: {rollout}%")
```

## Documentation

- **Implementation Guide**: `ADMIN_MULTI_AGENT_GUIDE.md`
- **Full Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Multi-Agent Docs**: `MULTI_AGENT_README.md`
- **Migration Guide**: `MULTI_AGENT_MIGRATION_GUIDE.md`
