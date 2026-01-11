"""Helper functions for Streamlit UI."""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from servicenow_client import ServiceNowClient


def get_learned_rules() -> List[Dict[str, str]]:
    """
    Parse learned_memories.txt and return list of rules.
    
    Returns:
        List of dictionaries with 'timestamp' and 'rule' keys
    """
    rules_file = Path("./user_context_data/learned_memories.txt")
    
    if not rules_file.exists():
        return []
    
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        rules = []
        lines = content.split('\n')
        current_timestamp = None
        current_rule = []
        in_rule = False
        
        for line in lines:
            line = line.strip()
            
            # Check if line is a timestamp (ISO format)
            if line and not line.startswith('---') and not line.startswith('='):
                try:
                    # Try to parse as timestamp
                    datetime.fromisoformat(line)
                    # If we have a previous rule, save it
                    if current_timestamp and current_rule:
                        rules.append({
                            'timestamp': current_timestamp,
                            'rule': '\n'.join(current_rule).strip()
                        })
                    current_timestamp = line
                    current_rule = []
                    in_rule = False
                    continue
                except (ValueError, TypeError):
                    pass
            
            # Check for separator
            if line.startswith('---'):
                in_rule = True
                continue
            
            # Skip separator lines
            if line.startswith('=') or not line:
                if in_rule and current_rule:
                    in_rule = False
                continue
            
            # Collect rule text
            if in_rule and current_timestamp:
                current_rule.append(line)
        
        # Don't forget the last rule
        if current_timestamp and current_rule:
            rules.append({
                'timestamp': current_timestamp,
                'rule': '\n'.join(current_rule).strip()
            })
        
        return rules
    except Exception as e:
        print(f"Error parsing learned rules: {e}")
        return []


def delete_learned_rule(timestamp: str) -> bool:
    """
    Remove a specific rule from learned_memories.txt by timestamp.
    
    Args:
        timestamp: ISO format timestamp of the rule to delete
        
    Returns:
        True if successful, False otherwise
    """
    rules_file = Path("./user_context_data/learned_memories.txt")
    
    if not rules_file.exists():
        return False
    
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        new_lines = []
        skip_section = False
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line is the timestamp we want to delete
            if line.strip() == timestamp:
                skip_section = True
                # Skip until we hit the next timestamp or end of file
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    # Check if next line is a timestamp
                    try:
                        datetime.fromisoformat(next_line)
                        # Found next timestamp, stop skipping
                        skip_section = False
                        break
                    except (ValueError, TypeError):
                        pass
                    i += 1
                continue
            
            if not skip_section:
                new_lines.append(line)
            
            i += 1
        
        # Write back
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        # Re-index the file
        from knowledge_base import ingest_user_file
        try:
            ingest_user_file(str(rules_file))
        except Exception as e:
            print(f"Warning: Could not re-index after deleting rule: {e}")
        
        return True
    except Exception as e:
        print(f"Error deleting learned rule: {e}")
        return False


async def test_sn_connection_async(instance: str, username: str, password: str) -> Tuple[bool, str]:
    """
    Test ServiceNow connection asynchronously.
    
    Args:
        instance: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        client = ServiceNowClient(instance=instance, username=username, password=password)
        # Try to get a simple record
        result = await client.get_table_records("sys_user", limit=1)
        
        if result and "result" in result:
            return True, "Connection successful"
        else:
            return False, "Connection failed: No data returned"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def test_sn_connection(instance: str, username: str, password: str) -> Tuple[bool, str]:
    """
    Test ServiceNow connection (synchronous wrapper).
    
    Args:
        instance: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        return asyncio.run(test_sn_connection_async(instance, username, password))
    except Exception as e:
        return False, f"Error testing connection: {str(e)}"


def check_connection_health(instance: str, username: str, password: str) -> Tuple[bool, str, str]:
    """
    Check ServiceNow connection health.
    
    Args:
        instance: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password
        
    Returns:
        Tuple of (success: bool, message: str, status: str)
        status can be: "connected", "failed", or "not_configured"
    """
    if not instance or not username or not password:
        return False, "Connection not configured", "not_configured"
    
    try:
        success, message = test_sn_connection(instance, username, password)
        if success:
            return True, message, "connected"
        else:
            return False, message, "failed"
    except Exception as e:
        return False, f"Health check error: {str(e)}", "failed"
