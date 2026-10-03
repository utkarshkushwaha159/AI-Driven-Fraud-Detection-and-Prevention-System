"""
Transaction and payment processing service.
Handles payment flow, fraud screening, server-side verification, admin decisions, and state validation.
"""
import uuid
import json
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.models.transaction import Transaction, TransactionStatus
from app.models.account import Account
from app.models.device import Device
from app.models.ip_address import IpAddress
from app.models.merchant import Merchant
from app.models.model_prediction import ModelPrediction
from app.models.fraud_alert import FraudAlert, AlertSeverity, AlertStatus
from app.models.investigation import Investigation, InvestigationStatus
from app.ml.predict import get_predictor
from app.services.audit_service import AuditService
from app.services.investigation_service import InvestigationService


class TransactionService:
    """Business logic for transaction processing, fraud screening, and lifecycle management."""

    @staticmethod
    def process_payment(db: Session, payment_data: dict, actor: str = "customer") -> dict:
        """
        Process a payment through the fraud screening pipeline.
        SAFE: PENDING -> ANALYZING -> APPROVED
        SUSPICIOUS: PENDING -> ANALYZING -> HELD (Verification required)
        HIGH RISK: PENDING -> ANALYZING -> HELD -> Alert -> Investigation
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
        print("DEBUG tx_data:", tx_data)

        # Run ML prediction
        predictor = get_predictor()
        try:
            prediction = predictor.predict(tx_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            prediction = {
                "fraud_probability": 0.05,
                "anomaly_score": -0.5,
                "risk_level": "safe",
                "explanation": {"factors": [], "method": "fallback"},
                "features_used": {},
                "model_version": "unavailable",
            }

        risk_level = prediction["risk_level"]
        fraud_prob = float(prediction["fraud_probability"])
        anomaly_score = float(prediction["anomaly_score"])
        print(f"DEBUG: risk_level={risk_level}, fraud_prob={fraud_prob}, anomaly={anomaly_score}")

        # Determine transaction status and security workflow
        now = datetime.utcnow()
        verification_code = None
        code_expires = None
        requires_admin = 0

        if risk_level == "high_risk":
            status = TransactionStatus.HELD.value
            requires_admin = 1
            customer_msg = "Your payment is temporarily held for security review."
        elif risk_level == "suspicious":
            status = TransactionStatus.HELD.value
            verification_code = "123456"  # Deterministic test code (or standard OTP for demo)
            code_expires = now + timedelta(minutes=5)
            customer_msg = "This payment requires additional verification for security purposes."
        else:
            status = TransactionStatus.APPROVED.value
            customer_msg = "Payment approved. No unusual activity was detected."

        # Create transaction record
        transaction = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            device_id=device.id if device else None,
            ip_id=ip_addr.id if ip_addr else None,
            merchant_id=merchant.id if merchant else None,
            amount=payment_data["amount"],
            currency="INR",
            description=payment_data.get("description", ""),
            status=status,
            risk_level=risk_level,
            customer_status_message=customer_msg,
            verification_code=verification_code,
            verification_attempts=0,
            verification_code_expires_at=code_expires,
            requires_admin_review=requires_admin,
            failed_attempts=features.get("failed_attempts", 0),
            is_new_device=features.get("is_new_device", 0),
            is_new_ip=features.get("is_new_ip", 0),
            transaction_frequency=features.get("transaction_frequency", 0),
            account_average_amount=features.get("account_average_amount", 0),
            time_since_last_transaction=features.get("time_since_last_transaction", 0),
            merchant_frequency=features.get("merchant_frequency", 0),
            device_usage_count=features.get("device_usage_count", 1),
            ip_usage_count=features.get("ip_usage_count", 1),
            created_at=now,
        )
        db.add(transaction)

        # Store model prediction
        model_pred = ModelPrediction(
            id=str(uuid.uuid4()),
            transaction_id=transaction.id,
            fraud_probability=fraud_prob,
            anomaly_score=anomaly_score,
            risk_level=risk_level,
            model_version=prediction.get("model_version", "1.0"),
            feature_vector=json.dumps(prediction.get("features_used", {})),
            explanation=json.dumps(prediction.get("explanation", {})),
            network_risk_score=0.0,
            prediction_timestamp=now,
        )
        db.add(model_pred)

        # Log audit trail for payment creation and ML analysis
        AuditService.log(
            db,
            actor=actor,
            role="customer",
            action="payment_initiated",
            target_id=transaction.id,
            previous_status=None,
            new_status=status,
            details=f"Payment ₹{transaction.amount:.2f} processed. ML risk: {risk_level} (prob: {fraud_prob:.3f})",
        )

        # For HIGH-RISK transactions: Automatically create Alert and Investigation
        if risk_level == "high_risk":
            alert = FraudAlert(
                id=str(uuid.uuid4()),
                transaction_id=transaction.id,
                fraud_probability=fraud_prob,
                anomaly_score=anomaly_score,
                severity=AlertSeverity.CRITICAL.value,
                status=AlertStatus.NEW.value,
                description=f"Critical high-risk anomaly detected. Amount: ₹{transaction.amount:.2f}, Risk probability: {(fraud_prob * 100):.1f}%",
                created_at=now,
            )
            db.add(alert)
            db.flush()

            # Create investigation case automatically
            InvestigationService.create_investigation(
                db,
                {
                    "transaction_id": transaction.id,
                    "alert_id": alert.id,
                    "title": f"High-Risk Fraud Case - ₹{transaction.amount:,.2f}",
                    "description": f"Automated fraud investigation for high-risk transfer to merchant {merchant.name if merchant else 'unknown'}. Fraud probability: {(fraud_prob*100):.1f}%. Awaiting analyst review.",
                    "priority": "critical",
                    "status": InvestigationStatus.OPEN.value,
                    "assigned_to": None,
                },
            )

            AuditService.log(
                db,
                actor="system",
                role="system",
                action="investigation_created",
                target_id=transaction.id,
                new_status="open",
                details="Investigation automatically opened for high-risk payment.",
            )

        db.commit()

        messages = {
            "safe": "Payment approved. No unusual activity was detected.",
            "suspicious": "This payment requires additional verification for security purposes.",
            "high_risk": "Your payment is temporarily held for security review.",
        }

        return {
            "transaction_id": transaction.id,
            "status": status,
            "fraud_probability": fraud_prob,
            "risk_level": risk_level,
            "message": messages.get(risk_level, "Payment processed."),
            "amount": payment_data["amount"],
            "requires_verification": risk_level == "suspicious",
            "customer_status_message": transaction.customer_status_message,
            "verification_attempts": 0,
            "attempts_remaining": 2 if risk_level == "suspicious" else 0,
        }

    @staticmethod
    def verify_payment(db: Session, transaction_id: str, verification_code: str, actor: str = "customer") -> dict:
        """
        Verify a suspicious payment using verification code.
        - Maximum 2 verification attempts server-side.
        - Correct on attempt 1 or 2 -> VERIFIED -> automatically APPROVED.
        - Wrong attempt 1 -> allow exactly one final attempt.
        - Wrong attempt 2 -> BLOCKED/REJECTED -> create Alert & Investigation.
        - Attempt 3+ -> strictly rejected with HTTP 400.
        """
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        # Enforce server-side attempt limits (Strict Max 2 attempts)
        if tx.verification_attempts >= 2:
            raise HTTPException(
                status_code=400,
                detail="Maximum verification attempts exceeded. Transaction is permanently blocked."
            )

        # State validation: reject if transaction is already in terminal state
        if tx.status in (TransactionStatus.BLOCKED.value, TransactionStatus.REJECTED.value):
            raise HTTPException(status_code=400, detail="Transaction is blocked/rejected and cannot be verified.")

        if tx.status == TransactionStatus.APPROVED.value:
            raise HTTPException(status_code=400, detail="Transaction is already approved.")

        # High-risk transactions cannot be released via customer OTP
        if tx.risk_level == "high_risk":
            raise HTTPException(
                status_code=400,
                detail="High-risk payments cannot be released via customer verification. They are held for administrator security review."
            )

        # Check code expiration (5 minutes)
        if tx.verification_code_expires_at and datetime.utcnow() > tx.verification_code_expires_at:
            raise HTTPException(
                status_code=400,
                detail="Verification code has expired. Please initiate a new payment."
            )

        # Record attempt
        tx.verification_attempts += 1
        attempt_num = tx.verification_attempts

        # Check verification code
        is_correct = (
            verification_code == tx.verification_code or
            verification_code == "123456"  # Standard test code support
        )

        if is_correct:
            # SUCCESS on attempt 1 or 2 -> automatically APPROVED
            tx.status = TransactionStatus.APPROVED.value
            tx.customer_status_message = "Payment verified and approved successfully."
            tx.updated_at = datetime.utcnow()

            AuditService.log(
                db,
                actor=actor,
                role="customer",
                action="verification_success",
                target_id=tx.id,
                previous_status="held",
                new_status="approved",
                details=f"Verification successful on attempt {attempt_num} of 2.",
            )
            db.commit()

            return {
                "transaction_id": tx.id,
                "status": "approved",
                "message": "Payment verified and approved successfully.",
                "attempts_remaining": 0,
                "verified": True,
                "customer_status_message": tx.customer_status_message,
            }

        else:
            # FAILURE
            if attempt_num == 1:
                # Wrong attempt 1 -> allow exactly one final attempt
                tx.customer_status_message = "Incorrect code. 1 attempt remaining."
                tx.updated_at = datetime.utcnow()

                AuditService.log(
                    db,
                    actor=actor,
                    role="customer",
                    action="verification_attempt_failed",
                    target_id=tx.id,
                    previous_status="held",
                    new_status="held",
                    details="Incorrect verification code on attempt 1 of 2.",
                )
                db.commit()

                return {
                    "transaction_id": tx.id,
                    "status": "held",
                    "message": "Incorrect verification code. You have 1 final attempt remaining.",
                    "attempts_remaining": 1,
                    "verified": False,
                    "customer_status_message": tx.customer_status_message,
                }
            else:
                # Wrong attempt 2 -> permanently BLOCKED / REJECTED -> Alert & Investigation
                tx.status = TransactionStatus.BLOCKED.value
                tx.customer_status_message = "Verification failed. Your payment has been blocked and sent for security review."
                tx.updated_at = datetime.utcnow()

                # Create Fraud Alert
                alert = FraudAlert(
                    id=str(uuid.uuid4()),
                    transaction_id=tx.id,
                    fraud_probability=0.85,
                    anomaly_score=0.75,
                    severity=AlertSeverity.CRITICAL.value,
                    status=AlertStatus.NEW.value,
                    description=f"Verification failed 2 consecutive attempts. Potential account takeover. Amount: ₹{tx.amount:,.2f}",
                    created_at=datetime.utcnow(),
                )
                db.add(alert)
                db.flush()

                # Automatically create / link investigation case
                InvestigationService.create_investigation(
                    db,
                    {
                        "transaction_id": tx.id,
                        "alert_id": alert.id,
                        "title": f"Failed Verification Challenge - ₹{tx.amount:,.2f}",
                        "description": "Customer failed two consecutive multi-factor verification attempts. Transaction blocked and flagged for analyst review.",
                        "priority": "critical",
                        "status": InvestigationStatus.OPEN.value,
                    },
                )

                AuditService.log(
                    db,
                    actor=actor,
                    role="customer",
                    action="verification_blocked",
                    target_id=tx.id,
                    previous_status="held",
                    new_status="blocked",
                    details="Verification failed 2 attempts. Payment permanently blocked and sent for security review.",
                )
                db.commit()

                return {
                    "transaction_id": tx.id,
                    "status": "blocked",
                    "message": "Verification failed. Your payment has been blocked and sent for security review.",
                    "attempts_remaining": 0,
                    "verified": False,
                    "customer_status_message": tx.customer_status_message,
                }

    @staticmethod
    def admin_decision(db: Session, transaction_id: str, decision: str, admin_user: dict, reason: str = "") -> dict:
        """
        Execute final administrator decision for high-risk / held transactions.
        Only Admin can approve or reject high-risk transactions.
        APPROVE -> payment status APPROVED
        REJECT -> payment status BLOCKED / REJECTED
        """
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            raise HTTPException(status_code=404, detail="Transaction not found.")

        # Validate decision value
        clean_decision = decision.lower().strip()
        if clean_decision not in ("approve", "reject"):
            raise HTTPException(status_code=400, detail="Decision must be either 'approve' or 'reject'.")

        prev_status = tx.status
        now = datetime.utcnow()
        admin_username = admin_user.get("username", "admin")

        if clean_decision == "approve":
            tx.status = TransactionStatus.APPROVED.value
            tx.admin_decision = "approved"
            tx.admin_decision_by = admin_username
            tx.admin_decision_at = now
            tx.customer_status_message = "Payment approved after administrator security review."
            new_status = "approved"
            action = "admin_approve"
        else:
            tx.status = TransactionStatus.BLOCKED.value
            tx.admin_decision = "rejected"
            tx.admin_decision_by = admin_username
            tx.admin_decision_at = now
            tx.customer_status_message = "Payment blocked and rejected after security review."
            new_status = "blocked"
            action = "admin_reject"

        tx.updated_at = now

        # Update linked investigation if exists
        inv = db.query(Investigation).filter(Investigation.transaction_id == tx.id).first()
        if inv:
            inv.status = InvestigationStatus.RESOLVED.value
            inv.final_decision = f"{clean_decision.capitalize()}d by Administrator {admin_username}. Reason: {reason or 'Administrative review complete.'}"
            inv.decided_by = admin_username
            inv.decided_at = now
            inv.resolved_at = now
            inv.updated_at = now

        # Record audit log
        AuditService.log(
            db,
            actor=admin_username,
            role="admin",
            action=action,
            target_id=tx.id,
            previous_status=prev_status,
            new_status=new_status,
            details=f"Admin {action}: {reason or 'Final review completed'}",
        )

        db.commit()
        db.refresh(tx)

        return {
            "transaction_id": tx.id,
            "status": tx.status,
            "admin_decision": tx.admin_decision,
            "admin_decision_by": tx.admin_decision_by,
            "customer_status_message": tx.customer_status_message,
            "message": f"Transaction has been {new_status} by administrator.",
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
                "risk_level": tx.risk_level,
                "customer_status_message": tx.customer_status_message,
                "verification_attempts": tx.verification_attempts,
                "requires_admin_review": tx.requires_admin_review,
                "admin_decision": tx.admin_decision,
                "device_id": tx.device_id,
                "ip_id": tx.ip_id,
                "merchant_id": tx.merchant_id,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "fraud_probability": None,
                "anomaly_score": None,
            }
            if tx.prediction:
                tx_dict["fraud_probability"] = tx.prediction.fraud_probability
                tx_dict["anomaly_score"] = tx.prediction.anomaly_score
                tx_dict["risk_level"] = tx.prediction.risk_level
            result.append(tx_dict)

        return {"transactions": result, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    def get_transaction_detail(db: Session, transaction_id: str) -> dict:
        """Get detailed transaction info with prediction, SHAP explanation, and investigation status."""
        tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not tx:
            return None

        inv = db.query(Investigation).filter(Investigation.transaction_id == tx.id).first()

        detail = {
            "id": tx.id,
            "account_id": tx.account_id,
            "amount": tx.amount,
            "currency": tx.currency,
            "description": tx.description,
            "status": tx.status,
            "risk_level": tx.risk_level,
            "customer_status_message": tx.customer_status_message,
            "verification_attempts": tx.verification_attempts,
            "requires_admin_review": tx.requires_admin_review,
            "admin_decision": tx.admin_decision,
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
            "explanation": None,
            "network_risk_score": None,
            "device_fingerprint": None,
            "ip": None,
            "merchant_name": None,
            "merchant_code": None,
            "investigation_id": inv.id if inv else None,
            "investigation_status": inv.status if inv else None,
        }

        if tx.prediction:
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
        history = db.query(Transaction).filter(
            Transaction.account_id == account_id
        ).order_by(desc(Transaction.created_at)).limit(100).all()

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

            failed = sum(1 for tx in recent if tx.status in ("held", "blocked", "rejected"))

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
