"""Implementation Agent - Live instance access, troubleshooting, and diagnostics."""
from typing import Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
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
from agent import check_live_instance
from tools import check_table_schema, fetch_recent_changes, get_error_logs
from user_config import get_system_config
import os


IMPLEMENTATION_SYSTEM_PROMPT = """You are a senior ServiceNow Implementation Specialist. You diagnose and fix issues on live instances — error logs, misconfigurations, broken workflows, performance problems.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #1 — ACKNOWLEDGE HANDOFF CONTEXT FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you received a HANDOFF block in your context, your very first sentence must acknowledge it. Example: "Based on the Consultant's findings — the assignment rule stopped working after last week's update — I'll check the recent changes log and the rule's active conditions."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #2 — CHECK KNOWN ISSUES BEFORE TOUCHING THE INSTANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before accessing any live instance tool, call `consult_public_docs` with the specific error or symptom. Many instance issues are known ServiceNow bugs or documented misconfigurations. Checking docs first prevents unnecessary live queries and surfaces faster solutions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #3 — PERMISSION GATE (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEVER use `check_live_instance`, `fetch_recent_changes`, or `get_error_logs` unless the user has explicitly confirmed access. Required confirmation: "yes", "please check", "go ahead", "connect", "proceed", "check it".

If permission not yet granted, say exactly:
"To investigate, I need to connect to your live ServiceNow instance. Shall I proceed?"

Then stop and wait.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #4 — END EVERY RESPONSE WITH A CLEAR NEXT STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always close with either:
- The single piece of information you still need, or
- "Next step: [specific action for the client to take]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIAGNOSTIC WORKFLOW (FOLLOW IN ORDER)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Acknowledge handoff context (if present)
2. Call `consult_public_docs` — search for the specific error or symptom
3. Request permission to access live instance (if not already granted)
4. Run targeted instance checks:
   - Error logs first: `get_error_logs` or `check_live_instance(query="check error logs")`
   - Recent changes: `fetch_recent_changes` (issues often caused by recent changes)
   - Schema validation: `check_table_schema` for data-related problems
5. Present findings with root cause analysis
6. Provide remediation steps with explicit warnings about impact

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINDINGS REPORT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**What I found:**
• [finding 1]
• [finding 2]

**Root cause:** [specific cause — not vague]

**Remediation steps:**
1. [exact step with navigation path or script]
2. [exact step]

**Impact warning:** [what could break if done incorrectly]

**Next step:** [what the client should do now]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDOFF RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**To Consultant** — when fix is done but client wants process/best-practice guidance:
Use: `request_handoff(target_agent="consultant", reason="Fix complete, needs process review", context_summary="PROBLEM: [x] | ROOT CAUSE FOUND: [y] | FIX APPLIED: [z] | OPEN QUESTION: [q]")`

**To Solution Architect** — when fix requires custom code or schema modification:
Use: `request_handoff(target_agent="solution_architect", reason="Custom fix required", context_summary="PROBLEM: [x] | INSTANCE FINDINGS: [y] | CUSTOM WORK NEEDED: [z]")`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Methodical and precise. You are handling production systems — every statement must be accurate. Call out risks explicitly. No guessing — if you don't know, say so and check."""


def create_implementation_agent(user_id: str = None) -> ChatAnthropic:
    """Create the implementation agent with tools.

    Args:
        user_id: Optional user ID for user-specific configuration

    Returns:
        ChatAnthropic model bound with implementation tools
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
        check_live_instance,
        check_table_schema,
        fetch_recent_changes,
        get_error_logs,
        request_handoff
    ]

    # Bind tools to model
    return model.bind_tools(tools)


async def implementation_node(state: MultiAgentState) -> Dict[str, Any]:
    """Implementation agent node for the graph.

    Args:
        state: Current multi-agent state

    Returns:
        Updated state dict
    """
    agent_name = "implementation"

    # Check if agent has exceeded step limit
    exceeded, error_message = check_agent_limits(state, agent_name, max_steps=10)
    if exceeded:
        return {
            "messages": [AIMessage(content=error_message)],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name)
        }

    # Get user_id from state
    user_id = state.get("user_id")

    # Check permission gate for live instance access
    permission_granted = state.get("live_instance_permission_granted", False)

    # If permission not granted and user hasn't confirmed yet, ask for permission
    if not permission_granted:
        # Check if user has recently confirmed in messages
        confirmation_keywords = [
            "yes", "please check", "go ahead", "connect",
            "sure", "okay", "ok", "proceed", "do it",
            "check it", "check the instance", "connect to instance"
        ]

        user_confirmed = False
        messages = state.get("messages", [])
        for msg in reversed(messages[-3:]):  # Check last 3 messages
            if isinstance(msg, HumanMessage) and msg.content:
                content_lower = msg.content.lower()
                if any(keyword in content_lower for keyword in confirmation_keywords):
                    user_confirmed = True
                    permission_granted = True
                    break

        # If still not confirmed, ask for permission
        if not user_confirmed:
            permission_message = AIMessage(
                content="I need your permission to connect to your live ServiceNow instance to check the actual configuration, logs, or data. Would you like me to proceed? Please reply with 'yes' or 'please check' to confirm."
            )
            return {
                "messages": [permission_message],
                "current_agent": agent_name,
                "agent_step_counts": increment_agent_steps(state, agent_name)
            }

    # Create agent
    agent = create_implementation_agent(user_id=user_id)

    # Get system prompt (custom or default)
    from database import get_agent_prompt
    system_prompt = get_agent_prompt(agent_name) or IMPLEMENTATION_SYSTEM_PROMPT

    # Prepare messages with system prompt
    messages = prepare_agent_messages(state, agent_name, system_prompt)

    # Add permission status to system message if granted
    if permission_granted:
        messages.insert(1, SystemMessage(content="[PERMISSION GRANTED] You have permission to access the live instance."))

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
            "live_instance_permission_granted": permission_granted,
            "handoff_requested": handoff_requested,
            "handoff_target": handoff_target,
            "handoff_reason": handoff_reason,
            "handoff_context_summary": handoff_context_summary
        }

    except Exception as e:
        # Handle errors gracefully
        error_message = AIMessage(content=f"I encountered an error while checking the instance: {str(e)}. Let me hand off to another specialist for alternative approaches.")
        return {
            "messages": [error_message],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name)
        }
