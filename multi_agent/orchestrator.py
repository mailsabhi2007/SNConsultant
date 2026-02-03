"""Orchestrator for routing queries to appropriate specialist agents."""
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from multi_agent.state import MultiAgentState
from user_config import get_system_config
import os


class RouteDecision(BaseModel):
    """Structured output for routing decisions."""
    agent: Literal["consultant", "solution_architect", "implementation"] = Field(
        description="The specialist agent best suited to handle this query"
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )


ORCHESTRATOR_SYSTEM_PROMPT = """You are an intelligent routing orchestrator for a ServiceNow consulting system. Your job is to analyze user queries and route them to the most appropriate specialist agent.

**AVAILABLE AGENTS:**

1. **Consultant Agent** - BUSINESS & PROCESS FOCUS
   Route here for:
   - Business problems and requirements ("I need to...", "How should we...")
   - Process optimization questions
   - "What's the best practice..." questions
   - "How do I configure..." (OOB configuration)
   - Strategic decisions (OOB vs Custom)
   - Requirements gathering
   - Change management advice
   - General ServiceNow consulting
   - **ANY question about business processes or workflows**
   - When user hasn't provided enough context yet
   - When unsure which agent to use (default)

2. **Solution Architect Agent** - TECHNICAL IMPLEMENTATION
   Route here ONLY when:
   - User explicitly requests custom code ("Write a script...", "Create a business rule...")
   - Custom schema design is explicitly needed
   - Technical integration patterns
   - Code review or debugging existing code
   - **User has already decided custom solution is needed**
   - Complex technical architecture (not business process)

3. **Implementation Agent** - TROUBLESHOOTING & DIAGNOSTICS
   Route here ONLY when:
   - User reports a specific error or issue in their instance
   - "My system is broken...", "Getting errors..."
   - Log analysis needed
   - Debugging why something isn't working
   - Recent change investigation
   - Performance issues in live instance

**CRITICAL ROUTING RULES:**

**Business Problems → Consultant:**
- "I need to auto-assign incidents" → **consultant** (business requirement, not technical request)
- "We want to improve our approval process" → **consultant** (process optimization)
- "How should we handle change requests?" → **consultant** (business process)
- "What's the best way to manage incidents?" → **consultant** (best practices)

**Technical Requests → Solution Architect:**
- "Write a business rule to auto-assign incidents" → **solution_architect** (explicit code request)
- "Create a custom table for tracking assets" → **solution_architect** (explicit custom request)
- "Build an integration with Salesforce" → **solution_architect** (technical integration)

**Instance Problems → Implementation:**
- "My incidents aren't auto-assigning" → **implementation** (troubleshooting)
- "I'm seeing errors in my logs" → **implementation** (error diagnosis)
- "Why is my approval not working?" → **implementation** (debugging)

**IMPORTANT:**
- **Bias toward Consultant** - When in doubt, route to Consultant
- Most queries are business problems that need context-gathering, not immediate solutions
- Consultant will gather context and handoff to others if truly needed
- Users often think they need custom code when OOB can solve it
- Consultant protects users from unnecessary customization"""


def create_orchestrator() -> ChatAnthropic:
    """Create the orchestrator LLM for routing.

    Returns:
        ChatAnthropic model configured for routing
    """
    # Get API key and model from config
    api_key = get_system_config("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in system config or environment variables")

    os.environ["ANTHROPIC_API_KEY"] = api_key

    # Use a faster model for routing (Haiku) to reduce latency and cost
    model_name = "claude-3-5-haiku-20241022"  # Fast and cheap for routing

    # Create model with structured output
    model = ChatAnthropic(model=model_name, temperature=0)
    return model.with_structured_output(RouteDecision)


async def orchestrator_node(state: MultiAgentState) -> Dict[str, Any]:
    """Orchestrator node that routes initial queries to specialist agents.

    Args:
        state: Current multi-agent state

    Returns:
        Updated state with routing decision
    """
    # Get the most recent user message
    messages = state.get("messages", [])
    user_query = None

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    if not user_query:
        # No user query found, default to consultant
        return {
            "current_agent": "consultant",
            "previous_agent": "orchestrator"
        }

    # Create orchestrator
    orchestrator = create_orchestrator()

    # Get system prompt (custom or default)
    from database import get_agent_prompt
    system_prompt = get_agent_prompt("orchestrator") or ORCHESTRATOR_SYSTEM_PROMPT

    # Prepare routing prompt
    routing_messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Route this query to the appropriate agent:\n\n{user_query}")
    ]

    try:
        # Get routing decision
        decision: RouteDecision = await orchestrator.ainvoke(routing_messages)

        # Return routing decision
        return {
            "current_agent": decision.agent,
            "previous_agent": "orchestrator",
            "agent_step_counts": state.get("agent_step_counts", {})
        }

    except Exception as e:
        # On error, default to consultant
        print(f"Orchestrator error: {e}, defaulting to consultant")
        return {
            "current_agent": "consultant",
            "previous_agent": "orchestrator"
        }
