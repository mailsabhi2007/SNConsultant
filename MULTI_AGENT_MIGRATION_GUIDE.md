# Multi-Agent System Migration Guide

## Pre-Deployment Checklist

### 1. Database Migration

The `agent_handoffs` table has been created automatically. Verify:

```bash
python database.py
```

Should show "Database initialized successfully" with no errors.

### 2. Dependencies Check

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Key dependencies for multi-agent:
- `langgraph` - Graph orchestration
- `langchain-anthropic` - Claude integration
- `pydantic` - Structured outputs

### 3. Configuration Validation

Verify system config:

```python
from user_config import get_system_config

# Check API key is set
api_key = get_system_config("anthropic_api_key")
assert api_key, "ANTHROPIC_API_KEY not configured"

# Check model is set
model = get_system_config("anthropic_model")
print(f"Model: {model}")
```

## Deployment Steps

### Step 1: Test Multi-Agent Locally

```bash
python test_multi_agent.py
```

Expected output:
- Successful routing to appropriate agents
- No errors in agent execution
- Proper tool usage

### Step 2: Initialize Feature Flag (Disabled)

```python
from user_config import set_multi_agent_rollout_percentage

# Start with 0% - disabled for all users
set_multi_agent_rollout_percentage(0)
```

### Step 3: Deploy Code

Deploy all new files to production:
- `multi_agent/` directory
- `api/services/multi_agent_service.py`
- Updated `database.py`
- Updated `user_config.py`
- Updated `api/services/agent_service.py`
- Updated `api/routes/chat.py`

### Step 4: Restart Application

```bash
# Stop existing server
# Start new server
uvicorn api.main:app --reload
```

Verify application starts without errors.

## Alpha Phase: Admin-Only Testing

### Enable for Admin User

```python
from user_config import set_multi_agent_override

# Enable for your admin account
set_multi_agent_override("your_admin_user_id", True)
```

### Test via Direct Endpoint

Make requests to `/api/chat/multi-agent/message`:

```bash
curl -X POST http://localhost:8000/api/chat/multi-agent/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is best practice for incident assignment?"}'
```

### Test via Regular Endpoint (Feature Flag)

Since admin has override enabled, regular endpoint should use multi-agent:

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a business rule to auto-assign incidents"}'
```

### Monitor Handoffs

```python
from api.services.multi_agent_service import get_handoff_analytics

# Check handoff patterns
analytics = get_handoff_analytics(days=7)
print(analytics)
```

Expected metrics:
- `total_handoffs`: Number of handoffs
- `handoff_paths`: Which agent transitions occurred
- `handoff_rate_percentage`: % of conversations with handoffs

### Testing Checklist

- [ ] Consultant agent handles best practice queries
- [ ] Solution Architect agent generates code
- [ ] Implementation agent asks for permission before live instance
- [ ] Handoffs work correctly between agents
- [ ] Circular handoff prevention works
- [ ] Step limits enforced (max 10 per agent)
- [ ] Permission gate blocks live instance access
- [ ] Handoffs saved to database
- [ ] No errors in logs
- [ ] Response quality is good

### Duration

**Recommended: 1 week**

Fix any bugs discovered before proceeding to beta.

## Beta Phase: 10% Rollout

### Enable for 10% of Users

```python
from user_config import set_multi_agent_rollout_percentage

# 10% rollout
set_multi_agent_rollout_percentage(10)
```

This uses consistent hashing - same user always gets same result.

### Monitor Key Metrics

1. **Error Rate**

```sql
-- Check for errors in conversation logs
SELECT COUNT(*)
FROM messages
WHERE role = 'assistant'
  AND content LIKE '%error%'
  AND created_at >= datetime('now', '-7 days');
```

2. **Handoff Rate**

```python
analytics = get_handoff_analytics(days=7)
print(f"Handoff rate: {analytics['handoff_rate_percentage']}%")
```

Target: <20% handoff rate (most queries resolved by first agent)

3. **User Satisfaction**

Monitor user feedback and conversation quality.

4. **Routing Accuracy**

```sql
-- Check if orchestrator picks correct agent initially
SELECT
  from_agent,
  COUNT(*) as handoffs
FROM agent_handoffs
WHERE from_agent = 'orchestrator'
  AND timestamp >= datetime('now', '-7 days')
