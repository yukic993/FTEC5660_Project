import os
import time
import json
import pandas as pd
from datetime import datetime
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool

# --- Logger Functions (from ipynb) ---
def log(section: str, message: str):
    ts = datetime.utcnow().strftime("%H:%M:%S")
    print(f"[{ts}] [{section}] {message}")

def pretty(obj: Any, max_len: int = 800):
    text = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    return text if len(text) <= max_len else text[:max_len] + "\n...<truncated>"

# --- 1. Define Tools ---
@tool
def monitor_transaction(user_id: str, amount: float, payment_type: str, receiver_id: str,
                        receiver_country: str, sender_country: str, device_id: str,
                        login_attempts: int, time_since_last_txn: int, hour: int) -> dict:
    """Monitors a transaction against user history and returns a dictionary of detected risk features."""
    try:
        df = pd.read_csv("transactions.csv")
    except FileNotFoundError:
        return {"error": "transactions.csv file not found."}

    user_history = df[df["user_id"] == user_id]
    if user_history.empty:
        return {"error": f"No history found for user {user_id}."}

    known_receivers = user_history["receiver_id"].tolist()
    known_devices = user_history["device_id"].tolist()
    avg_amount = user_history["amount"].mean()

    features = {
        "new_receiver": receiver_id not in known_receivers,
        "new_device": device_id not in known_devices,
        "large_amount": amount > (avg_amount * 5),
        "international_transfer": receiver_country != sender_country,
        "late_night": 0 <= hour <= 5,
        "many_login_attempts": login_attempts >= 3,
        "rapid_transfer": time_since_last_txn < 10,
        "high_risk_payment_rail": payment_type.upper() == "SWIFT"
    }
    return features

@tool
def assess_risk(features: dict) -> dict:
    """Assesses the risk of a transaction based on detected features."""
    if "error" in features:
        return features

    score = 0
    if features.get("new_receiver"): score += 2
    if features.get("new_device"): score += 2
    if features.get("large_amount"): score += 2
    if features.get("international_transfer"): score += 1
    if features.get("late_night"): score += 2
    if features.get("many_login_attempts"): score += 2
    if features.get("rapid_transfer"): score += 1
    if features.get("high_risk_payment_rail"): score += 1

    if score <= 2:
        risk, action = "LOW", "APPROVE"
    elif score <= 5:
        risk, action = "MEDIUM", "REVIEW"
    else:
        risk, action = "HIGH", "BLOCK"

    return {"risk": risk, "action": action, "score": score}

SYSTEM_PROMPT = """
You are an AI fraud analyst working for a bank.
You have access to tools to evaluate transactions.

Step 1: Use `monitor_transaction` to extract risk features.
Step 2: Pass those features into `assess_risk` to get the final score, risk level, and action.
Step 3: Write a clear explanation of why this transaction is suspicious or safe based on the tool outputs.

Rules for final output:
- Explain the specific triggered features.
- Keep the explanation under 100 words.
- End exactly with: 'Recommendation: <action>'
"""

# --- 2. The Agent Loop (Modeled after Moltbook IPYNB) ---
def run_fraud_agent_loop(transaction_data: dict, api_key: str, max_turns: int = 5):
    log("INIT", "Starting manual fraud agent loop")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        vertexai=True,
        temperature=0.2,
        api_key=api_key,
    )

    tools = [monitor_transaction, assess_risk]
    
    # Structure the tool call by binding them to the LLM
    agent = llm.bind_tools(tools)
    
    # Initialize message history
    history = [
        ("system", SYSTEM_PROMPT),
        ("human", f"Please analyze this transaction: {json.dumps(transaction_data)}")
    ]

    # Main Agent execution loop
    for turn in range(1, max_turns + 1):
        log("TURN", f"Turn {turn}/{max_turns} started")
        turn_start = time.time()

        # 1. Ask Gemini
        response = agent.invoke(history)
        history.append(response)

        # 2. Stop Condition: If Gemini doesn't request a tool, it's done!
        if not response.tool_calls:
            elapsed = round(time.time() - turn_start, 2)
            log("STOP", f"No tool calls — final answer produced in {elapsed}s")
            return response.content

        # 3. Tool Execution: If Gemini requests a tool, run it
        for i, call in enumerate(response.tool_calls, start=1):
            tool_name = call["name"]
            args = call["args"]
            tool_id = call["id"]

            log("TOOL", f"[{i}] Calling `{tool_name}`")
            log("TOOL.ARGS", pretty(args))

            # Execute actual python function
            if tool_name == "monitor_transaction":
                result = monitor_transaction.invoke(args)
            elif tool_name == "assess_risk":
                result = assess_risk.invoke(args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            log("TOOL.RESULT", pretty(result))

            # 4. Append tool result back to history so Gemini can read it
            history.append(
                ToolMessage(
                    tool_call_id=tool_id,
                    content=str(result),
                )
            )

    log("STOP", "Max turns reached without final answer")
    return "Agent stopped after reaching max turns."