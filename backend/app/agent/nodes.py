from sqlalchemy.orm import Session
from app.agent.state import TaxState
from app.services.tax_aggregator import aggregate_tax_data
from app.services.tax_service import TaxService
from app.agent.llm import get_llm, VALIDATOR_PROMPT

def aggregator_node(state: TaxState, db: Session) -> TaxState:
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
                if not state.get("tax_year"):
                    missing_fields.append("tax_year")
            else:
                extracted_year = list(extracted_years)[0]
                if not state.get("tax_year"):
                    state["tax_year"] = extracted_year
    
    # Validate Mandatory Fields presence
    mandatory_personal_fields = ["filer_name", "filer_ssn", "home_address", "digital_assets", "occupation"]
    for field in mandatory_personal_fields:
        if not personal_info.get(field):
            missing_fields.append(field)
            
    state["personal_info"] = personal_info
    
    if not state.get("filing_status"):
        missing_fields.append("filing_status")
        
    if not state.get("tax_year"):
        missing_fields.append("tax_year")
    elif state["tax_year"] != "2024":
        state["warnings"].append(f"⚠️ Tax year {state['tax_year']} is not supported. This system only supports 2024 tax calculations.")
        state["status"] = "error"
        return state
    
    if missing_fields:
        state["missing_fields"] = missing_fields
        state["status"] = "waiting_for_user"
        return state

    try:
        tax_input = aggregate_tax_data(state["session_id"], db)
        
        aggregated = {
            "total_wages": tax_input.total_wages,
            "total_interest": tax_input.total_interest,
            "total_nec_income": tax_input.total_nec_income,
            "total_withholding": tax_input.total_withholding,
        }
        
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
        
        gross_income = aggregated["total_wages"] + aggregated["total_interest"] + aggregated["total_nec_income"]
        
        if gross_income == 0:
            missing_fields.append("income_data")
            state["warnings"].append("No income data found in extracted documents. Please provide income information.")
        
        state["aggregated_data"] = aggregated
        
        if missing_fields:
            state["missing_fields"] = missing_fields
            state["status"] = "waiting_for_user"
        else:
            state["status"] = "aggregated"
        
    except Exception as e:
        state["warnings"].append(f"Aggregation error: {str(e)}")
        state["status"] = "error"
    
    return state

def calculator_node(state: TaxState, db: Session) -> TaxState:
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
        
    except Exception as e:
        state["warnings"].append(f"Calculation error: {str(e)}")
        state["status"] = "error"
    
    return state

def validator_node(state: TaxState) -> TaxState:
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
        
        state["status"] = "validated"
        
    except Exception as e:
        state["warnings"].append(f"Validation error: {str(e)}")
        state["status"] = "error"
    
    return state

