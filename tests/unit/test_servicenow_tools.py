"""Unit tests for servicenow_tools.py"""

import pytest
from unittest.mock import Mock, patch
from servicenow_tools import get_public_knowledge_tool


class TestGetPublicKnowledgeTool:
    """Test get_public_knowledge_tool function."""
    
    def test_tool_creation_with_valid_api_key(self, mock_env_vars):
        """Test tool creation with valid API key."""
        with patch('servicenow_tools.TavilySearchResults') as mock_tavily:
            mock_tool = Mock()
            mock_tavily.return_value = mock_tool
            
            tool = get_public_knowledge_tool()
            
            assert tool is not None
            mock_tavily.assert_called_once()
    
    def test_missing_tavily_api_key_raises_error(self, monkeypatch):
        """Test missing TAVILY_API_KEY raises ValueError."""
        monkeypatch.delenv("TAVILY_API_KEY", raising=False)
        
        with pytest.raises(ValueError, match="TAVILY_API_KEY"):
            get_public_knowledge_tool()
    
    def test_tool_name_is_consult_public_docs(self, mock_env_vars):
        """Test tool name is 'consult_public_docs'."""
        with patch('servicenow_tools.TavilySearchResults') as mock_tavily:
            mock_tool = Mock()
            mock_tavily.return_value = mock_tool
            
            tool = get_public_knowledge_tool()
            
            call_args = mock_tavily.call_args
            assert call_args[1]['name'] == "consult_public_docs"
    
    def test_domain_restrictions_are_set(self, mock_env_vars):
        """Test domain restrictions are set."""
        with patch('servicenow_tools.TavilySearchResults') as mock_tavily:
            mock_tool = Mock()
            mock_tavily.return_value = mock_tool
            
            get_public_knowledge_tool()
            
            call_args = mock_tavily.call_args
            assert 'include_domains' in call_args[1]
            domains = call_args[1]['include_domains']
            assert 'docs.servicenow.com' in domains
            assert 'community.servicenow.com' in domains
    
    def test_search_depth_is_advanced(self, mock_env_vars):
        """Test search_depth is 'advanced'."""
        with patch('servicenow_tools.TavilySearchResults') as mock_tavily:
            mock_tool = Mock()
            mock_tavily.return_value = mock_tool
            
            get_public_knowledge_tool()
            
            call_args = mock_tavily.call_args
            assert call_args[1]['search_depth'] == 'advanced'
    
    def test_max_results_is_5(self, mock_env_vars):
        """Test max_results is 5."""
        with patch('servicenow_tools.TavilySearchResults') as mock_tavily:
            mock_tool = Mock()
            mock_tavily.return_value = mock_tool
            
            get_public_knowledge_tool()
            
            call_args = mock_tavily.call_args
            assert call_args[1]['max_results'] == 5
