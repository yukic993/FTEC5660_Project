import pandas as pd
from math import radians, sin, cos, sqrt, atan2

def monitor_transaction(
    user_id,
    amount,
    payment_type,
    receiver_id,
    receiver_country,
    sender_country,
    device_id,
    login_attempts,
    time_since_last_txn,
    hour
):
    df = pd.read_csv("transactions.csv")

    user_history = df[df["user_id"] == user_id]

    if user_history.empty:
        raise ValueError("No history found for this user.")

    known_receivers = user_history["receiver_id"].tolist()
    known_devices = user_history["device_id"].tolist()

    avg_amount = user_history["amount"].mean()
    normal_country = user_history["receiver_country"].mode()[0]


    features = {
        "new_receiver": receiver_id not in known_receivers,
        "new_device": device_id not in known_devices,
        "large_amount": amount > avg_amount * 5,
        "international_transfer": receiver_country != sender_country,
        "late_night": 0 <= hour <= 5,
        "many_login_attempts": login_attempts >= 3,
        "rapid_transfer": time_since_last_txn < 10,
        "high_risk_payment_rail": payment_type.upper() == "SWIFT"
    }

    return features