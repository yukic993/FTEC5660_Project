import os
import json
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
        "hour"
    ],
    template="""
You are a fraud monitoring agent.

Analyze the transaction and output ONLY JSON.

Transaction:
- Amount: £{amount}
- Payment Type: {payment_type}
- Receiver: {receiver_id}
- Receiver Country: {receiver_country}
- Sender Country: {sender_country}
- Device ID: {device_id}
- Login Attempts: {login_attempts}
- Time Since Last Transaction: {time_since_last_txn} minutes
- Hour: {hour}

Return JSON with:
- new_receiver (true/false)
- new_device (true/false)
- large_amount (true/false)
- international_transfer (true/false)
- late_night (true/false)
- many_login_attempts (true/false)
- rapid_transfer (true/false)
- high_risk_payment_rail (true/false)

Do not include explanation. Only JSON.
"""
)

chain = prompt_template | llm | parser


def monitor_transaction(data: dict):
    response = chain.invoke(data)
    response = response.strip()

    if response.startswith("```"):
        response = response.replace("```json", "").replace("```", "").strip()


    try:
        features = json.loads(response)
    except:
        raise ValueError("LLM did not return valid JSON:\n" + response)

    return features