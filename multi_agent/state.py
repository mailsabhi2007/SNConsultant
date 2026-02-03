"""State schema for multi-agent orchestration."""
from typing import TypedDict, Optional, Sequence, Dict, Any, List, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from datetime import datetime


class HandoffRecord(TypedDict):
    """Record of a single handoff between agents."""
    from_agent: str
    to_agent: str
    reason: str
    timestamp: datetime
    context_summary: str


class AgentContext(TypedDict):
    """Context accumulated by a specific agent."""
    agent_name: str
    findings: List[str]  # Key findings discovered by this agent
    recommendations: List[str]  # Recommendations made
    constraints: List[str]  # Constraints or limitations identified
    open_questions: List[str]  # Unresolved questions
    last_active: Optional[datetime]


class MultiAgentState(TypedDict):
    """Extended state schema for multi-agent orchestration."""

    # Core (existing from single agent)
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_id: Optional[str]
    conversation_id: Optional[int]
    is_cached: Optional[bool]
    judge_result: Optional[Dict[str, Any]]

    # Agent tracking
    current_agent: Optional[str]  # "orchestrator", "consultant", "solution_architect", "implementation"
    previous_agent: Optional[str]
    handoff_history: List[HandoffRecord]
    agent_contexts: Dict[str, AgentContext]  # Each agent's accumulated findings

    # Handoff control
    handoff_requested: Optional[bool]
    handoff_target: Optional[str]
    handoff_reason: Optional[str]
    handoff_context_summary: Optional[str]

    # Permission tracking
    live_instance_permission_granted: Optional[bool]
    agent_step_counts: Dict[str, int]  # Prevent infinite loops


def create_initial_state(
    user_id: Optional[str] = None,
    conversation_id: Optional[int] = None
) -> MultiAgentState:
    """Create initial state for a new conversation."""
    return {
        "messages": [],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "is_cached": False,
        "judge_result": None,
        "current_agent": "orchestrator",
        "previous_agent": None,
        "handoff_history": [],
        "agent_contexts": {},
        "handoff_requested": False,
        "handoff_target": None,
        "handoff_reason": None,
        "handoff_context_summary": None,
        "live_instance_permission_granted": False,
        "agent_step_counts": {
            "orchestrator": 0,
            "consultant": 0,
            "solution_architect": 0,
            "implementation": 0
        }
    }


def create_agent_context(agent_name: str) -> AgentContext:
    """Create initial context for an agent."""
    return {
        "agent_name": agent_name,
        "findings": [],
        "recommendations": [],
        "constraints": [],
        "open_questions": [],
        "last_active": None
    }
