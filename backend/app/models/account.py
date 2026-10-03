import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_number = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    balance = Column(Float, default=10000.0)
    account_type = Column(String, default="checking")
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(String, default="true")

    user = relationship("User", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
