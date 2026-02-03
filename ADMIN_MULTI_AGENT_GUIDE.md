# Admin & Superadmin Multi-Agent Management Guide

## Overview

This guide explains the admin and superadmin features for managing the multi-agent system. Admins can control user access and rollout, while superadmins can customize agent behavior and system prompts.

## User Roles

### Admin
- View system analytics and user management
- Control multi-agent rollout percentage
- Enable/disable multi-agent for specific users
- View handoff analytics

### Superadmin
- All admin capabilities, plus:
- Edit system prompts for each agent
- Configure multi-agent system settings
- Manage advanced configurations

**Note:** The first user created automatically becomes both admin and superadmin. Users with username "superadmin" also get superadmin privileges.

## Database Schema Updates

### New Columns
- `users.is_superadmin` - Boolean flag for superadmin access

### New Tables
1. **agent_prompts** - Stores custom system prompts for agents
   - `prompt_id`, `agent_name`, `system_prompt`, `is_active`, `updated_at`, `updated_by`

2. **multi_agent_config** - Stores multi-agent configuration settings
   - `config_id`, `config_key`, `config_value`, `config_type`, `description`, `is_active`, `updated_at`, `updated_by`

## Backend API Endpoints

### Admin Endpoints (Requires `is_admin = true`)

#### Multi-Agent Analytics
```
GET /api/admin/multi-agent/analytics?days=30
```
Returns handoff statistics and metrics.

**Response:**
```json
{
  "total_handoffs": 45,
  "handoff_paths": [
    {"from": "consultant", "to": "solution_architect", "count": 20},
    {"from": "solution_architect", "to": "implementation", "count": 15}
  ],
  "conversations_with_handoffs": 25,
  "total_conversations": 100,
  "handoff_rate_percentage": 25.0,
  "days": 30
}
```

#### Rollout Management
```
GET /api/admin/multi-agent/rollout
```
Get current rollout percentage.

```
PUT /api/admin/multi-agent/rollout
Body: {"percentage": 50}
```
Update rollout percentage (0-100).

#### User Management
```
GET /api/admin/multi-agent/users
```
Get all users with their multi-agent status.

**Response:**
```json
{
  "users": [
    {
      "user_id": "user123",
      "username": "john_doe",
      "email": "john@example.com",
      "is_admin": false,
      "is_superadmin": false,
      "is_active": true,
      "multi_agent_enabled": true,
      "multi_agent_source": "rollout"
    }
  ],
  "total_count": 10
}
```

```
PUT /api/admin/multi-agent/users/{user_id}
Body: {"enabled": true}
```
Enable/disable multi-agent for a specific user.

```
DELETE /api/admin/multi-agent/users/{user_id}/override
```
Remove user-specific override (revert to system rollout).

### Superadmin Endpoints (Requires `is_superadmin = true`)

#### Agent Prompt Management
```
GET /api/admin/multi-agent/prompts
```
Get all agent prompts.

```
GET /api/admin/multi-agent/prompts/{agent_name}
```
Get specific agent prompt (consultant, solution_architect, implementation, orchestrator).

**Response:**
```json
{
  "agent_name": "consultant",
  "custom_prompt": "Custom prompt text...",
  "is_using_custom": true,
  "default_prompt": "Default prompt text..."
}
```

```
PUT /api/admin/multi-agent/prompts/{agent_name}
Body: {"system_prompt": "New custom prompt..."}
```
Update agent system prompt.

```
POST /api/admin/multi-agent/prompts/{agent_name}/reset
```
Reset agent prompt to default.

#### System Configuration
```
GET /api/admin/multi-agent/config
```
Get all multi-agent configurations.

```
PUT /api/admin/multi-agent/config/{config_key}
Body: {
  "config_value": "value",
  "config_type": "string",
  "description": "Description of config"
}
```
Update configuration setting.

## Frontend Integration

### Admin Service Functions

All functions are available in `frontend/src/services/admin.ts`:

