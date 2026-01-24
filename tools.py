"""LangChain tools for ServiceNow operations."""

import os
from typing import Optional, Dict
from langchain_core.tools import tool
from servicenow_client import ServiceNowClient
from user_config import get_user_config


# Cache for user-specific clients
_user_clients: Dict[str, ServiceNowClient] = {}


def get_client(user_id: Optional[str] = None) -> ServiceNowClient:
    """
    Get or create ServiceNow client instance.

    Args:
        user_id: Optional user ID to get user-specific credentials

    Returns:
        ServiceNowClient instance
    """
    global _user_clients

    # Try to get user-specific credentials first
    instance = None
    username = None
    password = None

    if user_id:
        instance = get_user_config(user_id, "servicenow", "instance_url")
        username = get_user_config(user_id, "servicenow", "username")
        password = get_user_config(user_id, "servicenow", "password")

    # Fall back to environment variables if not set in user config
    instance = instance or os.getenv("SN_INSTANCE")
    username = username or os.getenv("SN_USER")
    password = password or os.getenv("SN_PASSWORD")

    # Create cache key
    cache_key = f"{user_id or 'default'}:{instance}:{username}"

    # Return cached client if available and credentials haven't changed
    if cache_key in _user_clients:
        return _user_clients[cache_key]

    # Create new client
    client = ServiceNowClient(
        instance=instance,
        username=username,
        password=password
    )

    # Cache the client
    _user_clients[cache_key] = client

    return client


@tool
async def fetch_recent_changes(days_ago: int = 7) -> str:
    """
    Fetch recent changes from ServiceNow sys_update_xml table created by non-system users.
    
    Args:
        days_ago: Number of days to look back (default: 7)
        
    Returns:
        String containing information about recent changes
    """
    try:
        client = get_client()
    except ValueError as e:
        error_detail = str(e)
        if "SN_INSTANCE" in error_detail:
            return ("Error: ServiceNow instance URL is not configured. "
                   "Please set SN_INSTANCE in your .env file or configure it in Settings.")
        elif "SN_USER" in error_detail:
            return ("Error: ServiceNow username is not configured. "
                   "Please set SN_USER in your .env file or configure it in Settings.")
        elif "SN_PASSWORD" in error_detail:
            return ("Error: ServiceNow password is not configured. "
                   "Please set SN_PASSWORD in your .env file or configure it in Settings.")
        else:
            return f"Error: ServiceNow credentials not configured. {error_detail}"
    except Exception as e:
        return f"Error initializing ServiceNow client: {str(e)}"
    
    # Build ServiceNow query: created in last N days AND not created by system users
    # Using JavaScript date function for better compatibility
    query_string = f"sys_created_on>=javascript:gs.daysAgo({days_ago})^sys_created_byNOT INsystem,admin"
    
    try:
        result = await client.get_table_records(
            table_name="sys_update_xml",
            query_string=query_string,
            limit=100
        )
        
        records = result.get("result", [])
        
        if not records:
            return f"No recent changes found from non-system users in the last {days_ago} days."
        
        # Format the results
        changes_info = [f"Found {len(records)} recent changes from non-system users in the last {days_ago} days:\n"]
        
        for i, record in enumerate(records[:10], 1):  # Show first 10
            table_name = record.get("name", "N/A")
            created_by = record.get("sys_created_by", "N/A")
            created_on = record.get("sys_created_on", "N/A")
            action = record.get("action", "N/A")
            
            changes_info.append(f"{i}. Table: {table_name} | Action: {action} | Created by: {created_by} | Date: {created_on}")
        
        if len(records) > 10:
            changes_info.append(f"\n... and {len(records) - 10} more changes")
        
        return "\n".join(changes_info)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return ("Error: Authentication failed. Please check your ServiceNow username and password.")
        elif "403" in error_msg or "Forbidden" in error_msg:
            return ("Error: Access denied. Your ServiceNow user may not have permission to access sys_update_xml table.")
        elif "404" in error_msg or "Not Found" in error_msg:
            return ("Error: ServiceNow instance not found. Please verify your instance URL (SN_INSTANCE) is correct.")
        elif "timeout" in error_msg.lower():
            return ("Error: Connection timeout. Please check your network connection and try again.")
        else:
            return f"Error fetching recent changes: {error_msg}"


