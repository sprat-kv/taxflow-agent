from sqlalchemy.orm import Session
from datetime import datetime
from app.agent.state import TaxState
from app.services.tax_aggregator import aggregate_tax_data
from app.services.tax_service import TaxService
from app.agent.llm import get_llm, VALIDATOR_PROMPT

ADVISOR_PROMPT = """
Role: You are a friendly, knowledgeable, and empathetic AI Financial Advisor.

Task: Provide a personalized summary and actionable next steps based on the user's tax calculation.

User Data:
- Name: {filer_name}
- Total Income: ${gross_income}
- Outcome: {status} of ${refund_or_owed}
- Income Sources: {sources}
- Filing Status: {filing_status}

Guidelines:
1. **Tone**: Warm, professional, and encouraging.
2. **The Result**: Clearly state if they are getting a refund or owe money.
   - If Refund: Celebrate! Suggest a smart way to use it (savings, debt, investment).
   - If Owed: Be supportive. Provide the immediate next step (e.g., "Pay via IRS Direct Pay").
3. **The Tip**: Provide ONE specific, high-impact tax tip for next year based on their profile.
   - If Freelance (1099): Mention estimated quarterly payments or expense tracking.
   - If W-2 only: Mention adjusting W-4 withholding.
   - If High Income: Mention 401(k)/IRA contributions.

Output Format:
[Warm Greeting & Result Summary]

[Actionable Next Step / Payment Instruction]

Pro Tip: [The Specific Advice]
"""

def log_event(state: TaxState, node: str, message: str, type: str = "info"):
    if "logs" not in state:
        state["logs"] = []
    
    state["logs"].append({
        "timestamp": datetime.now().isoformat(),
        "node": node,
        "message": message,
        "type": type
    })

