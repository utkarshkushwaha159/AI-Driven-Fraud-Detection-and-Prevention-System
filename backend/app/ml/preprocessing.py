"""
Preprocessing pipeline for fraud detection ML model.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


class FraudPreprocessor:
    """Handles data cleaning and preprocessing for fraud detection."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
        self.fitted = False

    def clean_data(self, df):
        """Clean raw data: handle missing values, remove duplicates."""
        df = df.copy()

        # Remove exact duplicate rows
        df = df.drop_duplicates()

        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())

        string_cols = df.select_dtypes(include=["object"]).columns
        for col in string_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna("unknown")

        # Clip extreme outliers for amount
        if "amount" in df.columns:
            q99 = df["amount"].quantile(0.99)
            df["amount"] = df["amount"].clip(upper=q99 * 2)

        return df

    def fit_transform(self, features_df):
        """Fit the scaler on training features and transform."""
        self.feature_names = features_df.columns.tolist()
        scaled = self.scaler.fit_transform(features_df)
        self.fitted = True
        return pd.DataFrame(scaled, columns=self.feature_names, index=features_df.index)

    def transform(self, features_df):
        """Transform new data using fitted scaler."""
        if not self.fitted:
            raise ValueError("Preprocessor not fitted. Call fit_transform first.")
        # Ensure columns match
        for col in self.feature_names:
            if col not in features_df.columns:
                features_df[col] = 0
        features_df = features_df[self.feature_names]
        scaled = self.scaler.transform(features_df)
        return pd.DataFrame(scaled, columns=self.feature_names, index=features_df.index)

    def save(self, path=None):
        """Save the preprocessing pipeline."""
        if path is None:
            path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            "scaler": self.scaler,
            "feature_names": self.feature_names,
            "fitted": self.fitted,
        }, path)
        print(f"Preprocessor saved to {path}")

    @classmethod
    def load(cls, path=None):
        """Load a saved preprocessing pipeline."""
        if path is None:
            path = os.path.join(ARTIFACTS_DIR, "preprocessor.joblib")
        data = joblib.load(path)
        preprocessor = cls()
        preprocessor.scaler = data["scaler"]
        preprocessor.feature_names = data["feature_names"]
        preprocessor.fitted = data["fitted"]
        return preprocessor
