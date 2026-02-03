# Multi-Agent Orchestration Implementation

## Overview

The multi-agent system transforms the single ServiceNow Consultant agent into a coordinated team of three specialists:

1. **Consultant Agent** - Best practices, OOB configurations, general advice
2. **Solution Architect Agent** - Custom code, scripts, schema design
3. **Implementation Agent** - Live instance troubleshooting and diagnostics

An intelligent **Orchestrator** routes queries to the appropriate specialist and enables agent-to-agent handoffs.

## Architecture

### Pattern: Hybrid Supervisor + Autonomous Handoff

- **Orchestrator** (LLM-based) routes initial queries to the best-suited specialist
- **Agents** can detect when they need help and request handoffs to other specialists
- **Single StateGraph** with all agents as nodes for simpler state management
- **Tool-based handoffs** using LangGraph Command pattern

### Graph Flow

```
Entry: orchestrator (routes to specialist)
  ↓
  ├─→ consultant (default, can handoff to architect/implementation)
  │     ↓ tools ↰ (returns to consultant)
  ├─→ solution_architect (custom solutions, can handoff to implementation)
  │     ↓ tools ↰ (returns to architect)
  └─→ implementation (live instance, can handoff back to consultant)
        ↓ tools ↰ (returns to implementation)
```

## Directory Structure

```
multi_agent/
├── __init__.py
├── state.py                    # MultiAgentState schema, HandoffRecord, AgentContext
├── handoff_tools.py            # request_handoff tool
├── utils.py                    # Helper functions for context and handoffs
├── orchestrator.py             # LLM-based routing logic
├── graph.py                    # StateGraph assembly
└── agents/
    ├── __init__.py
    ├── base_agent.py           # Shared utilities for all agents
    ├── consultant.py           # Consultant agent implementation
    ├── solution_architect.py   # Solution Architect agent implementation
    └── implementation.py       # Implementation agent implementation
```

## Key Components

### 1. State Schema (`multi_agent/state.py`)

Extended state tracking for multi-agent orchestration:

```python
class MultiAgentState(TypedDict):
    # Core (existing)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: Optional[str]
    conversation_id: Optional[int]
    is_cached: Optional[bool]
    judge_result: Optional[Dict[str, Any]]

    # Agent tracking (NEW)
    current_agent: Optional[str]
    previous_agent: Optional[str]
    handoff_history: List[HandoffRecord]
    agent_contexts: Dict[str, AgentContext]

    # Handoff control (NEW)
    handoff_requested: Optional[bool]
    handoff_target: Optional[str]
    handoff_reason: Optional[str]

    # Permission tracking (NEW)
    live_instance_permission_granted: Optional[bool]
    agent_step_counts: Dict[str, int]
```

### 2. Handoff Tool (`multi_agent/handoff_tools.py`)

Agents use this tool to request handoffs:

```python
@tool
def request_handoff(
    target_agent: Literal["consultant", "solution_architect", "implementation"],
    reason: str,
    context_summary: str
) -> str:
    """Request handoff to another specialist."""
```

### 3. Orchestrator (`multi_agent/orchestrator.py`)

LLM-based routing with structured output:

```python
class RouteDecision(BaseModel):
    agent: Literal["consultant", "solution_architect", "implementation"]
    reasoning: str
```

Uses Claude 3.5 Haiku for fast, cost-effective routing.

### 4. Specialized Agents

Each agent has:
- **Custom system prompt** tailored to their specialty
- **Specific tool set** for their domain
- **Handoff detection** logic to recognize when another agent is needed
- **Context tracking** to accumulate findings and recommendations

#### Consultant Agent (`multi_agent/agents/consultant.py`)

**Tools:**
- `consult_public_docs` - ServiceNow documentation
- `consult_user_context` - User-uploaded documents
- `save_learned_preference` - Learn from feedback
- `request_handoff` - Hand off to other agents

**Expertise:**
- Best practices and recommendations
- OOB configurations
- General consulting advice
- Documentation interpretation

#### Solution Architect Agent (`multi_agent/agents/solution_architect.py`)

**Tools:**
- `consult_public_docs` - API documentation
- `consult_user_context` - Coding standards
- `check_table_schema` - Schema information
- `save_learned_preference` - Learn preferences
- `request_handoff` - Hand off to other agents

**Expertise:**
- Custom script development
- Business rules, client scripts, UI actions
- Schema and table design
- Integration patterns
- Security best practices