def aggregator_node(state: TaxState, db: Session) -> TaxState:
    state["current_step"] = "aggregating"
    log_event(state, "aggregator", "Starting document analysis and data aggregation...", "info")

    from app.models.models import UploadSession
    from app.schemas.schemas import W2Data, NEC1099Data, INT1099Data
    
    missing_fields = []
    personal_info = state.get("personal_info", {})
    
    extracted_name = None
    extracted_ssn = None
    extracted_address = None
    
    db_session = db.query(UploadSession).filter(UploadSession.id == state["session_id"]).first()
    if db_session:
        extracted_years = set()
        for document in db_session.documents:
            if document.extraction_result:
                doc_type = document.extraction_result.document_type
                structured_data = document.extraction_result.structured_data
                
                try:
                    if doc_type == "tax.us.w2":
                        w2_data = W2Data(**structured_data)
                        if w2_data.employee_name and not extracted_name:
                            extracted_name = w2_data.employee_name
                        if w2_data.employee_ssn and not extracted_ssn:
                            extracted_ssn = w2_data.employee_ssn
                        if w2_data.tax_year:
                            extracted_years.add(w2_data.tax_year)
                    elif doc_type == "tax.us.1099NEC":
                        nec_data = NEC1099Data(**structured_data)
                        if nec_data.recipient_name and not extracted_name:
                            extracted_name = nec_data.recipient_name
                        if nec_data.recipient_tin and not extracted_ssn:
                            extracted_ssn = nec_data.recipient_tin
                        if nec_data.tax_year:
                            extracted_years.add(nec_data.tax_year)
                    elif doc_type == "tax.us.1099INT":
                        int_data = INT1099Data(**structured_data)
                        if int_data.recipient_name and not extracted_name:
                            extracted_name = int_data.recipient_name
                        if int_data.recipient_tin and not extracted_ssn:
                            extracted_ssn = int_data.recipient_tin
                        if int_data.tax_year:
                            extracted_years.add(int_data.tax_year)
                except Exception:
                    pass
        
        if extracted_name and not personal_info.get("filer_name"):
            personal_info["filer_name"] = extracted_name
        if extracted_ssn and not personal_info.get("filer_ssn"):
            personal_info["filer_ssn"] = extracted_ssn
        if extracted_years:
            if len(extracted_years) > 1:
                state["warnings"].append(f"Multiple tax years detected in documents: {', '.join(sorted(extracted_years))}. Please specify which year to use.")
                log_event(state, "aggregator", f"Ambiguous tax year: Found {', '.join(sorted(extracted_years))}", "warning")
                if not state.get("tax_year"):
                    missing_fields.append("tax_year")
            else:
                extracted_year = list(extracted_years)[0]
                if not state.get("tax_year"):
                    state["tax_year"] = extracted_year
                    log_event(state, "aggregator", f"Identified Tax Year: {extracted_year}", "success")
    
    # Validate Mandatory Fields presence
    mandatory_personal_fields = ["filer_name", "filer_ssn", "home_address", "digital_assets", "occupation"]
    missing_personal_fields = []
    for field in mandatory_personal_fields:
        if not personal_info.get(field):
            missing_fields.append(field)
            missing_personal_fields.append(field)
            
    if missing_personal_fields:
        log_event(state, "aggregator", f"Missing personal details: {', '.join(missing_personal_fields)}", "warning")
            
    state["personal_info"] = personal_info
    
    if not state.get("filing_status"):
        missing_fields.append("filing_status")
        log_event(state, "aggregator", "Missing Filing Status", "warning")
        
    if not state.get("tax_year"):
        missing_fields.append("tax_year")
    elif state["tax_year"] != "2024":
        msg = f"⚠️ Tax year {state['tax_year']} is not supported. This system only supports 2024 tax calculations."
        state["warnings"].append(msg)
        log_event(state, "aggregator", msg, "error")
        state["status"] = "error"
        return state
    
    if missing_fields:
        state["missing_fields"] = missing_fields
        state["status"] = "waiting_for_user"
        log_event(state, "aggregator", f"Pausing workflow. Waiting for {len(missing_fields)} mandatory fields.", "warning")
        return state

    try:
        tax_input = aggregate_tax_data(state["session_id"], db)
        
        aggregated = {
            "total_wages": tax_input.total_wages,
            "total_interest": tax_input.total_interest,
            "total_nec_income": tax_input.total_nec_income,
            "total_withholding": tax_input.total_withholding,
        }
        
        log_event(state, "aggregator", f"Aggregated Income: Wages=${aggregated['total_wages']:,.2f}, NEC=${aggregated['total_nec_income']:,.2f}, Interest=${aggregated['total_interest']:,.2f}", "info")
        
        user_inputs = state.get("user_inputs", {})
        if user_inputs:
            if "total_wages" in user_inputs:
                aggregated["total_wages"] = float(user_inputs["total_wages"])
            if "total_interest" in user_inputs:
                aggregated["total_interest"] = float(user_inputs["total_interest"])
            if "total_nec_income" in user_inputs:
                aggregated["total_nec_income"] = float(user_inputs["total_nec_income"])
            if "total_withholding" in user_inputs:
                aggregated["total_withholding"] = float(user_inputs["total_withholding"])
            log_event(state, "aggregator", "Applied user manual overrides to financial data", "info")
        
        gross_income = aggregated["total_wages"] + aggregated["total_interest"] + aggregated["total_nec_income"]
        
        if gross_income == 0:
            missing_fields.append("income_data")
            state["warnings"].append("No income data found in extracted documents. Please provide income information.")
            log_event(state, "aggregator", "No income sources found in documents", "warning")
        
        state["aggregated_data"] = aggregated
        
        if missing_fields:
            state["missing_fields"] = missing_fields
            state["status"] = "waiting_for_user"
            log_event(state, "aggregator", "Income data missing. Pausing workflow.", "warning")
        else:
            state["status"] = "aggregated"
            log_event(state, "aggregator", "Data aggregation complete. Proceeding to calculation.", "success")
        
    except Exception as e:
        state["warnings"].append(f"Aggregation error: {str(e)}")
        log_event(state, "aggregator", f"Aggregation failed: {str(e)}", "error")
        state["status"] = "error"
    
    return state

