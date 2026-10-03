"""
Transaction and payment processing service.
Handles payment flow, fraud screening, and transaction management.
"""
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.models.transaction import Transaction, TransactionStatus
from app.models.account import Account
from app.models.device import Device
from app.models.ip_address import IpAddress
from app.models.merchant import Merchant
from app.models.model_prediction import ModelPrediction
from app.models.fraud_alert import FraudAlert, AlertSeverity, AlertStatus
from app.ml.predict import get_predictor
from app.services.network_service import NetworkService


class TransactionService:
    """Business logic for transaction processing and fraud screening."""

    @staticmethod
    def process_payment(db: Session, payment_data: dict) -> dict:
        """
        Process a payment through the fraud screening pipeline.
        1. Resolve or create device/IP/merchant entities
        2. Compute behavioural features from history
        3. Run ML prediction
        4. Create transaction with appropriate status
        5. Create alerts if needed
        """
        # Resolve entities
        device = TransactionService._resolve_device(db, payment_data)
        ip_addr = TransactionService._resolve_ip(db, payment_data)
        merchant = TransactionService._resolve_merchant(db, payment_data.get("merchant_code", "unknown"))

        # Compute behavioural features from account history
        account_id = payment_data["account_id"]
        features = TransactionService._compute_behavioural_features(
            db, account_id, payment_data["amount"],
            device.id if device else None,
            ip_addr.id if ip_addr else None,
            merchant.id if merchant else None,
        )

        # Build transaction data for ML prediction
        tx_data = {
            "amount": payment_data["amount"],
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "device_id": device.device_fingerprint if device else "unknown",
            "ip_address": ip_addr.ip if ip_addr else "0.0.0.0",
            "merchant_id": merchant.merchant_code if merchant else "unknown",
            **features,
        }

        # Run ML prediction
        predictor = get_predictor()
        try:
            prediction = predictor.predict(tx_data)
        except Exception as e:
            # If model not loaded, create transaction in pending state
            prediction = {
                "fraud_probability": 0.0,
                "anomaly_score": 0.0,
                "risk_level": "safe",
                "explanation": {"factors": [], "method": "fallback"},
                "features_used": {},
                "model_version": "unavailable",
            }

        # Determine transaction status based on risk level
        risk_level = prediction["risk_level"]
        if risk_level == "high_risk":
            status = TransactionStatus.HELD.value
        elif risk_level == "suspicious":
            status = TransactionStatus.SUSPICIOUS.value
        else:
            status = TransactionStatus.APPROVED.value

        # Create transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            device_id=device.id if device else None,
            ip_id=ip_addr.id if ip_addr else None,
            merchant_id=merchant.id if merchant else None,
            amount=payment_data["amount"],
            description=payment_data.get("description", ""),
            status=status,
            failed_attempts=features.get("failed_attempts", 0),
            is_new_device=features.get("is_new_device", 0),
            is_new_ip=features.get("is_new_ip", 0),
            transaction_frequency=features.get("transaction_frequency", 0),
            account_average_amount=features.get("account_average_amount", 0),
            time_since_last_transaction=features.get("time_since_last_transaction", 0),
            merchant_frequency=features.get("merchant_frequency", 0),
            device_usage_count=features.get("device_usage_count", 1),
            ip_usage_count=features.get("ip_usage_count", 1),
        )
        db.add(transaction)

        # Store prediction
        import json
        model_pred = ModelPrediction(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            fraud_probability=prediction["fraud_probability"],
            anomaly_score=prediction["anomaly_score"],
            risk_level=risk_level,
            model_version=prediction.get("model_version", "1.0"),
            feature_vector=json.dumps(prediction.get("features_used", {})),
            explanation=json.dumps(prediction.get("explanation", {})),
            network_risk_score=0.0,
        )
        db.add(model_pred)

        # Create alert for suspicious/high-risk transactions
        if risk_level in ("suspicious", "high_risk"):
            severity = AlertSeverity.CRITICAL.value if risk_level == "high_risk" else AlertSeverity.MEDIUM.value
            alert = FraudAlert(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                fraud_probability=prediction["fraud_probability"],
                anomaly_score=prediction["anomaly_score"],
                severity=severity,
                status=AlertStatus.NEW.value,
                description=f"Transaction flagged as {risk_level.replace('_', ' ')}. Amount: ₹{payment_data['amount']:.2f}",
            )
            db.add(alert)

        db.commit()

        # Build response message
        messages = {
            "safe": "Payment approved. No unusual activity was detected.",
            "suspicious": "This payment requires additional verification for security purposes.",
            "high_risk": "This transaction has been temporarily held for security review.",
        }

        return {
            "transaction_id": transaction.id,
            "status": status,
            "fraud_probability": prediction["fraud_probability"],
            "risk_level": risk_level,
            "message": messages.get(risk_level, "Payment processed."),
            "amount": payment_data["amount"],
            "requires_verification": risk_level == "suspicious",
        }

    @staticmethod
    def get_transactions(db: Session, page=1, page_size=20, search=None,
                         status_filter=None, sort_by="created_at",
                         sort_dir="desc", account_id=None):
        """Get paginated transactions with filtering."""
        query = db.query(Transaction)

        if account_id:
            query = query.filter(Transaction.account_id == account_id)

        if status_filter and status_filter != "all":
            query = query.filter(Transaction.status == status_filter)

        if search:
            query = query.filter(
                or_(
                    Transaction.id.contains(search),
                    Transaction.account_id.contains(search),
                    Transaction.description.contains(search),
                )
            )

        total = query.count()

        if sort_dir == "desc":
            query = query.order_by(desc(getattr(Transaction, sort_by, Transaction.created_at)))
        else:
            query = query.order_by(getattr(Transaction, sort_by, Transaction.created_at))

        transactions = query.offset((page - 1) * page_size).limit(page_size).all()

        result = []
        for tx in transactions:
            tx_dict = {
                "id": tx.id,
                "account_id": tx.account_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "description": tx.description,
                "status": tx.status,
                "device_id": tx.device_id,
                "ip_id": tx.ip_id,
                "merchant_id": tx.merchant_id,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "fraud_probability": None,
                "anomaly_score": None,
                "risk_level": None,
            }
            if tx.prediction:
                tx_dict["fraud_probability"] = tx.prediction.fraud_probability
                tx_dict["anomaly_score"] = tx.prediction.anomaly_score
                tx_dict["risk_level"] = tx.prediction.risk_level
            result.append(tx_dict)

        return {"transactions": result, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def get_transaction_detail(db: Session, transaction_id: str) -> dict:
        """Get detailed transaction info with prediction and explanation."""
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return None

        detail = {
            "id": tx.id,
            "account_id": tx.account_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "description": tx.description,
            "status": tx.status,
            "device_id": tx.device_id,
            "ip_id": tx.ip_id,
            "merchant_id": tx.merchant_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "failed_attempts": tx.failed_attempts,
            "is_new_device": tx.is_new_device,
            "is_new_ip": tx.is_new_ip,
            "transaction_frequency": tx.transaction_frequency,
            "account_average_amount": tx.account_average_amount,
            "time_since_last_transaction": tx.time_since_last_transaction,
            "merchant_frequency": tx.merchant_frequency,
            "device_usage_count": tx.device_usage_count,
            "ip_usage_count": tx.ip_usage_count,
            "fraud_probability": None,
            "anomaly_score": None,
            "risk_level": None,
            "explanation": None,
            "network_risk_score": None,
            "device_fingerprint": None,
            "ip": None,
            "merchant_name": None,
            "merchant_code": None,
        }

        if tx.prediction:
            import json
            detail["fraud_probability"] = tx.prediction.fraud_probability
            detail["anomaly_score"] = tx.prediction.anomaly_score
            detail["risk_level"] = tx.prediction.risk_level
            detail["network_risk_score"] = tx.prediction.network_risk_score
            try:
                detail["explanation"] = json.loads(tx.prediction.explanation) if tx.prediction.explanation else None
            except (json.JSONDecodeError, TypeError):
                detail["explanation"] = None

        if tx.device:
            detail["device_fingerprint"] = tx.device.device_fingerprint
        if tx.ip_address:
            detail["ip"] = tx.ip_address.ip
        if tx.merchant:
            detail["merchant_name"] = tx.merchant.name
            detail["merchant_code"] = tx.merchant.merchant_code

        return detail

    @staticmethod
    def _resolve_device(db: Session, payment_data: dict):
        """Find or create device record."""
        fingerprint = payment_data.get("device_fingerprint", "unknown")
        device = db.query(Device).filter(Device.device_fingerprint == fingerprint).first()
        if not device:
            device = Device(
                id=str(uuid.uuid4()),
                device_fingerprint=fingerprint,
                device_type=payment_data.get("device_type", "desktop"),
                os=payment_data.get("os_name", "unknown"),
                browser=payment_data.get("browser", "unknown"),
            )
            db.add(device)
            db.flush()
        else:
            device.last_seen = datetime.utcnow()
        return device

    @staticmethod
    def _resolve_ip(db: Session, payment_data: dict):
        """Find or create IP address record."""
        ip = payment_data.get("ip_address", "0.0.0.0")
        ip_addr = db.query(IpAddress).filter(IpAddress.ip == ip).first()
        if not ip_addr:
            ip_addr = IpAddress(
                id=str(uuid.uuid4()),
                ip=ip,
            )
            db.add(ip_addr)
            db.flush()
        else:
            ip_addr.last_seen = datetime.utcnow()
        return ip_addr

    @staticmethod
    def _resolve_merchant(db: Session, merchant_code: str):
        """Find or create merchant record."""
        merchant = db.query(Merchant).filter(Merchant.merchant_code == merchant_code).first()
        if not merchant:
            merchant = Merchant(
                id=str(uuid.uuid4()),
                merchant_code=merchant_code,
                name=f"Merchant {merchant_code}",
                category="general",
            )
            db.add(merchant)
            db.flush()
        return merchant

    @staticmethod
    def _compute_behavioural_features(db: Session, account_id: str, amount: float,
                                       device_id=None, ip_id=None, merchant_id=None):
        """Compute behavioural features from account history."""
        from sqlalchemy import func

        # Get account transaction history
        history = db.query(Transaction).filter(
            Transaction.account_id == account_id
        ).order_by(desc(Transaction.created_at)).limit(100).all()

        # Transaction frequency (transactions in last 24 hours)
        tx_freq = 0
        avg_amount = amount
        time_since_last = 24.0
        failed = 0

        if history:
            now = datetime.utcnow()
            recent = [tx for tx in history if (now - tx.created_at).total_seconds() < 86400]
            tx_freq = len(recent)

            amounts = [tx.amount for tx in history]
            avg_amount = sum(amounts) / len(amounts) if amounts else amount

            last_tx = history[0]
            time_since_last = (now - last_tx.created_at).total_seconds() / 3600.0

            failed = sum(1 for tx in recent if tx.status in ("held", "blocked"))

        # Check if device/IP are new for this account
        is_new_device = 0
        is_new_ip = 0
        device_count = 1
        ip_count = 1
        merchant_freq = 0

        if device_id:
            existing_device_tx = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.device_id == device_id
            ).count()
            is_new_device = 1 if existing_device_tx == 0 else 0
            device_count = db.query(Transaction).filter(Transaction.device_id == device_id).count() + 1

        if ip_id:
            existing_ip_tx = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.ip_id == ip_id
            ).count()
            is_new_ip = 1 if existing_ip_tx == 0 else 0
            ip_count = db.query(Transaction).filter(Transaction.ip_id == ip_id).count() + 1

        if merchant_id:
            merchant_freq = db.query(Transaction).filter(
                Transaction.account_id == account_id,
                Transaction.merchant_id == merchant_id
            ).count()

        return {
            "failed_attempts": failed,
            "is_new_device": is_new_device,
            "is_new_ip": is_new_ip,
            "transaction_frequency": tx_freq,
            "account_average_amount": avg_amount,
            "time_since_last_transaction": time_since_last,
            "merchant_frequency": merchant_freq,
            "device_usage_count": device_count,
            "ip_usage_count": ip_count,
        }
