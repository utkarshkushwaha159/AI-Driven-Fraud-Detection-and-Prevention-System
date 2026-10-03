"""
Database seed script - populates the database with realistic demo data.
"""
import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import engine, SessionLocal, Base, init_db
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus
from app.models.device import Device
from app.models.ip_address import IpAddress
from app.models.merchant import Merchant
from app.models.fraud_alert import FraudAlert, AlertSeverity, AlertStatus
from app.models.investigation import Investigation, InvestigationNote
from app.models.model_prediction import ModelPrediction
from app.services.auth_service import hash_password

import json


def seed_database():
    """Seed the database with demo data."""
    print("Seeding database...")

    # Drop and recreate all tables
    Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    random.seed(42)

    try:
        # ============ USERS ============
        users_data = [
            {"username": "customer1", "email": "customer1@example.com", "full_name": "Alice Johnson", "role": UserRole.CUSTOMER},
            {"username": "customer2", "email": "customer2@example.com", "full_name": "Bob Smith", "role": UserRole.CUSTOMER},
            {"username": "customer3", "email": "customer3@example.com", "full_name": "Carol Williams", "role": UserRole.CUSTOMER},
            {"username": "analyst", "email": "analyst@example.com", "full_name": "David Chen", "role": UserRole.ANALYST},
            {"username": "analyst2", "email": "analyst2@example.com", "full_name": "Eva Martinez", "role": UserRole.ANALYST},
            {"username": "admin", "email": "admin@example.com", "full_name": "Frank Admin", "role": UserRole.ADMIN},
        ]

        users = []
        for u in users_data:
            user = User(
                id=str(uuid.uuid4()),
                username=u["username"],
                email=u["email"],
                full_name=u["full_name"],
                role=u["role"],
                password_hash=hash_password("password123"),
            )
            db.add(user)
            users.append(user)

        db.flush()
        print(f"  Created {len(users)} users")

        # ============ ACCOUNTS ============
        accounts = []
        for i, user in enumerate(users[:3]):
            for j in range(random.randint(1, 2)):
                acct = Account(
                    id=str(uuid.uuid4()),
                    account_number=f"ACC-{str(i*10+j).zfill(5)}",
                    user_id=user.id,
                    balance=random.uniform(1000, 50000),
                    account_type=random.choice(["checking", "savings"]),
                )
                db.add(acct)
                accounts.append(acct)

        db.flush()
        print(f"  Created {len(accounts)} accounts")

        # ============ DEVICES ============
        devices = []
        device_types = ["desktop", "mobile", "tablet"]
        os_names = ["Windows 11", "macOS 14", "Android 14", "iOS 17", "Linux"]
        browsers = ["Chrome 120", "Firefox 121", "Safari 17", "Edge 120"]

        for i in range(20):
            dev = Device(
                id=str(uuid.uuid4()),
                device_fingerprint=f"fp-{uuid.uuid4().hex[:12]}",
                device_type=random.choice(device_types),
                os=random.choice(os_names),
                browser=random.choice(browsers),
            )
            db.add(dev)
            devices.append(dev)

        db.flush()
        print(f"  Created {len(devices)} devices")

        # ============ IP ADDRESSES ============
        ips = []
        for i in range(30):
            ip_obj = IpAddress(
                id=str(uuid.uuid4()),
                ip=f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                country=random.choice(["US", "UK", "DE", "FR", "JP", "BR", "IN", "RU", "CN", "NG"]),
                city=random.choice(["New York", "London", "Berlin", "Tokyo", "Mumbai", "Lagos"]),
                is_vpn="true" if random.random() < 0.15 else "false",
                is_tor="true" if random.random() < 0.05 else "false",
            )
            db.add(ip_obj)
            ips.append(ip_obj)

        db.flush()
        print(f"  Created {len(ips)} IP addresses")

        # ============ MERCHANTS ============
        merchants_data = [
            ("MER-0001", "TechMart Electronics", "electronics"),
            ("MER-0002", "FreshGrocery Co", "grocery"),
            ("MER-0003", "CloudHost Services", "digital_services"),
            ("MER-0004", "GamerZone", "gaming"),
            ("MER-0005", "QuickTransfer", "money_transfer"),
            ("MER-0006", "LuxuryWatch Store", "luxury"),
            ("MER-0007", "PetroFuel Station", "fuel"),
            ("MER-0008", "BookWorld Online", "retail"),
            ("MER-0009", "CryptoExchange", "crypto"),
            ("MER-0010", "TravelBuddy", "travel"),
            ("MER-0011", "PharmaCare", "pharmacy"),
            ("MER-0012", "FoodDelivery Express", "food"),
        ]

        merchants = []
        for code, name, cat in merchants_data:
            m = Merchant(
                id=str(uuid.uuid4()),
                merchant_code=code,
                name=name,
                category=cat,
                average_transaction=random.uniform(20, 500),
            )
            db.add(m)
            merchants.append(m)

        db.flush()
        print(f"  Created {len(merchants)} merchants")

        # ============ TRANSACTIONS ============
        transactions = []
        predictions = []
        alerts_list = []
        investigations_list = []

        # Load predictor for real predictions
        from app.ml.predict import get_predictor
        predictor = get_predictor()
        use_model = predictor.loaded

        now = datetime.utcnow()

        for i in range(150):
            acct = random.choice(accounts)
            dev = random.choice(devices)
            ip_obj = random.choice(ips)
            merchant = random.choice(merchants)

            # Create varied transaction patterns
            if i < 100:  # Normal transactions
                amount = round(random.lognormexp() if hasattr(random, 'lognormexp') else abs(random.gauss(80, 60)), 2)
                amount = max(5, min(amount, 2000))
                hours_ago = random.randint(0, 168)
                status_choices = [TransactionStatus.APPROVED.value] * 9 + [TransactionStatus.SUSPICIOUS.value]
                failed_attempts = 0 if random.random() > 0.1 else random.randint(1, 2)
                is_new_device = 1 if random.random() < 0.1 else 0
                is_new_ip = 1 if random.random() < 0.12 else 0
            elif i < 130:  # Suspicious
                amount = round(random.uniform(500, 5000), 2)
                hours_ago = random.randint(0, 72)
                status_choices = [TransactionStatus.SUSPICIOUS.value]
                failed_attempts = random.randint(1, 4)
                is_new_device = 1 if random.random() < 0.5 else 0
                is_new_ip = 1 if random.random() < 0.5 else 0
            else:  # High-risk
                amount = round(random.uniform(3000, 15000), 2)
                hours_ago = random.randint(0, 48)
                status_choices = [TransactionStatus.HELD.value]
                failed_attempts = random.randint(2, 6)
                is_new_device = 1
                is_new_ip = 1 if random.random() < 0.7 else 0

            tx_time = now - timedelta(hours=hours_ago, minutes=random.randint(0, 59))
            tx_freq = random.uniform(0.5, 15.0)
            avg_amount = amount * random.uniform(0.5, 1.5)
            time_since_last = random.uniform(0.1, 48.0)
            merchant_freq = random.uniform(0, 10)
            device_count = random.randint(1, 20)
            ip_count = random.randint(1, 15)

            tx = Transaction(
                id=str(uuid.uuid4()),
                account_id=acct.id,
                device_id=dev.id,
                ip_id=ip_obj.id,
                merchant_id=merchant.id,
                amount=amount,
                currency="INR",
                description=f"Payment to {merchant.name}",
                status=random.choice(status_choices),
                failed_attempts=failed_attempts,
                is_new_device=is_new_device,
                is_new_ip=is_new_ip,
                transaction_frequency=round(tx_freq, 4),
                account_average_amount=round(avg_amount, 2),
                time_since_last_transaction=round(time_since_last, 4),
                merchant_frequency=round(merchant_freq, 4),
                device_usage_count=device_count,
                ip_usage_count=ip_count,
                created_at=tx_time,
            )
            db.add(tx)
            transactions.append(tx)

        db.flush()
        print(f"  Created {len(transactions)} transactions")

        # ============ PREDICTIONS ============
        for tx in transactions:
            tx_data = {
                "amount": tx.amount,
                "timestamp": tx.created_at.isoformat(),
                "account_id": tx.account_id,
                "device_id": tx.device_id or "unknown",
                "ip_address": "0.0.0.0",
                "merchant_id": tx.merchant_id or "unknown",
                "failed_attempts": tx.failed_attempts,
                "is_new_device": tx.is_new_device,
                "is_new_ip": tx.is_new_ip,
                "transaction_frequency": tx.transaction_frequency,
                "account_average_amount": tx.account_average_amount,
                "time_since_last_transaction": tx.time_since_last_transaction,
                "merchant_frequency": tx.merchant_frequency,
                "device_usage_count": tx.device_usage_count,
                "ip_usage_count": tx.ip_usage_count,
            }

            if use_model:
                try:
                    pred = predictor.predict(tx_data)
                    fraud_prob = pred["fraud_probability"]
                    anomaly_score = pred["anomaly_score"]
                    risk_level = pred["risk_level"]
                    explanation = json.dumps(pred.get("explanation", {}))
                except Exception:
                    fraud_prob = random.uniform(0, 0.3) if tx.status == "approved" else random.uniform(0.4, 0.95)
                    anomaly_score = random.uniform(0, 0.5) if tx.status == "approved" else random.uniform(0.3, 0.9)
                    risk_level = "safe" if tx.status == "approved" else "suspicious" if tx.status == "suspicious" else "high_risk"
                    explanation = json.dumps({"factors": [], "method": "seed_fallback"})
            else:
                # Generate realistic probability ranges based on status
                if tx.status == "approved":
                    fraud_prob = round(random.uniform(0.01, 0.25), 4)
                    anomaly_score = round(random.uniform(0.01, 0.3), 4)
                    risk_level = "safe"
                elif tx.status == "suspicious":
                    fraud_prob = round(random.uniform(0.35, 0.65), 4)
                    anomaly_score = round(random.uniform(0.3, 0.6), 4)
                    risk_level = "suspicious"
                else:
                    fraud_prob = round(random.uniform(0.65, 0.98), 4)
                    anomaly_score = round(random.uniform(0.6, 0.95), 4)
                    risk_level = "high_risk"
                explanation = json.dumps({"factors": [], "method": "seed_fallback"})

            # Update transaction status based on model output
            if use_model:
                if risk_level == "high_risk":
                    tx.status = TransactionStatus.HELD.value
                elif risk_level == "suspicious":
                    tx.status = TransactionStatus.SUSPICIOUS.value
                else:
                    tx.status = TransactionStatus.APPROVED.value

            model_pred = ModelPrediction(
                id=str(uuid.uuid4()),
                transaction_id=tx.id,
                fraud_probability=fraud_prob,
                anomaly_score=anomaly_score,
                risk_level=risk_level,
                model_version="1.0",
                explanation=explanation,
            )
            db.add(model_pred)

            # Create alerts for risky transactions
            if risk_level in ("suspicious", "high_risk"):
                severity = AlertSeverity.CRITICAL.value if risk_level == "high_risk" else AlertSeverity.MEDIUM.value
                alert = FraudAlert(
                    id=str(uuid.uuid4()),
                    transaction_id=tx.id,
                    fraud_probability=fraud_prob,
                    anomaly_score=anomaly_score,
                    severity=severity,
                    status=random.choice([AlertStatus.NEW.value, AlertStatus.ACKNOWLEDGED.value]),
                    description=f"Transaction flagged as {risk_level.replace('_', ' ')}. Amount: ₹{tx.amount:.2f}",
                    created_at=tx.created_at,
                )
                db.add(alert)
                alerts_list.append(alert)

        db.flush()
        print(f"  Created {len(transactions)} predictions")
        print(f"  Created {len(alerts_list)} alerts")

        # ============ INVESTIGATIONS ============
        alert_sample = alerts_list[:min(8, len(alerts_list))]
        analyst_user = users[3]  # analyst

        for i, alert in enumerate(alert_sample):
            inv = Investigation(
                id=str(uuid.uuid4()),
                transaction_id=alert.transaction_id,
                alert_id=alert.id,
                assigned_to=analyst_user.id,
                title=f"Investigation: {alert.description[:50]}",
                description=f"Auto-generated investigation for alert {alert.id[:8]}",
                status=random.choice(["open", "under_review", "escalated", "resolved"]),
                priority=random.choice(["low", "medium", "high", "critical"]),
                created_at=alert.created_at + timedelta(minutes=random.randint(5, 60)),
            )
            db.add(inv)
            db.flush()

            # Add notes to some investigations
            for j in range(random.randint(0, 3)):
                note = InvestigationNote(
                    id=str(uuid.uuid4()),
                    investigation_id=inv.id,
                    author_id=analyst_user.id,
                    content=random.choice([
                        "Reviewed transaction details. Amount is significantly higher than account average.",
                        "Checked device history. This device has been used by multiple accounts.",
                        "IP address traced to a known proxy service. Escalating for further review.",
                        "Contacted account holder for verification. Awaiting response.",
                        "Transaction appears legitimate after account holder confirmation.",
                        "Pattern matches known fraud ring activity. Recommending account freeze.",
                        "Cross-referencing with other flagged transactions from same merchant.",
                    ]),
                    created_at=inv.created_at + timedelta(hours=j + 1),
                )
                db.add(note)

            investigations_list.append(inv)

        db.commit()
        print(f"  Created {len(investigations_list)} investigations")

        print("\nDatabase seeded successfully!")
        print("\nDemo credentials:")
        print("  Customer: customer1 / password123")
        print("  Analyst:  analyst / password123")
        print("  Admin:    admin / password123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# Fix for random.lognormexp not existing
import random as _random
_orig_gauss = _random.gauss


if __name__ == "__main__":
    seed_database()
