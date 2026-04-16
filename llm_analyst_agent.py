import os
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
        "login_attempts",
        "time_since_last_txn",
        "new_receiver",
        "new_device",
        "large_amount",
        "international_transfer",
        "late_night",
        "many_login_attempts",
        "rapid_transfer",
        "high_risk_payment_rail",
        "risk",
        "action"
    ],
    template="""
You are an AI fraud analyst working for a bank.

Transaction Information:
- Amount: ${amount}
- Payment Type: {payment_type}
- Receiver: {receiver_id}
- Receiver Country: {receiver_country}
- Login Attempts: {login_attempts}
- Time Since Last Transaction: {time_since_last_txn} minutes

Detected Features:
- New Receiver: {new_receiver}
- New Device: {new_device}
- Large Amount: {large_amount}
- International Transfer: {international_transfer}
- Late Night: {late_night}
- Many Login Attempts: {many_login_attempts}
- Rapid Transfer: {rapid_transfer}
- High Risk Payment Rail: {high_risk_payment_rail}

Risk Level: {risk}
Recommended Action: {action}

Explain clearly why this transaction is suspicious or safe.
End with: Recommendation: <action>
Keep under 100 words.
"""
)


def generate_explanation(
    amount,
    payment_type,
    receiver_id,
    receiver_country,
    login_attempts,
    time_since_last_txn,
    features,
    risk,
    action
):
    # Flatten features 
    inputs = {
        "amount": amount,
        "payment_type": payment_type,
        "receiver_id": receiver_id,
        "receiver_country": receiver_country,
        "login_attempts": login_attempts,
        "time_since_last_txn": time_since_last_txn,
        "new_receiver": features["new_receiver"],
        "new_device": features["new_device"],
        "large_amount": features["large_amount"],
        "international_transfer": features["international_transfer"],
        "late_night": features["late_night"],
        "many_login_attempts": features["many_login_attempts"],
        "rapid_transfer": features["rapid_transfer"],
        "high_risk_payment_rail": features["high_risk_payment_rail"],
        "risk": risk,
        "action": action
    }

    chain = prompt_template | llm | parser

    response = chain.invoke(inputs)

    return response