def calculator_node(state: TaxState, db: Session) -> TaxState:
    state["current_step"] = "calculating"
    log_event(state, "calculator", "Starting tax liability calculation...", "info")
    try:
        result = TaxService.calculate_tax(
            state["session_id"],
            state["filing_status"],
            db
        )
        
        state["calculation_result"] = {
            "gross_income": result.gross_income,
            "standard_deduction": result.standard_deduction,
            "taxable_income": result.taxable_income,
            "tax_liability": result.tax_liability,
            "total_withholding": result.total_withholding,
            "refund_or_owed": result.refund_or_owed,
            "status": result.status
        }
        state["status"] = "calculated"
        
        log_event(state, "calculator", f"Calculation Complete. Taxable Income: ${result.taxable_income:,.2f}", "success")
        if result.status == "refund":
             log_event(state, "calculator", f"Estimated Refund: ${result.refund_or_owed:,.2f}", "success")
        else:
             log_event(state, "calculator", f"Estimated Tax Due: ${result.refund_or_owed:,.2f}", "info")
        
    except Exception as e:
        state["warnings"].append(f"Calculation error: {str(e)}")
        log_event(state, "calculator", f"Calculation failed: {str(e)}", "error")
        state["status"] = "error"
    
    return state

def validator_node(state: TaxState) -> TaxState:
    state["current_step"] = "validating"
    log_event(state, "validator", "AI Auditor reviewing calculation results...", "info")
    
    if not state.get("calculation_result"):
        state["warnings"].append("No calculation result to validate")
        state["status"] = "error"
        return state
    
    try:
        llm = get_llm()
        calc = state["calculation_result"]
        
        prompt = VALIDATOR_PROMPT.format(
            gross_income=calc["gross_income"],
            standard_deduction=calc["standard_deduction"],
            taxable_income=calc["taxable_income"],
            tax_liability=calc["tax_liability"],
            total_withholding=calc["total_withholding"],
            status=calc["status"],
            refund_or_owed=calc["refund_or_owed"],
            filing_status=state["filing_status"]
        )
        
        response = llm.invoke(prompt)
        validation_text = response.content
        
        state["validation_result"] = validation_text
        
        if "WARNING" in validation_text or "MISSING" in validation_text:
            state["warnings"].append(validation_text)
            log_event(state, "validator", "Audit flagged potential issues", "warning")
        else:
            log_event(state, "validator", "AI Audit Passed. Results look consistent.", "success")
        
        state["status"] = "validated"
        
    except Exception as e:
        state["warnings"].append(f"Validation error: {str(e)}")
        log_event(state, "validator", f"Validation failed: {str(e)}", "error")
        state["status"] = "error"
    
    return state

def advisor_node(state: TaxState) -> TaxState:
    state["current_step"] = "advising"
    log_event(state, "advisor", "Generating personalized financial advice...", "info")
    
    if state.get("status") == "error":
        return state
        
    try:
        llm = get_llm()
        calc = state["calculation_result"]
        personal_info = state["personal_info"]
        aggregated = state["aggregated_data"]
        
        # Determine income sources
        sources = []
        if aggregated.get("total_wages", 0) > 0: sources.append("W-2 (Employment)")
        if aggregated.get("total_nec_income", 0) > 0: sources.append("1099-NEC (Freelance)")
        if aggregated.get("total_interest", 0) > 0: sources.append("1099-INT (Interest)")
        sources_str = ", ".join(sources) if sources else "Unknown"
        
        prompt = ADVISOR_PROMPT.format(
            filer_name=personal_info.get("filer_name", "Valued Client"),
            gross_income=f"{calc['gross_income']:,.2f}",
            status=calc["status"].title(),
            refund_or_owed=f"{calc['refund_or_owed']:,.2f}",
            sources=sources_str,
            filing_status=state["filing_status"]
        )
        
        response = llm.invoke(prompt)
        state["advisor_feedback"] = response.content
        
        log_event(state, "advisor", "Advice generated successfully.", "success")
        state["status"] = "complete"
        
    except Exception as e:
        state["warnings"].append(f"Advisor error: {str(e)}")
        log_event(state, "advisor", f"Failed to generate advice: {str(e)}", "warning")
        # Don't fail the whole workflow just because advice failed
        state["status"] = "complete" 
        
    return state

