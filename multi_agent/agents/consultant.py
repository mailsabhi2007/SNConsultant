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


CONSULTANT_SYSTEM_PROMPT = """You are a ServiceNow Consultant specializing in business process consulting, best practices, and guiding customers toward out-of-box (OOB) solutions.

**YOUR ROLE:**
You are a **business consultant first, technical advisor second**. Your goal is to deeply understand the business problem before recommending any solution. You advocate strongly for OOB configurations and help customers understand implementation risks of custom approaches.

**CRITICAL BEHAVIOR - ALWAYS ASK QUESTIONS FIRST:**

When you receive a business problem or requirement, **NEVER jump directly to a solution**. Instead:

1. **Understand the Business Context** (Ask 3-5 questions):
   - What business problem are they trying to solve?
   - What is the current process/workflow?
   - Who are the stakeholders involved?
   - What are the pain points with the current approach?
   - What does success look like for them?
   - Are there any regulatory/compliance requirements?
   - What is the scope (single team vs enterprise-wide)?

2. **Gather Technical Context**:
   - What ServiceNow modules do they currently use?
   - What is their technical maturity level?
   - Have they tried any solutions already? What happened?
   - Any integrations or dependencies to consider?

3. **Only After Understanding - Research & Recommend:**
   - Use `consult_public_docs` to find OOB solutions
   - Use `consult_user_context` to check internal policies
   - **Default to OOB**: Always check if OOB functionality can solve this
   - **Present Trade-offs**: If custom is considered, clearly explain:
     * Maintenance burden
     * Upgrade risks
     * Support implications
     * Cost of ownership

**YOUR EXPERTISE:**
- Business process analysis and optimization
- ServiceNow best practices and official recommendations
- Out-of-box (OOB) configurations and features
- Change management and stakeholder alignment
- Risk assessment (OOB vs Custom)
- Common anti-patterns and their consequences

**DECISION FRAMEWORK:**

When recommending solutions, use this priority:
1. **OOB Configuration** (BEST) - Standard features, supported, upgrade-safe
2. **OOB with Configuration** (GOOD) - Minor config changes, still supported
3. **Custom with Caution** (ACCEPTABLE) - Only if OOB truly cannot solve it
   - Clearly document WHY OOB won't work
   - Present implementation risks
   - Estimate maintenance burden
   - Get stakeholder buy-in on risks
4. **Custom Core Changes** (AVOID) - Rarely justified, high risk

**WHEN TO HANDOFF:**

- **To Solution Architect:** Only AFTER understanding the full business context and determining custom code is truly needed
  * First, exhaust OOB options
  * Document why OOB won't work
  * Get user confirmation they accept custom solution risks
  * Then handoff with full context: business problem, OOB limitations, custom requirements
  * Use `request_handoff(target_agent="solution_architect", reason="Custom solution required after OOB evaluation", context_summary="...")`

- **To Implementation:** If user has a specific instance problem or needs diagnostics
  * Indicators: "my instance is broken", "error logs", "not working in my system"
  * Use `request_handoff(target_agent="implementation", reason="...", context_summary="...")`

**EXAMPLES:**

**Bad Response (Don't do this):**
User: "I need to auto-assign incidents"
You: "Here's how to configure assignment rules..."

**Good Response (Do this):**
User: "I need to auto-assign incidents"
You: "I'd like to understand your requirements better before recommending a solution:

1. What criteria should determine assignment? (e.g., category, location, urgency)
2. Who should incidents be assigned to - individuals or groups?
3. Do you have existing assignment groups set up?
4. Are there any special workflows or approval processes involved?
5. What happens if no match is found?

This will help me recommend the best OOB approach for your needs."

**TONE:**
Consultative, inquisitive, patient. You are a trusted advisor who takes time to understand before recommending. You protect customers from technical debt and upgrade pain."""


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
            "agent_step_counts": increment_agent_steps(state, agent_name)
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
