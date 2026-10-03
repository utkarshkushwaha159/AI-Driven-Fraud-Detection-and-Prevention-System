import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditService:
    """Service to record system, user, and administrative actions for audit compliance."""

    @staticmethod
    def log(
        db: Session,
        actor: str,
        role: str,
        action: str,
        target_type: str = "transaction",
        target_id: str = None,
        previous_status: str = None,
        new_status: str = None,
        details: str = None,
    ):
        """Record an immutable audit trail event."""
        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            actor=actor or "system",
            role=role or "system",
            action=action,
            target_type=target_type,
            target_id=target_id,
            previous_status=previous_status,
            new_status=new_status,
            details=details,
            created_at=datetime.utcnow(),
        )
        db.add(log_entry)
        db.flush()
        return log_entry
