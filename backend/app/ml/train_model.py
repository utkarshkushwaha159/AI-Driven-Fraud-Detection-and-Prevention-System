"""
XGBoost-based fraud detection model training pipeline.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score,
    confusion_matrix, classification_report
)
from xgboost import XGBClassifier
import joblib

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.ml.feature_engineering import engineer_features, FEATURE_NAMES
from app.ml.preprocessing import FraudPreprocessor
from app.ml.generate_dataset import generate_dataset
from app.ml.anomaly_detector import AnomalyDetector

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")


def train_model(dataset_path=None):
    """Full training pipeline for the fraud detection model."""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # Step 1: Load or generate dataset
    print("=" * 60)
    print("FRAUD DETECTION MODEL TRAINING PIPELINE")
    print("=" * 60)

    if dataset_path and os.path.exists(dataset_path):
        print(f"\nLoading dataset from: {dataset_path}")
        df = pd.read_csv(dataset_path)
    else:
        default_path = os.path.join(ARTIFACTS_DIR, "dataset.csv")
        if os.path.exists(default_path):
            print(f"\nLoading existing dataset: {default_path}")
            df = pd.read_csv(default_path)
        else:
            print("\nNo dataset found. Generating synthetic data...")
            df = generate_dataset(n_samples=20000, fraud_rate=0.05, output_path=default_path)

    print(f"\nDataset shape: {df.shape}")
    print(f"Fraud distribution:\n{df['fraud_label'].value_counts()}")
    print(f"Fraud rate: {df['fraud_label'].mean():.4f}")

    # Step 2: Clean data
    print("\n--- Data Cleaning ---")
    preprocessor = FraudPreprocessor()
    df = preprocessor.clean_data(df)
    print(f"After cleaning: {df.shape}")

    # Step 3: Feature engineering
    print("\n--- Feature Engineering ---")
    X = engineer_features(df, is_training=True)
    y = df["fraud_label"].astype(int)
    print(f"Features: {X.shape[1]} ({', '.join(X.columns[:5])}...)")

    # Step 4: Split data
    print("\n--- Train/Validation/Test Split ---")
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.176, random_state=42, stratify=y_train_val
    )
    print(f"Train: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

    # Step 5: Handle class imbalance with SMOTE
    print("\n--- Handling Class Imbalance (SMOTE) ---")
    try:
        from imblearn.over_sampling import SMOTE
        smote = SMOTE(random_state=42, k_neighbors=min(5, y_train.sum() - 1))
        X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)
        print(f"After SMOTE - Train: {X_train_balanced.shape[0]}")
        print(f"Class distribution:\n{pd.Series(y_train_balanced).value_counts()}")
    except Exception as e:
        print(f"SMOTE failed ({e}), using scale_pos_weight instead")
        X_train_balanced = X_train
        y_train_balanced = y_train

    # Step 6: Fit preprocessor (scaler)
    print("\n--- Fitting Preprocessor ---")
    X_train_scaled = preprocessor.fit_transform(X_train_balanced)
    X_val_scaled = preprocessor.transform(X_val)
    X_test_scaled = preprocessor.transform(X_test)

    # Step 7: Train XGBoost model
    print("\n--- Training XGBoost Classifier ---")
    neg_count = (y_train_balanced == 0).sum()
    pos_count = (y_train_balanced == 1).sum()
    scale_weight = neg_count / max(pos_count, 1)

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_weight,
        eval_metric="logloss",
        random_state=42,
        use_label_encoder=False,
    )

    model.fit(
        X_train_scaled, y_train_balanced,
        eval_set=[(X_val_scaled, y_val)],
        verbose=True
    )

    # Step 8: Evaluate
    print("\n--- Model Evaluation ---")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)

    print(f"\nPrecision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"PR-AUC:    {pr_auc:.4f}")
    print(f"\nConfusion Matrix:\n{cm}")
    print(f"\n{classification_report(y_test, y_pred, zero_division=0)}")

    # Step 9: Train Anomaly Detector
    print("\n--- Training Anomaly Detector ---")
    anomaly_detector = AnomalyDetector()
    anomaly_detector.fit(X_train_scaled)
    anomaly_detector.save()
    print("Anomaly detector trained and saved.")

    # Step 10: Save model and artifacts
    print("\n--- Saving Model Artifacts ---")
    model_path = os.path.join(ARTIFACTS_DIR, "xgb_fraud_model.joblib")
    joblib.dump(model, model_path)
    print(f"Model saved: {model_path}")

    preprocessor.save()
    print("Preprocessor saved.")

    # Save metadata
    metadata = {
        "model_type": "XGBClassifier",
        "model_version": "1.0",
        "training_date": datetime.utcnow().isoformat(),
        "n_samples": int(len(df)),
        "n_features": int(X.shape[1]),
        "feature_names": FEATURE_NAMES,
        "metrics": {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "roc_auc": float(roc_auc),
            "pr_auc": float(pr_auc),
            "confusion_matrix": cm.tolist(),
        },
        "fraud_rate": float(df["fraud_label"].mean()),
        "train_size": int(X_train.shape[0]),
        "val_size": int(X_val.shape[0]),
        "test_size": int(X_test.shape[0]),
    }

    metadata_path = os.path.join(ARTIFACTS_DIR, "model_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved: {metadata_path}")

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)

    return model, preprocessor, metadata


if __name__ == "__main__":
    train_model()
