"""
Investigation and case management service.
Handles investigation lifecycles, analyst notes, and status transitions.
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.investigation import Investigation, InvestigationNote, InvestigationStatus


class InvestigationService:
    """Business logic for fraud case investigations."""

    @staticmethod
    def create_investigation(db: Session, data: dict) -> Investigation:
        """Create a new fraud investigation case."""
        investigation = Investigation(
            id=str(uuid.uuid4()),
            transaction_id=data.get("transaction_id"),
            alert_id=data.get("alert_id"),
            title=data.get("title", "Fraud Investigation"),
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
            status=InvestigationStatus.OPEN.value,
            assigned_to=data.get("assigned_to"),
        )
        db.add(investigation)
        db.commit()
        db.refresh(investigation)
        return investigation

    @staticmethod
    def get_investigations(db: Session, page: int = 1, page_size: int = 20, status: str = None) -> dict:
        """Retrieve paginated investigations."""
        query = db.query(Investigation)
        if status and status != "all":
            query = query.filter(Investigation.status == status)

        total = query.count()
        items = (
            query.order_by(desc(Investigation.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
        }

    @staticmethod
    def get_investigation_detail(db: Session, investigation_id: str):
        """Retrieve single investigation with its notes and associations."""
        return db.query(Investigation).filter(Investigation.id == investigation_id).first()

    @staticmethod
    def update_investigation(db: Session, investigation_id: str, updates: dict) -> Investigation:
        """Update status, assignment, or notes of an investigation."""
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            return None

        if "status" in updates and updates["status"]:
            inv.status = updates["status"]
            if updates["status"] in ("resolved", "false_positive"):
                inv.resolved_at = datetime.utcnow()
        if "priority" in updates and updates["priority"]:
            inv.priority = updates["priority"]
        if "assigned_to" in updates:
            inv.assigned_to = updates["assigned_to"]
        if "resolution_notes" in updates:
            inv.resolution_notes = updates["resolution_notes"]

        inv.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(inv)
        return inv

    @staticmethod
    def add_note(db: Session, investigation_id: str, content: str, user_id: str = None) -> InvestigationNote:
        """Add an analyst note to an investigation."""
        note = InvestigationNote(
            id=str(uuid.uuid4()),
            investigation_id=investigation_id,
            author_id=user_id,
            content=content,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note
