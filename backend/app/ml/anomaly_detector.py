"""
Isolation Forest anomaly detector for secondary fraud detection.
"""
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


class AnomalyDetector:
    """Isolation Forest-based anomaly detection for transactions."""

    def __init__(self, contamination=0.05, n_estimators=100, random_state=42):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1,
        )
        self.fitted = False

    def fit(self, X):
        """Fit the anomaly detector on training data."""
        if isinstance(X, pd.DataFrame):
            X = X.values
        self.model.fit(X)
        self.fitted = True

    def predict(self, X):
        """
        Get anomaly scores for transactions.
        Returns scores between 0 and 1, where higher = more anomalous.
        """
        if not self.fitted:
            return np.zeros(len(X))

        if isinstance(X, pd.DataFrame):
            X = X.values

        # Raw scores from Isolation Forest (negative = anomalous)
        raw_scores = self.model.decision_function(X)

        # Convert to 0-1 scale where 1 = most anomalous
        min_score = raw_scores.min()
        max_score = raw_scores.max()
        if max_score == min_score:
            return np.zeros(len(X))

        normalized = 1.0 - (raw_scores - min_score) / (max_score - min_score)
        return np.clip(normalized, 0, 1)

    def save(self, path=None):
        """Save the anomaly detector."""
        if path is None:
            path = os.path.join(ARTIFACTS_DIR, "anomaly_detector.joblib")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "fitted": self.fitted}, path)

    @classmethod
    def load(cls, path=None):
        """Load a saved anomaly detector."""
        if path is None:
            path = os.path.join(ARTIFACTS_DIR, "anomaly_detector.joblib")
        if not os.path.exists(path):
            return cls()
        data = joblib.load(path)
        detector = cls()
        detector.model = data["model"]
        detector.fitted = data["fitted"]
        return detector
