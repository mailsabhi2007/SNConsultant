"""Multi-agent graph assembly with orchestration and handoffs."""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage
from multi_agent.state import MultiAgentState, HandoffRecord
from multi_agent.orchestrator import orchestrator_node
from multi_agent.agents.consultant import consultant_node, create_consultant_agent
from multi_agent.agents.solution_architect import solution_architect_node, create_solution_architect_agent
from multi_agent.agents.implementation import implementation_node, create_implementation_agent
from multi_agent.utils import (
    detect_circular_handoff,
    create_handoff_summary,
    filter_messages_for_handoff
)
from multi_agent.handoff_tools import request_handoff
from servicenow_tools import get_public_knowledge_tool
from agent import consult_user_context, save_learned_preference, check_live_instance
from tools import check_table_schema, fetch_recent_changes, get_error_logs
from datetime import datetime


def agent_should_continue(state: MultiAgentState) -> Literal["tools", "consultant", "solution_architect", "implementation", "end"]:
    """Determine next node for individual agents (consultant, architect, implementation).

    Args:
        state: Current multi-agent state

    Returns:
        Next node to execute
    """
    current_agent = state.get("current_agent")
    messages = state.get("messages", [])

    if not messages:
        return "end"

    last_message = messages[-1]

    # Check if handoff is requested
    if state.get("handoff_requested"):
        handoff_target = state.get("handoff_target")
        handoff_history = state.get("handoff_history", [])
        from_agent = current_agent

        # Check for circular handoff
        if detect_circular_handoff(handoff_history, from_agent, handoff_target):
            # Prevent circular handoff - end with error message
            error_msg = AIMessage(
                content="I've detected a circular handoff pattern. Let me provide you with what we've discovered so far rather than continuing to pass between agents."
            )
            state["messages"].append(error_msg)
            return "end"

        # Valid handoff - route to target agent
        return handoff_target

    # Check if last message has tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Otherwise, end
    return "end"


def orchestrator_should_continue(state: MultiAgentState) -> Literal["consultant", "solution_architect", "implementation", "end"]:
    """Determine next node for orchestrator.

    Args:
        state: Current multi-agent state

    Returns:
        Next node to execute
    """
    current_agent = state.get("current_agent")

    if not current_agent or current_agent == "orchestrator":
        # Default to consultant if no agent selected
        return "consultant"

    # Route to the selected agent
    return current_agent


def handle_handoff(state: MultiAgentState) -> MultiAgentState:
    """Process handoff between agents.

    Args:
        state: Current multi-agent state

    Returns:
        Updated state with handoff processed
    """
    from_agent = state.get("current_agent")
    to_agent = state.get("handoff_target")
    reason = state.get("handoff_reason", "")
    context_summary = state.get("handoff_context_summary", "")

    # Create handoff record
    handoff_record: HandoffRecord = {
        "from_agent": from_agent,
        "to_agent": to_agent,
        "reason": reason,
        "timestamp": datetime.now(),
        "context_summary": context_summary
    }

    # Update handoff history
    handoff_history = state.get("handoff_history", []).copy()
    handoff_history.append(handoff_record)

    # Filter messages to reduce token usage
    filtered_messages = filter_messages_for_handoff(state.get("messages", []))

    # Create handoff summary
    summary = create_handoff_summary(state, from_agent)

    # Add summary as system message
    filtered_messages.append(SystemMessage(content=f"\n--- Handoff Context ---\n{summary}"))

    # Update state
    updated_state = state.copy()
    updated_state["messages"] = filtered_messages
    updated_state["handoff_history"] = handoff_history
    updated_state["previous_agent"] = from_agent
    updated_state["current_agent"] = to_agent
    updated_state["handoff_requested"] = False
    updated_state["handoff_target"] = None
    updated_state["handoff_reason"] = None
    updated_state["handoff_context_summary"] = None

    return updated_state


