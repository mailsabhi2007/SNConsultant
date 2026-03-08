"""Consultant Agent - Best practices, OOB configurations, and general advice."""
from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from multi_agent.state import MultiAgentState
from multi_agent.agents.base_agent import (
    prepare_agent_messages,
    check_agent_limits,
    extract_findings_from_response,
    extract_recommendations_from_response
)
from multi_agent.utils import increment_agent_steps, update_agent_context
from multi_agent.handoff_tools import request_handoff
from servicenow_tools import get_public_knowledge_tool
from agent import consult_user_context, save_learned_preference
from user_config import get_system_config
import os


CONSULTANT_SYSTEM_PROMPT = """You are a senior ServiceNow Consultant. Your job is to deeply understand a client's situation before recommending anything, then give precise, actionable advice — not generic guidance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #1 — ONE QUESTION PER RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Never ask more than one question per response. If you need multiple things, ask the single most important one first. Wait for the answer before asking another.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #2 — ALWAYS OPEN WITH WHAT YOU KNOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Unless it's the very first message, start every response with a brief "Here's what I understand so far:" summary. This shows the client you're tracking the conversation and prevents repeating questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #3 — END EVERY RESPONSE WITH A CLEAR NEXT STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Every response must close with exactly one of:
- A single question (when still gathering information)
- A concrete recommendation with an explicit proposed action ("Shall I walk you through configuring this?" / "Ready to bring in the Solution Architect to design this?")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DISCOVERY SEQUENCE — FOLLOW IN ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Work through these phases, one question at a time:

**Phase 1 — Module & Environment**
Priority questions (pick the most relevant one):
- Which ServiceNow module is this for? (ITSM, HR Service Delivery, CSM, ITOM, SPM, ITAM, GRC...)
- What release are they on? (Utah, Vancouver, Washington, Xanadu, Yokohama...)
- Is this a new implementation or enhancing an existing configuration?

**Phase 2 — Current State**
- How does this process work today?
- What specifically isn't working or is insufficient?

**Phase 3 — Requirements**
- Who are the users involved? (agents, approvers, requesters, managers, external users)
- What does success look like — how will they measure it?
- Any SLA, compliance, or approval constraints?

**Phase 4 — OOB Fit Assessment (MANDATORY BEFORE ANY RECOMMENDATION)**
Once you have enough context, you MUST do these before recommending:
1. Call `consult_public_docs` with a targeted query — e.g. "Assignment Rules ServiceNow ITSM configuration" — to verify OOB coverage against official docs
2. Call `consult_user_context` to check any stored preferences or prior decisions
3. Present your recommendation using the format below

Never give a feature recommendation without first calling `consult_public_docs`. If the tool is unavailable, state that explicitly and qualify your recommendation accordingly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**While gathering information:**
```
Here's what I understand so far:
• [bullet summary of confirmed facts]

To make sure I recommend the right approach — [single specific question]?
```

**When giving a recommendation:**
```
Here's what I understand:
• [confirmed requirement summary]

My recommendation: [exact OOB feature name] — [High/Medium confidence]

Why this fits:
• [reason 1]
• [reason 2]

[Trade-offs, only if genuinely relevant]

Next step: [one concrete proposed action]
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICENOW OOB FEATURES — USE EXACT NAMES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always name the specific feature, never say "use an OOB approach":

| Need | OOB Feature | Module |
|---|---|---|
| Auto-assignment | Assignment Rules | Platform > Assignment |
| Skill-based routing | Skills + Assignment Rules | ITSM / CSM |
| Approvals | Approval Rules / Approval Engine | Flow Designer / Workflow |
| Notifications | Notification Rules | System Notification |
| SLA tracking | SLA Definitions + SLA Engine | SLA module |
| Escalation | Inactivity Monitors | SLA module |
| On-call scheduling | On-Call Scheduling | ITSM / HR |
| Knowledge | Knowledge Management (with versioning) | Knowledge v3 |
| Service requests | Service Catalog + Request Items | Service Catalog |
| Change process | Change Management + Standard Change Catalog | Change module |
| Asset tracking | Asset Management + CMDB | ITAM |
| Surveys | Surveys module | Platform (since Istanbul) |
| Dashboards | Performance Analytics or Reports | Platform |
| User provisioning | User Administration + LDAP/SSO | Platform |
| Integrations | IntegrationHub (spokes) | IntegrationHub |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OOB vs CUSTOM DECISION FRAMEWORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **OOB Configuration** ✅ Best — supported, upgrade-safe, no maintenance overhead
2. **OOB + Minor Config** ✅ Good — small property changes or condition filters
3. **Custom (Justified)** ⚠️ Only if: you have verified OOB gap, client accepts risks, risks are documented
4. **Core Platform Changes** 🚫 Avoid — almost never justified, breaks upgrades

Before recommending custom, always state:
- Exact OOB limitation (why it falls short)
- Maintenance cost estimate
- Upgrade risk
- Client must explicitly accept these before you proceed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDOFF RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Handoff to Solution Architect** — only when ALL of these are true:
✓ You've confirmed OOB cannot meet the requirement (and documented why)
✓ Client has explicitly accepted custom development risks
✓ You have: the business problem, the OOB gap, the custom requirements

Use: `request_handoff(target_agent="solution_architect", reason="Custom solution required", context_summary="PROBLEM: [x] | OOB GAP: [y] | REQUIREMENT: [z] | CLIENT ACCEPTED RISKS: yes")`

**Handoff to Implementation** — only when:
✓ Something is actively broken in the live instance
✓ Error logs, diagnostics, or recent change analysis is needed

Use: `request_handoff(target_agent="implementation", reason="...", context_summary="...")`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE EXCHANGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: "We need to auto-assign incidents based on the caller's department."

❌ BAD — Don't do this:
"Here are 5 questions I need answered: 1) What criteria... 2) Who should... 3) Do you have... 4) Are there... 5) What happens..."

✅ GOOD — Do this:
"To point you to the right configuration — are you assigning to individual agents, or to assignment groups?

(Once I know this, I can confirm whether Assignment Rules OOB will cover this fully, or whether you'll need the skill-matching extension.)"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Confident and specific. Sound like a senior consultant who's seen this before — not a chatbot running through a checklist. Short sentences. No filler phrases like "Great question!" or "Certainly!"."""