#### Admin Functions
```typescript
// Analytics
const analytics = await getMultiAgentAnalytics(30); // days

// Rollout management
const rollout = await getMultiAgentRollout();
await updateMultiAgentRollout(50); // Set to 50%

// User management
const {users} = await getMultiAgentUsers();
await toggleMultiAgentForUser("user123", true);
await removeMultiAgentOverride("user123");
```

#### Superadmin Functions
```typescript
// Prompt management
const {prompts} = await getAllAgentPrompts();
const promptDetail = await getAgentPrompt("consultant");
await updateAgentPrompt("consultant", "New prompt...");
await resetAgentPrompt("consultant");

// Configuration management
const {configs} = await getAllMultiAgentConfigs();
await updateMultiAgentConfig("key", "value", "string", "Description");
```

### UI Components (To Be Implemented)

Recommended components to add to `frontend/src/pages/Admin.tsx`:

1. **Multi-Agent Dashboard Tab**
   - Rollout percentage slider
   - Analytics cards (handoff rate, total handoffs)
   - Handoff path visualization

2. **User Management Table**
   - List all users
   - Toggle multi-agent for each user
   - Show current status (override vs rollout)
   - Remove override button

3. **Superadmin Settings Tab** (Only visible to superadmins)
   - Agent prompt editor for each agent
   - Preview default vs custom prompts
   - Reset to default button
   - Configuration editor

## Usage Examples

### As Admin: Enable Multi-Agent for Beta Testing

1. **Start with 0% rollout:**
```python
from user_config import set_multi_agent_rollout_percentage
set_multi_agent_rollout_percentage(0)
```

2. **Enable for specific beta testers via API:**
```bash
curl -X PUT http://localhost:8000/api/admin/multi-agent/users/beta_user1 \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

3. **Gradually increase rollout:**
```bash
# 10% rollout
curl -X PUT http://localhost:8000/api/admin/multi-agent/rollout \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"percentage": 10}'
```

4. **Monitor analytics:**
```bash
curl -X GET http://localhost:8000/api/admin/multi-agent/analytics?days=7 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### As Superadmin: Customize Agent Prompts

1. **View current prompt:**
```bash
curl -X GET http://localhost:8000/api/admin/multi-agent/prompts/consultant \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
```

2. **Update prompt:**
```bash
curl -X PUT http://localhost:8000/api/admin/multi-agent/prompts/consultant \
  -H "Authorization: Bearer SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"system_prompt": "You are an expert consultant with 20 years experience..."}'
```

3. **Reset to default if needed:**
```bash
curl -X POST http://localhost:8000/api/admin/multi-agent/prompts/consultant/reset \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
```

## Python API Usage

### Admin Operations

```python
from user_config import (
    set_multi_agent_rollout_percentage,
    set_multi_agent_override,
    is_multi_agent_enabled
)

# Set system-wide rollout
set_multi_agent_rollout_percentage(25)  # 25% of users

# Enable for specific user
set_multi_agent_override("user123", True)

# Disable for specific user
set_multi_agent_override("user456", False)

# Check if enabled for user
enabled = is_multi_agent_enabled("user123")
print(f"Multi-agent enabled: {enabled}")
```

### Superadmin Operations

```python
from database import (
    set_agent_prompt,
    get_agent_prompt,
    reset_agent_prompt
)

# Set custom prompt
set_agent_prompt(
    agent_name="consultant",
    system_prompt="Custom prompt for consultant agent...",
    updated_by="superadmin_user_id"
)

# Get current prompt (returns None if using default)
custom_prompt = get_agent_prompt("consultant")

# Reset to default
reset_agent_prompt("consultant")
```

## Security Considerations

1. **Role Verification**
   - Admin endpoints check `is_admin` flag
   - Superadmin endpoints check `is_superadmin` flag
   - JWT tokens include role information

2. **Audit Trail**
   - All prompt changes tracked with `updated_by` user ID
   - All configuration changes tracked
   - Timestamps recorded for all changes

