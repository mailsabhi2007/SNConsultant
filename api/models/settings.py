"""Settings request/response models."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ConfigUpdateRequest(BaseModel):
    config_type: str = Field(..., min_length=1)
    config_key: str = Field(..., min_length=1)
    config_value: Any


class BulkConfigUpdateRequest(BaseModel):
    configs: Dict[str, Dict[str, Any]]


class SettingsResponse(BaseModel):
    configs: Dict[str, Dict[str, Any]]
    user_id: Optional[str] = None
