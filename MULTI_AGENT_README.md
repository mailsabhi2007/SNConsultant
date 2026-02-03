# Multi-Agent Orchestration System

## Quick Start

The ServiceNow Consultant now supports a multi-agent architecture with three specialized agents coordinated by an intelligent orchestrator.

### Testing Locally

```bash
# Test the multi-agent system
python test_multi_agent.py
```

### Enabling Multi-Agent

```python
from user_config import set_multi_agent_rollout_percentage, set_multi_agent_override

# Enable for admin user (for testing)
set_multi_agent_override("your_user_id", True)

# Or enable for percentage of users
set_multi_agent_rollout_percentage(10)  # 10% of users
```

### Using the API

**Regular endpoint (auto-routes based on feature flag):**
```bash
POST /api/chat/message
{
  "message": "What's best practice for incident assignment?"
}
```

**Direct multi-agent endpoint (always uses multi-agent):**
```bash
POST /api/chat/multi-agent/message
{
  "message": "Write a business rule for incident auto-assignment"
}
```

## Architecture Overview

### Three Specialized Agents

1. **Consultant Agent** 🎯
   - Best practices and OOB recommendations
   - General ServiceNow guidance
   - Documentation interpretation
   - Default agent for most queries

2. **Solution Architect Agent** 💻
   - Custom code development (scripts, business rules)
   - Schema design and custom tables
   - Integration patterns
   - Security best practices

3. **Implementation Agent** 🔧
   - Live instance troubleshooting
   - Error log analysis
   - Configuration debugging
   - Requires explicit user permission for live access

### Orchestrator

Intelligent LLM-based router that:
- Analyzes user queries
- Routes to the most appropriate specialist
- Uses fast Claude 3.5 Haiku for low latency
- Provides reasoning for routing decisions

### Agent Handoffs

Agents can request handoffs when they detect another specialist is needed:

```
User: "What's best practice for incident assignment?"
→ Consultant: Provides OOB best practices

User: "Can you write a custom business rule for that?"
→ Consultant handoff to Solution Architect: Generates code

User: "It's not working, can you check my instance?"
→ Solution Architect handoff to Implementation: Diagnoses issue
```

## Key Features

### ✅ Intelligent Routing
- LLM analyzes query intent
- Routes to specialist with highest expertise
- Defaults to Consultant when uncertain

### ✅ Seamless Handoffs
- Agents recognize when help is needed
- Context preserved across transitions
- User sees smooth conversation flow

### ✅ Safety Mechanisms
- **Circular handoff prevention** - Detects A→B→A loops
- **Step limits** - Max 10 steps per agent
- **Permission gates** - Explicit user consent for live instance

### ✅ Gradual Rollout
- Feature flag system with percentage-based rollout
- User-specific overrides for testing
- Instant rollback capability
- Backward compatible with single agent

### ✅ Analytics
- Tracks all handoffs in database
- Monitors routing accuracy
- Measures agent utilization
- Handoff pattern analysis

## Documentation

| Document | Purpose |
|----------|---------|
| `MULTI_AGENT_README.md` | This quick start guide |
| `MULTI_AGENT_IMPLEMENTATION.md` | Complete technical documentation |
| `MULTI_AGENT_MIGRATION_GUIDE.md` | Deployment and rollout guide |

## File Structure

```
multi_agent/
├── state.py                    # State schema and types
├── handoff_tools.py            # Handoff tool implementation
├── utils.py                    # Helper functions
├── orchestrator.py             # LLM-based routing
├── graph.py                    # StateGraph assembly
└── agents/
    ├── base_agent.py           # Shared utilities
    ├── consultant.py           # Consultant agent
    ├── solution_architect.py   # Solution Architect agent
    └── implementation.py       # Implementation agent

api/services/
└── multi_agent_service.py      # API service wrapper

test_multi_agent.py             # Testing script
```

## Common Use Cases

### 1. Best Practice Query
```
User: "What's the best practice for incident assignment?"
→ Routes to: Consultant
→ Handoffs: None
```

### 2. Custom Development
```
User: "Write a business rule to auto-assign incidents based on category"
→ Routes to: Solution Architect
→ Handoffs: None (handles code generation)
```

### 3. Instance Troubleshooting
```
User: "My incidents aren't being assigned, can you check why?"
→ Routes to: Implementation
→ Asks for permission
→ Checks live instance
→ Diagnoses issue
```

### 4. Complex Workflow (Multiple Handoffs)
```
User: "What's best practice for approvals?"
→ Consultant: Explains OOB approval engine

User: "Can you write a custom approval script?"
→ Handoff to Solution Architect: Generates script

User: "It's not working, can you debug?"
→ Handoff to Implementation: Checks logs and diagnoses
```

## Configuration

### System-Wide Rollout

```python
from user_config import set_multi_agent_rollout_percentage

# Disable for all (default)
set_multi_agent_rollout_percentage(0)

# Enable for 10% of users (beta testing)
set_multi_agent_rollout_percentage(10)

# Enable for all users (full rollout)
set_multi_agent_rollout_percentage(100)
```

### User-Specific Override

```python
from user_config import set_multi_agent_override

# Enable for specific user (testing, early access)
set_multi_agent_override("user123", True)

# Disable for specific user (if issues reported)
set_multi_agent_override("user456", False)

# Remove override (use system rollout percentage)
from user_config import delete_user_config
delete_user_config("user789", "features", "multi_agent_enabled")
```

