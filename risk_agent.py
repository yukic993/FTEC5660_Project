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
    input_variables=["features"],
    template="""
You are a bank fraud risk assessment agent.

Your job is to calculate a risk score based on the rules below.

Scoring Rules:
- new_receiver = true → +2
- new_device = true → +2
- large_amount = true → +2
- many_login_attempts = true → +2
- international_transfer = true → +1
- late_night = true → +1
- rapid_transfer = true → +1
- high_risk_payment_rail = true → +1

Steps:
1. Read the features
2. Add the score based on the rules
3. Compute total score

Risk Levels:
- 0 to 2 → LOW
- 3 to 5 → MEDIUM
- 6+ → HIGH

Actions:
- LOW → APPROVE
- MEDIUM → REVIEW
- HIGH → BLOCK

Features:
{features}

Return ONLY JSON:
{{
  "score": number,
  "risk": "LOW | MEDIUM | HIGH",
  "action": "APPROVE | REVIEW | BLOCK",
  "reason": "short explanation referencing key features"
}}
"""
)

chain = prompt_template | llm | parser


def assess_risk(features: dict):
    response = chain.invoke({
        "features": json.dumps(features)
    })
    # 🔧 CLEAN RESPONSE (same as monitoring agent)
    response = response.strip()
    response = response.replace("```json", "").replace("```", "").strip()

    # Extract JSON safely
    start = response.find("{")
    end = response.rfind("}") + 1
    response = response[start:end]


    try:
        result = json.loads(response)
    except:
        raise ValueError("LLM did not return valid JSON:\n" + response)

    return result["risk"], result["action"], result["score"], result["reason"]