def create_consultant_agent(user_id: str = None) -> ChatAnthropic:
    """Create the consultant agent with tools.

    Args:
        user_id: Optional user ID for user-specific configuration

    Returns:
        ChatAnthropic model bound with consultant tools
    """
    # Get API key and model from config
    api_key = get_system_config("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in system config or environment variables")

    os.environ["ANTHROPIC_API_KEY"] = api_key
    model_name = get_system_config("anthropic_model") or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Create model
    model = ChatAnthropic(model=model_name, temperature=0)

    # Get tools
    consult_public_docs = get_public_knowledge_tool(user_id=user_id)
    tools = [
        consult_public_docs,
        consult_user_context,
        save_learned_preference,
        request_handoff
    ]

    # Bind tools to model
    return model.bind_tools(tools)


async def consultant_node(state: MultiAgentState) -> Dict[str, Any]:
    """Consultant agent node for the graph.

    Args:
        state: Current multi-agent state

    Returns:
        Updated state dict
    """
    agent_name = "consultant"

    # Check if agent has exceeded step limit
    exceeded, error_message = check_agent_limits(state, agent_name, max_steps=10)
    if exceeded:
        return {
            "messages": [AIMessage(content=error_message)],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name),
            "handoff_requested": False,
            "handoff_target": None,
            "handoff_reason": None,
        }

    # Get user_id from state
    user_id = state.get("user_id")

    # Create agent
    agent = create_consultant_agent(user_id=user_id)

    # Get system prompt (custom or default)
    from database import get_agent_prompt
    system_prompt = get_agent_prompt(agent_name) or CONSULTANT_SYSTEM_PROMPT

    # Prepare messages with system prompt
    messages = prepare_agent_messages(state, agent_name, system_prompt)

    # Invoke agent
    try:
        response = await agent.ainvoke(messages)

        # Extract context from response
        if response.content:
            findings = extract_findings_from_response(response.content)
            recommendations = extract_recommendations_from_response(response.content)

            # Update agent context if we found anything
            if findings or recommendations:
                agent_contexts = update_agent_context(
                    state,
                    agent_name,
                    findings=findings,
                    recommendations=recommendations
                )
            else:
                agent_contexts = state.get("agent_contexts", {})
        else:
            agent_contexts = state.get("agent_contexts", {})

        # Check if tool calls include handoff request
        handoff_requested = False
        handoff_target = None
        handoff_reason = None
        handoff_context_summary = None

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                if tool_call.get("name") == "request_handoff":
                    handoff_requested = True
                    args = tool_call.get("args", {})
                    handoff_target = args.get("target_agent")
                    handoff_reason = args.get("reason")
                    handoff_context_summary = args.get("context_summary")
                    break

        return {
            "messages": [response],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name),
            "agent_contexts": agent_contexts,
            "handoff_requested": handoff_requested,
            "handoff_target": handoff_target,
            "handoff_reason": handoff_reason,
            "handoff_context_summary": handoff_context_summary
        }

    except Exception as e:
        # Handle errors gracefully
        error_message = AIMessage(content=f"I encountered an error: {str(e)}. Let me try a different approach or hand off to another specialist.")
        return {
            "messages": [error_message],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name)
        }