@tool
async def check_table_schema(table_name: str) -> str:
    """
    Check the schema (columns and types) for a given ServiceNow table.
    
    Args:
        table_name: Name of the ServiceNow table to check (e.g., 'sys_user', 'incident')
        
    Returns:
        String containing table schema information with columns and their types
    """
    try:
        client = get_client()
    except ValueError as e:
        error_detail = str(e)
        if "SN_INSTANCE" in error_detail:
            return ("Error: ServiceNow instance URL is not configured. "
                   "Please set SN_INSTANCE in your .env file or configure it in Settings.")
        elif "SN_USER" in error_detail:
            return ("Error: ServiceNow username is not configured. "
                   "Please set SN_USER in your .env file or configure it in Settings.")
        elif "SN_PASSWORD" in error_detail:
            return ("Error: ServiceNow password is not configured. "
                   "Please set SN_PASSWORD in your .env file or configure it in Settings.")
        else:
            return f"Error: ServiceNow credentials not configured. {error_detail}"
    except Exception as e:
        return f"Error initializing ServiceNow client: {str(e)}"
    
    try:
        # Query sys_dictionary for the table
        # name field contains the table name, and we want non-empty internal_type
        query_string = f"name={table_name}^internal_type!="
        
        result = await client.get_table_records(
            table_name="sys_dictionary",
            query_string=query_string,
            limit=500
        )
        
        records = result.get("result", [])
        
        if not records:
            return f"No schema found for table '{table_name}'. Please verify the table name is correct."
        
        # Format the schema information
        schema_info = [f"Schema for table '{table_name}':\n"]
        schema_info.append(f"Total columns: {len(records)}\n\n")
        
        for record in sorted(records, key=lambda x: x.get("column_label", x.get("element", ""))):
            column_name = record.get("column_label") or record.get("element", "N/A")
            internal_type = record.get("internal_type", "N/A")
            max_length = record.get("max_length", "")
            reference = record.get("reference", "")
            mandatory = record.get("mandatory", "false")
            
            type_info = internal_type
            if max_length:
                type_info += f"({max_length})"
            if reference:
                type_info += f" -> {reference}"
            if mandatory == "true":
                type_info += " [REQUIRED]"
            
            schema_info.append(f"  - {column_name}: {type_info}")
        
        return "\n".join(schema_info)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            return ("Error: Authentication failed. Please check your ServiceNow username and password.")
        elif "403" in error_msg or "Forbidden" in error_msg:
            return ("Error: Access denied. Your ServiceNow user may not have permission to access sys_dictionary table.")
        elif "404" in error_msg or "Not Found" in error_msg:
            return ("Error: ServiceNow instance not found. Please verify your instance URL (SN_INSTANCE) is correct.")
        elif "timeout" in error_msg.lower():
            return ("Error: Connection timeout. Please check your network connection and try again.")
        else:
            return f"Error checking table schema: {error_msg}"


