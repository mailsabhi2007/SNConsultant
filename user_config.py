"""User-specific configuration management."""

import json
from typing import Optional, Dict, Any, List
from database import get_db_connection


def get_user_config(user_id: str, config_type: str, config_key: str, default: Any = None) -> Any:
    """
    Get a user configuration value.
    
    Args:
        user_id: User ID
        config_type: Type of config (e.g., 'servicenow', 'preferences', 'model_settings')
        config_key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value (parsed from JSON if needed)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT config_value FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (user_id, config_type, config_key))
        
        result = cursor.fetchone()
        if not result:
            return default
        
        value = result[0]
        if value is None:
            return default
        
        # Try to parse as JSON, fallback to string
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value


def set_user_config(user_id: str, config_type: str, config_key: str, config_value: Any) -> bool:
    """
    Set a user configuration value.
    
    Args:
        user_id: User ID
        config_type: Type of config
        config_key: Configuration key
        config_value: Value to store (will be JSON-encoded if needed)
        
    Returns:
        True if successful
    """
    # Convert value to JSON string if it's not already a string
    if not isinstance(config_value, str):
        value_str = json.dumps(config_value)
    else:
        value_str = config_value
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if config exists
        cursor.execute("""
            SELECT config_id FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (user_id, config_type, config_key))
        
        exists = cursor.fetchone()
        
        if exists:
            # Update existing
            cursor.execute("""
                UPDATE user_configs
                SET config_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND config_type = ? AND config_key = ?
            """, (value_str, user_id, config_type, config_key))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO user_configs (user_id, config_type, config_key, config_value)
                VALUES (?, ?, ?, ?)
            """, (user_id, config_type, config_key, value_str))
        
        return True


def get_user_servicenow_config(user_id: str) -> Dict[str, str]:
    """
    Get user's ServiceNow configuration.
    
    Note: Only instance is user-configurable. Username/password are system-level.
    
    Returns:
        Dictionary with 'instance' key only
    """
    return {
        'instance': get_user_config(user_id, 'servicenow', 'instance', '')
    }


def set_user_servicenow_config(user_id: str, instance: str) -> bool:
    """
    Set user's ServiceNow instance configuration.
    
    Note: Only instance is user-configurable. Username/password are managed at system level.
    """
    set_user_config(user_id, 'servicenow', 'instance', instance)
    return True


def get_system_config(config_key: str, default: Any = None) -> Any:
    """
    Get system-level configuration (for admin/superadmin).
    
    This is used for API keys and other system-wide settings that are not user-specific.
    Uses a special 'system' user_id in the config table.
    
    Args:
        config_key: Configuration key (e.g., 'anthropic_api_key', 'openai_api_key', 'servicenow_username', 'servicenow_password')
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    SYSTEM_USER_ID = 'system'
    return get_user_config(SYSTEM_USER_ID, 'system', config_key, default)


def set_system_config(config_key: str, config_value: Any) -> bool:
    """
    Set system-level configuration (for admin/superadmin).
    
    Args:
        config_key: Configuration key
        config_value: Value to store
    """
    SYSTEM_USER_ID = 'system'
    return set_user_config(SYSTEM_USER_ID, 'system', config_key, config_value)


def get_system_servicenow_credentials() -> Dict[str, str]:
    """
    Get system-level ServiceNow credentials (username/password).
    
    These are shared across all users and managed by system admin.
    
    Returns:
        Dictionary with 'username' and 'password' keys
    """
    return {
        'username': get_system_config('servicenow_username', ''),
        'password': get_system_config('servicenow_password', '')
    }


def set_system_servicenow_credentials(username: str, password: str) -> bool:
    """Set system-level ServiceNow credentials."""
    set_system_config('servicenow_username', username)
    set_system_config('servicenow_password', password)
    return True


