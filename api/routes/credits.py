"""User-facing credit endpoints."""

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_current_user
from api.models.credits import CreditBalanceResponse, CreditHistoryResponse, CreditTransaction
from api.services.credit_service import get_balance, get_transaction_history

router = APIRouter()


@router.get("/balance", response_model=CreditBalanceResponse)
def balance(current_user: dict = Depends(get_current_user)) -> CreditBalanceResponse:
    """Return the current user's credit balance."""
    history = get_transaction_history(current_user["user_id"], limit=1)
    last_at = history[0]["created_at"] if history else None
    return CreditBalanceResponse(
        balance=get_balance(current_user["user_id"]),
        last_transaction_at=last_at,
    )


@router.get("/history", response_model=CreditHistoryResponse)
def history(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
) -> CreditHistoryResponse:
    """Return paginated transaction history for the current user."""
    txns = get_transaction_history(current_user["user_id"], limit=limit, offset=offset)
    return CreditHistoryResponse(
        transactions=[CreditTransaction(**t) for t in txns],
        total=len(txns),
    )
