import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class IpAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip = Column(String, unique=True, nullable=False, index=True)
    country = Column(String, nullable=True)
    city = Column(String, nullable=True)
    is_vpn = Column(String, default="false")
    is_tor = Column(String, default="false")
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="ip_address")