3. **Permission Hierarchy**
   - Superadmin has all admin permissions
   - Admin cannot modify prompts or configurations
   - Regular users cannot access admin endpoints

## Monitoring & Analytics

### Key Metrics to Track

1. **Handoff Rate**
   - Target: <20%
   - Indicates routing accuracy
   - High rate may mean poor initial routing

2. **Most Common Handoff Paths**
   - Shows which agent transitions occur most
   - Helps identify routing issues
   - Example: If consultant→architect is very common, maybe route directly to architect

3. **User Distribution**
   - How many users on multi-agent
   - How many via override vs rollout
   - Helps plan full deployment

### Admin Dashboard Queries

```sql
-- Users with overrides
SELECT u.username, uc.config_value
FROM users u
JOIN user_configs uc ON u.user_id = uc.user_id
WHERE uc.config_type = 'features'
  AND uc.config_key = 'multi_agent_enabled';

-- Custom prompts in use
SELECT agent_name, updated_by, updated_at
FROM agent_prompts
WHERE is_active = 1;

-- Recent handoffs
SELECT from_agent, to_agent, COUNT(*) as count
FROM agent_handoffs
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY from_agent, to_agent
ORDER BY count DESC;
```

## Troubleshooting

### Issue: Admin can't access endpoints
**Diagnosis:**
```python
from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT username, is_admin, is_superadmin FROM users WHERE username = ?", ("admin_username",))
    print(cursor.fetchone())
```

**Fix:**
```python
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ("admin_username",))
```

### Issue: Superadmin can't edit prompts
**Diagnosis:**
```python
# Check if user is superadmin
from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT is_superadmin FROM users WHERE user_id = ?", ("user_id",))
    print(cursor.fetchone())
```

**Fix:**
```python
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_superadmin = 1 WHERE user_id = ?", ("user_id",))
```

### Issue: Custom prompts not being used
**Diagnosis:**
```python
from database import get_agent_prompt

# Check if custom prompt exists and is active
custom = get_agent_prompt("consultant")
print(f"Custom prompt: {custom is not None}")
```

**Fix:**
```python
from database import set_agent_prompt

# Ensure prompt is set and active
set_agent_prompt("consultant", "Your custom prompt...", "superadmin_id")
```

## Best Practices

1. **Rollout Strategy**
   - Start with 0% (disabled)
   - Enable for admins/beta testers via overrides
   - Gradually increase: 5% → 10% → 25% → 50% → 100%
   - Monitor metrics at each step

2. **Prompt Customization**
   - Test custom prompts with direct endpoint first
   - Document why changes were made
   - Keep default prompts for reference
   - Can always reset to default

3. **User Management**
   - Use overrides for VIP users or beta testers
   - Use rollout percentage for gradual deployment
   - Remove overrides when not needed (simplifies management)

4. **Monitoring**
   - Check analytics daily during rollout
   - Alert on handoff rate >30%
   - Review handoff paths weekly
   - Track prompt change impact

## Future Enhancements

1. **UI Improvements**
   - Multi-agent tab in Admin page
   - Visual handoff flow diagram
   - Prompt diff viewer (compare default vs custom)
   - Rollout scheduler (auto-increase percentage)

2. **Analytics**
   - Per-agent response quality metrics
   - Routing accuracy tracking
   - User satisfaction by agent
   - Cost tracking per agent

3. **Features**
   - A/B testing framework
   - Prompt version history
   - Automated prompt optimization
   - Agent performance dashboards

## Summary

With these admin and superadmin features, you can:

✅ **Admins:**
- Control multi-agent rollout (0-100%)
- Enable/disable for specific users
- Monitor handoff analytics
- Manage user access

✅ **Superadmins:**
- Customize agent system prompts
- Configure multi-agent settings
- Track all changes with audit trail
- Reset to defaults when needed

All changes are tracked, reversible, and can be managed via API or Python functions.
