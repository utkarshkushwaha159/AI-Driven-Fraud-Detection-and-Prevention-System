"""
SHAP-based model explanation module.
Generates human-readable explanations for fraud predictions.
"""
import os
import numpy as np
import pandas as pd
try:
    import shap
except ImportError:
    shap = None
import joblib

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "model_artifacts")

# Human-readable feature descriptions
FEATURE_DESCRIPTIONS = {
    "amount": "Transaction amount",
    "log_amount": "Transaction amount (log scale)",
    "amount_zscore": "Amount compared to typical range",
    "hour": "Time of transaction (hour)",
    "day_of_week": "Day of the week",
    "is_weekend": "Weekend transaction",
    "is_night": "Late-night transaction",
    "failed_attempts": "Number of failed payment attempts",
    "is_new_device": "Transaction from a new device",
    "is_new_ip": "Transaction from a new IP address",
    "transaction_frequency": "Transaction frequency (recent activity)",
    "log_tx_freq": "Transaction frequency (log scale)",
    "amount_to_avg_ratio": "Amount compared to account average",
    "amount_deviation": "Deviation from typical spending",
    "time_since_last_transaction": "Time since previous transaction",
    "log_time_since_last": "Time since last transaction (log scale)",
    "merchant_frequency": "Activity at this merchant",
    "device_usage_count": "Device usage history",
    "ip_usage_count": "IP address usage history",
    "log_device_count": "Device familiarity",
    "log_ip_count": "IP familiarity",
    "behavioural_score": "Behavioural pattern indicator",
    "velocity_score": "Transaction velocity indicator",
    "device_ip_interaction": "New device and IP combination",
    "amount_freq_interaction": "Amount and frequency pattern",
}


class FraudExplainer:
    """Generate SHAP-based explanations for fraud predictions."""

    def __init__(self, model=None):
        self.model = model
        self.explainer = None

    def initialize(self, model):
        """Initialize SHAP explainer with the trained model."""
        self.model = model
        try:
            self.explainer = shap.TreeExplainer(model)
        except Exception:
            self.explainer = None

    def explain(self, features_df, top_n=5):
        """
        Generate explanation for a prediction.
        Returns top contributing factors with human-readable descriptions.
        """
        if self.explainer is None or self.model is None:
            return self._fallback_explanation(features_df, top_n)

        try:
            shap_values = self.explainer.shap_values(features_df)

            # For binary classification, shap_values might be a list
            if isinstance(shap_values, list):
                shap_vals = shap_values[1]  # class 1 (fraud)
            else:
                shap_vals = shap_values

            if len(shap_vals.shape) > 1:
                shap_vals = shap_vals[0]

            feature_names = features_df.columns.tolist()
            feature_values = features_df.iloc[0].values

            # Build explanation
            explanations = []
            indices = np.argsort(np.abs(shap_vals))[::-1][:top_n]

            for idx in indices:
                feat_name = feature_names[idx]
                shap_val = float(shap_vals[idx])
                feat_val = float(feature_values[idx])
                description = FEATURE_DESCRIPTIONS.get(feat_name, feat_name)
                direction = "increases" if shap_val > 0 else "decreases"

                explanations.append({
                    "feature": feat_name,
                    "description": description,
                    "shap_value": round(shap_val, 4),
                    "feature_value": round(feat_val, 4),
                    "direction": direction,
                    "impact": "high" if abs(shap_val) > 0.5 else "medium" if abs(shap_val) > 0.1 else "low",
                    "message": self._generate_message(feat_name, feat_val, shap_val),
                })

            return {
                "factors": explanations,
                "base_value": float(self.explainer.expected_value) if not isinstance(
                    self.explainer.expected_value, list) else float(self.explainer.expected_value[1]),
                "method": "shap",
            }
        except Exception as e:
            return self._fallback_explanation(features_df, top_n)

    def _generate_message(self, feature_name, value, shap_value):
        """Generate a human-readable message for a feature contribution."""
        direction = "risk" if shap_value > 0 else "safety"
        impact = "significantly" if abs(shap_value) > 0.5 else "moderately" if abs(shap_value) > 0.1 else "slightly"

        messages = {
            "amount": f"Transaction amount (₹{value:.2f}) {impact} {'increases' if shap_value > 0 else 'decreases'} risk",
            "log_amount": f"Transaction size {impact} contributes to {direction} assessment",
            "amount_zscore": f"Amount is {'unusually high' if value > 1.5 else 'unusually low' if value < -1.5 else 'within normal range'}",
            "hour": f"Transaction time ({int(value)}:00) {impact} affects {direction} level",
            "is_night": f"{'Late-night transaction' if value > 0 else 'Daytime transaction'} {impact} {'raises' if shap_value > 0 else 'lowers'} concern",
            "is_weekend": f"{'Weekend' if value > 0 else 'Weekday'} transaction {impact} affects {direction}",
            "failed_attempts": f"{int(value)} failed attempt(s) {impact} {'increase' if shap_value > 0 else 'decrease'} risk",
            "is_new_device": f"{'New' if value > 0 else 'Known'} device {impact} {'raises' if shap_value > 0 else 'lowers'} concern",
            "is_new_ip": f"{'New' if value > 0 else 'Known'} IP address {impact} {'raises' if shap_value > 0 else 'lowers'} concern",
            "transaction_frequency": f"Transaction frequency ({value:.1f}) {impact} contributes to {direction}",
            "amount_to_avg_ratio": f"Amount is {value:.1f}x the account average",
            "amount_deviation": f"Spending deviation of ₹{value:.2f} {impact} affects {direction}",
            "time_since_last_transaction": f"Time since last transaction ({value:.1f}h) {impact} affects {direction}",
            "device_usage_count": f"Device used {int(value)} time(s) {impact} affects {direction}",
            "ip_usage_count": f"IP used {int(value)} time(s) {impact} affects {direction}",
            "velocity_score": f"Transaction velocity {impact} contributes to {direction}",
            "behavioural_score": f"Behavioural pattern {impact} contributes to {direction}",
            "device_ip_interaction": f"{'Both device and IP are new' if value > 0 else 'Familiar device/IP combination'}",
        }

        return messages.get(feature_name,
                           f"{FEATURE_DESCRIPTIONS.get(feature_name, feature_name)} {impact} contributes to {direction}")

    def _fallback_explanation(self, features_df, top_n):
        """Fallback when SHAP is unavailable — use feature importance."""
        feature_names = features_df.columns.tolist()
        feature_values = features_df.iloc[0].values

        # Use absolute feature values as rough importance
        abs_vals = np.abs(feature_values)
        indices = np.argsort(abs_vals)[::-1][:top_n]

        explanations = []
        for idx in indices:
            feat_name = feature_names[idx]
            feat_val = float(feature_values[idx])
            description = FEATURE_DESCRIPTIONS.get(feat_name, feat_name)

            explanations.append({
                "feature": feat_name,
                "description": description,
                "shap_value": 0.0,
                "feature_value": round(feat_val, 4),
                "direction": "notable",
                "impact": "medium",
                "message": f"{description}: {feat_val:.4f}",
            })

        return {"factors": explanations, "base_value": 0.0, "method": "feature_values"}
