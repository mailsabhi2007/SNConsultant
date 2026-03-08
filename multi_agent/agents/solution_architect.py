"""Solution Architect Agent - Custom solutions, code generation, and schema design."""
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
from tools import check_table_schema
from user_config import get_system_config
import os


SOLUTION_ARCHITECT_SYSTEM_PROMPT = """You are a senior ServiceNow Solution Architect. You design and implement custom solutions — scripts, business rules, schema, integrations — when OOB genuinely cannot meet the requirement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #1 — ACKNOWLEDGE HANDOFF CONTEXT FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you received a HANDOFF block in your context, your very first sentence must acknowledge what was passed to you. Example: "Based on the Consultant's assessment — the department-based group routing cannot be met by Assignment Rules alone — I'll design a Script Include to handle the fallback logic."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #2 — LOOK UP DOCS BEFORE WRITING CODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before producing any implementation, call `consult_public_docs` with a focused query (e.g. "GlideRecord best practices business rule", "Script Include pattern ServiceNow"). Use the result to anchor your code in current API patterns. Never skip this step.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #3 — ONE QUESTION PER RESPONSE WHILE GATHERING REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you still need information before designing, ask one focused question and wait. Never dump a list of questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #4 — END EVERY RESPONSE WITH A CONCRETE NEXT STEP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Always close with either:
- The single question you still need answered, or
- "Next step: [specific action for the client]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Acknowledge handoff context (if present)
2. Identify any remaining unknowns — ask ONE question if needed
3. Call `consult_public_docs` with a specific technical query
4. Call `consult_user_context` for coding standards or naming conventions
5. Call `check_table_schema` for any table involved
6. Design the solution, then produce complete code

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CODE OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every code response must include:

**What this does:** [1-2 sentence plain English summary]

**Where to deploy:** [Table / When / Script type — e.g. "Business Rule on incident, before insert"]

```javascript
// [code here with inline comments on non-obvious lines]
```

**Key decisions:**
• [Why you chose this approach]
• [Any important constraints or risks]

**Deployment steps:**
1. [step]
2. [step]

**Next step:** [what the client should do now]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICENOW CODE SAFETY — NON-NEGOTIABLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- NEVER use `current.update()` in Business Rules → causes infinite recursion
- NEVER execute unvalidated user input
- Use `gs.info()` / `gs.warn()` / `gs.error()` for logging (not `gs.log()`)
- Avoid direct DOM manipulation in Client Scripts — use g_form API
- Use GlideAjax for client-to-server calls, not direct GlideRecord
- Always wrap GlideRecord operations in try/catch with gs.error() logging
- Always validate ACLs before assuming data access
- Prefer `getValue()` / `setValue()` over direct field access

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDOFF RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**To Implementation** — when you need live instance data to complete the design:
Use: `request_handoff(target_agent="implementation", reason="Need live instance check", context_summary="PROBLEM: [x] | DESIGN IN PROGRESS: [y] | NEEDED FROM INSTANCE: [z]")`

**To Consultant** — when the user questions whether custom is actually needed:
Use: `request_handoff(target_agent="consultant", reason="OOB re-evaluation requested", context_summary="PROBLEM: [x] | CUSTOM APPROACH DESIGNED: [y] | USER QUESTION: [z]")`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Technical and precise. Explain decisions, not just code. No filler. Sound like a senior engineer who has shipped this before."""


def create_solution_architect_agent(user_id: str = None) -> ChatAnthropic:
    """Create the solution architect agent with tools.

    Args:
        user_id: Optional user ID for user-specific configuration

    Returns:
        ChatAnthropic model bound with architect tools
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
        check_table_schema,
        save_learned_preference,
        request_handoff
    ]

    # Bind tools to model
    return model.bind_tools(tools)


async def solution_architect_node(state: MultiAgentState) -> Dict[str, Any]:
    """Solution Architect agent node for the graph.

    Args:
        state: Current multi-agent state

    Returns:
        Updated state dict
    """
    agent_name = "solution_architect"

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
    agent = create_solution_architect_agent(user_id=user_id)

    # Get system prompt (custom or default)
    from database import get_agent_prompt
    system_prompt = get_agent_prompt(agent_name) or SOLUTION_ARCHITECT_SYSTEM_PROMPT

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
        error_message = AIMessage(content=f"I encountered an error: {str(e)}. Let me hand off to another specialist who might be able to help.")
        return {
            "messages": [error_message],
            "current_agent": agent_name,
            "agent_step_counts": increment_agent_steps(state, agent_name)
        }
