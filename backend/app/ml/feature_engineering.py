"""
Feature engineering module for fraud detection.
Transforms raw transaction data into ML-ready features.
"""
import numpy as np
import pandas as pd


FEATURE_NAMES = [
    "amount", "log_amount", "amount_zscore",
    "hour", "day_of_week", "is_weekend", "is_night",
    "failed_attempts", "is_new_device", "is_new_ip",
    "transaction_frequency", "log_tx_freq",
    "amount_to_avg_ratio", "amount_deviation",
    "time_since_last_transaction", "log_time_since_last",
    "merchant_frequency", "device_usage_count", "ip_usage_count",
    "log_device_count", "log_ip_count",
    "behavioural_score", "velocity_score",
    "device_ip_interaction", "amount_freq_interaction",
]


def engineer_features(df, is_training=True):
    """
    Generate ML features from transaction data.
    Avoids target leakage by only using pre-transaction data.
    """
    features = pd.DataFrame()

    # Amount features
    features["amount"] = df["amount"].astype(float)
    features["log_amount"] = np.log1p(features["amount"])
    if is_training:
        mean_amt = features["amount"].mean()
        std_amt = features["amount"].std()
        if std_amt == 0:
            std_amt = 1.0
    else:
        mean_amt = features["amount"].mean()
        std_amt = features["amount"].std()
        if std_amt == 0:
            std_amt = 1.0
    features["amount_zscore"] = (features["amount"] - mean_amt) / std_amt

    # Time features
    if "timestamp" in df.columns:
        timestamps = pd.to_datetime(df["timestamp"])
        features["hour"] = timestamps.dt.hour
        features["day_of_week"] = timestamps.dt.dayofweek
        features["is_weekend"] = (features["day_of_week"] >= 5).astype(int)
        features["is_night"] = ((features["hour"] < 6) | (features["hour"] > 22)).astype(int)
    else:
        features["hour"] = 12
        features["day_of_week"] = 3
        features["is_weekend"] = 0
        features["is_night"] = 0

    # Behavioural features
    features["failed_attempts"] = df.get("failed_attempts", pd.Series(0, index=df.index)).fillna(0).astype(int)
    features["is_new_device"] = df.get("is_new_device", pd.Series(0, index=df.index)).fillna(0).astype(int)
    features["is_new_ip"] = df.get("is_new_ip", pd.Series(0, index=df.index)).fillna(0).astype(int)

    # Frequency features
    features["transaction_frequency"] = df.get("transaction_frequency", pd.Series(0, index=df.index)).fillna(0).astype(float)
    features["log_tx_freq"] = np.log1p(features["transaction_frequency"])

    # Amount deviation from account average
    avg_amount = df.get("account_average_amount", pd.Series(features["amount"].mean(), index=df.index)).fillna(features["amount"].mean()).astype(float)
    avg_amount = avg_amount.replace(0, features["amount"].mean())
    features["amount_to_avg_ratio"] = features["amount"] / avg_amount.clip(lower=1.0)
    features["amount_deviation"] = (features["amount"] - avg_amount).abs()

    # Time since last transaction
    features["time_since_last_transaction"] = df.get("time_since_last_transaction", pd.Series(24.0, index=df.index)).fillna(24.0).astype(float)
    features["log_time_since_last"] = np.log1p(features["time_since_last_transaction"])

    # Merchant and entity features
    features["merchant_frequency"] = df.get("merchant_frequency", pd.Series(0, index=df.index)).fillna(0).astype(float)
    features["device_usage_count"] = df.get("device_usage_count", pd.Series(1, index=df.index)).fillna(1).astype(int)
    features["ip_usage_count"] = df.get("ip_usage_count", pd.Series(1, index=df.index)).fillna(1).astype(int)
    features["log_device_count"] = np.log1p(features["device_usage_count"])
    features["log_ip_count"] = np.log1p(features["ip_usage_count"])

    # Composite scores (derived from features, NOT rules)
    features["behavioural_score"] = (
        features["is_new_device"] * 0.3 +
        features["is_new_ip"] * 0.3 +
        features["is_night"] * 0.2 +
        (features["failed_attempts"] > 0).astype(int) * 0.2
    )

    features["velocity_score"] = (
        np.clip(features["transaction_frequency"] / 10.0, 0, 1) * 0.5 +
        np.clip(1.0 / (features["time_since_last_transaction"] + 0.01), 0, 1) * 0.5
    )

    # Interaction features
    features["device_ip_interaction"] = features["is_new_device"] * features["is_new_ip"]
    features["amount_freq_interaction"] = features["log_amount"] * features["log_tx_freq"]

    # Fill any remaining NaN
    features = features.fillna(0)

    # Ensure feature order
    for col in FEATURE_NAMES:
        if col not in features.columns:
            features[col] = 0

    return features[FEATURE_NAMES]


def engineer_single_transaction(tx_data: dict) -> pd.DataFrame:
    """Engineer features for a single transaction (prediction time)."""
    df = pd.DataFrame([tx_data])
    return engineer_features(df, is_training=False)
