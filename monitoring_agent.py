import os
import json
import pandas as pd
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

api_key=os.getenv("GEMINI_API_KEY")

# Setup Gemini via LangChain
llm = ChatGoogleGenerativeAI(
     model="gemini-2.5-flash",
     api_key=api_key,
     vertexai=True,
     temperature=0.2
 )
    
parser = StrOutputParser()

# -------- Prompt --------
prompt_template = PromptTemplate(
    input_variables=[
        "amount",
        "payment_type",
        "receiver_id",
        "receiver_country",
        "sender_country",
        "device_id",
        "login_attempts",
        "time_since_last_txn",
        "hour",
        "known_receivers",
        "known_devices",
        "avg_amount"
    ],
    template="""
You are a fraud monitoring agent.

Use BOTH transaction details AND historical behaviour.

Historical Context:
- Known Receivers: {known_receivers}
- Known Devices: {known_devices}
- Average Amount: {avg_amount}

Transaction:
- Amount: ${amount}
- Payment Type: {payment_type}
- Receiver: {receiver_id}
- Receiver Country: {receiver_country}
- Sender Country: {sender_country}
- Device ID: {device_id}
- Login Attempts: {login_attempts}
- Time Since Last Transaction: {time_since_last_txn} minutes
- Hour: {hour}

Rules:
- new_receiver = receiver not in known receivers
- new_device = device not in known devices
- large_amount = amount > 5x average
- international_transfer = sender != receiver country
- late_night = hour between 0 to 5
- many_login_attempts = >=3
- rapid_transfer = <10 minutes
- high_risk_payment_rail = SWIFT

Return ONLY JSON:
{{
  "new_receiver": true/false,
  "new_device": true/false,
  "large_amount": true/false,
  "international_transfer": true/false,
  "late_night": true/false,
  "many_login_attempts": true/false,
  "rapid_transfer": true/false,
  "high_risk_payment_rail": true/false
}}
"""
)

chain = prompt_template | llm | parser

# -------- Main Function --------
def monitor_transaction(data: dict):
    # Load transaction history
    df = pd.read_csv("transactions_expanded.csv")

    user_id = data["user_id"]
    user_history = df[df["user_id"] == user_id]

    if user_history.empty:
        raise ValueError(f"No history found for user {user_id}")

    # Extract historical patterns
    known_receivers = user_history["receiver_id"].unique().tolist()
    known_devices = user_history["device_id"].unique().tolist()
    avg_amount = user_history["amount"].mean()

    # Call LLM
    response = chain.invoke({
        **data,
        "known_receivers": known_receivers,
        "known_devices": known_devices,
        "avg_amount": round(avg_amount, 2)
    })

    # -------- Clean LLM Output (CRITICAL) --------
    response = response.strip()
    response = response.replace("```json", "").replace("```", "").strip()

    start = response.find("{")
    end = response.rfind("}") + 1
    response = response[start:end]

    try:
        features = json.loads(response)
    except:
        raise ValueError("LLM did not return valid JSON:\n" + response)

    return features