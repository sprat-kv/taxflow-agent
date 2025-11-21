from sqlalchemy.orm import Session
from app.models.models import ExtractionResult
from app.schemas.schemas import TaxInput, W2Data, NEC1099Data, INT1099Data

def aggregate_w2_data(extraction_results: list[ExtractionResult]) -> tuple[float, float]:
    total_wages = 0.0
    total_withholding = 0.0
    
    for result in extraction_results:
        if result.document_type == "tax.us.w2":
            try:
                w2_data = W2Data(**result.structured_data)
                
                if w2_data.wages_tips_other_compensation:
                    total_wages += w2_data.wages_tips_other_compensation
                
                if w2_data.federal_income_tax_withheld:
                    total_withholding += w2_data.federal_income_tax_withheld
                    
            except Exception:
                continue
    
    return total_wages, total_withholding

def aggregate_1099nec_data(extraction_results: list[ExtractionResult]) -> tuple[float, float]:
    total_nec_income = 0.0
    total_withholding = 0.0
    
    for result in extraction_results:
        if result.document_type == "tax.us.1099NEC":
            try:
                nec_data = NEC1099Data(**result.structured_data)
                
                if nec_data.nonemployee_compensation:
                    total_nec_income += nec_data.nonemployee_compensation
                
                if nec_data.federal_income_tax_withheld:
                    total_withholding += nec_data.federal_income_tax_withheld
                    
            except Exception:
                continue
    
    return total_nec_income, total_withholding

def aggregate_1099int_data(extraction_results: list[ExtractionResult]) -> tuple[float, float]:
    total_interest = 0.0
    total_withholding = 0.0
    
    for result in extraction_results:
        if result.document_type == "tax.us.1099INT":
            try:
                int_data = INT1099Data(**result.structured_data)
                
                if int_data.interest_income:
                    total_interest += int_data.interest_income
                
                if int_data.federal_income_tax_withheld:
                    total_withholding += int_data.federal_income_tax_withheld
                    
            except Exception:
                continue
    
    return total_interest, total_withholding

def aggregate_tax_data(session_id: str, db: Session) -> TaxInput:
    from app.models.models import UploadSession, Document
    
    db_session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not db_session:
        raise ValueError(f"Session {session_id} not found")
    
    extraction_results = []
    for document in db_session.documents:
        if document.extraction_result:
            extraction_results.append(document.extraction_result)
    
    if not extraction_results:
        raise ValueError(f"No extraction results found for session {session_id}")
    
    w2_wages, w2_withholding = aggregate_w2_data(extraction_results)
    nec_income, nec_withholding = aggregate_1099nec_data(extraction_results)
    interest, int_withholding = aggregate_1099int_data(extraction_results)
    
    return TaxInput(
        total_wages=w2_wages,
        total_interest=interest,
        total_nec_income=nec_income,
        total_withholding=w2_withholding + nec_withholding + int_withholding
    )

