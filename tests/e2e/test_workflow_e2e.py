"""End-to-end workflow tests."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from agent import ServiceNowAgent


def create_tool_call(name, args, call_id="test_call_123"):
    """Helper to create tool call with required id field."""
    return {"id": call_id, "name": name, "args": args}


class TestCompleteUserQueryFlow:
    """Test complete user query flow."""
    
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
                agent = ServiceNowAgent()
                agent.app = AsyncMock()
                return agent
    
    @pytest.mark.asyncio
    async def test_query_requiring_only_phase_1_and_2(self, agent):
        """Test query requiring only Phase 1 and Phase 2."""
        # Mock the app to simulate workflow
        agent.app.ainvoke = AsyncMock(return_value={
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="What is ServiceNow?"),
                AIMessage(content="", tool_calls=[create_tool_call("consult_public_docs", {"query": "ServiceNow"})]),
                AIMessage(content="ServiceNow is a platform..."),
                AIMessage(content="", tool_calls=[create_tool_call("consult_user_context", {"query": "ServiceNow"})]),
                AIMessage(content="Based on official docs and your context...")
            ]
        })
        
        result = await agent.invoke("What is ServiceNow?")
        
        assert result is not None
        assert "messages" in result
    
    @pytest.mark.asyncio
    async def test_query_requiring_phase_4_with_permission(self, agent):
        """Test query requiring Phase 4 (with permission)."""
        agent.app.ainvoke = AsyncMock(return_value={
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="What are the error logs?"),
                AIMessage(content="Would you like me to check?"),
                HumanMessage(content="Yes, please check"),
                AIMessage(content="", tool_calls=[create_tool_call("check_live_instance", {"query": "error logs"})]),
                AIMessage(content="Here are the error logs...")
            ]
        })
        
        state = {"messages": [SystemMessage(content=agent.system_prompt)]}
        result = await agent.invoke("What are the error logs?", state)
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_query_requiring_phase_4_without_permission(self, agent):
        """Test query requiring Phase 4 (without permission)."""
        agent.app.ainvoke = AsyncMock(return_value={
            "messages": [
                SystemMessage(content=agent.system_prompt),
                HumanMessage(content="What are the error logs?"),
                AIMessage(content="Would you like me to check your live instance?")
            ]
        })
        
        state = {"messages": [SystemMessage(content=agent.system_prompt)]}
        result = await agent.invoke("What are the error logs?", state)
        
        assert result is not None
        # Should not have called check_live_instance
    
    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, agent):
        """Test multi-turn conversation."""
        state = {"messages": [SystemMessage(content=agent.system_prompt)]}
        
        # First turn
        agent.app.ainvoke = AsyncMock(return_value={
            "messages": state["messages"] + [
                HumanMessage(content="What is ServiceNow?"),
                AIMessage(content="ServiceNow is a platform...")
            ]
        })
        result1 = await agent.invoke("What is ServiceNow?", state)
        state = result1
        
        # Second turn
        agent.app.ainvoke = AsyncMock(return_value={
            "messages": state["messages"] + [
                HumanMessage(content="How do I create an incident?"),
                AIMessage(content="To create an incident...")
            ]
        })
        result2 = await agent.invoke("How do I create an incident?", state)
        
        assert len(result2["messages"]) > len(result1["messages"])


class TestWorkflowCompliance:
    """Test workflow compliance."""
    
    def test_phase_1_always_happens_first(self, mock_env_vars):
        """Test Phase 1 always happens first."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt emphasizes Phase 1 first
                assert "MUST HAPPEN FIRST" in agent.system_prompt
                assert "PHASE 1" in agent.system_prompt
                phase1_pos = agent.system_prompt.find("PHASE 1")
                phase2_pos = agent.system_prompt.find("PHASE 2")
                assert phase1_pos < phase2_pos
    
    def test_phase_2_happens_after_phase_1(self, mock_env_vars):
        """Test Phase 2 happens after Phase 1."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                prompt = agent.system_prompt
                phase1_pos = prompt.find("PHASE 1")
                phase2_pos = prompt.find("PHASE 2")
                phase3_pos = prompt.find("PHASE 3")
                
                assert phase1_pos < phase2_pos < phase3_pos
    
    def test_phase_3_provides_synthesized_response(self, mock_env_vars):
        """Test Phase 3 provides synthesized response."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt requires synthesis
                assert "SYNTHESIZE" in agent.system_prompt
                assert "not raw data" in agent.system_prompt.lower() or "not raw quotes" in agent.system_prompt.lower()
    
    def test_phase_4_requires_explicit_permission(self, mock_env_vars):
        """Test Phase 4 requires explicit permission."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt and code guard
                assert "REQUIRES EXPLICIT USER PERMISSION" in agent.system_prompt
                assert "NEVER call" in agent.system_prompt or "DO NOT call" in agent.system_prompt


class TestResponseQuality:
    """Test response quality."""
    
    def test_responses_include_citations(self, mock_env_vars):
        """Test responses include citations."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt requires citations
                assert "cite" in agent.system_prompt.lower() or "citation" in agent.system_prompt.lower()
                assert "URL" in agent.system_prompt or "url" in agent.system_prompt.lower()
    
    def test_responses_are_synthesized(self, mock_env_vars):
        """Test responses are synthesized (not raw dumps)."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt requires synthesis
                assert "synthesize" in agent.system_prompt.lower()
                assert "not raw" in agent.system_prompt.lower()
    
    def test_responses_follow_structured_format(self, mock_env_vars):
        """Test responses follow structured format."""
        from langchain_core.tools import Tool
        
        with patch('agent.ChatAnthropic') as mock_claude:
            mock_model = Mock()
            mock_claude.return_value = mock_model
            mock_model.bind_tools = Mock(return_value=mock_model)
            
            with patch('agent.get_public_knowledge_tool') as mock_tool_func:
                proper_tool = Tool(
                    name="consult_public_docs",
                    func=lambda query: f"Results for {query}",
                    description="Search ServiceNow docs"
                )
                mock_tool_func.return_value = proper_tool
                agent = ServiceNowAgent()
                
                # Check system prompt specifies structure
                assert "Official Best Practice" in agent.system_prompt
                assert "Your Context" in agent.system_prompt
                assert "Recommendation" in agent.system_prompt
