import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.id"), unique=True, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    anomaly_score = Column(Float, default=0.0)
    risk_level = Column(String, nullable=False)  # safe, suspicious, high_risk
    model_version = Column(String, default="1.0")
    prediction_timestamp = Column(DateTime, default=datetime.utcnow)
    feature_vector = Column(Text, nullable=True)  # JSON string of features used
    explanation = Column(Text, nullable=True)  # JSON string of SHAP values
    network_risk_score = Column(Float, default=0.0)

    transaction = relationship("Transaction", back_populates="prediction")
