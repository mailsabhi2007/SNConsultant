"""CLI interface for ServiceNow consulting agent."""

import asyncio
from agent import get_agent


async def chat_loop():
    """Main chat loop for interacting with the agent."""
    print("=" * 80)
    print("ServiceNow Technical Consultant Agent")
    print("=" * 80)
    print("\nType your questions about ServiceNow instance health.")
    print("Type 'quit', 'exit', or 'bye' to end the conversation.\n")
    
    agent = get_agent()
    # Initialize state with system message
    from langchain_core.messages import SystemMessage
    state = {"messages": [SystemMessage(content=agent.system_prompt)]}
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye', 'q']:
                print("\nGoodbye! Have a great day!")
                break
            
            # Invoke the agent and stream the response
            result = await agent.invoke(user_input, state)
            
            # Update state with all messages
            state = result
            
            # Extract and display the agent's response
            messages = result.get("messages", [])
            
            # Find the final AI response
            final_response = None
            for msg in reversed(messages):
                if hasattr(msg, "content") and msg.content and not hasattr(msg, "tool_calls"):
                    final_response = msg
                    break
                elif hasattr(msg, "content") and msg.content:
                    final_response = msg
                    break
            
            # Display response
            if final_response:
                print("\nAgent:", final_response.content)
            else:
                # If no final response yet, show what happened
                last_msg = messages[-1] if messages else None
                if last_msg and hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    tool_names = [tc.get("name", "unknown") for tc in last_msg.tool_calls]
                    print(f"\nAgent: [Using tools: {', '.join(tool_names)}...]")
                else:
                    print("\nAgent: [Processing...]")
            
            print()  # Empty line for readability
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


if __name__ == "__main__":
    asyncio.run(chat_loop())
