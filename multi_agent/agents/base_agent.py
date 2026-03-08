"""Base utilities for all specialized agents."""
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, SystemMessage, AIMessage, ToolMessage
from multi_agent.state import MultiAgentState
from multi_agent.utils import (
    extract_agent_context,
    update_agent_context,
    has_exceeded_step_limit,
    increment_agent_steps
)


def sanitize_messages(messages: List[BaseMessage]) -> List[BaseMessage]:
    """Remove orphaned tool_use blocks that have no corresponding tool_result.

    The Anthropic API requires every tool_use block to be immediately followed
    by a tool_result block. During agent handoffs the graph skips the ToolNode,
    leaving the request_handoff tool_use without a result — causing a 400 error.
    This function drops such orphaned AIMessages (keeping their text content if
    any) so the receiving agent gets a clean message history.
    """
    sanitized = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            # Check whether the next message(s) are ToolMessages covering all tool_call ids
            tool_ids = {tc["id"] for tc in msg.tool_calls if "id" in tc}
            j = i + 1
            covered_ids = set()
            while j < len(messages) and isinstance(messages[j], ToolMessage):
                if hasattr(messages[j], "tool_call_id"):
                    covered_ids.add(messages[j].tool_call_id)
                j += 1

            if tool_ids and tool_ids != covered_ids:
                # Orphaned tool_use — keep text content only (if present)
                text = msg.content if isinstance(msg.content, str) else ""
                if text.strip():
                    sanitized.append(AIMessage(content=text))
                # Skip the partial tool results too
                i = j
                continue

        sanitized.append(msg)
        i += 1

    return sanitized


def prepare_agent_messages(state: MultiAgentState, agent_name: str, system_prompt: str) -> List[BaseMessage]:
    """Prepare messages for an agent including system prompt and context.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent
        system_prompt: System prompt for the agent

    Returns:
        List of messages ready for the agent
    """
    messages = []

    # Add system prompt
    messages.append(SystemMessage(content=system_prompt))

    # Add handoff context if this is a handoff — formatted so the receiving agent cannot miss it
    if state.get("handoff_context_summary"):
        from_agent = state.get("previous_agent", "another agent")
        handoff_block = (
            f"\n{'='*60}\n"
            f"HANDOFF FROM: {from_agent.upper()}\n"
            f"{'='*60}\n"
            f"{state['handoff_context_summary']}\n"
            f"{'='*60}\n"
            f"REQUIRED: Begin your response by explicitly acknowledging the above context "
            f"in 1-2 sentences before proceeding. Do NOT ignore this handoff summary.\n"
            f"{'='*60}\n"
        )
        messages.append(SystemMessage(content=handoff_block))

    # Add conversation messages — strip orphaned tool_use blocks first
    # to avoid Anthropic 400 "tool_use without tool_result" errors on handoffs
    messages.extend(sanitize_messages(list(state["messages"])))

    return messages


def check_agent_limits(state: MultiAgentState, agent_name: str, max_steps: int = 10) -> tuple[bool, str]:
    """Check if agent has exceeded limits.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent
        max_steps: Maximum allowed steps

    Returns:
        Tuple of (exceeded, error_message)
    """
    if has_exceeded_step_limit(state, agent_name, max_steps):
        context = extract_agent_context(state, agent_name)
        summary_parts = [
            f"The {agent_name} agent has reached its step limit ({max_steps} steps).",
            "Here's what was discovered:"
        ]

        if context["findings"]:
            summary_parts.append("\nFindings:")
            for finding in context["findings"]:
                summary_parts.append(f"- {finding}")

        if context["recommendations"]:
            summary_parts.append("\nRecommendations:")
            for rec in context["recommendations"]:
                summary_parts.append(f"- {rec}")

        if context["open_questions"]:
            summary_parts.append("\nRemaining questions:")
            for question in context["open_questions"]:
                summary_parts.append(f"- {question}")

        return True, "\n".join(summary_parts)

    return False, ""


def extract_findings_from_response(response) -> List[str]:
    """Extract key findings from an agent's response.

    Args:
        response: Agent's response text (string or list)

    Returns:
        List of extracted findings
    """
    findings = []

    # Handle both string and list responses
    if isinstance(response, list):
        response = str(response)
    elif not isinstance(response, str):
        return findings

    # Look for common patterns indicating findings
    patterns = [
        "I found that",
        "I discovered",
        "The issue is",
        "The problem is",
        "Based on the documentation",
        "According to",
    ]

    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if any(pattern.lower() in line.lower() for pattern in patterns):
            findings.append(line)
        # Also capture bullet points
        elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
            findings.append(line.lstrip('-•* '))

    return findings[:5]  # Limit to top 5 findings


def extract_recommendations_from_response(response) -> List[str]:
    """Extract recommendations from an agent's response.

    Args:
        response: Agent's response text (string or list)

    Returns:
        List of extracted recommendations
    """
    recommendations = []

    # Handle both string and list responses
    if isinstance(response, list):
        response = str(response)
    elif not isinstance(response, str):
        return recommendations

    patterns = [
        "I recommend",
        "You should",
        "Consider",
        "Best practice",
        "Suggestion:",
    ]

    lines = response.split('\n')
    for line in lines:
        line = line.strip()
        if any(pattern.lower() in line.lower() for pattern in patterns):
            recommendations.append(line)

    return recommendations[:5]  # Limit to top 5


def should_request_handoff(response: str, tool_calls: List[Any]) -> tuple[bool, str, str]:
    """Determine if agent should request handoff based on response.

    Args:
        response: Agent's response text
        tool_calls: List of tool calls made

    Returns:
        Tuple of (should_handoff, target_agent, reason)
    """
    response_lower = response.lower()

    # Check for explicit handoff indicators
    handoff_indicators = {
        "solution_architect": [
            "custom code",
            "script",
            "business rule",
            "custom solution",
            "need to develop",
            "create a custom"
        ],
        "implementation": [
            "check the instance",
            "check your instance",
            "live instance",
            "check the logs",
            "error logs",
            "recent changes"
        ],
        "consultant": [
            "best practice",
            "out-of-box",
            "standard configuration",
            "recommended approach",
            "general guidance"
        ]
    }

    for target_agent, indicators in handoff_indicators.items():
        if any(indicator in response_lower for indicator in indicators):
            reason = f"Response suggests {target_agent} expertise needed"
            return True, target_agent, reason

    return False, "", ""
