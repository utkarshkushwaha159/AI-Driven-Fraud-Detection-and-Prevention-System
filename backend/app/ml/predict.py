"""
Prediction module - loads trained model and makes fraud predictions.
"""
import os
import json
import numpy as np
import pandas as pd
import joblib

from app.ml.feature_engineering import engineer_single_transaction, FEATURE_NAMES
from app.ml.preprocessing import FraudPreprocessor
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.explain import FraudExplainer

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


class FraudPredictor:
    """Loads trained model artifacts and makes fraud predictions."""

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.anomaly_detector = None
        self.explainer = None
        self.metadata = None
        self.loaded = False

    def load(self):
        """Load all model artifacts."""
        model_path = os.path.join(ARTIFACTS_DIR, "xgb_fraud_model.joblib")
        preprocessor_path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
        anomaly_path = os.path.join(ARTIFACTS_DIR, "anomaly_detector.joblib")
        metadata_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")

        if not os.path.exists(model_path):
            print(f"WARNING: Model not found at {model_path}. Run training first.")
            return False

        try:
            self.model = joblib.load(model_path)
            self.preprocessor = FraudPreprocessor.load(preprocessor_path)
            self.anomaly_detector = AnomalyDetector.load(anomaly_path)
            self.explainer = FraudExplainer(self.model)
            self.explainer.initialize(self.model)

            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)

            self.loaded = True
            print("Fraud detection model loaded successfully.")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def predict(self, transaction_data: dict) -> dict:
        """
        Predict fraud probability for a transaction.
        Returns prediction results with explanation.
        """
        if not self.loaded:
            raise RuntimeError("Model not loaded. Call load() first or train the model.")

        # Engineer features
        features = engineer_single_transaction(transaction_data)

        # Preprocess
        features_scaled = self.preprocessor.transform(features)

        # Get fraud probability from XGBoost
        fraud_prob = float(self.model.predict_proba(features_scaled)[0][1])

        # Get anomaly score from Isolation Forest
        anomaly_score = float(self.anomaly_detector.predict(features_scaled)[0])

        # Determine risk level based on model output
        risk_level = self._determine_risk_level(fraud_prob, anomaly_score)

        # Generate explanation
        explanation = self.explainer.explain(features_scaled, top_n=5)

        return {
            "fraud_probability": round(fraud_prob, 4),
            "anomaly_score": round(anomaly_score, 4),
            "risk_level": risk_level,
            "explanation": explanation,
            "features_used": {name: round(float(features_scaled.iloc[0][name]), 4)
                             for name in features_scaled.columns},
            "model_version": self.metadata.get("model_version", "1.0") if self.metadata else "1.0",
        }

    def _determine_risk_level(self, fraud_prob, anomaly_score):
        """Determine risk level from model output probabilities."""
        # Combined score using model outputs (not rules)
        combined = fraud_prob * 0.7 + anomaly_score * 0.3

        if combined >= 0.6 or fraud_prob >= 0.7:
            return "high_risk"
        elif combined >= 0.3 or fraud_prob >= 0.4:
            return "suspicious"
        else:
            return "safe"

    def get_model_info(self) -> dict:
        """Get model metadata and status."""
        if not self.loaded or not self.metadata:
            return {
                "model_type": "XGBClassifier",
                "model_version": "not_trained",
                "training_date": None,
                "metrics": {},
                "feature_names": FEATURE_NAMES,
                "status": "not_loaded",
            }
        return {
            "model_type": self.metadata.get("model_type", "XGBClassifier"),
            "model_version": self.metadata.get("model_version", "1.0"),
            "training_date": self.metadata.get("training_date"),
            "metrics": self.metadata.get("metrics", {}),
            "feature_names": self.metadata.get("feature_names", FEATURE_NAMES),
            "status": "loaded",
        }


# Singleton instance
_predictor = None


def get_predictor() -> FraudPredictor:
    """Get or create the singleton predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = FraudPredictor()
        _predictor.load()
    return _predictor
