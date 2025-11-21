from langchain_openai import ChatOpenAI
from app.core.config import settings

def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0
    )

VALIDATOR_PROMPT = """You are a tax validation assistant. Review the following tax calculation and identify any anomalies or concerns.

Tax Calculation Summary:
- Gross Income: ${gross_income:,.2f}
- Standard Deduction: ${standard_deduction:,.2f}
- Taxable Income: ${taxable_income:,.2f}
- Tax Liability: ${tax_liability:,.2f}
- Total Withholding: ${total_withholding:,.2f}
- Result: {status} of ${refund_or_owed:,.2f}

Filing Status: {filing_status}

Review this calculation and respond with:
1. "VALID" if everything looks reasonable
2. "WARNING: [specific concern]" if you notice any anomalies (e.g., unusually high/low withholding, negative values where unexpected)
3. "MISSING: [required information]" if critical data is missing

Keep your response concise and actionable."""