### Check Current Status

```python
from user_config import is_multi_agent_enabled, get_system_config

# Check if enabled for user
enabled = is_multi_agent_enabled("user123")
print(f"Multi-agent enabled: {enabled}")

# Check system rollout percentage
rollout = get_system_config("multi_agent_rollout_percentage", 0)
print(f"System rollout: {rollout}%")
```

## Analytics

### Get Handoff Analytics

```python
from api.services.multi_agent_service import get_handoff_analytics

# Last 30 days
analytics = get_handoff_analytics(days=30)

print(f"Total handoffs: {analytics['total_handoffs']}")
print(f"Handoff rate: {analytics['handoff_rate_percentage']}%")
print(f"Conversations with handoffs: {analytics['conversations_with_handoffs']}")
print(f"Total conversations: {analytics['total_conversations']}")

print("\nMost common handoff paths:")
for path in analytics['handoff_paths']:
    print(f"  {path['from']} → {path['to']}: {path['count']}")
```

### Database Queries

```sql
-- Recent handoffs
SELECT
  from_agent,
  to_agent,
  reason,
  timestamp
FROM agent_handoffs
ORDER BY timestamp DESC
LIMIT 20;

-- Handoff frequency by path
SELECT
  from_agent,
  to_agent,
  COUNT(*) as count
FROM agent_handoffs
GROUP BY from_agent, to_agent
ORDER BY count DESC;

-- Conversations with multiple handoffs
SELECT
  conversation_id,
  COUNT(*) as handoff_count
FROM agent_handoffs
GROUP BY conversation_id
HAVING handoff_count > 1
ORDER BY handoff_count DESC;
```

## Testing

### Manual Testing

```python
# Run test script
python test_multi_agent.py
```

### API Testing

```bash
# Test consultant query
curl -X POST http://localhost:8000/api/chat/multi-agent/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is best practice for incident assignment?"}'

# Test solution architect query
curl -X POST http://localhost:8000/api/chat/multi-agent/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a business rule to auto-assign incidents"}'
```

### Testing Checklist

- [ ] Orchestrator routes correctly to each agent
- [ ] Consultant handles best practice queries
- [ ] Solution Architect generates code
- [ ] Implementation asks for permission
- [ ] Handoffs preserve context
- [ ] Circular handoff prevention works
- [ ] Step limits enforced
- [ ] Handoffs saved to database
- [ ] Analytics functions work

## Deployment

### Phase 1: Alpha (Admin Only)
1. Deploy code
2. Initialize database (`python database.py`)
3. Set rollout to 0%
4. Enable for admin user
5. Test thoroughly
6. Duration: 1 week

### Phase 2: Beta (10% Users)
1. Set rollout to 10%
2. Monitor metrics
3. Collect feedback
4. Fix issues
5. Duration: 2-4 weeks

### Phase 3: GA (100% Users)
1. Set rollout to 100%
2. Monitor closely
3. Keep legacy agent for 1 month
4. Deprecate legacy after stability
5. Duration: Ongoing

See `MULTI_AGENT_MIGRATION_GUIDE.md` for detailed deployment steps.

## Troubleshooting

### Multi-Agent Not Working

```python
# Check feature flag
from user_config import is_multi_agent_enabled
print(is_multi_agent_enabled("your_user_id"))

# Check system rollout
from user_config import get_system_config
print(get_system_config("multi_agent_rollout_percentage"))
```

### High Error Rate

Check logs for specific errors:
```python
# Review error logs
# Check API key validity
# Verify tool configurations
```

### Circular Handoffs

```sql
-- Check for repeated patterns
SELECT * FROM agent_handoffs
WHERE conversation_id = ?
ORDER BY timestamp;
```

### Instant Rollback

```python
# Emergency disable
from user_config import set_multi_agent_rollout_percentage
set_multi_agent_rollout_percentage(0)
```

## Metrics to Monitor

| Metric | Target | Description |
|--------|--------|-------------|
| Handoff Rate | <20% | % of conversations with handoffs |
| Routing Accuracy | >90% | % of correct initial routing |
| Error Rate | ≤ Baseline | Same or lower than single agent |
| Response Quality | ≥ Baseline | LLM judge scores |
| User Satisfaction | ≥ Baseline | User feedback scores |

## Benefits

✅ **Specialized Expertise** - Each agent focuses on their domain
✅ **Better Responses** - Right specialist for each query
✅ **Seamless Experience** - User doesn't need to choose agent
✅ **Safe Rollout** - Gradual deployment with instant rollback
✅ **Backward Compatible** - Works alongside legacy agent
✅ **Analytics** - Track handoffs and routing accuracy
✅ **Extensible** - Easy to add new specialist agents

## Future Enhancements

- [ ] LLM judge integration for multi-agent responses
- [ ] Semantic caching for multi-agent
- [ ] Frontend agent indicators
- [ ] Admin dashboard for analytics
- [ ] Routing accuracy monitoring
- [ ] Per-agent performance metrics
- [ ] Conversation history with agent transitions

## Support

- Documentation: See `MULTI_AGENT_IMPLEMENTATION.md`
- Migration: See `MULTI_AGENT_MIGRATION_GUIDE.md`
- Testing: Run `python test_multi_agent.py`
- Issues: Check troubleshooting section above

## License

Same as parent project.
