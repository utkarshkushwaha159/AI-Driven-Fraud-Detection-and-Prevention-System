"""
Dashboard and reports API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics and trends."""
    return DashboardService.get_dashboard_stats(db)


@router.get("/reports/summary")
def get_report_summary(db: Session = Depends(get_db)):
    """Get comprehensive report data."""
    return DashboardService.get_report_summary(db)
