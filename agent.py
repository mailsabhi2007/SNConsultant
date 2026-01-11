"""LangGraph ReAct agent for ServiceNow consulting."""

from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from tools import fetch_recent_changes, check_table_schema, get_error_logs, save_learned_preference
from servicenow_client import ServiceNowClient
from knowledge_base import query_knowledge_base
from servicenow_tools import get_public_knowledge_tool


# Define the agent state as TypedDict
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


@tool
def consult_user_context(query: str) -> str:
    """
    Search internal client uploaded documents and policies stored in the knowledge base.
    
    WORKFLOW ORDER: Use this SECOND, after consulting public documentation with consult_public_docs.
    This tool checks for internal rules, naming conventions, or client-specific policies that may
    differ from or supplement the official ServiceNow standards.
    
    Args:
        query: The search query to find relevant information in user-uploaded documents
    
    Returns:
        String containing relevant information from the knowledge base with sources cited.
    """
    try:
        # Only search user_context (internal documents)
        results = query_knowledge_base(query, filter_type='user_context', k=3)
        
        if not results:
            return f"No relevant information found in internal documents for: {query}"
        
        # Format the results with citations
        formatted_response = []
        for i, result in enumerate(results, 1):
            source = result.get('source', 'Unknown')
            content = result.get('content', '')
            
            citation = f"According to your internal policy ({source})"
            formatted_response.append(f"{citation}:\n{content}")
        
        return "\n\n".join(formatted_response)
    except Exception as e:
        return f"Error querying knowledge base: {str(e)}"


@tool
async def check_live_instance(query: str, table_name: Optional[str] = None, days_ago: Optional[int] = None) -> str:
    """
    Check the live ServiceNow instance for current configuration, logs, or data.
    
    ⚠️ CRITICAL WARNING - EXPLICIT USER PERMISSION REQUIRED ⚠️
    
    DO NOT call this tool automatically. This tool requires EXPLICIT user confirmation.
    You MUST ask the user for permission first and only call this tool if they explicitly confirm
    with words like "Yes", "please check", "go ahead", "connect", or similar explicit permission.
    
    If the user has not given explicit permission, DO NOT call this tool. Instead, ask them:
    "Would you like me to connect to your live instance to check the actual configuration/logs?"
    
    This tool can:
    - Check table schemas (provide table_name parameter)
    - Fetch recent changes (provide days_ago parameter, default 7)
    - Get error logs (no additional parameters needed)
    
    Args:
        query: Description of what to check (e.g., "check error logs", "get incident table schema")
        table_name: Optional table name for schema checks (e.g., 'incident', 'sys_user')
        days_ago: Optional number of days to look back for recent changes (default: 7)
    
    Returns:
        String containing the results from the live instance check
    """
    try:
        query_lower = query.lower()
        
        # Determine which action to take based on query
        if 'schema' in query_lower or 'table' in query_lower:
            if not table_name:
                return "Error: table_name parameter is required to check table schema. Please specify which table to check."
            return await check_table_schema(table_name)
        elif 'error' in query_lower or 'log' in query_lower:
            return await get_error_logs()
        elif 'change' in query_lower or 'recent' in query_lower:
            days = days_ago if days_ago else 7
            return await fetch_recent_changes(days)
        else:
            # Default: try to get error logs if no specific request
            return await get_error_logs()
    except Exception as e:
        return f"Error checking live instance: {str(e)}"