@tool
async def get_error_logs() -> str:
    """
    Get error logs (level=2) from ServiceNow syslog table for the last 24 hours.
    
    Returns:
        String containing error log entries from the last 24 hours
    """
    try:
        client = get_client()
    except ValueError as e:
        # Missing credentials
        error_detail = str(e)
        if "SN_INSTANCE" in error_detail:
            return ("Error: ServiceNow instance URL is not configured. "
                   "Please set SN_INSTANCE in your .env file or configure it in Settings.")
        elif "SN_USER" in error_detail:
            return ("Error: ServiceNow username is not configured. "
                   "Please set SN_USER in your .env file or configure it in Settings.")
        elif "SN_PASSWORD" in error_detail:
            return ("Error: ServiceNow password is not configured. "
                   "Please set SN_PASSWORD in your .env file or configure it in Settings.")
        else:
            return f"Error: ServiceNow credentials not configured. {error_detail}"
    except Exception as e:
        return f"Error initializing ServiceNow client: {str(e)}"
    
    try:
        # Query syslog for level=2 (errors) in last 24 hours
        # Using JavaScript date function for better compatibility
        query_string = "level=2^sys_created_on>=javascript:gs.hoursAgo(24)"
        
        result = await client.get_table_records(
            table_name="syslog",
            query_string=query_string,
            limit=100
        )
        
        records = result.get("result", [])
        
        if not records:
            return "No error logs found in the last 24 hours."
        
        # Format error logs
        log_info = [f"Found {len(records)} error logs in the last 24 hours:\n"]
        
        for i, record in enumerate(records[:20], 1):  # Show first 20
            message = record.get("message", "N/A")
            source = record.get("source", "N/A")
            created = record.get("sys_created_on", "N/A")
            logger = record.get("logger", "N/A")
            level = record.get("level", "N/A")
            
            log_info.append(f"{i}. [{created}] Level {level} | {source}/{logger}")
            log_info.append(f"   Message: {message}\n")
        
        if len(records) > 20:
            log_info.append(f"... and {len(records) - 20} more errors")
        
        return "\n".join(log_info)
    except Exception as e:
        error_msg = str(e)
        # Provide more helpful error messages
        if "401" in error_msg or "Unauthorized" in error_msg:
            return ("Error: Authentication failed. Please check your ServiceNow username and password. "
                   "The credentials may be incorrect or the account may be locked.")
        elif "403" in error_msg or "Forbidden" in error_msg:
            return ("Error: Access denied. Your ServiceNow user account may not have permission to access the syslog table. "
                   "Please contact your ServiceNow administrator.")
        elif "404" in error_msg or "Not Found" in error_msg:
            return ("Error: ServiceNow instance not found. Please verify your instance URL (SN_INSTANCE) is correct. "
                   "Format should be: your-instance.service-now.com (without https://)")
        elif "timeout" in error_msg.lower() or "Timeout" in error_msg:
            return ("Error: Connection timeout. The ServiceNow instance may be unreachable or slow to respond. "
                   "Please check your network connection and try again.")
        elif "Request error" in error_msg or "Connection" in error_msg:
            return (f"Error: Unable to connect to ServiceNow instance. {error_msg} "
                   "Please verify your instance URL and network connectivity.")
        else:
            return f"Error fetching error logs: {error_msg}"


@tool
def save_learned_preference(preference_text: str) -> str:
    """
    Save a learned preference or memory to the knowledge base.
    
    This tool saves user preferences, learned information, or important
    context that should be remembered for future conversations. The
    preference is saved to a file and then re-indexed into the vector store.
    
    Args:
        preference_text: The preference or memory text to save
        
    Returns:
        String confirmation message with number of chunks created
    """
    from pathlib import Path
    from datetime import datetime
    from knowledge_base import ingest_user_file
    
    try:
        # Create directory if it doesn't exist
        data_dir = Path("./user_context_data")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file path
        file_path = data_dir / "learned_memories.txt"
        
        # Generate timestamp
        timestamp = datetime.now().isoformat()
        
        # Format entry
        entry = f"{timestamp}\n---\n{preference_text}\n{'=' * 80}\n\n"
        
        # Append to file
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        # Re-index the file
        try:
            chunks_count = ingest_user_file(str(file_path))
            return f"Successfully saved preference and indexed {chunks_count} chunks. The preference is now available for future queries."
        except Exception as ingestion_error:
            # File is saved, but ingestion failed
            return f"Successfully saved preference to file, but indexing failed: {str(ingestion_error)}. The preference is saved but may not be searchable yet."
    except Exception as e:
        return f"Error saving preference: {str(e)}"


# List of all tools for easy import
__all__ = ["fetch_recent_changes", "check_table_schema", "get_error_logs", "save_learned_preference"]