#### Implementation Agent (`multi_agent/agents/implementation.py`)

**Tools:**
- `consult_public_docs` - Known errors
- `check_live_instance` - Live instance access (with permission)
- `check_table_schema` - Table structure
- `fetch_recent_changes` - Recent modifications
- `get_error_logs` - Error diagnostics
- `request_handoff` - Hand off to other agents

**Expertise:**
- Live instance troubleshooting
- Error log analysis
- Configuration debugging
- Recent change investigation

### 5. Graph Assembly (`multi_agent/graph.py`)

Single StateGraph with conditional routing:

```python
workflow.add_conditional_edges(
    "consultant",
    should_continue,
    {
        "tools": "tools",
        "solution_architect": "solution_architect",
        "implementation": "implementation",
        "end": END
    }
)
```

## Safety Features

### Circular Handoff Prevention

Detects and prevents infinite handoff loops:
- Tracks last 5 handoffs in state
- Detects A→B→A ping-pong patterns
- Blocks if same path appears 3+ times
- Gracefully ends with summary of findings

### Agent Step Limits

Prevents infinite tool loops:
- Maximum 10 steps per agent
- Gracefully ends with summary when limit reached
- Step counts tracked in state

### Permission Gate for Live Instance

Implementation agent requires explicit user permission:
- Checks `live_instance_permission_granted` in state
- Asks for permission before accessing live instance
- Permission persists for entire conversation
- Follows same confirmation keywords as legacy agent

## API Integration

### Feature Flag System

Gradual rollout using percentage-based feature flag:

```python
def is_multi_agent_enabled(user_id: str) -> bool:
    """Check if multi-agent is enabled for user."""
    # 1. Check user-specific override
    # 2. Check system rollout percentage
    # 3. Use consistent hashing for stable rollout
```

**Configuration:**
- `multi_agent_rollout_percentage` (system config): 0-100
- `multi_agent_enabled` (user config): per-user override

### Endpoints

1. **`POST /api/chat/message`** - Main endpoint
   - Automatically routes to multi-agent if enabled for user
   - Backward compatible with single agent

2. **`POST /api/chat/multi-agent/message`** - Direct access
   - Always uses multi-agent system
   - Bypasses feature flag
   - Useful for testing and admin preview

### Service Layer

**`api/services/agent_service.py`** - Routes based on feature flag:

```python
async def send_message(message, user_id, conversation_id):
    if is_multi_agent_enabled(user_id):
        return await send_multi_agent_message(...)
    else:
        # Legacy single agent
        agent = get_agent(user_id)
        return await agent.invoke(...)
```

**`api/services/multi_agent_service.py`** - Multi-agent wrapper:

```python
async def send_multi_agent_message(message, user_id, conversation_id):
    orchestrator = MultiAgentOrchestrator(user_id)
    result = await orchestrator.invoke(message, conversation_id)
    # Save handoff records to database
    # Return formatted response
```

## Database Schema

### Agent Handoffs Table

```sql
CREATE TABLE agent_handoffs (
    handoff_id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,
    reason TEXT,
    context_summary TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
)
```

**Indexes:**
- `idx_agent_handoffs_conversation` - Query by conversation
- `idx_agent_handoffs_timestamp` - Time-based analytics

## Analytics

### Handoff Analytics (`api/services/multi_agent_service.py`)

```python
def get_handoff_analytics(days=30):
    """Get analytics on agent handoffs."""
    return {
        "total_handoffs": int,
        "handoff_paths": [{"from": str, "to": str, "count": int}],
        "conversations_with_handoffs": int,
        "total_conversations": int,
        "handoff_rate_percentage": float
    }
```

**Metrics to Track:**
- Handoff rate (% conversations with handoffs)
- Most common paths (Consultant→Architect, etc.)
- Routing accuracy (initial agent selection)
- Agent utilization (% queries handled by each)
- Response quality by agent (via LLM judge)

## Deployment Strategy

### Phase 1: Alpha (Month 1) - Admin Only

```python
# Set admin-only access
set_multi_agent_override("admin_user_id", True)
set_multi_agent_rollout_percentage(0)  # Disabled for all others
```

Access via `/api/chat/multi-agent/message` endpoint.

**Goals:**
- Fix bugs and edge cases
- Monitor handoff patterns
- Collect initial metrics

