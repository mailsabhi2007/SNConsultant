"""Configuration management for ServiceNow Consultant app."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

CONFIG_FILE = Path("./config.json")
DEFAULT_CONFIG = {
    "servicenow": {
        "instance": "",
        "username": "",
        "password": ""
    },
    "search_domains": [
        "docs.servicenow.com",
        "community.servicenow.com",
        "developer.servicenow.com"
    ],
    "safety_level": "strict"
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from config.json file.
    
    Returns:
        Dictionary containing configuration. Returns default config if file doesn't exist.
    """
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                merged = DEFAULT_CONFIG.copy()
                merged.update(config)
                # Ensure nested dicts are merged properly
                if "servicenow" in config:
                    merged["servicenow"].update(config["servicenow"])
                return merged
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}. Using defaults.")
            return DEFAULT_CONFIG.copy()
    else:
        # Create default config file
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to config.json file.
    
    Args:
        config: Configuration dictionary to save
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        raise IOError(f"Error saving config: {e}")


def get_search_domains() -> List[str]:
    """
    Get list of search domains from config.
    
    Returns:
        List of domain strings
    """
    config = load_config()
    return config.get("search_domains", DEFAULT_CONFIG["search_domains"])


def get_sn_credentials() -> Dict[str, str]:
    """
    Get ServiceNow credentials from config.
    
    Returns:
        Dictionary with 'instance', 'username', 'password' keys
    """
    config = load_config()
    return config.get("servicenow", DEFAULT_CONFIG["servicenow"])


def update_sn_credentials(instance: str, username: str, password: str) -> None:
    """
    Update ServiceNow credentials in config.
    
    Args:
        instance: ServiceNow instance URL
        username: ServiceNow username
        password: ServiceNow password
    """
    config = load_config()
    config["servicenow"] = {
        "instance": instance,
        "username": username,
        "password": password
    }
    save_config(config)


def add_search_domain(domain: str) -> None:
    """
    Add a new search domain to config.
    
    Args:
        domain: Domain string to add (e.g., 'docs.servicenow.com')
    """
    config = load_config()
    domains = config.get("search_domains", [])
    if domain not in domains:
        domains.append(domain)
        config["search_domains"] = domains
        save_config(config)


def remove_search_domain(domain: str) -> None:
    """
    Remove a search domain from config.
    
    Args:
        domain: Domain string to remove
    """
    config = load_config()
    domains = config.get("search_domains", [])
    if domain in domains:
        domains.remove(domain)
        config["search_domains"] = domains
        save_config(config)


def get_safety_level() -> str:
    """
    Get safety level from config.
    
    Returns:
        Safety level string ('strict' or 'open')
    """
    config = load_config()
    return config.get("safety_level", "strict")


def update_safety_level(level: str) -> None:
    """
    Update safety level in config.
    
    Args:
        level: Safety level ('strict' or 'open')
    """
    config = load_config()
    config["safety_level"] = level
    save_config(config)
