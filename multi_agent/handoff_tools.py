"""Handoff tool for agent-to-agent transitions."""
from typing import Literal
from langchain_core.tools import tool
from langgraph.types import Command


@tool
def request_handoff(
    target_agent: Literal["consultant", "solution_architect", "implementation"],
    reason: str,
    context_summary: str
) -> str:
    """Request handoff to another specialist agent.

    Use this when you realize another agent is better suited to handle the user's request.

    Args:
        target_agent: The agent to hand off to:
            - consultant: For best practices, OOB configurations, general advice
            - solution_architect: For custom solutions, code generation, schema design
            - implementation: For live instance access, troubleshooting, diagnostics
        reason: Brief explanation of why handoff is needed
        context_summary: Summary of what you've discovered so far (findings, constraints, open questions)

    Returns:
        Confirmation message
    """
    return f"Handoff requested to {target_agent}. Reason: {reason}"
