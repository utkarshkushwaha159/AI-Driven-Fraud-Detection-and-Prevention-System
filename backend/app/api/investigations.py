"""
Investigation API routes.
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.investigation import Investigation, InvestigationNote
from app.schemas.schemas import InvestigationCreate, InvestigationUpdate, InvestigationNoteCreate

router = APIRouter(prefix="/api/investigations", tags=["investigations"])


@router.post("")
def create_investigation(req: InvestigationCreate, db: Session = Depends(get_db)):
    """Create a new investigation case."""
    investigation = Investigation(
        id=str(uuid.uuid4()),
        transaction_id=req.transaction_id,
        alert_id=req.alert_id,
        title=req.title,
        description=req.description,
        priority=req.priority,
        status="open",
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return {
        "id": investigation.id,
        "transaction_id": investigation.transaction_id,
        "title": investigation.title,
        "status": investigation.status,
        "priority": investigation.priority,
        "created_at": investigation.created_at.isoformat(),
    }


@router.get("")
def list_investigations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get paginated investigations."""
    query = db.query(Investigation)
    if status and status != "all":
        query = query.filter(Investigation.status == status)

    total = query.count()
    investigations = query.order_by(desc(Investigation.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for inv in investigations:
        result.append({
            "id": inv.id,
            "transaction_id": inv.transaction_id,
            "alert_id": inv.alert_id,
            "assigned_to": inv.assigned_to,
            "title": inv.title,
            "description": inv.description,
            "status": inv.status,
            "priority": inv.priority,
            "findings": inv.findings,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
            "resolved_at": inv.resolved_at.isoformat() if inv.resolved_at else None,
            "notes": [
                {
                    "id": n.id,
                    "content": n.content,
                    "author_id": n.author_id,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                }
                for n in inv.notes
            ],
        })

    return {"investigations": result, "total": total, "page": page, "page_size": page_size}


@router.get("/{investigation_id}")
def get_investigation(investigation_id: str, db: Session = Depends(get_db)):
    """Get investigation detail."""
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    return {
        "id": inv.id,
        "transaction_id": inv.transaction_id,
        "alert_id": inv.alert_id,
        "assigned_to": inv.assigned_to,
        "title": inv.title,
        "description": inv.description,
        "status": inv.status,
        "priority": inv.priority,
        "findings": inv.findings,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        "resolved_at": inv.resolved_at.isoformat() if inv.resolved_at else None,
        "notes": [
            {
                "id": n.id,
                "content": n.content,
                "author_id": n.author_id,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in inv.notes
        ],
    }


@router.patch("/{investigation_id}")
def update_investigation(investigation_id: str, req: InvestigationUpdate, db: Session = Depends(get_db)):
    """Update investigation status/details."""
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if req.status:
        inv.status = req.status
        if req.status in ("resolved", "false_positive"):
            inv.resolved_at = datetime.utcnow()
    if req.priority:
        inv.priority = req.priority
    if req.findings:
        inv.findings = req.findings
    if req.assigned_to:
        inv.assigned_to = req.assigned_to

    inv.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Investigation updated", "id": investigation_id, "status": inv.status}


@router.post("/{investigation_id}/notes")
def add_note(investigation_id: str, req: InvestigationNoteCreate, db: Session = Depends(get_db)):
    """Add a note to an investigation."""
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    note = InvestigationNote(
        id=str(uuid.uuid4()),
        investigation_id=investigation_id,
        content=req.content,
    )
    db.add(note)
    db.commit()

    return {
        "id": note.id,
        "content": note.content,
        "created_at": note.created_at.isoformat() if note.created_at else None,
    }
