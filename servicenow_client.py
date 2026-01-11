"""ServiceNow API Client using httpx for async requests."""

import os
from pathlib import Path
from typing import Dict, Optional, Any
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
# Try both the script directory and current working directory
env_paths = [
    Path(__file__).parent / ".env",
    Path.cwd() / ".env"
]
env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        env_loaded = True
        break
if not env_loaded:
    # If no .env file found, try default behavior (current directory)
    load_dotenv()


class ServiceNowClient:
    """Client for interacting with ServiceNow REST API."""
    
    def __init__(
        self,
        instance: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize ServiceNow client.
        
        Args:
            instance: ServiceNow instance URL (e.g., 'dev12345.service-now.com')
            username: ServiceNow username
            password: ServiceNow password
            
        If not provided, values will be read from environment variables:
        - SN_INSTANCE
        - SN_USER
        - SN_PASSWORD
        """
        self.instance = instance or os.getenv("SN_INSTANCE")
        self.username = username or os.getenv("SN_USER")
        self.password = password or os.getenv("SN_PASSWORD")
        
        if not self.instance:
            raise ValueError("ServiceNow instance URL is required (SN_INSTANCE env var or instance parameter)")
        if not self.username:
            raise ValueError("ServiceNow username is required (SN_USER env var or username parameter)")
        if not self.password:
            raise ValueError("ServiceNow password is required (SN_PASSWORD env var or password parameter)")
        
        # Ensure instance URL doesn't have protocol
        self.instance = self.instance.replace("https://", "").replace("http://", "")
        self.base_url = f"https://{self.instance}"
        
        # Create httpx client with BasicAuth
        self.client = httpx.AsyncClient(
            auth=(self.username, self.password),
            timeout=30.0
        )
    
    async def get_table_records(
        self,
        table_name: str,
        query_params: Optional[Dict[str, Any]] = None,
        query_string: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieve records from a ServiceNow table.
        
        Args:
            table_name: Name of the ServiceNow table (e.g., 'sys_user')
            query_params: Optional dictionary of query parameters to filter records
            query_string: Optional raw ServiceNow query string (takes precedence over query_params)
            limit: Optional maximum number of records to return
            
        Returns:
            Dictionary containing the API response with records
            
        Example:
            >>> client = ServiceNowClient()
            >>> records = await client.get_table_records(
            ...     'sys_user',
            ...     query_params={'active': 'true'},
            ...     limit=10
            ... )
            >>> # Or with raw query string:
            >>> records = await client.get_table_records(
            ...     'sys_user',
            ...     query_string='active=true^sys_created_on>=javascript:gs.daysAgo(7)',
            ...     limit=10
            ... )
        """
        url = f"{self.base_url}/api/now/table/{table_name}"
        
        params = {}
        if query_string:
            # Use raw query string if provided
            params["sysparm_query"] = query_string
        elif query_params:
            # Convert query_params to ServiceNow query string format
            query_string = "^".join([f"{k}={v}" for k, v in query_params.items()])
            params["sysparm_query"] = query_string
        
        if limit:
            params["sysparm_limit"] = str(limit)
        
        # Always request JSON response
        params["sysparm_display_value"] = "false"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"ServiceNow API error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")
    
    async def close(self):
        """Close the httpx client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
