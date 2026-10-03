"""
End-to-end automated test suite verifying requirements A through H:
- TEST A: Safe payment -> ML analysis -> APPROVED -> customer sees APPROVED
- TEST B: Suspicious -> HELD -> wrong code -> wrong code -> BLOCKED/REJECTED -> Alert -> Investigation
- TEST C: Suspicious -> HELD -> wrong code -> correct code -> APPROVED -> customer sees APPROVED
- TEST D: Suspicious -> HELD -> correct code first attempt -> APPROVED
- TEST E: High risk -> HELD -> Alert -> Investigation -> Analyst investigates -> Ready for Admin -> Admin APPROVE -> APPROVED
- TEST F: High risk -> HELD -> Investigation -> Analyst investigates -> Ready for Admin -> Admin REJECT -> BLOCKED/REJECTED
- TEST G: Analyst attempts Admin-only API -> HTTP 403
- TEST H: Verification attempt 3 -> rejected with HTTP 400
"""
import os
import sys
import unittest
from datetime import datetime
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus
from app.models.fraud_alert import FraudAlert
from app.models.investigation import Investigation, InvestigationStatus
from app.services.auth_service import create_token, hash_password


class TestEndToEndWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Create or ensure test users
        cls.customer_user = cls.db.query(User).filter(User.username == "test_customer").first()
        if not cls.customer_user:
            cls.customer_user = User(
                username="test_customer",
                email="cust@test.com",
                password_hash=hash_password("password123"),
                full_name="Test Customer",
                role=UserRole.CUSTOMER,
            )
            cls.db.add(cls.customer_user)
            cls.db.flush()

        cls.analyst_user = cls.db.query(User).filter(User.username == "test_analyst").first()
        if not cls.analyst_user:
            cls.analyst_user = User(
                username="test_analyst",
                email="analyst@test.com",
                password_hash=hash_password("password123"),
                full_name="Test Analyst",
                role=UserRole.ANALYST,
            )
            cls.db.add(cls.analyst_user)
            cls.db.flush()

        cls.admin_user = cls.db.query(User).filter(User.username == "test_admin").first()
        if not cls.admin_user:
            cls.admin_user = User(
                username="test_admin",
                email="admin@test.com",
                password_hash=hash_password("password123"),
                full_name="Test Admin",
                role=UserRole.ADMIN,
            )
            cls.db.add(cls.admin_user)
            cls.db.flush()

        # Ensure account
        cls.account = cls.db.query(Account).filter(Account.account_number == "ACC-TEST-001").first()
        if not cls.account:
            cls.account = Account(
                account_number="ACC-TEST-001",
                user_id=cls.customer_user.id,
                balance=500000.0,
                account_type="checking",
            )
            cls.db.add(cls.account)

        cls.db.commit()

        # Create authentication tokens
        cls.cust_token = create_token(cls.customer_user.id, "test_customer", "customer")
        cls.analyst_token = create_token(cls.analyst_user.id, "test_analyst", "analyst")
        cls.admin_token = create_token(cls.admin_user.id, "test_admin", "admin")

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_a_safe_payment_approved(self):
        """TEST A: Safe payment -> ML analysis -> APPROVED -> customer sees APPROVED."""
        payload = {
            "account_id": self.account.id,
            "amount": 450.00,
            "merchant_code": "WMT_RETAIL",
            "description": "Everyday groceries",
            "device_fingerprint": "DEV-SAFE-01",
            "ip_address": "192.168.1.10",
        }
        res = self.client.post("/api/payments/check", json=payload, headers={"Authorization": f"Bearer {self.cust_token}"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "approved")
        self.assertEqual(data["risk_level"], "safe")
        self.assertFalse(data["requires_verification"])

        # Customer checks account transactions
        tx_res = self.client.get(f"/api/accounts/{self.account.id}/transactions")
        self.assertEqual(tx_res.status_code, 200)
        tx_data = tx_res.json()
        tx = next((t for t in tx_data["transactions"] if t["id"] == data["transaction_id"]), None)
        self.assertIsNotNone(tx)
        self.assertEqual(tx["status"], "approved")

    def test_b_suspicious_two_wrong_attempts_blocked(self):
        """TEST B: Suspicious -> HELD -> wrong code -> wrong code -> BLOCKED -> Alert -> Investigation created."""
        payload = {
            "account_id": self.account.id,
            "amount": 42000.00,
            "merchant_code": "APPL_STORE",
            "description": "Electronics purchase from unverified device",
            "device_fingerprint": "DEV-UNKNOWN-99",
            "ip_address": "198.51.100.22",
        }
        res = self.client.post("/api/payments/check", json=payload)
        self.assertEqual(res.status_code, 200)
        tx_id = res.json()["transaction_id"]
        self.assertEqual(res.json()["status"], "held")
        self.assertTrue(res.json()["requires_verification"])

        # Attempt 1: wrong code
        v1 = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "000000"})
        self.assertEqual(v1.status_code, 200)
        self.assertEqual(v1.json()["status"], "held")
        self.assertEqual(v1.json()["attempts_remaining"], 1)
        self.assertFalse(v1.json()["verified"])

        # Attempt 2: wrong code -> permanently BLOCKED / REJECTED
        v2 = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "999999"})
        self.assertEqual(v2.status_code, 200)
        self.assertEqual(v2.json()["status"], "blocked")
        self.assertEqual(v2.json()["attempts_remaining"], 0)
        self.assertFalse(v2.json()["verified"])

        # Verify Alert and Investigation were created
        tx_detail = self.client.get(f"/api/transactions/{tx_id}").json()
        self.assertEqual(tx_detail["status"], "blocked")
        self.assertIsNotNone(tx_detail["investigation_id"])

        inv = self.client.get(f"/api/investigations/{tx_detail['investigation_id']}").json()
        self.assertEqual(inv["status"], "open")
        self.assertEqual(inv["priority"], "critical")

    def test_c_suspicious_wrong_then_correct_approved(self):
        """TEST C: Suspicious -> HELD -> wrong code -> correct code -> APPROVED -> customer sees APPROVED."""
        payload = {
            "account_id": self.account.id,
            "amount": 35000.00,
            "merchant_code": "APPL_STORE",
            "description": "Tablet purchase",
            "device_fingerprint": "DEV-UNKNOWN-88",
            "ip_address": "198.51.100.33",
        }
        res = self.client.post("/api/payments/check", json=payload)
        tx_id = res.json()["transaction_id"]
        self.assertEqual(res.json()["status"], "held")

        # Attempt 1: wrong code
        v1 = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "111111"})
        self.assertEqual(v1.json()["attempts_remaining"], 1)

        # Attempt 2: correct code ("123456")
        v2 = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "123456"})
        self.assertEqual(v2.status_code, 200)
        self.assertEqual(v2.json()["status"], "approved")
        self.assertTrue(v2.json()["verified"])

        # Verify transaction status updated in DB
        tx = self.client.get(f"/api/transactions/{tx_id}").json()
        self.assertEqual(tx["status"], "approved")

    def test_d_suspicious_correct_first_attempt_approved(self):
        """TEST D: Suspicious -> HELD -> correct code first attempt -> APPROVED."""
        payload = {
            "account_id": self.account.id,
            "amount": 28000.00,
            "merchant_code": "APPL_STORE",
            "description": "Hardware device checkout",
            "device_fingerprint": "DEV-UNKNOWN-77",
            "ip_address": "198.51.100.44",
        }
        res = self.client.post("/api/payments/check", json=payload)
        tx_id = res.json()["transaction_id"]

        # Attempt 1: correct code
        v = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "123456"})
        self.assertEqual(v.status_code, 200)
        self.assertEqual(v.json()["status"], "approved")
        self.assertTrue(v.json()["verified"])

    def test_e_high_risk_analyst_review_and_admin_approve(self):
        """TEST E: High risk -> HELD -> Alert -> Investigation -> Analyst investigates -> Ready for Admin -> Admin APPROVE -> APPROVED."""
        payload = {
            "account_id": self.account.id,
            "amount": 275000.00,
            "merchant_code": "CRYPTO_EX",
            "description": "Large wire to crypto gateway",
            "device_fingerprint": "DEV-PROXY-EMULATOR-009",
            "ip_address": "203.0.113.195",
        }
        res = self.client.post("/api/payments/check", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        tx_id = data["transaction_id"]
        self.assertEqual(data["status"], "held")
        self.assertEqual(data["risk_level"], "high_risk")

        # 1. Check investigation was automatically opened
        tx_detail = self.client.get(f"/api/transactions/{tx_id}").json()
        inv_id = tx_detail["investigation_id"]
        self.assertIsNotNone(inv_id)

        # 2. Analyst adds note and updates status to "ready_for_admin_review"
        note_res = self.client.post(
            f"/api/investigations/{inv_id}/notes",
            json={"content": "Verified source of funds with customer. Legitimate high-value transfer."},
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(note_res.status_code, 200)

        update_res = self.client.patch(
            f"/api/investigations/{inv_id}",
            json={"status": "ready_for_admin_review", "findings": "Account holder verified KYC documents."},
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )
        self.assertEqual(update_res.status_code, 200)

        # 3. Admin APPROVE
        admin_res = self.client.post(
            f"/api/admin/transactions/{tx_id}/approve",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(admin_res.status_code, 200)
        self.assertEqual(admin_res.json()["status"], "approved")

        # 4. Customer verifies status is now APPROVED
        cust_tx = self.client.get(f"/api/transactions/{tx_id}").json()
        self.assertEqual(cust_tx["status"], "approved")
        self.assertEqual(cust_tx["admin_decision"], "approved")

    def test_f_high_risk_analyst_review_and_admin_reject(self):
        """TEST F: High risk -> HELD -> Investigation -> Analyst investigates -> Ready for Admin -> Admin REJECT -> BLOCKED/REJECTED."""
        payload = {
            "account_id": self.account.id,
            "amount": 320000.00,
            "merchant_code": "CRYPTO_EX",
            "description": "Suspicious rapid drain wire",
            "device_fingerprint": "DEV-BOTNET-007",
            "ip_address": "185.220.101.5",
        }
        res = self.client.post("/api/payments/check", json=payload)
        tx_id = res.json()["transaction_id"]
        self.assertEqual(res.json()["status"], "held")

        tx_detail = self.client.get(f"/api/transactions/{tx_id}").json()
        inv_id = tx_detail["investigation_id"]

        # Analyst marks ready for admin review
        self.client.patch(
            f"/api/investigations/{inv_id}",
            json={"status": "ready_for_admin_review", "findings": "Confirmed botnet proxy IP matching known syndicate."},
            headers={"Authorization": f"Bearer {self.analyst_token}"},
        )

        # Admin REJECT
        admin_res = self.client.post(
            f"/api/admin/transactions/{tx_id}/reject",
            headers={"Authorization": f"Bearer {self.admin_token}"},
        )
        self.assertEqual(admin_res.status_code, 200)
        self.assertEqual(admin_res.json()["status"], "blocked")

        # Customer sees final status BLOCKED
        cust_tx = self.client.get(f"/api/transactions/{tx_id}").json()
        self.assertEqual(cust_tx["status"], "blocked")
        self.assertEqual(cust_tx["admin_decision"], "rejected")

    def test_g_analyst_forbidden_on_admin_routes(self):
        """TEST G: Analyst attempts Admin-only API -> HTTP 403."""
        # 1. Analyst attempts audit logs
        res1 = self.client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {self.analyst_token}"})
        self.assertEqual(res1.status_code, 403)

        # 2. Analyst attempts admin approve
        res2 = self.client.post("/api/admin/transactions/fake-id/approve", headers={"Authorization": f"Bearer {self.analyst_token}"})
        self.assertEqual(res2.status_code, 403)

        # 3. Analyst attempts model retrain
        res3 = self.client.post("/api/admin/models/retrain", headers={"Authorization": f"Bearer {self.analyst_token}"})
        self.assertEqual(res3.status_code, 403)

    def test_h_verification_attempt_three_rejected(self):
        """TEST H: Verification attempt 3 -> must be rejected by backend (HTTP 400)."""
        payload = {
            "account_id": self.account.id,
            "amount": 29000.00,
            "merchant_code": "APPL_STORE",
            "description": "Challenge limit test",
            "device_fingerprint": "DEV-UNKNOWN-66",
            "ip_address": "198.51.100.55",
        }
        res = self.client.post("/api/payments/check", json=payload)
        tx_id = res.json()["transaction_id"]

        # Attempt 1: wrong code
        self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "000000"})
        # Attempt 2: wrong code (blocks transaction)
        self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "000000"})

        # Attempt 3: rejected by backend with HTTP 400
        res3 = self.client.post("/api/payments/verify", json={"transaction_id": tx_id, "verification_code": "123456"})
        self.assertEqual(res3.status_code, 400)
        self.assertIn("Maximum verification attempts exceeded", res3.json()["detail"])


if __name__ == "__main__":
    unittest.main()
