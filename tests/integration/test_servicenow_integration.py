"""Integration tests for ServiceNow API integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from tools import fetch_recent_changes, check_table_schema, get_error_logs
from servicenow_client import ServiceNowClient


class TestAPIIntegrations:
    """Test API interactions."""
    
    @pytest.mark.asyncio
    async def test_fetch_recent_changes_calls_api_correctly(self, mock_servicenow_client):
        """Test fetch_recent_changes calls ServiceNow API correctly."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "name": "incident",
                    "action": "insert",
                    "sys_created_by": "admin",
                    "sys_created_on": "2024-01-01"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await fetch_recent_changes(7)
            
            # Verify API was called
            mock_servicenow_client.get_table_records.assert_called_once()
            call_args = mock_servicenow_client.get_table_records.call_args
            
            # Verify correct table and query
            assert "sys_update_xml" in str(call_args)
            assert "daysAgo" in str(call_args) or "7" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_check_table_schema_queries_sys_dictionary(self, mock_servicenow_client):
        """Test check_table_schema queries sys_dictionary correctly."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "column_label": "Number",
                    "element": "number",
                    "internal_type": "string"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await check_table_schema("incident")
            
            mock_servicenow_client.get_table_records.assert_called_once()
            call_args = mock_servicenow_client.get_table_records.call_args
            
            # Verify sys_dictionary table was queried
            assert call_args[0][0] == "sys_dictionary" or "sys_dictionary" in str(call_args)
    
    @pytest.mark.asyncio
    async def test_get_error_logs_queries_syslog(self, mock_servicenow_client):
        """Test get_error_logs queries syslog correctly."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "message": "Error occurred",
                    "level": "2",
                    "sys_created_on": "2024-01-01"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await get_error_logs()
            
            mock_servicenow_client.get_table_records.assert_called_once()
            call_args = mock_servicenow_client.get_table_records.call_args
            
            # Verify syslog table was queried
            assert call_args[0][0] == "syslog" or "syslog" in str(call_args)


class TestErrorHandling:
    """Test error handling for various HTTP status codes."""
    
    @pytest.mark.asyncio
    async def test_handles_401_error(self, mock_servicenow_client):
        """Test handles 401 error."""
        import httpx
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=Mock(), response=mock_response
        )
        
        mock_servicenow_client.client = AsyncMock()
        mock_servicenow_client.client.get = AsyncMock(return_value=mock_response)
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            with pytest.raises(Exception):
                await fetch_recent_changes(7)
    
    @pytest.mark.asyncio
    async def test_handles_500_error(self, mock_servicenow_client):
        """Test handles 500 error."""
        import httpx
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )
        
        mock_servicenow_client.client = AsyncMock()
        mock_servicenow_client.client.get = AsyncMock(return_value=mock_response)
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            with pytest.raises(Exception):
                await check_table_schema("incident")
