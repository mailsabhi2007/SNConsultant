"""Pytest configuration and shared fixtures."""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
import pytest
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import Tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("SN_INSTANCE", "test-instance.service-now.com")
    monkeypatch.setenv("SN_USER", "test-user")
    monkeypatch.setenv("SN_PASSWORD", "test-password")


@pytest.fixture
def test_db_path(tmp_path):
    """Temporary ChromaDB path for testing."""
    db_path = tmp_path / "test_chroma_db"
    return str(db_path)


@pytest.fixture
def cleanup_test_db(test_db_path):
    """Cleanup test database after tests."""
    yield
    if Path(test_db_path).exists():
        shutil.rmtree(test_db_path)


@pytest.fixture
def mock_llm_response():
    """Mock LLM response with tool calls."""
    def _create_response(tool_calls=None, content="Test response"):
        msg = AIMessage(content=content)
        if tool_calls:
            msg.tool_calls = tool_calls
        return msg
    return _create_response


@pytest.fixture
def sample_messages():
    """Sample conversation messages for testing."""
    return [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="What is ServiceNow?"),
    ]


@pytest.fixture
def agent_state(sample_messages):
    """Initial agent state for testing."""
    return {"messages": sample_messages}


@pytest.fixture
def mock_servicenow_response():
    """Sample ServiceNow API response."""
    return {
        "result": [
            {
                "sys_id": "123",
                "name": "incident",
                "sys_created_by": "admin",
                "sys_created_on": "2024-01-01 12:00:00"
            }
        ]
    }


@pytest.fixture
def mock_httpx_client():
    """Mocked HTTP client for ServiceNow."""
    client = AsyncMock()
    response = Mock()
    response.json.return_value = {"result": []}
    response.status_code = 200
    response.raise_for_status = Mock()
    client.get = AsyncMock(return_value=response)
    return client


@pytest.fixture
def mock_servicenow_client(mock_httpx_client):
    """Mocked ServiceNow client."""
    with patch('servicenow_client.ServiceNowClient') as mock_client_class:
        mock_client = Mock()
        mock_client.get_table_records = AsyncMock(return_value={"result": []})
        mock_client.client = mock_httpx_client
        mock_client.base_url = "https://test-instance.service-now.com"
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def test_vector_store(test_db_path, mock_env_vars):
    """Temporary vector store for testing."""
    with patch('knowledge_base._chroma_db_path', test_db_path):
        from knowledge_base import get_vector_store
        store = get_vector_store()
        yield store
        # Cleanup
        if Path(test_db_path).exists():
            shutil.rmtree(test_db_path)


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    from langchain_core.documents import Document
    return [
        Document(
            page_content="This is a test document about ServiceNow.",
            metadata={"source": "test.txt", "source_type": "user_context"}
        ),
        Document(
            page_content="ServiceNow is a cloud-based platform.",
            metadata={"source": "test2.txt", "source_type": "user_context"}
        ),
    ]


@pytest.fixture
def populated_kb(test_vector_store, sample_documents):
    """Knowledge base with test data."""
    test_vector_store.add_documents(sample_documents)
    return test_vector_store


@pytest.fixture
def mock_tavily_tool():
    """Mocked Tavily search tool."""
    from langchain_core.tools import Tool
    tool = Tool(
        name="consult_public_docs",
        func=lambda query: f"Search results for: {query}",
        description="Search official ServiceNow documentation"
    )
    return tool


@pytest.fixture
def mock_public_docs_tool(mock_tavily_tool):
    """Mocked public docs tool."""
    with patch('servicenow_tools.get_public_knowledge_tool', return_value=mock_tavily_tool):
        yield mock_tavily_tool
