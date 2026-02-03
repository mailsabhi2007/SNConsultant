"""Test script for multi-agent system."""
import asyncio
from multi_agent.graph import MultiAgentOrchestrator


async def test_multi_agent():
    """Test the multi-agent orchestrator."""
    print("Testing Multi-Agent Orchestrator\n")

    # Create orchestrator
    orchestrator = MultiAgentOrchestrator(user_id="test_user")

    # Test queries for different agents
    test_queries = [
        "What's the best practice for incident assignment?",  # Should route to consultant
        "Write a business rule to auto-assign incidents",  # Should route to solution_architect
        # "My incidents aren't being assigned, can you check my instance?",  # Should route to implementation
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}: {query}")
        print(f"{'='*80}\n")

        try:
            result = await orchestrator.invoke(message=query)

            print(f"Routed to: {result.get('current_agent')}")
            print(f"\nResponse:\n{result.get('response')}")

            if result.get('handoff_history'):
                print(f"\nHandoffs: {len(result.get('handoff_history'))}")
                for handoff in result.get('handoff_history'):
                    print(f"  {handoff['from_agent']} → {handoff['to_agent']}: {handoff['reason']}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

        print()


if __name__ == "__main__":
    asyncio.run(test_multi_agent())