GROUP BY from_agent;
```

Low handoffs from first routed agent = good routing accuracy.

### A/B Testing

Compare multi-agent (10%) vs single-agent (90%):

- Response quality (LLM judge scores)
- User engagement (conversation length)
- Error rate
- User satisfaction

### Rollback if Needed

If issues detected:

```python
# Instant rollback - disable multi-agent
set_multi_agent_rollout_percentage(0)
```

All users fall back to legacy single agent immediately.

### Duration

**Recommended: 2-4 weeks**

Collect sufficient data for comparison.

## General Availability: 100% Rollout

### Prerequisites

- [ ] Error rate same or lower than single agent
- [ ] User satisfaction same or higher
- [ ] No critical bugs
- [ ] Handoff rate <20%
- [ ] Routing accuracy >90%

### Enable for All Users

```python
from user_config import set_multi_agent_rollout_percentage

# Full rollout
set_multi_agent_rollout_percentage(100)
```

### Monitor Closely

Watch metrics for first week:
- Error rate
- Handoff patterns
- User feedback
- Performance (latency)

### Keep Legacy Agent as Fallback

Don't delete legacy agent code for 1 month.

If major issues:
```python
set_multi_agent_rollout_percentage(0)  # Instant fallback
```

### Deprecate Legacy Agent

After 1 month of stable 100% rollout:
1. Remove feature flag check from `agent_service.py`
2. Delete legacy agent code (optional)
3. Update frontend to show agent indicators

### Duration

**Recommended: 1 month monitoring, then deprecate legacy**

## Configuration Management

### System-Wide Config

```python
from user_config import set_system_config, get_system_config

# Get current rollout
percentage = get_system_config('multi_agent_rollout_percentage', 0)
print(f"Current rollout: {percentage}%")

# Update rollout
set_multi_agent_rollout_percentage(25)  # 25%
```

### User-Specific Overrides

```python
from user_config import set_multi_agent_override, get_user_config

# Enable for specific user (e.g., early access beta testers)
set_multi_agent_override("user123", True)

# Disable for specific user (e.g., if they report issues)
set_multi_agent_override("user456", False)

# Check user status
enabled = get_user_config("user789", "features", "multi_agent_enabled")
print(f"Multi-agent enabled: {enabled}")
```

### Gradual Rollout Schedule Example

```python
# Week 1: Admin only
set_multi_agent_rollout_percentage(0)
set_multi_agent_override("admin_user", True)

# Week 2: 5% users
set_multi_agent_rollout_percentage(5)

# Week 3: 10% users
set_multi_agent_rollout_percentage(10)

# Week 5: 25% users (if metrics look good)
set_multi_agent_rollout_percentage(25)

# Week 7: 50% users
set_multi_agent_rollout_percentage(50)

# Week 9: 75% users
set_multi_agent_rollout_percentage(75)

# Week 11: 100% users
set_multi_agent_rollout_percentage(100)
```

## Monitoring & Analytics

### Real-Time Monitoring

```python
from api.services.multi_agent_service import get_handoff_analytics

# Last 24 hours
analytics = get_handoff_analytics(days=1)

print(f"Total handoffs: {analytics['total_handoffs']}")
print(f"Handoff rate: {analytics['handoff_rate_percentage']}%")
print("\nMost common paths:")
for path in analytics['handoff_paths'][:5]:
    print(f"  {path['from']} → {path['to']}: {path['count']}")
```

### Database Queries

```sql
-- Handoffs in last 7 days
SELECT
  from_agent,
  to_agent,
  COUNT(*) as count
FROM agent_handoffs
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY from_agent, to_agent
ORDER BY count DESC;

-- Conversations with most handoffs
SELECT
  conversation_id,
  COUNT(*) as handoff_count
FROM agent_handoffs
GROUP BY conversation_id
HAVING handoff_count > 2
ORDER BY handoff_count DESC;

-- Agent utilization (initial routing)
SELECT
  current_agent,
  COUNT(*) as count
FROM (
  -- Get first message in each conversation
  SELECT
    conversation_id,
    MIN(timestamp) as first_message
  FROM messages
  WHERE created_at >= datetime('now', '-7 days')
  GROUP BY conversation_id
) AS first_messages
JOIN messages m ON m.conversation_id = first_messages.conversation_id
WHERE m.timestamp = first_messages.first_message
GROUP BY current_agent;
```

### Performance Metrics

Monitor:
- Response latency (should be comparable to single agent)
- Token usage (may be higher due to multiple agents)
- API costs (orchestrator uses Haiku, agents use Sonnet)

### Alerts

Set up alerts for:
- Error rate spikes
- Handoff rate >30%
- Circular handoffs detected
- Step limits frequently hit
- Permission gate failures

## Troubleshooting

### Issue: Multi-Agent Not Activating

**Symptoms:** Users still getting single agent responses

**Diagnosis:**
```python
from user_config import is_multi_agent_enabled

