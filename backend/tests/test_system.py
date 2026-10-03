"""
Unit and integration test suite for AI-Driven Fraud Detection and Prevention System.
Tests feature engineering, DSA graph algorithms, database models, payment screening, and investigations.
"""
import os
import sys
import unittest
import uuid
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.account import Account
from app.models.transaction import Transaction, TransactionStatus
from app.models.device import Device
from app.models.ip_address import IpAddress
from app.models.merchant import Merchant
from app.models.fraud_alert import FraudAlert, AlertSeverity, AlertStatus
from app.models.investigation import Investigation, InvestigationStatus
from app.dsa.graph import Graph
from app.dsa.algorithms import knapsack_01, longest_common_subsequence, graph_coloring, sum_of_subsets
from app.dsa.trees import BST, AVLTree, MaxHeap
from app.services.auth_service import hash_password, verify_password, create_token, validate_token
from app.services.network_service import NetworkService
from app.services.transaction_service import TransactionService
from app.services.investigation_service import InvestigationService


class TestDSAComponents(unittest.TestCase):
    """Test Data Structures and Algorithms implementations."""

    def test_bst_operations(self):
        bst = BST()
        for val in [50, 30, 70, 20, 40, 60, 80]:
            bst.insert(val, value=val)
        self.assertEqual(bst.search(40), 40)
        self.assertIsNone(bst.search(99))
        inorder = bst.inorder()
        self.assertEqual(inorder, sorted(inorder))

    def test_avl_tree_balance(self):
        avl = AVLTree()
        # Insert strictly ascending values which would degenerate a plain BST
        for val in [10, 20, 30, 40, 50, 25]:
            avl.insert(val, value=val)
        self.assertEqual(avl.search(30), 30)
        self.assertTrue(abs(avl._balance_factor(avl.root)) <= 1)

    def test_max_heap(self):
        heap = MaxHeap()
        for val in [15, 30, 5, 40, 25]:
            heap.insert(val, f"item_{val}")
        max1 = heap.extract_max()
        max2 = heap.extract_max()
        self.assertEqual(max1[0], 40)
        self.assertEqual(max2[0], 30)

    def test_graph_algorithms(self):
        g = Graph(directed=False)
        g.add_edge("Account_A", "Device_1", weight=1.0)
        g.add_edge("Account_B", "Device_1", weight=1.0)
        g.add_edge("Account_B", "IP_1", weight=1.0)
        g.add_edge("Account_C", "IP_2", weight=1.0)

        # Connected components (suspicious shared entity detection)
        components = g.connected_components()
        self.assertEqual(len(components), 2)

        # BFS traversal
        order, parent = g.bfs("Account_A")
        self.assertIn("Account_B", order)
        self.assertIn("IP_1", order)

        # Dijkstra
        dist, prev = g.dijkstra("Account_A")
        self.assertEqual(dist["Account_B"], 2.0)

    def test_dynamic_programming_knapsack(self):
        weights = [1, 2, 3, 5]
        values = [10, 20, 30, 60]
        capacity = 5
        max_val, items = knapsack_01(weights, values, capacity)
        self.assertEqual(max_val, 60)

    def test_lcs(self):
        lcs_len, lcs_str = longest_common_subsequence("ABCBDAB", "BDCAB")
        self.assertEqual(lcs_len, 4)

    def test_graph_coloring(self):
        # 3-node triangle graph requires 3 colors
        adj = [
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ]
        colors = graph_coloring(adj, 3)
        self.assertIsNotNone(colors)
        self.assertNotEqual(colors[0], colors[1])
        self.assertNotEqual(colors[1], colors[2])


class TestDatabaseAndAuth(unittest.TestCase):
    """Test database setup, password hashing, and authentication."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_password_hashing(self):
        pwd = "Secr3tPassword!"
        pwd_hash = hash_password(pwd)
        self.assertNotEqual(pwd, pwd_hash)
        self.assertTrue(verify_password(pwd, pwd_hash))
        self.assertFalse(verify_password("WrongPassword", pwd_hash))

    def test_jwt_token_generation(self):
        token = create_token("user_test_123", "analyst_user", "analyst")
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 20)
        user_info = validate_token(token)
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["role"], "analyst")

    def test_user_creation(self):
        uname = f"test_{uuid.uuid4().hex[:6]}"
        user = User(
            id=str(uuid.uuid4()),
            username=uname,
            email=f"{uname}@test.com",
            full_name="Test User",
            role=UserRole.CUSTOMER,
            password_hash=hash_password("testpass"),
        )
        self.db.add(user)
        self.db.commit()

        fetched = self.db.query(User).filter(User.username == uname).first()
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.full_name, "Test User")


class TestFraudWorkflows(unittest.TestCase):
    """Test payment simulation and investigation case management."""

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_payment_processing(self):
        # Test payment submission
        payment_data = {
            "account_id": f"ACC-UNIT-{uuid.uuid4().hex[:4]}",
            "amount": 49.99,
            "merchant_code": "AMZN_US",
            "description": "Book purchase",
            "device_fingerprint": "DEV-TEST-001",
            "ip_address": "127.0.0.1",
            "device_type": "desktop",
            "os_name": "Windows",
            "browser": "Chrome",
        }
        res = TransactionService.process_payment(self.db, payment_data)
        self.assertIn("transaction_id", res)
        self.assertIn("status", res)
        self.assertIn("fraud_probability", res)
        self.assertIn(res["status"], ["approved", "suspicious", "held"])

    def test_investigation_lifecycle(self):
        # Create a transaction to investigate
        tx = Transaction(
            id=str(uuid.uuid4()),
            account_id="ACC-INV-TEST",
            amount=2500.0,
            status=TransactionStatus.HELD.value,
        )
        self.db.add(tx)
        self.db.commit()

        # Create investigation
        case_data = {
            "transaction_id": tx.id,
            "title": "High value wire to unrecognized beneficiary",
            "description": "Sudden deviation from regular spending pattern.",
            "priority": "high",
        }
        inv = InvestigationService.create_investigation(self.db, case_data)
        self.assertIsNotNone(inv)
        self.assertEqual(inv.status, InvestigationStatus.OPEN.value)

        # Update status to under review and add note
        updated = InvestigationService.update_investigation(
            self.db, inv.id, {"status": "under_review"}
        )
        self.assertEqual(updated.status, "under_review")

        note = InvestigationService.add_note(
            self.db, inv.id, "Contacted customer to verify transaction origin.", user_id=None
        )
        self.assertIsNotNone(note)
        self.assertEqual(note.content, "Contacted customer to verify transaction origin.")


if __name__ == "__main__":
    unittest.main()
