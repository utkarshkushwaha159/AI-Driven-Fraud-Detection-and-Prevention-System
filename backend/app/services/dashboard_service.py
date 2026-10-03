"""
Dashboard and reporting service.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.transaction import Transaction
from app.models.fraud_alert import FraudAlert
from app.models.investigation import Investigation
from app.models.model_prediction import ModelPrediction
from app.dsa.trees import AVLTree, BST


class DashboardService:
    """Provides dashboard statistics and report data."""

    @staticmethod
    def get_dashboard_stats(db: Session) -> dict:
        """Get comprehensive dashboard statistics."""
        total = db.query(Transaction).count()
        approved = db.query(Transaction).filter(Transaction.status == "approved").count()
        suspicious = db.query(Transaction).filter(Transaction.status == "suspicious").count()
        held = db.query(Transaction).filter(Transaction.status == "held").count()
        blocked = db.query(Transaction).filter(Transaction.status == "blocked").count()
        verified = db.query(Transaction).filter(Transaction.status == "verified").count()

        total_alerts = db.query(FraudAlert).count()
        open_investigations = db.query(Investigation).filter(
            Investigation.status.in_(["open", "under_review", "escalated"])
        ).count()

        # Calculate fraud rate
        fraud_predictions = db.query(ModelPrediction).filter(
            ModelPrediction.risk_level.in_(["suspicious", "high_risk"])
        ).count()
        fraud_rate = fraud_predictions / max(total, 1)

        # Average fraud probability
        avg_prob_result = db.query(func.avg(ModelPrediction.fraud_probability)).scalar()
        avg_fraud_prob = float(avg_prob_result) if avg_prob_result else 0.0

        # Total amount
        total_amount_result = db.query(func.sum(Transaction.amount)).scalar()
        total_amount = float(total_amount_result) if total_amount_result else 0.0

        stats = {
            "total_transactions": total,
            "approved_transactions": approved + verified,
            "suspicious_transactions": suspicious,
            "held_transactions": held,
            "blocked_transactions": blocked,
            "total_alerts": total_alerts,
            "open_investigations": open_investigations,
            "fraud_rate": round(fraud_rate, 4),
            "avg_fraud_probability": round(avg_fraud_prob, 4),
            "total_amount": round(total_amount, 2),
        }

        # Trends (last 7 days)
        trends = DashboardService._get_trends(db, days=7)

        # Risk distribution
        risk_dist = DashboardService._get_risk_distribution(db)

        # Recent alerts
        recent_alerts = DashboardService._get_recent_alerts(db, limit=5)

        # High risk transactions
        high_risk = DashboardService._get_high_risk_transactions(db, limit=5)

        return {
            "stats": stats,
            "trends": trends,
            "risk_distribution": risk_dist,
            "recent_alerts": recent_alerts,
            "high_risk_transactions": high_risk,
        }

    @staticmethod
    def _get_trends(db: Session, days=7):
        """Get daily transaction trends."""
        trends = []
        today = datetime.utcnow().date()

        for i in range(days, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())

            total = db.query(Transaction).filter(
                Transaction.created_at >= day_start,
                Transaction.created_at <= day_end
            ).count()

            fraud = db.query(Transaction).filter(
                Transaction.created_at >= day_start,
                Transaction.created_at <= day_end,
                Transaction.status.in_(["held", "blocked"])
            ).count()

            suspicious = db.query(Transaction).filter(
                Transaction.created_at >= day_start,
                Transaction.created_at <= day_end,
                Transaction.status == "suspicious"
            ).count()

            trends.append({
                "date": day.isoformat(),
                "total": total,
                "fraud": fraud,
                "suspicious": suspicious,
            })

        return trends

    @staticmethod
    def _get_risk_distribution(db: Session):
        """Get distribution of risk levels."""
        dist = {}
        for level in ["safe", "suspicious", "high_risk"]:
            count = db.query(ModelPrediction).filter(
                ModelPrediction.risk_level == level
            ).count()
            dist[level] = count
        return dist

    @staticmethod
    def _get_recent_alerts(db: Session, limit=5):
        """Get most recent alerts."""
        alerts = db.query(FraudAlert).order_by(
            desc(FraudAlert.created_at)
        ).limit(limit).all()

        result = []
        for alert in alerts:
            tx = db.query(Transaction).filter(Transaction.id == alert.transaction_id).first()
            result.append({
                "id": alert.id,
                "transaction_id": alert.transaction_id,
                "fraud_probability": alert.fraud_probability,
                "severity": alert.severity,
                "status": alert.status,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
                "amount": tx.amount if tx else 0,
                "account_id": tx.account_id if tx else None,
            })
        return result

    @staticmethod
    def _get_high_risk_transactions(db: Session, limit=5):
        """Get highest risk transactions."""
        predictions = db.query(ModelPrediction).order_by(
            desc(ModelPrediction.fraud_probability)
        ).limit(limit).all()

        result = []
        for pred in predictions:
            tx = db.query(Transaction).filter(Transaction.id == pred.transaction_id).first()
            if tx:
                result.append({
                    "id": tx.id,
                    "amount": tx.amount,
                    "status": tx.status,
                    "fraud_probability": pred.fraud_probability,
                    "risk_level": pred.risk_level,
                    "created_at": tx.created_at.isoformat() if tx.created_at else None,
                    "account_id": tx.account_id,
                })
        return result

    @staticmethod
    def get_report_summary(db: Session) -> dict:
        """Generate comprehensive report data."""
        total = db.query(Transaction).count()
        total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0

        approved = db.query(Transaction).filter(
            Transaction.status.in_(["approved", "verified"])
        ).count()
        approval_rate = approved / max(total, 1)

        fraud_count = db.query(Transaction).filter(
            Transaction.status.in_(["held", "blocked"])
        ).count()
        suspicious_count = db.query(Transaction).filter(
            Transaction.status == "suspicious"
        ).count()

        # Transaction volume by date
        volume = DashboardService._get_trends(db, days=30)

        # Risk distribution
        risk_dist = DashboardService._get_risk_distribution(db)

        # Merchant analysis - use BST for sorted retrieval
        merchant_tree = BST()
        merchant_stats = db.query(
            Transaction.merchant_id,
            func.count(Transaction.id).label("count"),
            func.sum(Transaction.amount).label("total"),
            func.avg(Transaction.amount).label("avg"),
        ).group_by(Transaction.merchant_id).all()

        merchant_analysis = []
        for m_id, count, total_m, avg_m in merchant_stats:
            if m_id:
                data = {
                    "merchant_id": m_id,
                    "transaction_count": count,
                    "total_amount": round(float(total_m or 0), 2),
                    "avg_amount": round(float(avg_m or 0), 2),
                }
                merchant_tree.insert(count, data)
                merchant_analysis.append(data)

        # Sort merchant analysis by transaction count desc
        merchant_analysis.sort(key=lambda x: x["transaction_count"], reverse=True)

        # Device stats
        unique_devices = db.query(func.count(func.distinct(Transaction.device_id))).scalar() or 0
        # IP stats
        unique_ips = db.query(func.count(func.distinct(Transaction.ip_id))).scalar() or 0
        # Account stats
        unique_accounts = db.query(func.count(func.distinct(Transaction.account_id))).scalar() or 0

        avg_prob = db.query(func.avg(ModelPrediction.fraud_probability)).scalar() or 0

        return {
            "total_transactions": total,
            "total_amount": round(float(total_amount), 2),
            "approval_rate": round(approval_rate, 4),
            "fraud_count": fraud_count,
            "suspicious_count": suspicious_count,
            "held_count": fraud_count,
            "blocked_count": db.query(Transaction).filter(Transaction.status == "blocked").count(),
            "avg_fraud_probability": round(float(avg_prob), 4),
            "transaction_volume": volume,
            "risk_distribution": risk_dist,
            "merchant_analysis": merchant_analysis[:20],
            "daily_trends": volume,
            "device_stats": {"unique_devices": unique_devices},
            "ip_stats": {"unique_ips": unique_ips},
            "account_stats": {"unique_accounts": unique_accounts},
        }
