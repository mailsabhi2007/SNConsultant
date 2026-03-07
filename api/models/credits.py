"""Credit system Pydantic models."""

from typing import Optional
from pydantic import BaseModel, Field


class CreditBalanceResponse(BaseModel):
    balance: int
    last_transaction_at: Optional[str] = None


class CreditTransaction(BaseModel):
    txn_id: str
    amount: int
    type: str
    description: Optional[str] = None
    ref_message_id: Optional[str] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    model: Optional[str] = None
    granted_by: Optional[str] = None
    created_at: str


class CreditHistoryResponse(BaseModel):
    transactions: list[CreditTransaction]
    total: int


class GrantCreditsRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0)
    description: Optional[str] = "Admin grant"


class RateConfigEntry(BaseModel):
    model: str
    display_name: str
    credits_per_1k_input_tokens: float = Field(..., gt=0)
    credits_per_1k_output_tokens: float = Field(..., gt=0)
    api_cost_per_1k_input_usd: float = Field(..., ge=0)
    api_cost_per_1k_output_usd: float = Field(..., ge=0)
    typical_input_ratio: float = Field(default=0.70, ge=0.0, le=1.0)
    is_active: bool = True
    updated_at: Optional[str] = None


class UpdateRateConfigRequest(BaseModel):
    rates: list[RateConfigEntry]


class UserCreditBalance(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    balance: int
    last_transaction_at: Optional[str] = None
    total_debits: int


class CostEstimateModel(BaseModel):
    model: str
    display_name: str
    estimated_api_cost_usd: float
    estimated_input_tokens: int
    estimated_output_tokens: int


class CostEstimateResponse(BaseModel):
    credits: int
    models: list[CostEstimateModel]
    min_cost_usd: float
    max_cost_usd: float
    blended_cost_usd: float