def create_multi_agent_graph(user_id: str = None):
    """Create the multi-agent graph with all nodes and edges.

    Args:
        user_id: Optional user ID for user-specific configuration

    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(MultiAgentState)

    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("consultant", consultant_node)
    workflow.add_node("solution_architect", solution_architect_node)
    workflow.add_node("implementation", implementation_node)

    # Create tools node with all tools
    consult_public_docs = get_public_knowledge_tool(user_id=user_id)
    all_tools = [
        consult_public_docs,
        consult_user_context,
        check_live_instance,
        check_table_schema,
        fetch_recent_changes,
        get_error_logs,
        save_learned_preference,
        request_handoff
    ]
    workflow.add_node("tools", ToolNode(all_tools))

    # Set entry point
    workflow.set_entry_point("orchestrator")

    # Add conditional edges from agents
    workflow.add_conditional_edges(
        "consultant",
        agent_should_continue,
        {
            "tools": "tools",
            "solution_architect": "solution_architect",
            "implementation": "implementation",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "solution_architect",
        agent_should_continue,
        {
            "tools": "tools",
            "consultant": "consultant",
            "implementation": "implementation",
            "end": END
        }
    )

    workflow.add_conditional_edges(
        "implementation",
        agent_should_continue,
        {
            "tools": "tools",
            "consultant": "consultant",
            "solution_architect": "solution_architect",
            "end": END
        }
    )

    # Add conditional edge from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator_should_continue,
        {
            "consultant": "consultant",
            "solution_architect": "solution_architect",
            "implementation": "implementation",
            "end": END
        }
    )

    # Tools always return to current agent
    def route_after_tools(state: MultiAgentState) -> str:
        """Route back to the current agent after tool execution."""
        return state.get("current_agent", "consultant")

    workflow.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "consultant": "consultant",
            "solution_architect": "solution_architect",
            "implementation": "implementation"
        }
    )

    # Compile and return
    return workflow.compile()


class MultiAgentOrchestrator:
    """Orchestrator for multi-agent system."""

    def __init__(self, user_id: str = None):
        """Initialize the orchestrator.

        Args:
            user_id: Optional user ID for user-specific configuration
        """
        self.user_id = user_id
        self.graph = create_multi_agent_graph(user_id=user_id)

    async def invoke(self, message: str, conversation_id: int = None) -> dict:
        """Invoke the multi-agent system.

        Args:
            message: User message
            conversation_id: Optional conversation ID

        Returns:
            Dictionary with response and metadata
        """
        from multi_agent.state import create_initial_state
        from langchain_core.messages import HumanMessage, AIMessage
        from history_manager import create_conversation, add_message
        # from semantic_cache import check_cache, store_cache  # Disabled for now

        # Caching temporarily disabled
        cached_result = None
        cache_similarity = 0.0

        # Create conversation if needed
        if not conversation_id and self.user_id:
            print(f"[MULTI-AGENT] Creating new conversation for user: {self.user_id}")
            conversation_id = create_conversation(self.user_id)
            print(f"[MULTI-AGENT] Created conversation ID: {conversation_id}")
        else:
            print(f"[MULTI-AGENT] Using existing conversation ID: {conversation_id}, user_id: {self.user_id}")

        # Save user message to history
        if conversation_id:
            print(f"[MULTI-AGENT] Saving user message to conversation {conversation_id}")
            add_message(
                conversation_id=conversation_id,
                role="user",
                content=message
            )
            print(f"[MULTI-AGENT] User message saved")
        else:
            print(f"[MULTI-AGENT] WARNING: No conversation_id, message NOT saved!")

        # Create initial state
        state = create_initial_state(user_id=self.user_id, conversation_id=conversation_id)
        state["messages"] = [HumanMessage(content=message)]

        # Invoke graph
        print(f"[MULTI-AGENT] Invoking multi-agent graph")
        result = await self.graph.ainvoke(state)

        # Extract final assistant response
        assistant_response = None
        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) and msg.content:
                assistant_response = msg.content
                break

        print(f"[MULTI-AGENT] Extracted assistant response: {len(assistant_response) if assistant_response else 0} characters")

        # Save assistant message to history
        if conversation_id and assistant_response:
            print(f"[MULTI-AGENT] Saving assistant message to conversation {conversation_id}")
            print(f"[MULTI-AGENT] Response length: {len(assistant_response)}")
            metadata = {
                "current_agent": result.get("current_agent"),
                "handoff_count": len(result.get("handoff_history", []))
            }
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_response,
                metadata=metadata
            )
            print(f"[MULTI-AGENT] Assistant message saved successfully")

            # Generate title for new conversations (after first exchange)
            try:
                from history_manager import get_conversation, update_conversation_title, generate_conversation_title
                conv = get_conversation(conversation_id)
                if conv and not conv.get("title"):
                    print(f"[MULTI-AGENT] Generating title for conversation {conversation_id}")
                    title = generate_conversation_title(message, assistant_response)
                    if title:
                        update_conversation_title(conversation_id, title)
                        print(f"[MULTI-AGENT] Title generated: {title}")
            except Exception as e:
                print(f"[MULTI-AGENT] Title generation failed: {e}")
        else:
            print(f"[MULTI-AGENT] WARNING: Not saving assistant message. conversation_id={conversation_id}, has_response={bool(assistant_response)}")

        print(f"[MULTI-AGENT] Returning conversation_id: {conversation_id}")
        return {
            "messages": result.get("messages", []),
            "response": assistant_response,
            "current_agent": result.get("current_agent"),
            "handoff_history": result.get("handoff_history", []),
            "conversation_id": conversation_id,
            "is_cached": False,
            "similarity": None
        }
