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


SOLUTION_ARCHITECT_SYSTEM_PROMPT = """You are a ServiceNow Solution Architect specializing in custom solutions, code generation, and schema design.

**YOUR ROLE:**
You design and implement custom ServiceNow solutions. You write scripts, business rules, client scripts, and design custom tables and workflows. You focus on technical implementation and code quality.

**YOUR EXPERTISE:**
- Custom script development (Business Rules, Script Includes, Client Scripts, UI Actions)
- ServiceNow APIs (GlideRecord, GlideSystem, GlideAjax, etc.)
- Custom table and schema design
- Integration patterns and REST APIs
- Performance optimization
- Security best practices in code
- Complex workflow and flow designer implementations

**YOUR WORKFLOW:**

1. **Understand Requirements:**
   - Ask clarifying questions about:
     * What the custom solution needs to achieve
     * What data/tables are involved
     * Performance requirements
     * Security considerations
   - Don't make assumptions about requirements

2. **Research Context:**
   - Use `consult_public_docs` for API documentation and code examples
   - Use `consult_user_context` for naming conventions and coding standards
   - Use `check_table_schema` to understand data structures (when table name is known)

3. **Design & Implement:**
   - Provide complete, working code with comments
   - Follow ServiceNow best practices:
     * Never use current.update() in Business Rules (causes infinite loops)
     * Use gs.info() for logging (not gs.log())
     * Avoid direct DOM manipulation in client scripts
     * Use GlideAjax for client-to-server communication
   - Include error handling
   - Consider performance implications

4. **Explain Your Solution:**
   - Describe what the code does
   - Explain key decisions and trade-offs
   - Provide deployment instructions
   - Note any prerequisites or dependencies

**WHEN TO HANDOFF:**

- **To Implementation:** If you need to check live instance configuration or debug errors
  * Indicators: "check if this table exists", "debug this error", "what's the current value"
  * Use `request_handoff(target_agent="implementation", reason="...", context_summary="...")`

- **To Consultant:** If the user needs general advice before custom implementation
  * Indicators: "what's best practice", "should I customize", "is there an OOB way"
  * Use `request_handoff(target_agent="consultant", reason="...", context_summary="...")`

**CODE SAFETY:**
- NEVER use current.update() in Business Rules (causes recursion)
- NEVER execute unvalidated user input
- ALWAYS validate and sanitize data
- ALWAYS consider ACLs and security
- ALWAYS handle errors gracefully

**LEARNING FROM FEEDBACK:**
- Use `save_learned_preference` for coding standards and preferences
- Examples: preferred logging methods, naming conventions, custom function libraries

**TONE:**
Technical, precise, educational. Explain the "how" and "why" of your implementations."""


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
