"""Unit tests for agent.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import END

from agent import ServiceNowAgent, get_agent, consult_user_context, check_live_instance


class TestServiceNowAgent:
    """Test ServiceNowAgent class."""
    
    def test_agent_init_with_valid_api_key(self, mock_env_vars):
        """Test agent initialization with valid API key."""
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                agent = ServiceNowAgent()
                
                assert agent is not None
                assert agent.model is not None
                mock_claude.assert_called_once()
    
    def test_agent_init_fails_without_api_key(self, monkeypatch):
        """Test agent initialization fails without ANTHROPIC_API_KEY."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            ServiceNowAgent()
    
    def test_agent_init_with_custom_model(self, mock_env_vars, monkeypatch):
        """Test agent initialization with custom model name."""
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-opus")
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                agent = ServiceNowAgent()
                
                mock_claude.assert_called_once()
                # Check model was called with custom name
                call_args = mock_claude.call_args
                assert call_args[1]['model'] == "claude-3-opus"
    
    def test_tools_are_bound_to_model(self, mock_env_vars):
        """Test tools are properly bound to model."""
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                agent = ServiceNowAgent()
                
                assert mock_model.bind_tools.called
                # Check tools were passed to bind_tools
                call_args = mock_model.bind_tools.call_args
                assert len(call_args[0][0]) == 3  # Three tools
    
    def test_workflow_graph_constructed(self, mock_env_vars):
        """Test workflow graph is correctly constructed."""
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool:
                mock_tool.return_value = Mock()
                agent = ServiceNowAgent()
                
                assert agent.workflow is not None
                assert agent.app is not None


class TestShouldContinue:
    """Test _should_continue method."""
    
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
    
    def test_returns_tools_when_tool_calls_exist(self, agent):
        """Test returns 'tools' when tool calls exist."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                AIMessage(content="", tool_calls=[{"name": "consult_public_docs", "args": {"query": "test"}}])
            ]
        }
        
        result = agent._should_continue(state)
        assert result == "tools"
    
    def test_returns_end_when_no_tool_calls(self, agent):
        """Test returns END when no tool calls."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                AIMessage(content="Response without tools")
            ]
        }
        
        result = agent._should_continue(state)
        assert result == END
    
    def test_code_guard_blocks_live_instance_without_confirmation(self, agent):
        """Test code guard intercepts check_live_instance without user confirmation."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                HumanMessage(content="What is the error log?"),
                AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "error logs"}}])
            ]
        }
        
        result = agent._should_continue(state)
        assert isinstance(result, dict)
        assert "messages" in result
        assert "permission" in result["messages"][0].content.lower() or "explicit" in result["messages"][0].content.lower()
    
    def test_code_guard_allows_live_instance_with_confirmation(self, agent):
        """Test code guard allows check_live_instance with user confirmation."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                HumanMessage(content="What is the error log?"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="Yes, please check"),
                AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "error logs"}}])
            ]
        }
        
        result = agent._should_continue(state)
        assert result == "tools"
    
    def test_confirmation_keywords_detected(self, agent):
        """Test confirmation keyword detection."""
        keywords = ["yes", "please check", "go ahead", "connect", "sure", "okay", "ok", "proceed"]
        
        for keyword in keywords:
            state = {
                "messages": [
                    SystemMessage(content="Test"),
                    HumanMessage(content=f"{keyword}"),
                    AIMessage(content="", tool_calls=[{"name": "check_live_instance", "args": {"query": "test"}}])
                ]
            }
            
            result = agent._should_continue(state)
            assert result == "tools", f"Keyword '{keyword}' should allow tool call"
    
    def test_other_tool_calls_proceed_normally(self, agent):
        """Test other tool calls proceed normally."""
        state = {
            "messages": [
                SystemMessage(content="Test"),
                AIMessage(content="", tool_calls=[{"name": "consult_public_docs", "args": {"query": "test"}}])
            ]
        }
        
        result = agent._should_continue(state)
        assert result == "tools"


class TestCallModel:
    """Test _call_model method."""
    
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
                agent.model_with_tools = mock_model
                return agent
    
    def test_model_invocation_with_state(self, agent):
        """Test model invocation with state messages."""
        state = {
            "messages": [
                SystemMessage(content="Test system prompt"),
                HumanMessage(content="Test query")
            ]
        }
        
        mock_response = AIMessage(content="Test response")
        agent.model_with_tools.invoke = Mock(return_value=mock_response)
        
        result = agent._call_model(state)
        
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0] == mock_response
        agent.model_with_tools.invoke.assert_called_once()


