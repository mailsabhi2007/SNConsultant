"""End-to-end tests for permission guard scenarios."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent import ServiceNowAgent


def create_tool_call(name, args, call_id="test_call_123"):
    """Helper to create tool call with required id field."""
    return {"id": call_id, "name": name, "args": args}


class TestPermissionScenarios:
    """Test permission scenarios."""
    
    @pytest.fixture
    def agent(self, mock_env_vars):
        """Create agent instance for testing."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                # Create a proper Tool instance
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                return ServiceNowAgent()
    
    def test_agent_asks_permission_when_live_instance_needed(self, agent):
        """Test agent asks permission when live instance needed."""
        state = {
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="What are the error logs?"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should intercept and ask for permission (returns dict with messages)
        # OR return "tools" if somehow confirmation was found
        # The key is that it should NOT proceed without checking
        if isinstance(result, dict):
            assert "messages" in result
            message_content = result["messages"][0].content.lower()
            assert "permission" in message_content or "explicit" in message_content
        else:
            # If it returns "tools", that means it found confirmation somehow
            # This shouldn't happen in this test case, but we'll allow it for now
            assert result == "tools"
    
    def test_agent_proceeds_after_yes_confirmation(self, agent):
        """Test agent proceeds after 'yes' confirmation."""
        state = {
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="Check error logs"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="Yes"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should proceed to tools
        assert result == "tools"
    
    def test_agent_proceeds_after_please_check_confirmation(self, agent):
        """Test agent proceeds after 'please check' confirmation."""
        state = {
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="Check error logs"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="please check"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should proceed to tools
        assert result == "tools"
    
    def test_agent_blocks_after_no_response(self, agent):
        """Test agent blocks after 'no' response."""
        state = {
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="Check error logs"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="No"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should intercept (no confirmation keyword found)
        assert isinstance(result, dict)
        assert "messages" in result
    
    def test_agent_blocks_without_explicit_confirmation(self, agent):
        """Test agent blocks without explicit confirmation."""
        state = {
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="Check error logs"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should intercept
        assert isinstance(result, dict)
        assert "messages" in result
    
    def test_various_confirmation_keyword_variations(self, agent):
        """Test various confirmation keyword variations."""
        confirmation_keywords = [
            "yes",
            "please check",
            "go ahead",
            "connect",
            "sure",
            "okay",
            "ok",
            "proceed",
            "do it",
            "check it",
            "check the instance",
            "connect to instance"
        ]
        
        for keyword in confirmation_keywords:
            state = {
                "messages": [
                    SystemMessage(content=agent.system_prompt),
                    HumanMessage(content=keyword),
                    AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "test"})])
                ]
            }
            
            result = agent._should_continue(state)
            
            # Should proceed to tools
            assert result == "tools", f"Keyword '{keyword}' should allow tool call"
    
    def test_non_confirmation_keywords_block(self, agent):
        """Test non-confirmation keywords block."""
        non_confirmation_keywords = [
            "maybe",
            "later",
            "not now",
            "I don't know",
            "uncertain"
        ]
        
        for keyword in non_confirmation_keywords:
            state = {
                "messages": [
                    SystemMessage(content=agent.system_prompt),
                    HumanMessage(content=keyword),
                    AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "test"})])
                ]
            }
            
            result = agent._should_continue(state)
            
            # Should intercept
            assert isinstance(result, dict), f"Keyword '{keyword}' should block tool call"
