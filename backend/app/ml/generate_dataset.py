"""
Synthetic fraud dataset generator.
Creates realistic transaction data with fraud patterns.
"""
import numpy as np
import pandas as pd
import os
import uuid
from datetime import datetime, timedelta


def generate_dataset(n_samples=20000, fraud_rate=0.05, output_path=None):
    """Generate a realistic synthetic fraud dataset."""
    np.random.seed(42)

    n_fraud = int(n_samples * fraud_rate)
    n_legit = n_samples - n_fraud

    # Generate accounts, devices, IPs, merchants
    n_accounts = max(200, n_samples // 50)
    n_devices = max(150, n_samples // 60)
    n_ips = max(300, n_samples // 40)
    n_merchants = 50

    accounts = [f"ACC-{str(i).zfill(5)}" for i in range(n_accounts)]
    devices = [f"DEV-{str(i).zfill(5)}" for i in range(n_devices)]
    ips = [f"{np.random.randint(1,255)}.{np.random.randint(0,255)}.{np.random.randint(0,255)}.{np.random.randint(1,255)}" for i in range(n_ips)]
    merchant_codes = [f"MER-{str(i).zfill(4)}" for i in range(n_merchants)]

    records = []

    # Generate legitimate transactions
    for i in range(n_legit):
        acct = np.random.choice(accounts)
        dev = np.random.choice(devices[:n_devices // 2])  # legit users use fewer devices
        ip = np.random.choice(ips[:n_ips // 2])
        merchant = np.random.choice(merchant_codes)

        # Normal transaction patterns
        amount = np.random.lognormal(mean=3.5, sigma=1.0)
        amount = min(amount, 5000)
        amount = round(amount, 2)

        hour = int(np.random.choice(range(6, 23), p=_business_hours_dist()))
        day_offset = int(np.random.randint(0, 90))
        minute = int(np.random.randint(0, 60))
        timestamp = datetime(2024, 1, 1) + timedelta(days=day_offset, hours=int(hour), minutes=minute)

        failed_attempts = 0 if np.random.random() > 0.05 else np.random.randint(1, 3)
        is_new_device = 1 if np.random.random() < 0.08 else 0
        is_new_ip = 1 if np.random.random() < 0.10 else 0
        tx_freq = np.random.exponential(2.0)
        avg_amount = amount * np.random.uniform(0.7, 1.3)
        time_since_last = np.random.exponential(24.0)
        merchant_freq = np.random.exponential(3.0)
        device_count = np.random.randint(1, 20)
        ip_count = np.random.randint(1, 15)

        records.append({
            "transaction_id": str(uuid.uuid4()),
            "account_id": acct,
            "device_id": dev,
            "ip_address": ip,
            "merchant_id": merchant,
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "failed_attempts": failed_attempts,
            "is_new_device": is_new_device,
            "is_new_ip": is_new_ip,
            "transaction_frequency": round(tx_freq, 4),
            "account_average_amount": round(avg_amount, 2),
            "time_since_last_transaction": round(time_since_last, 4),
            "merchant_frequency": round(merchant_freq, 4),
            "device_usage_count": device_count,
            "ip_usage_count": ip_count,
            "fraud_label": 0,
        })

    # Generate fraudulent transactions with distinct patterns
    fraud_accounts = np.random.choice(accounts, size=max(20, n_accounts // 10), replace=False)
    for i in range(n_fraud):
        acct = np.random.choice(fraud_accounts)
        dev = np.random.choice(devices[n_devices // 2:])  # fraudsters use uncommon devices
        ip = np.random.choice(ips[n_ips // 2:])
        merchant = np.random.choice(merchant_codes[:10])  # target specific merchants

        # Fraudulent patterns
        pattern = np.random.choice(["high_amount", "rapid_fire", "unusual_time",
                                     "new_everything", "mixed"], p=[0.25, 0.2, 0.15, 0.2, 0.2])

        if pattern == "high_amount":
            amount = np.random.uniform(2000, 15000)
            hour = np.random.randint(0, 24)
            failed_attempts = np.random.randint(0, 3)
            is_new_device = np.random.choice([0, 1], p=[0.4, 0.6])
            is_new_ip = np.random.choice([0, 1], p=[0.4, 0.6])
            tx_freq = np.random.exponential(5.0)
            time_since_last = np.random.exponential(2.0)

        elif pattern == "rapid_fire":
            amount = np.random.uniform(50, 800)
            hour = np.random.randint(0, 24)
            failed_attempts = np.random.randint(1, 6)
            is_new_device = np.random.choice([0, 1])
            is_new_ip = np.random.choice([0, 1])
            tx_freq = np.random.uniform(8, 30)
            time_since_last = np.random.uniform(0.01, 1.0)

        elif pattern == "unusual_time":
            amount = np.random.lognormal(mean=4.5, sigma=0.8)
            hour = np.random.choice([0, 1, 2, 3, 4, 5])
            failed_attempts = np.random.randint(0, 4)
            is_new_device = np.random.choice([0, 1], p=[0.5, 0.5])
            is_new_ip = np.random.choice([0, 1], p=[0.3, 0.7])
            tx_freq = np.random.exponential(3.0)
            time_since_last = np.random.exponential(1.0)

        elif pattern == "new_everything":
            amount = np.random.uniform(200, 5000)
            hour = np.random.randint(0, 24)
            failed_attempts = np.random.randint(2, 7)
            is_new_device = 1
            is_new_ip = 1
            tx_freq = np.random.uniform(0.1, 2.0)
            time_since_last = np.random.uniform(0.001, 0.5)

        else:  # mixed
            amount = np.random.uniform(500, 8000)
            hour = np.random.randint(0, 24)
            failed_attempts = np.random.randint(1, 5)
            is_new_device = np.random.choice([0, 1], p=[0.3, 0.7])
            is_new_ip = np.random.choice([0, 1], p=[0.3, 0.7])
            tx_freq = np.random.exponential(6.0)
            time_since_last = np.random.exponential(1.5)

        amount = round(amount, 2)
        avg_amount = amount * np.random.uniform(0.2, 0.5)
        merchant_freq = np.random.exponential(1.0)
        device_count = np.random.randint(1, 5)
        ip_count = np.random.randint(1, 4)

        day_offset = int(np.random.randint(0, 90))
        minute = int(np.random.randint(0, 60))
        timestamp = datetime(2024, 1, 1) + timedelta(days=day_offset, hours=int(hour), minutes=minute)

        records.append({
            "transaction_id": str(uuid.uuid4()),
            "account_id": acct,
            "device_id": dev,
            "ip_address": ip,
            "merchant_id": merchant,
            "amount": amount,
            "timestamp": timestamp.isoformat(),
            "failed_attempts": failed_attempts,
            "is_new_device": is_new_device,
            "is_new_ip": is_new_ip,
            "transaction_frequency": round(tx_freq, 4),
            "account_average_amount": round(avg_amount, 2),
            "time_since_last_transaction": round(time_since_last, 4),
            "merchant_frequency": round(merchant_freq, 4),
            "device_usage_count": device_count,
            "ip_usage_count": ip_count,
            "fraud_label": 1,
        })

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "model_artifacts", "dataset.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset generated: {len(df)} samples ({n_fraud} fraud, {n_legit} legitimate)")
    print(f"Fraud rate: {fraud_rate * 100:.1f}%")
    print(f"Saved to: {output_path}")
    return df


def _business_hours_dist():
    """Probability distribution for business hours (6-22)."""
    hours = list(range(6, 23))
    probs = [0.02, 0.03, 0.05, 0.08, 0.10, 0.10, 0.09,
             0.08, 0.08, 0.07, 0.06, 0.05, 0.04, 0.04,
             0.04, 0.04, 0.03]
    total = sum(probs)
    return [p / total for p in probs]


if __name__ == "__main__":
    generate_dataset()
