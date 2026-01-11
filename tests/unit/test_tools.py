"""Unit tests for tools.py"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from tools import fetch_recent_changes, check_table_schema, get_error_logs


class TestFetchRecentChanges:
    """Test fetch_recent_changes tool."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch_with_days_ago(self, mock_servicenow_client):
        """Test successful fetch with days_ago parameter."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "name": "incident",
                    "action": "insert",
                    "sys_created_by": "admin",
                    "sys_created_on": "2024-01-01 12:00:00"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await fetch_recent_changes(7)
            
            assert "Found" in result
            assert "recent changes" in result.lower()
            mock_servicenow_client.get_table_records.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_default_days_ago(self, mock_servicenow_client):
        """Test default days_ago=7."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={"result": []})
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            await fetch_recent_changes()
            
            call_args = mock_servicenow_client.get_table_records.call_args
            assert "sys_update_xml" in call_args[1]["table_name"] or call_args[0][0] == "sys_update_xml"
    
    @pytest.mark.asyncio
    async def test_empty_results_handling(self, mock_servicenow_client):
        """Test empty results handling."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={"result": []})
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await fetch_recent_changes(7)
            
            assert "No recent changes found" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_servicenow_client):
        """Test error handling."""
        mock_servicenow_client.get_table_records = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await fetch_recent_changes(7)
            
            assert "Error" in result


class TestCheckTableSchema:
    """Test check_table_schema tool."""
    
    @pytest.mark.asyncio
    async def test_successful_schema_retrieval(self, mock_servicenow_client):
        """Test successful schema retrieval."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "column_label": "Number",
                    "element": "number",
                    "internal_type": "string",
                    "max_length": "40"
                },
                {
                    "column_label": "State",
                    "element": "state",
                    "internal_type": "integer"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await check_table_schema("incident")
            
            assert "Schema for table 'incident'" in result
            assert "Number" in result or "number" in result
            mock_servicenow_client.get_table_records.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_table_not_found_handling(self, mock_servicenow_client):
        """Test table not found handling."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={"result": []})
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await check_table_schema("nonexistent_table")
            
            assert "No schema found" in result or "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_schema_formatting(self, mock_servicenow_client):
        """Test schema formatting."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "column_label": "Test Column",
                    "internal_type": "string",
                    "max_length": "100",
                    "mandatory": "true"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await check_table_schema("test_table")
            
            assert "Test Column" in result
            assert "string" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_servicenow_client):
        """Test error handling."""
        mock_servicenow_client.get_table_records = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await check_table_schema("incident")
            
            assert "Error" in result


class TestGetErrorLogs:
    """Test get_error_logs tool."""
    
    @pytest.mark.asyncio
    async def test_successful_log_retrieval(self, mock_servicenow_client):
        """Test successful log retrieval."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "message": "Test error message",
                    "source": "test_source",
                    "sys_created_on": "2024-01-01 12:00:00",
                    "logger": "test_logger",
                    "level": "2"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await get_error_logs()
            
            assert "Found" in result or "error logs" in result.lower()
            assert "Test error message" in result
            mock_servicenow_client.get_table_records.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_empty_logs_handling(self, mock_servicenow_client):
        """Test empty logs handling."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={"result": []})
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await get_error_logs()
            
            assert "No error logs found" in result
    
    @pytest.mark.asyncio
    async def test_log_formatting(self, mock_servicenow_client):
        """Test log formatting."""
        mock_servicenow_client.get_table_records = AsyncMock(return_value={
            "result": [
                {
                    "message": "Error occurred",
                    "source": "script",
                    "sys_created_on": "2024-01-01",
                    "logger": "app",
                    "level": "2"
                }
            ]
        })
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await get_error_logs()
            
            assert "Error occurred" in result
            assert "2024-01-01" in result
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_servicenow_client):
        """Test error handling."""
        mock_servicenow_client.get_table_records = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('tools.get_client', return_value=mock_servicenow_client):
            result = await get_error_logs()
            
            assert "Error" in result
