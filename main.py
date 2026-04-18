from monitoring_agent import monitor_transaction
from risk_agent import assess_risk
from llm_analyst_agent import generate_explanation

print("=== Wire Transfer Scam Prevention Multi-Agent System ===")

# -------- Input --------
user_id = input("User ID: ")
amount = float(input("Amount ($): "))
payment_type = input("Payment Type (CHATS/FPS/SWIFT): ")
receiver_id = input("Receiver ID: ")
receiver_country = input("Receiver Country: ")
sender_country = input("Sender Country: ")
device_id = input("Device ID: ")
login_attempts = int(input("Login Attempts Before Transfer: "))
time_since_last_txn = int(input("Minutes Since Last Transaction: "))
hour = int(input("Hour of Transaction (0-23): "))

# -------- Prepare data for LLM --------
data = {
    "user_id": user_id,
    "amount": amount,
    "payment_type": payment_type,
    "receiver_id": receiver_id,
    "receiver_country": receiver_country,
    "sender_country": sender_country,
    "device_id": device_id,
    "login_attempts": login_attempts,
    "time_since_last_txn": time_since_last_txn,
    "hour": hour
}

# -------- Monitoring Agent --------
print("\n[1] Running Monitoring Agent (LLM)...")

features = monitor_transaction(data)

for key, value in features.items():
    print(f"{key}: {value}")

# -------- Risk Agent --------
print("\n[2] Running Risk Assessment Agent (LLM)...")

risk, action, score, reason = assess_risk(features)

print(f"Risk Score: {score}")
print(f"Risk Level: {risk}")
print(f"System Action: {action}")
print(f"Reason: {reason}")

# -------- LLM Analyst --------
print("\n[3] Running Gemini Fraud Analyst Agent...")

analysis = generate_explanation(
    amount=amount,
    payment_type=payment_type,
    receiver_id=receiver_id,
    receiver_country=receiver_country,
    login_attempts=login_attempts,
    time_since_last_txn=time_since_last_txn,
    features=features,
    risk=risk,
    action=action
)

print("\n=== AI Fraud Analysis ===")
print(analysis)