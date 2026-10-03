"""
Network analysis API routes.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.network_service import NetworkService

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/{transaction_id}")
def get_transaction_network(
    transaction_id: str,
    depth: int = Query(2, ge=1, le=4),
    db: Session = Depends(get_db),
):
    """Get network graph for a transaction."""
    return NetworkService.build_transaction_network(db, transaction_id, depth=depth)


@router.get("")
def get_full_network(
    limit: int = Query(100, ge=10, le=500),
    db: Session = Depends(get_db),
):
    """Get overview network graph."""
    return NetworkService.get_full_network(db, limit=limit)
