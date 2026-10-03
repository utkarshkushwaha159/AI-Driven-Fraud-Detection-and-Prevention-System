"""
Fraud alerts API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.fraud_alert import FraudAlert
from app.models.transaction import Transaction

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    severity: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get paginated alerts with filtering."""
    query = db.query(FraudAlert)

    if status and status != "all":
        query = query.filter(FraudAlert.status == status)
    if severity and severity != "all":
        query = query.filter(FraudAlert.severity == severity)

    total = query.count()
    alerts = query.order_by(desc(FraudAlert.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for alert in alerts:
        tx = db.query(Transaction).filter(Transaction.id == alert.transaction_id).first()
        result.append({
            "id": alert.id,
            "transaction_id": alert.transaction_id,
            "fraud_probability": alert.fraud_probability,
            "anomaly_score": alert.anomaly_score,
            "severity": alert.severity,
            "status": alert.status,
            "description": alert.description,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
            "transaction_amount": tx.amount if tx else None,
            "account_id": tx.account_id if tx else None,
        })

    return {"alerts": result, "total": total, "page": page, "page_size": page_size}


@router.get("/{alert_id}")
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get alert detail."""
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    tx = db.query(Transaction).filter(Transaction.id == alert.transaction_id).first()
    return {
        "id": alert.id,
        "transaction_id": alert.transaction_id,
        "fraud_probability": alert.fraud_probability,
        "anomaly_score": alert.anomaly_score,
        "severity": alert.severity,
        "status": alert.status,
        "description": alert.description,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
        "transaction_amount": tx.amount if tx else None,
        "account_id": tx.account_id if tx else None,
    }


@router.patch("/{alert_id}")
def update_alert(alert_id: str, status: str = None, db: Session = Depends(get_db)):
    """Update alert status."""
    alert = db.query(FraudAlert).filter(FraudAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if status:
        alert.status = status
    db.commit()
    return {"message": "Alert updated", "id": alert_id, "status": alert.status}