user_id = "test_user"
enabled = is_multi_agent_enabled(user_id)
print(f"Multi-agent enabled for {user_id}: {enabled}")

# Check system rollout
from user_config import get_system_config
rollout = get_system_config('multi_agent_rollout_percentage', 0)
print(f"System rollout: {rollout}%")
```

**Fix:**
- Ensure rollout percentage > 0
- Check user isn't explicitly disabled via override
- Verify feature flag logic in `agent_service.py`

### Issue: Circular Handoffs

**Symptoms:** Same handoff pattern repeating (A→B→A)

**Diagnosis:**
```sql
SELECT * FROM agent_handoffs
WHERE conversation_id = ?
ORDER BY timestamp;
```

**Fix:**
- Review agent system prompts - ensure clear handoff criteria
- Check handoff detection logic in `should_continue()`
- Verify circular detection threshold (currently 3 same paths)

### Issue: Permission Gate Not Working

**Symptoms:** Implementation agent accessing instance without permission

**Diagnosis:**
- Check `live_instance_permission_granted` in state
- Review confirmation keywords in user messages
- Check permission message is being sent

**Fix:**
- Update confirmation keywords if needed
- Ensure permission state persists in conversation
- Review implementation agent permission gate logic

### Issue: High Error Rate

**Symptoms:** Agents throwing errors frequently

**Diagnosis:**
```sql
SELECT
  role,
  content
FROM messages
WHERE content LIKE '%error%'
  AND created_at >= datetime('now', '-24 hours')
ORDER BY created_at DESC
LIMIT 50;
```

**Fix:**
- Check API key validity
- Review error logs for specific failures
- Verify tool configurations (ServiceNow credentials, etc.)
- Check model availability

### Issue: Poor Routing Accuracy

**Symptoms:** Many handoffs from initially routed agent

**Diagnosis:**
```sql
SELECT
  COUNT(*) as handoffs
FROM agent_handoffs
WHERE from_agent IN ('consultant', 'solution_architect', 'implementation')
  AND timestamp >= datetime('now', '-7 days');
```

**Fix:**
- Review orchestrator system prompt
- Add more examples to routing guidelines
- Consider collecting user feedback on routing accuracy
- Fine-tune routing decision criteria

## Success Criteria

### Before Beta (10%)
- [ ] Zero critical bugs in alpha
- [ ] Handoffs work correctly
- [ ] Permission gate functional
- [ ] No circular handoffs
- [ ] Admin approval

### Before GA (100%)
- [ ] Error rate ≤ single agent baseline
- [ ] Handoff rate <20%
- [ ] Routing accuracy >90%
- [ ] User satisfaction ≥ single agent baseline
- [ ] Performance within acceptable range
- [ ] No critical bugs in beta

### Post-GA Success
- [ ] 1 month stable operation
- [ ] User feedback positive
- [ ] Analytics showing value (better responses, fewer errors)
- [ ] Legacy agent can be deprecated

## Rollback Procedures

### Emergency Rollback (Production Issue)

```python
from user_config import set_multi_agent_rollout_percentage

# IMMEDIATE - disable for all users
set_multi_agent_rollout_percentage(0)

# Verify
rollout = get_system_config('multi_agent_rollout_percentage')
assert rollout == 0, "Rollback failed!"
```

No code deployment needed - takes effect immediately.

### Partial Rollback (Specific Users)

```python
from user_config import set_multi_agent_override

# Disable for specific users reporting issues
problem_users = ["user123", "user456"]
for user_id in problem_users:
    set_multi_agent_override(user_id, False)
```

### Gradual Rollback

```python
# Reduce rollout percentage gradually
set_multi_agent_rollout_percentage(50)  # From 100%
# Monitor...
set_multi_agent_rollout_percentage(25)  # From 50%
# Monitor...
set_multi_agent_rollout_percentage(0)   # Complete rollback
```

## Support & Documentation

- **Implementation Docs**: `MULTI_AGENT_IMPLEMENTATION.md`
- **Migration Guide**: This file
- **Test Script**: `test_multi_agent.py`
- **Code**: `multi_agent/` directory

For issues:
1. Check troubleshooting section above
2. Review error logs
3. Check database for handoff patterns
4. Test with `test_multi_agent.py`
5. Roll back if critical issue

## Timeline Summary

| Phase | Duration | Rollout | Goal |
|-------|----------|---------|------|
| Alpha | 1 week | Admin only | Fix bugs, validate system |
| Beta | 2-4 weeks | 10% users | A/B test, collect metrics |
| GA | Ongoing | 100% users | Full deployment |
| Deprecation | 1 month after GA | N/A | Remove legacy agent |

**Total: ~6-9 weeks from deployment to full GA**
