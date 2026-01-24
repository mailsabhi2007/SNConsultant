"""Admin stats model."""

from typing import Any, Dict

from pydantic import BaseModel


class AdminStatsResponse(BaseModel):
    database: Dict[str, Any]
    knowledge_base: Dict[str, Any]