def get_all_user_configs(user_id: str, config_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Get all configurations for a user, optionally filtered by type.
    
    Args:
        user_id: User ID
        config_type: Optional filter by config type
        
    Returns:
        Dictionary of configurations organized by type and key
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if config_type:
            cursor.execute("""
                SELECT config_type, config_key, config_value
                FROM user_configs
                WHERE user_id = ? AND config_type = ?
            """, (user_id, config_type))
        else:
            cursor.execute("""
                SELECT config_type, config_key, config_value
                FROM user_configs
                WHERE user_id = ?
            """, (user_id,))
        
        configs = {}
        for row in cursor.fetchall():
            cfg_type, cfg_key, cfg_value = row
            
            if cfg_type not in configs:
                configs[cfg_type] = {}
            
            # Try to parse JSON
            try:
                configs[cfg_type][cfg_key] = json.loads(cfg_value)
            except (json.JSONDecodeError, TypeError):
                configs[cfg_type][cfg_key] = cfg_value
        
        return configs


def delete_user_config(user_id: str, config_type: str, config_key: str) -> bool:
    """Delete a user configuration."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM user_configs
            WHERE user_id = ? AND config_type = ? AND config_key = ?
        """, (user_id, config_type, config_key))
        return cursor.rowcount > 0


def get_user_learned_preferences(user_id: str) -> List[Dict[str, Any]]:
    """Get all learned preferences for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT preference_id, preference_text, context, created_at
            FROM user_learned_preferences
            WHERE user_id = ?
            ORDER BY created_at DESC
        """, (user_id,))
        
        preferences = []
        for row in cursor.fetchall():
            preferences.append({
                'preference_id': row[0],
                'preference_text': row[1],
                'context': row[2],
                'created_at': row[3]
            })
        
        return preferences


def add_user_learned_preference(user_id: str, preference_text: str, context: Optional[str] = None) -> int:
    """Add a learned preference for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_learned_preferences (user_id, preference_text, context)
            VALUES (?, ?, ?)
        """, (user_id, preference_text, context))
        
        return cursor.lastrowid


def delete_user_learned_preference(user_id: str, preference_id: int) -> bool:
    """Delete a learned preference."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM user_learned_preferences
            WHERE user_id = ? AND preference_id = ?
        """, (user_id, preference_id))
        return cursor.rowcount > 0


def is_multi_agent_enabled(user_id: str) -> bool:
    """Check if multi-agent system is enabled for a user.

    Uses a rollout percentage strategy:
    1. Check if user has explicit override (user_config)
    2. Check system rollout percentage
    3. Use consistent hashing to determine if user is in rollout percentage

    Args:
        user_id: User ID

    Returns:
        True if multi-agent is enabled for this user
    """
    # Check for user-specific override
    user_override = get_user_config(user_id, 'features', 'multi_agent_enabled')
    if user_override is not None:
        return bool(user_override)

    # Check system-wide rollout percentage
    rollout_percentage = get_system_config('multi_agent_rollout_percentage', 0)

    # If 0%, disabled for all
    if rollout_percentage <= 0:
        return False

    # If 100%, enabled for all
    if rollout_percentage >= 100:
        return True

    # Use consistent hashing to determine rollout
    # This ensures same user always gets same result for same percentage
    import hashlib
    user_hash = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    user_bucket = user_hash % 100  # 0-99

    return user_bucket < rollout_percentage


def set_multi_agent_override(user_id: str, enabled: bool) -> bool:
    """Set user-specific multi-agent override.

    Args:
        user_id: User ID
        enabled: Whether to enable multi-agent for this user

    Returns:
        True if successful
    """
    return set_user_config(user_id, 'features', 'multi_agent_enabled', enabled)


def set_multi_agent_rollout_percentage(percentage: int) -> bool:
    """Set system-wide multi-agent rollout percentage.

    Args:
        percentage: Rollout percentage (0-100)

    Returns:
        True if successful
    """
    if percentage < 0 or percentage > 100:
        raise ValueError("Rollout percentage must be between 0 and 100")

    return set_system_config('multi_agent_rollout_percentage', percentage)