class ServiceNowAgent:
    """ServiceNow consulting agent using LangGraph."""
    
    def __init__(self):
        """Initialize the agent."""
        import os
        # Check if API key is set
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Please add it to your .env file."
            )
        
        # Initialize Claude model
        # Using Claude Sonnet 4 as specified
        # You can override by setting ANTHROPIC_MODEL in .env
        model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        
        self.model = ChatAnthropic(
            model=model_name,
            temperature=0,
        )
        
        # System prompt
        self.system_prompt = (
            "You are an expert Senior ServiceNow Solution Architect. Your goal is to provide accurate, safe, and context-aware advice.\n\n"
            "### YOUR WORKFLOW - STRICT ORDER REQUIRED\n"
            "For every user query, you MUST follow this exact sequence. DO NOT skip steps or change the order:\n\n"
            "**PHASE 1 - ESTABLISH THE STANDARD (MUST HAPPEN FIRST):**\n"
            "   - You MUST start by using `consult_public_docs` to find the official ServiceNow documentation, Best Practices, or Known Errors related to the query.\n"
            "   - This establishes the baseline standard from ServiceNow's official sources.\n"
            "   - Citations must be from 'docs.servicenow.com', 'support.servicenow.com', or 'community.servicenow.com'.\n"
            "   - DO NOT proceed to Phase 2 until you have completed Phase 1.\n\n"
            "**PHASE 2 - CHECK INTERNAL CONTEXT (MUST HAPPEN SECOND):**\n"
            "   - After Phase 1 is complete, use `consult_user_context` to check if the user has uploaded any design documents, naming conventions, or legacy manuals.\n"
            "   - This helps identify client-specific policies, customizations, or deviations from standard.\n"
            "   - Look for conflicts (e.g., 'Standard says X, but Client Doc says Y').\n"
            "   - If no internal context is found, note that in your response.\n\n"
            "**PHASE 3 - SYNTHESIZE & RESPOND (PROVIDE STRUCTURED ANSWER, NOT RAW DATA):**\n"
            "   - DO NOT simply dump raw search results. You must synthesize and analyze the information.\n"
            "   - Compare and contrast the public documentation with internal context (if available).\n"
            "   - Provide a clear, structured answer that synthesizes both sources.\n"
            "   - Structure your answer as:\n"
            "     - **Official Best Practice:** [Synthesized summary of what ServiceNow documentation says, not raw quotes]\n"
            "     - **Your Context:** [Synthesized summary of what their internal docs say, if any, or note if none found]\n"
            "     - **Analysis:** [Compare the two sources, identify any conflicts or alignments]\n"
            "     - **Recommendation:** [Your synthesized advice based on the analysis]\n"
            "   - Always cite your sources with URLs, but present synthesized insights, not raw information dumps.\n\n"
            "**PHASE 4 - ESCALATION (Live Data - REQUIRES EXPLICIT USER PERMISSION):**\n"
            "   - If the answer depends on the current state of the system (e.g., 'Why is *my* specific incident broken?', 'What is the current value of property X?'), DO NOT guess.\n"
            "   - **CRITICAL: NEVER call the `check_live_instance` tool automatically. This tool requires explicit user confirmation.**\n"
            "   - Instead, end your response by asking the user: *'Would you like me to connect to your live instance to check the actual configuration/logs?'*\n"
            "   - Only call `check_live_instance` if the user explicitly replies with confirmation words like 'Yes', 'please check', 'go ahead', 'connect', or similar explicit permission.\n"
            "   - If the user says 'No' or does not confirm, do not call the tool.\n\n"
            "**LEARNING FROM USER FEEDBACK:**\n"
            "   - If the user provides a correction, a specific constraint, or explicit positive feedback on a specific method:\n"
            "     - Synthesize it into a single, standalone rule (e.g., 'User prefers gs.info over gs.log', 'Admin group name is SN_Admins').\n"
            "     - Call the `save_learned_preference` tool to memorize this for future conversations.\n"
            "     - After saving, acknowledge: 'Noted. I have updated my internal context. [How you'll use this in the future].'\n"
            "   - DO NOT save generic 'thank you' messages or vague positive feedback.\n"
            "   - Only save concrete, actionable facts or preferences that will affect future recommendations.\n\n"
            "### GUIDELINES\n"
            "- **Tone:** Professional, consultative, concise.\n"
            "- **Safety:** Never recommend scripts that use `current.update()` in a Business Rule.\n"
            "- **Transparency:** Always link the sources you found, but provide synthesized insights, not raw data dumps.\n"
            "- **Workflow Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 (if needed). Never skip or reorder phases.\n"
        )
        
        # Get public knowledge search tool
        consult_public_docs = get_public_knowledge_tool()
        
        # Bind the core tools
        self.tools = [
            consult_public_docs,
            consult_user_context,
            check_live_instance,
            save_learned_preference
        ]
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Create the graph
        self.workflow = StateGraph(AgentState)
        self.workflow.add_node("agent", self._call_model)
        self.workflow.add_node("tools", ToolNode(self.tools))
        self.workflow.set_entry_point("agent")
        
        # Add conditional edges
        self.workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        self.workflow.add_edge("tools", "agent")
        
        # Compile the graph
        self.app = self.workflow.compile()
    
    def _call_model(self, state: AgentState):
        """Call the model with the current state."""
        # State is passed as a dict in LangGraph
        messages = list(state["messages"])
        
        try:
            # Call the model (system prompt should already be in messages)
            response = self.model_with_tools.invoke(messages)
            return {"messages": [response]}
        except Exception as e:
            # Check for rate limit errors and re-raise with more context
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['rate limit', '429', 'too many requests', 'quota']):
                # Re-raise with original exception to preserve headers/response info
                raise e
            raise
    
    def _should_continue(self, state: AgentState):
        """Determine if we should continue to tools or end."""
        # State is passed as a dict in LangGraph
        messages = state["messages"]
        if not messages:
            return END
        
        last_message = messages[-1]
        
        # Check if there are tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # Code guard: Check if any tool call is to check_live_instance
            for tool_call in last_message.tool_calls:
                if tool_call.get("name") == "check_live_instance":
                    # Check conversation history for explicit user confirmation
                    confirmation_keywords = [
                        "yes", "please check", "go ahead", "connect", 
                        "sure", "okay", "ok", "proceed", "do it",
                        "check it", "check the instance", "connect to instance"
                    ]
                    
                    # Search recent messages for confirmation
                    user_confirmed = False
                    for msg in reversed(messages):
                        if hasattr(msg, "content") and isinstance(msg.content, str):
                            content_lower = msg.content.lower()
                            # Check if this is a user message with confirmation
                            if any(keyword in content_lower for keyword in confirmation_keywords):
                                user_confirmed = True
                                break
                    
                    # If no confirmation found, intercept and ask for permission
                    if not user_confirmed:
                        # Inject a message asking for permission instead of proceeding
                        permission_message = HumanMessage(
                            content=(
                                "I need your explicit permission before connecting to your live ServiceNow instance. "
                                "Would you like me to proceed with checking the live instance? "
                                "Please reply with 'Yes' or 'please check' to confirm."
                            )
                        )
                        return {"messages": [permission_message]}
            
            return "tools"
        
        return END
    
    async def invoke(self, message: str, state: dict = None):
        """Invoke the agent with a message."""
        if state is None:
            state = {"messages": [SystemMessage(content=self.system_prompt)]}
        
        # Add the new human message
        state["messages"].append(HumanMessage(content=message))
        
        # Invoke the agent
        result = await self.app.ainvoke(state)
        return result


# Create a singleton instance
_agent_instance = None


def get_agent():
    """Get or create the agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ServiceNowAgent()
    return _agent_instance
