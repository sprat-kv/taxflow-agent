import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load env vars
load_dotenv(dotenv_path=".env")

# Mock Data
SCENARIO_REFUND = {
    "filer_name": "John Doe",
    "gross_income": 75000,
    "refund_or_owed": 1250.00,
    "status": "refund",
    "sources": "W-2 only",
    "filing_status": "single"
}

SCENARIO_OWED = {
    "filer_name": "Jane Smith",
    "gross_income": 120000,
    "refund_or_owed": 450.00,
    "status": "owed",
    "sources": "W-2 and 1099-NEC (Freelance)",
    "filing_status": "married_filing_jointly"
}

# --- Iteration 1: Base Prompt ---
PROMPT_V1 = """
You are a tax advisor.
The user has the following tax result:
Name: {filer_name}
Income: {gross_income}
Result: {status} of ${refund_or_owed}
Sources: {sources}

Give them advice.
"""

# --- Iteration 2: Improved Structure ---
PROMPT_V2 = """
You are a helpful and empathetic AI Tax Advisor.
Analyze the user's tax situation below:
- Name: {filer_name}
- Total Income: ${gross_income}
- Outcome: {status} of ${refund_or_owed}
- Income Sources: {sources}
- Filing Status: {filing_status}

Write a response in two parts:
1. Reaction: A personalized message about their result (Happy for refund, supportive for owing).
2. Advice: One actionable tip to improve their situation next year based on their specific income sources.
"""

# --- Iteration 3: Final Polish (Action-Oriented & Payment Steps) ---
PROMPT_V3 = """
Role: You are a friendly, knowledgeable, and empathetic AI Financial Advisor.

Task: Provide a personalized summary and actionable next steps based on the user's tax calculation.

User Data:
- Name: {filer_name}
- Total Income: ${gross_income}
- Outcome: {status} of ${refund_or_owed}
- Income Sources: {sources}
- Filing Status: {filing_status}

Guidelines:
1. **Tone**: Warm, professional, and encouraging. Use an emoji or two.
2. **The Result**: Clearly state if they are getting a refund or owe money.
   - If Refund: Celebrate! 🎉 Suggest a smart way to use it (savings, debt, investment).
   - If Owed: Be supportive. Provide the immediate next step (e.g., "Pay via IRS Direct Pay").
3. **The Tip**: Provide ONE specific, high-impact tax tip for next year based on their profile.
   - If Freelance (1099): Mention estimated quarterly payments or expense tracking.
   - If W-2 only: Mention adjusting W-4 withholding.
   - If High Income: Mention 401(k)/IRA contributions.

Output Format:
[Warm Greeting & Result Summary]

[Actionable Next Step / Payment Instruction]

💡 **Pro Tip:** [The Specific Advice]
"""

def test_prompts():
    # Attempt to use the user's requested model, fallback if needed or let library handle
    # Using 'gpt-4o-mini' as a safe high-quality proxy for testing the prompt logic
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    except:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    
    print("--- TESTING SCENARIO 1: REFUND ---")
    
    print("\n--- Prompt V1 (Base) ---")
    p1 = ChatPromptTemplate.from_template(PROMPT_V1)
    chain1 = p1 | llm
    try:
        print(chain1.invoke(SCENARIO_REFUND).content)
    except Exception as e:
        print(f"Error invoking chain 1: {e}")
    
    print("\n--- Prompt V2 (Structured) ---")
    p2 = ChatPromptTemplate.from_template(PROMPT_V2)
    chain2 = p2 | llm
    try:
        print(chain2.invoke(SCENARIO_REFUND).content)
    except Exception as e:
        print(f"Error invoking chain 2: {e}")
    
    print("\n--- Prompt V3 (Final) ---")
    p3 = ChatPromptTemplate.from_template(PROMPT_V3)
    chain3 = p3 | llm
    try:
        print(chain3.invoke(SCENARIO_REFUND).content)
    except Exception as e:
        print(f"Error invoking chain 3: {e}")

    print("\n\n--- TESTING SCENARIO 2: OWED ---")
    print("\n--- Prompt V3 (Final) Only ---")
    try:
        print(chain3.invoke(SCENARIO_OWED).content)
    except Exception as e:
        print(f"Error invoking chain 3 (Owed): {e}")

if __name__ == "__main__":
    test_prompts()