class TestInvoke:
    """Test invoke method."""
    
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
                agent.app.ainvoke = AsyncMock(return_value={"messages": [AIMessage(content="Response")]})
                return agent
    
    @pytest.mark.asyncio
    async def test_agent_invocation_with_new_message(self, agent):
        """Test agent invocation with new message."""
        result = await agent.invoke("Test query")
        
        assert result is not None
        assert "messages" in result
        agent.app.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_state_persistence_across_invocations(self, agent):
        """Test state persistence across invocations."""
        state1 = await agent.invoke("First query")
        state2 = await agent.invoke("Second query", state1)
        
        assert len(state2["messages"]) > len(state1["messages"])
    
    @pytest.mark.asyncio
    async def test_system_message_initialization(self, agent):
        """Test system message initialization."""
        result = await agent.invoke("Test query")
        
        # Check that system message was added
        call_args = agent.app.ainvoke.call_args[0][0]
        assert len(call_args["messages"]) >= 1
        assert isinstance(call_args["messages"][0], SystemMessage)


class TestSingleton:
    """Test singleton pattern."""
    
    def test_get_agent_returns_same_instance(self, mock_env_vars):
        """Test get_agent() returns same instance."""
        with patch('agent.ServiceNowAgent') as mock_agent_class:
            mock_instance = Mock()
            mock_agent_class.return_value = mock_instance
            
            agent1 = get_agent()
            agent2 = get_agent()
            
            assert agent1 is agent2
            mock_agent_class.assert_called_once()


class TestTools:
    """Test tool functions."""
    
    def test_consult_user_context_success(self, mock_env_vars):
        """Test consult_user_context returns formatted results."""
        with patch('agent.query_knowledge_base') as mock_query:
            mock_query.return_value = [
                {"source": "test.txt", "content": "Test content"}
            ]
            
            result = consult_user_context("test query")
            
            assert "According to your internal policy" in result
            assert "test.txt" in result
            assert "Test content" in result
    
    def test_consult_user_context_empty_results(self, mock_env_vars):
        """Test consult_user_context handles empty results."""
        with patch('agent.query_knowledge_base') as mock_query:
            mock_query.return_value = []
            
            result = consult_user_context("test query")
            
            assert "No relevant information found" in result
    
    def test_consult_user_context_error_handling(self, mock_env_vars):
        """Test consult_user_context error handling."""
        with patch('agent.query_knowledge_base') as mock_query:
            mock_query.side_effect = Exception("Database error")
            
            result = consult_user_context("test query")
            
            assert "Error querying knowledge base" in result
    
    @pytest.mark.asyncio
    async def test_check_live_instance_schema_with_table(self, mock_env_vars):
        """Test check_live_instance schema check with table_name."""
        with patch('agent.check_table_schema') as mock_schema:
            mock_schema.return_value = "Schema information"
            
            result = await check_live_instance("check schema", table_name="incident")
            
            assert result == "Schema information"
            mock_schema.assert_called_once_with("incident")
    
    @pytest.mark.asyncio
    async def test_check_live_instance_schema_without_table(self, mock_env_vars):
        """Test check_live_instance schema check without table_name returns error."""
        result = await check_live_instance("check schema")
        
        assert "Error" in result
        assert "table_name" in result
    
    @pytest.mark.asyncio
    async def test_check_live_instance_error_logs(self, mock_env_vars):
        """Test check_live_instance error log retrieval."""
        with patch('agent.get_error_logs') as mock_logs:
            mock_logs.return_value = "Error log information"
            
            result = await check_live_instance("check error logs")
            
            assert result == "Error log information"
            mock_logs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_live_instance_recent_changes(self, mock_env_vars):
        """Test check_live_instance recent changes retrieval."""
        with patch('agent.fetch_recent_changes') as mock_changes:
            mock_changes.return_value = "Recent changes information"
            
            result = await check_live_instance("check recent changes", days_ago=7)
            
            assert result == "Recent changes information"
            mock_changes.assert_called_once_with(7)
    
    @pytest.mark.asyncio
    async def test_check_live_instance_default_days(self, mock_env_vars):
        """Test check_live_instance uses default days_ago=7."""
        with patch('agent.fetch_recent_changes') as mock_changes:
            mock_changes.return_value = "Recent changes"
            
            await check_live_instance("check recent changes")
            
            mock_changes.assert_called_once_with(7)
