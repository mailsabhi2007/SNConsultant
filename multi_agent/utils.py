"""Utility functions for multi-agent orchestration."""
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
from multi_agent.state import AgentContext, HandoffRecord, MultiAgentState
from datetime import datetime


def extract_agent_context(state: MultiAgentState, agent_name: str) -> AgentContext:
    """Extract context for a specific agent from state.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent

    Returns:
        AgentContext for the specified agent
    """
    if agent_name not in state.get("agent_contexts", {}):
        return {
            "agent_name": agent_name,
            "findings": [],
            "recommendations": [],
            "constraints": [],
            "open_questions": [],
            "last_active": None
        }
    return state["agent_contexts"][agent_name]


def update_agent_context(
    state: MultiAgentState,
    agent_name: str,
    findings: List[str] = None,
    recommendations: List[str] = None,
    constraints: List[str] = None,
    open_questions: List[str] = None
) -> Dict[str, AgentContext]:
    """Update context for a specific agent.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent
        findings: New findings to add
        recommendations: New recommendations to add
        constraints: New constraints to add
        open_questions: New open questions to add

    Returns:
        Updated agent_contexts dict
    """
    contexts = state.get("agent_contexts", {}).copy()
    if agent_name not in contexts:
        contexts[agent_name] = {
            "agent_name": agent_name,
            "findings": [],
            "recommendations": [],
            "constraints": [],
            "open_questions": [],
            "last_active": None
        }

    context = contexts[agent_name]
    if findings:
        context["findings"].extend(findings)
    if recommendations:
        context["recommendations"].extend(recommendations)
    if constraints:
        context["constraints"].extend(constraints)
    if open_questions:
        context["open_questions"].extend(open_questions)
    context["last_active"] = datetime.now()

    return contexts


def filter_messages_for_handoff(messages: List[BaseMessage], keep_tool_calls: bool = False) -> List[BaseMessage]:
    """Filter messages to reduce token usage during handoff.

    Keeps:
    - Original user query (first HumanMessage)
    - Most recent user message
    - Summary messages from other agents
    - Optionally: tool calls if keep_tool_calls=True

    Drops:
    - Intermediate tool call details
    - Redundant AI messages

    Args:
        messages: Original message list
        keep_tool_calls: Whether to keep tool call messages

    Returns:
        Filtered message list
    """
    if not messages:
        return []

    filtered = []

    # Always keep first user message (original query)
    first_human = next((m for m in messages if isinstance(m, HumanMessage)), None)
    if first_human:
        filtered.append(first_human)

    # Keep last few messages for context
    recent_messages = messages[-5:] if len(messages) > 5 else messages

    for msg in recent_messages:
        # Skip if it's the first human message we already added
        if msg == first_human:
            continue

        # Keep human messages
        if isinstance(msg, HumanMessage):
            filtered.append(msg)
        # Keep AI messages that aren't just tool calls
        elif isinstance(msg, AIMessage):
            if keep_tool_calls or not msg.tool_calls:
                filtered.append(msg)
        # Keep system messages (summaries)
        elif isinstance(msg, SystemMessage):
            filtered.append(msg)
        # Optionally keep tool messages
        elif isinstance(msg, ToolMessage) and keep_tool_calls:
            filtered.append(msg)

    return filtered


def create_handoff_summary(state: MultiAgentState, from_agent: str) -> str:
    """Create a summary for handoff to the next agent.

    Args:
        state: Current multi-agent state
        from_agent: Agent handing off

    Returns:
        Formatted summary string
    """
    context = extract_agent_context(state, from_agent)
    reason = state.get("handoff_reason", "No reason provided")

    summary_parts = [f"Handoff from {from_agent} agent."]
    summary_parts.append(f"Reason: {reason}")

    if context["findings"]:
        summary_parts.append(f"\nFindings:")
        for finding in context["findings"]:
            summary_parts.append(f"- {finding}")

    if context["recommendations"]:
        summary_parts.append(f"\nRecommendations:")
        for rec in context["recommendations"]:
            summary_parts.append(f"- {rec}")

    if context["constraints"]:
        summary_parts.append(f"\nConstraints:")
        for constraint in context["constraints"]:
            summary_parts.append(f"- {constraint}")

    if context["open_questions"]:
        summary_parts.append(f"\nOpen Questions:")
        for question in context["open_questions"]:
            summary_parts.append(f"- {question}")

    return "\n".join(summary_parts)


def detect_circular_handoff(handoff_history: List[HandoffRecord], from_agent: str, to_agent: str, lookback: int = 5) -> bool:
    """Detect if a handoff would create a circular pattern.

    Checks if the same handoff path (A→B) has occurred multiple times recently.

    Args:
        handoff_history: List of previous handoffs
        from_agent: Agent requesting handoff
        to_agent: Target agent
        lookback: Number of recent handoffs to check

    Returns:
        True if circular pattern detected, False otherwise
    """
    if len(handoff_history) < 2:
        return False

    recent_handoffs = handoff_history[-lookback:]

    # Count occurrences of this specific handoff path
    same_path_count = sum(
        1 for h in recent_handoffs
        if h["from_agent"] == from_agent and h["to_agent"] == to_agent
    )

    # Also check for ping-pong pattern (A→B→A)
    if len(recent_handoffs) >= 2:
        last_two = recent_handoffs[-2:]
        if (last_two[0]["from_agent"] == to_agent and last_two[0]["to_agent"] == from_agent and
            last_two[1]["from_agent"] == from_agent and last_two[1]["to_agent"] == to_agent):
            return True

    # Flag if same path appears 3+ times
    return same_path_count >= 3


def has_exceeded_step_limit(state: MultiAgentState, agent_name: str, max_steps: int = 10) -> bool:
    """Check if an agent has exceeded its step limit.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent
        max_steps: Maximum allowed steps

    Returns:
        True if limit exceeded, False otherwise
    """
    step_counts = state.get("agent_step_counts", {})
    return step_counts.get(agent_name, 0) >= max_steps


def increment_agent_steps(state: MultiAgentState, agent_name: str) -> Dict[str, int]:
    """Increment step count for an agent.

    Args:
        state: Current multi-agent state
        agent_name: Name of the agent

    Returns:
        Updated step counts dict
    """
    step_counts = state.get("agent_step_counts", {}).copy()
    step_counts[agent_name] = step_counts.get(agent_name, 0) + 1
    return step_counts
