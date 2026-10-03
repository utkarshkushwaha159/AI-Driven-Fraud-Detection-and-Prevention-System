"""
Payment and transaction API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.schemas import PaymentRequest, PaymentResponse, TransactionListResponse
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/api", tags=["transactions"])


@router.post("/payments/check", response_model=PaymentResponse)
def check_payment(req: PaymentRequest, db: Session = Depends(get_db)):
    """Process a payment through fraud screening."""
    try:
        result = TransactionService.process_payment(db, req.model_dump())
        return PaymentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")


@router.get("/transactions")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    status: str = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    account_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get paginated transaction list with filtering."""
    return TransactionService.get_transactions(
        db, page=page, page_size=page_size, search=search,
        status_filter=status, sort_by=sort_by, sort_dir=sort_dir,
        account_id=account_id,
    )


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get detailed transaction info."""
    detail = TransactionService.get_transaction_detail(db, transaction_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return detail


@router.get("/accounts/{account_id}/transactions")
def get_account_transactions(
    account_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get transactions for a specific account."""
    return TransactionService.get_transactions(
        db, page=page, page_size=page_size, account_id=account_id,
    )