### Phase 2: Beta (Month 2) - 10% Users

```python
# Gradual rollout
set_multi_agent_rollout_percentage(10)
```

**Goals:**
- A/B testing vs single agent
- Track user satisfaction
- Compare response quality
- Collect user feedback

### Phase 3: GA (Month 3) - 100% Users

```python
# Full rollout
set_multi_agent_rollout_percentage(100)
```

**Goals:**
- All users on multi-agent
- Keep legacy agent for 1 month as fallback
- Deprecate single agent after stability confirmed

## Testing

### Unit Tests

Create tests for:
- Each agent responds correctly with their tool set
- `request_handoff` tool sets state flags correctly
- Circular handoff detection works
- Permission gate blocks/allows appropriately
- Step limit enforcement

### Integration Tests

Test scenarios:
1. **Orchestrator routing** - Correct initial agent selection
2. **Handoff preservation** - Context maintained across handoffs
3. **Multi-turn conversations** - State consistency
4. **Tool execution** - Tools work in each agent

### End-to-End Tests

Use `test_multi_agent.py` for E2E testing:

```python
python test_multi_agent.py
```

Test flows:
1. **Consultant flow**: "What's best practice for incident assignment?"
2. **Handoff to Architect**: "I want a custom assignment rule"
3. **Handoff to Implementation**: "My incident table is broken"
4. **Permission gate**: Verify implementation asks for permission
5. **Circular prevention**: Force A→B→A, verify graceful stop

## Configuration

### System Config

```python
from user_config import set_system_config, set_multi_agent_rollout_percentage

# Set rollout percentage (0-100)
set_multi_agent_rollout_percentage(10)  # 10% of users
```

### User Override

```python
from user_config import set_multi_agent_override

# Enable for specific user
set_multi_agent_override("user123", True)

# Disable for specific user
set_multi_agent_override("user456", False)
```

### Feature Flag Check

```python
from user_config import is_multi_agent_enabled

if is_multi_agent_enabled(user_id):
    # Use multi-agent
    pass
```

## Rollback Plan

If issues arise:

```python
# Instant disable - all users fall back to legacy agent
set_multi_agent_rollout_percentage(0)
```

No code deployment needed - configuration change takes effect immediately.

## Future Enhancements

1. **LLM Judge Integration** - Evaluate multi-agent responses
2. **Semantic Caching** - Cache multi-agent responses
3. **History Manager** - Track agent transitions in conversation history
4. **Frontend Indicators** - Show which agent is responding
5. **Admin Dashboard** - Visualize handoff analytics
6. **Agent Performance Metrics** - Per-agent response quality tracking
7. **Routing Accuracy Monitoring** - Track orchestrator success rate

## Troubleshooting

### Multi-Agent Not Activating

Check:
1. Feature flag: `is_multi_agent_enabled(user_id)`
2. System config: `get_system_config('multi_agent_rollout_percentage')`
3. User override: `get_user_config(user_id, 'features', 'multi_agent_enabled')`

### Circular Handoffs

Review `agent_handoffs` table:

```sql
SELECT * FROM agent_handoffs
WHERE conversation_id = ?
ORDER BY timestamp;
```

Check for repeated patterns.

### Permission Gate Not Working

Verify confirmation keywords in user message:
- "yes", "please check", "go ahead", "connect", "sure", "okay", "proceed"

Check `live_instance_permission_granted` in state.

### Agent Step Limit Reached

Review `agent_step_counts` in state.
Check for tool loops in conversation history.

## Files Modified

- `database.py` - Added `agent_handoffs` table
- `user_config.py` - Added feature flag functions
- `api/services/agent_service.py` - Added routing logic
- `api/routes/chat.py` - Added multi-agent endpoint

## Files Created

- `multi_agent/` - Complete multi-agent system
- `api/services/multi_agent_service.py` - Service wrapper
- `test_multi_agent.py` - Test script
- `MULTI_AGENT_IMPLEMENTATION.md` - This documentation

## Next Steps

1. **Test the system**: Run `python test_multi_agent.py`
2. **Enable for admin**: Set admin user override to True
3. **Monitor handoffs**: Check `agent_handoffs` table
4. **Collect metrics**: Use `get_handoff_analytics()`
5. **Gradual rollout**: Increase percentage over time
6. **Add LLM judge**: Evaluate multi-agent response quality
7. **Build admin UI**: Visualize analytics and manage rollout
