"""Unit tests for servicenow_client.py"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import httpx

from servicenow_client import ServiceNowClient


class TestServiceNowClientInit:
    """Test ServiceNowClient initialization."""
    
    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        client = ServiceNowClient(
            instance="test.instance.com",
            username="test_user",
            password="test_pass"
        )
        
        assert client.instance == "test.instance.com"
        assert client.username == "test_user"
        assert client.password == "test_pass"
        assert client.base_url == "https://test.instance.com"
    
    def test_init_from_environment_variables(self, mock_env_vars):
        """Test initialization from environment variables."""
        client = ServiceNowClient()
        
        assert client.instance == "test-instance.service-now.com"
        assert client.username == "test-user"
        assert client.password == "test-password"
    
    def test_missing_instance_raises_error(self, monkeypatch):
        """Test missing instance raises ValueError."""
        monkeypatch.delenv("SN_INSTANCE", raising=False)
        
        with pytest.raises(ValueError, match="instance"):
            ServiceNowClient()
    
    def test_missing_username_raises_error(self, monkeypatch):
        """Test missing username raises ValueError."""
        monkeypatch.setenv("SN_INSTANCE", "test.instance.com")
        monkeypatch.delenv("SN_USER", raising=False)
        
        with pytest.raises(ValueError, match="username"):
            ServiceNowClient()
    
    def test_missing_password_raises_error(self, monkeypatch):
        """Test missing password raises ValueError."""
        monkeypatch.setenv("SN_INSTANCE", "test.instance.com")
        monkeypatch.setenv("SN_USER", "test_user")
        monkeypatch.delenv("SN_PASSWORD", raising=False)
        
        with pytest.raises(ValueError, match="password"):
            ServiceNowClient()
    
    def test_url_protocol_stripping(self):
        """Test URL protocol stripping."""
        client = ServiceNowClient(
            instance="https://test.instance.com",
            username="user",
            password="pass"
        )
        
        assert client.instance == "test.instance.com"
        assert client.base_url == "https://test.instance.com"


class TestGetTableRecords:
    """Test get_table_records method."""
    
    @pytest.fixture
    def client(self):
        """Create client instance for testing."""
        return ServiceNowClient(
            instance="test.instance.com",
            username="user",
            password="pass"
        )
    
    @pytest.mark.asyncio
    async def test_query_with_query_params(self, client):
        """Test query with query_params."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": [{"id": "123"}]}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        result = await client.get_table_records(
            "sys_user",
            query_params={"active": "true"},
            limit=10
        )
        
        assert "result" in result
        client.client.get.assert_called_once()
        call_args = client.client.get.call_args
        assert "sysparm_query" in call_args[1]["params"]
    
    @pytest.mark.asyncio
    async def test_query_with_query_string(self, client):
        """Test query with query_string."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        result = await client.get_table_records(
            "sys_user",
            query_string="active=true^state=1",
            limit=10
        )
        
        assert "result" in result
        call_args = client.client.get.call_args
        assert call_args[1]["params"]["sysparm_query"] == "active=true^state=1"
    
    @pytest.mark.asyncio
    async def test_query_with_limit_parameter(self, client):
        """Test query with limit parameter."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        await client.get_table_records("sys_user", limit=5)
        
        call_args = client.client.get.call_args
        assert call_args[1]["params"]["sysparm_limit"] == "5"
    
    @pytest.mark.asyncio
    async def test_sysparm_display_value_is_set(self, client):
        """Test sysparm_display_value is set."""
        mock_response = Mock()
        mock_response.json.return_value = {"result": []}
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        await client.get_table_records("sys_user")
        
        call_args = client.client.get.call_args
        assert call_args[1]["params"]["sysparm_display_value"] == "false"
    
    @pytest.mark.asyncio
    async def test_http_error_handling(self, client):
        """Test HTTP error handling."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(Exception, match="ServiceNow API error"):
            await client.get_table_records("sys_user")
    
    @pytest.mark.asyncio
    async def test_request_error_handling(self, client):
        """Test request error handling."""
        client.client = AsyncMock()
        client.client.get = AsyncMock(side_effect=httpx.RequestError("Connection error"))
        
        with pytest.raises(Exception, match="Request error"):
            await client.get_table_records("sys_user")
    
    @pytest.mark.asyncio
    async def test_successful_response_parsing(self, client):
        """Test successful response parsing."""
        expected_data = {"result": [{"id": "123", "name": "test"}]}
        mock_response = Mock()
        mock_response.json.return_value = expected_data
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        client.client = AsyncMock()
        client.client.get = AsyncMock(return_value=mock_response)
        
        result = await client.get_table_records("sys_user")
        
        assert result == expected_data


class TestAsyncContextManager:
    """Test async context manager."""
    
    @pytest.mark.asyncio
    async def test_aenter_and_aexit(self):
        """Test __aenter__ and __aexit__."""
        client = ServiceNowClient(
            instance="test.instance.com",
            username="user",
            password="pass"
        )
        client.close = AsyncMock()
        
        async with client:
            assert client is not None
        
        client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_cleanup(self):
        """Test client cleanup."""
        client = ServiceNowClient(
            instance="test.instance.com",
            username="user",
            password="pass"
        )
        client.client = AsyncMock()
        client.client.aclose = AsyncMock()
        
        await client.close()
        
        client.client.aclose.assert_called_once()
