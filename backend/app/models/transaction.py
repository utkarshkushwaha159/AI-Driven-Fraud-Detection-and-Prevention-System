import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPICIOUS = "suspicious"
    HELD = "held"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    VERIFIED = "verified"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), nullable=True)
    ip_id = Column(String, ForeignKey("ip_addresses.id"), nullable=True)
    merchant_id = Column(String, ForeignKey("merchants.id"), nullable=True)

    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    description = Column(String, nullable=True)
    status = Column(String, default=TransactionStatus.PENDING.value)
    risk_level = Column(String, default="safe")
    customer_status_message = Column(String, nullable=True)

    # Verification workflow fields (Server-side security)
    verification_code = Column(String, nullable=True)
    verification_attempts = Column(Integer, default=0)
    verification_code_expires_at = Column(DateTime, nullable=True)

    # Admin decision workflow fields
    requires_admin_review = Column(Integer, default=0)
    admin_decision = Column(String, nullable=True)
    admin_decision_by = Column(String, nullable=True)
    admin_decision_at = Column(DateTime, nullable=True)

    # Behavioural features stored at transaction time
    failed_attempts = Column(Integer, default=0)
    is_new_device = Column(Integer, default=0)
    is_new_ip = Column(Integer, default=0)
    transaction_frequency = Column(Float, default=0.0)
    account_average_amount = Column(Float, default=0.0)
    time_since_last_transaction = Column(Float, default=0.0)
    merchant_frequency = Column(Float, default=0.0)
    device_usage_count = Column(Integer, default=1)
    ip_usage_count = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    account = relationship("Account", back_populates="transactions")
    device = relationship("Device", back_populates="transactions")
    ip_address = relationship("IpAddress", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")
    prediction = relationship("ModelPrediction", back_populates="transaction", uselist=False)
    alerts = relationship("FraudAlert", back_populates="transaction")
    investigation = relationship("Investigation", back_populates="transaction", uselist=False)
