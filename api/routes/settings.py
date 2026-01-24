"""Settings endpoints."""

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user
from api.models.settings import ConfigUpdateRequest, BulkConfigUpdateRequest, SettingsResponse
from user_config import get_all_user_configs, set_user_config


router = APIRouter()


@router.get("/config", response_model=SettingsResponse)
def get_config(current_user: dict = Depends(get_current_user)) -> SettingsResponse:
    """Get all user config."""
    configs = get_all_user_configs(current_user["user_id"])
    return SettingsResponse(configs=configs, user_id=current_user["user_id"])


@router.put("/config", response_model=SettingsResponse)
def update_config(
    payload: ConfigUpdateRequest, current_user: dict = Depends(get_current_user)
) -> SettingsResponse:
    """Update a single config value."""
    set_user_config(
        current_user["user_id"],
        payload.config_type,
        payload.config_key,
        payload.config_value,
    )
    configs = get_all_user_configs(current_user["user_id"])
    return SettingsResponse(configs=configs, user_id=current_user["user_id"])


@router.put("/config/bulk", response_model=SettingsResponse)
def update_config_bulk(
    payload: BulkConfigUpdateRequest, current_user: dict = Depends(get_current_user)
) -> SettingsResponse:
    """Update multiple config values."""
    for config_type, items in payload.configs.items():
        for config_key, config_value in items.items():
            set_user_config(current_user["user_id"], config_type, config_key, config_value)
    configs = get_all_user_configs(current_user["user_id"])
    return SettingsResponse(configs=configs, user_id=current_user["user_id"])
