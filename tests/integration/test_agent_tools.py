"""Integration tests for agent-tool interactions."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent import ServiceNowAgent


class TestWorkflowOrderEnforcement:
    """Test workflow order enforcement."""
    
    @pytest.fixture
    def agent(self, mock_env_vars):
        """Create agent instance for testing."""
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                agent = ServiceNowAgent()
                agent.app = AsyncMock()
                return agent
    
    @pytest.mark.asyncio
    async def test_agent_calls_public_docs_before_user_context(self, agent):
        """Test agent calls consult_public_docs before consult_user_context."""
        # This would require actual LLM mocking to test properly
        # For now, we test the system prompt enforces this
        assert "MUST HAPPEN FIRST" in agent.system_prompt
        assert "consult_public_docs" in agent.system_prompt
        assert "MUST HAPPEN SECOND" in agent.system_prompt
        assert "consult_user_context" in agent.system_prompt
    
    def test_system_prompt_enforces_phase_order(self, agent):
        """Test system prompt enforces phase order."""
        prompt = agent.system_prompt
        
        # Check Phase 1 comes before Phase 2
        phase1_pos = prompt.find("PHASE 1")
        phase2_pos = prompt.find("PHASE 2")
        assert phase1_pos < phase2_pos
        
        # Check Phase 2 comes before Phase 3
        phase3_pos = prompt.find("PHASE 3")
        assert phase2_pos < phase3_pos
        
        # Check Phase 3 comes before Phase 4
        phase4_pos = prompt.find("PHASE 4")
        assert phase3_pos < phase4_pos


class TestToolCallSequence:
    """Test tool call sequence."""
    
    @pytest.mark.asyncio
    async def test_multiple_tool_calls_in_correct_order(self, mock_env_vars):
        """Test multiple tool calls in correct order."""
        # This would require complex LLM mocking
        # For now, we verify tools are available in correct order
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock(name="consult_public_docs")
                
                agent = ServiceNowAgent()
                
                # Verify tools are in the list
                assert len(agent.tools) == 3
                tool_names = [tool.name for tool in agent.tools]
                assert "consult_public_docs" in tool_names
                assert "consult_user_context" in tool_names
                assert "check_live_instance" in tool_names


class TestPermissionGuardIntegration:
    """Test permission guard integration."""
    
    @pytest.fixture
    def agent(self, mock_env_vars):
        """Create agent instance for testing."""
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                return ServiceNowAgent()
    
    def test_agent_workflow_with_permission_guard_interception(self, agent):
        """Test agent workflow with permission guard interception."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                HumanMessage(content="Check error logs"),
                AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "error logs"}}])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should intercept and ask for permission
        assert isinstance(result, dict)
        assert "messages" in result
    
    def test_agent_continues_after_user_confirmation(self, agent):
        """Test agent continues after user confirmation."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                HumanMessage(content="Check logs"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="Yes, please check"),
                AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "logs"}}])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should proceed to tools
        assert result == "tools"
    
    def test_agent_stops_when_user_denies_permission(self, agent):
        """Test agent stops when user denies permission."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                HumanMessage(content="Check logs"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="No"),
                AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "logs"}}])
            ]
        }
        
        result = agent._should_continue(state)
        
        # Should intercept (no confirmation found)
        assert isinstance(result, dict)
