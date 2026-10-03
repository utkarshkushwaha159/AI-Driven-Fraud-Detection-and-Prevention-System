"""
Payment and transaction API routes.
Enforces role-based permissions, payment verification, and administrative decisions.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.schemas import (
    PaymentRequest,
    PaymentResponse,
    PaymentVerificationRequest,
    PaymentVerificationResponse,
    AdminDecisionRequest,
    TransactionListResponse,
    TransactionDetailOut,
)
from app.services.transaction_service import TransactionService
from app.services.auth_service import require_role, get_current_user_info

router = APIRouter(prefix="/api", tags=["transactions"])


@router.post("/payments/check", response_model=PaymentResponse)
def check_payment(
    req: PaymentRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """Process a payment through fraud screening."""
    user = get_current_user_info(authorization)
    actor = user.get("username", "customer") if user else "customer"
    try:
        result = TransactionService.process_payment(db, req.model_dump(), actor=actor)
        return PaymentResponse(**result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Payment processing error: {str(e)}")


@router.post("/payments/verify", response_model=PaymentVerificationResponse)
def verify_payment(
    req: PaymentVerificationRequest,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
):
    """
    Verify a suspicious payment using a verification code.
    Maximum 2 attempts allowed. Wrong code on attempt 2 permanently blocks payment.
    """
    user = get_current_user_info(authorization)
    actor = user.get("username", "customer") if user else "customer"
    result = TransactionService.verify_payment(
        db,
        transaction_id=req.transaction_id,
        verification_code=req.verification_code,
        actor=actor,
    )
    return PaymentVerificationResponse(**result)


# --- ADMIN ONLY ROUTES (HTTP 403 for Analyst / Customer) ---

@router.post("/admin/transactions/{transaction_id}/approve")
def admin_approve_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_role(["admin"])),
):
    """
    Admin-only: Final approve decision for high-risk / held transactions.
    Returns HTTP 403 for analyst users.
    """
    return TransactionService.admin_decision(
        db, transaction_id=transaction_id, decision="approve", admin_user=admin_user
    )


@router.post("/admin/transactions/{transaction_id}/reject")
def admin_reject_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_role(["admin"])),
):
    """
    Admin-only: Final reject decision for high-risk / held transactions.
    Returns HTTP 403 for analyst users.
    """
    return TransactionService.admin_decision(
        db, transaction_id=transaction_id, decision="reject", admin_user=admin_user
    )


@router.post("/admin/transactions/{transaction_id}/decision")
def admin_transaction_decision(
    transaction_id: str,
    req: AdminDecisionRequest,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_role(["admin"])),
):
    """
    Admin-only: Final approve/reject decision with optional notes.
    Returns HTTP 403 for analyst users.
    """
    return TransactionService.admin_decision(
        db,
        transaction_id=transaction_id,
        decision=req.decision,
        admin_user=admin_user,
        reason=req.reason,
    )


# --- GENERAL TRANSACTION ROUTES ---

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
