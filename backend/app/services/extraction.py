from typing import Union, Tuple, List, Optional, Any
from pathlib import Path
from app.services.document_intelligence import get_document_intelligence_service
from app.schemas.schemas import W2Data, NEC1099Data, INT1099Data

def _get_field_value(fields: dict, field_name: str, value_attr: str = "content") -> Optional[Any]:
    if field_name not in fields:
        return None
    field = fields[field_name]
    return getattr(field, value_attr, None)

def map_w2_fields(fields: dict) -> W2Data:
    employee = _get_field_value(fields, "Employee", "value_object")
    employer = _get_field_value(fields, "Employer", "value_object")
    
    return W2Data(
        tax_year=_get_field_value(fields, "TaxYear", "value_string"),
        employee_ssn=_get_field_value(employee, "SocialSecurityNumber", "value_string") if employee else None,
        employee_name=_get_field_value(employee, "Name", "value_string") if employee else None,
        employer_ein=_get_field_value(employer, "IdNumber", "value_string") if employer else None,
        employer_name=_get_field_value(employer, "Name", "value_string") if employer else None,
        wages_tips_other_compensation=_get_field_value(fields, "WagesTipsAndOtherCompensation", "value_number"),
        federal_income_tax_withheld=_get_field_value(fields, "FederalIncomeTaxWithheld", "value_number"),
        social_security_wages=_get_field_value(fields, "SocialSecurityWages", "value_number"),
        social_security_tax_withheld=_get_field_value(fields, "SocialSecurityTaxWithheld", "value_number"),
        medicare_wages_and_tips=_get_field_value(fields, "MedicareWagesAndTips", "value_number"),
        medicare_tax_withheld=_get_field_value(fields, "MedicareTaxWithheld", "value_number")
    )

def map_1099nec_fields(fields: dict) -> NEC1099Data:
    payer = _get_field_value(fields, "Payer", "value_object")
    recipient = _get_field_value(fields, "Recipient", "value_object")
    
    return NEC1099Data(
        tax_year=_get_field_value(fields, "TaxYear", "value_string"),
        payer_tin=_get_field_value(payer, "TIN", "value_string") if payer else None,
        payer_name=_get_field_value(payer, "Name", "value_string") if payer else None,
        recipient_tin=_get_field_value(recipient, "TIN", "value_string") if recipient else None,
        recipient_name=_get_field_value(recipient, "Name", "value_string") if recipient else None,
        nonemployee_compensation=_get_field_value(fields, "Box1", "value_number"),
        federal_income_tax_withheld=_get_field_value(fields, "Box4", "value_number")
    )

def map_1099int_fields(fields: dict) -> INT1099Data:
    payer = _get_field_value(fields, "Payer", "value_object")
    recipient = _get_field_value(fields, "Recipient", "value_object")
    
    transactions = _get_field_value(fields, "Transactions", "value_array")
    first_transaction = None
    if transactions and len(transactions) > 0:
        first_transaction = getattr(transactions[0], "value_object", None)
    
    return INT1099Data(
        tax_year=_get_field_value(fields, "TaxYear", "value_string"),
        payer_tin=_get_field_value(payer, "TIN", "value_string") if payer else None,
        payer_name=_get_field_value(payer, "Name", "value_string") if payer else None,
        recipient_tin=_get_field_value(recipient, "TIN", "value_string") if recipient else None,
        recipient_name=_get_field_value(recipient, "Name", "value_string") if recipient else None,
        interest_income=_get_field_value(first_transaction, "Box1", "value_number") if first_transaction else None,
        early_withdrawal_penalty=_get_field_value(first_transaction, "Box2", "value_number") if first_transaction else None,
        interest_on_us_savings_bonds=_get_field_value(first_transaction, "Box3", "value_number") if first_transaction else None,
        federal_income_tax_withheld=_get_field_value(first_transaction, "Box4", "value_number") if first_transaction else None,
        investment_expenses=_get_field_value(first_transaction, "Box5", "value_number") if first_transaction else None,
        foreign_tax_paid=_get_field_value(first_transaction, "Box6", "value_number") if first_transaction else None
    )

def _normalize_document_type(doc_type_raw: str) -> str:
    if doc_type_raw == "other":
        return "other"
    
    if "." in doc_type_raw:
        parts = doc_type_raw.split(".")
        return ".".join(parts[:3]) if len(parts) >= 3 else doc_type_raw
    
    return doc_type_raw

def _infer_document_type_from_fields(fields: dict) -> str:
    if "WagesTipsAndOtherCompensation" in fields or "Employee" in fields:
        return "tax.us.w2"
    elif "Box1" in fields:
        if "InterestIncome" in str(fields) or "Transactions" in fields:
            return "tax.us.1099INT"
        return "tax.us.1099NEC"
    
    raise ValueError("Cannot determine document type from 'other' classification")

def process_document(pdf_path: str | Path) -> Tuple[str, Union[W2Data, NEC1099Data, INT1099Data], List[str]]:
    warnings = []
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    service = get_document_intelligence_service()
    result = service.analyze_tax_document(pdf_bytes)
    
    if not result.documents:
        raise ValueError("No documents detected in PDF")
    
    doc = result.documents[0]
    doc_type_raw = doc.doc_type
    
    if not hasattr(doc, 'fields') or doc.fields is None:
        raise ValueError(f"No fields extracted from document type: {doc_type_raw}")
    
    doc_type = _normalize_document_type(doc_type_raw)
    
    if doc_type == "other":
        warnings.append("Document classified as 'other', attempting to infer type from fields")
        doc_type = _infer_document_type_from_fields(doc.fields)
    
    try:
        if doc_type.startswith("tax.us.w2"):
            extracted_data = map_w2_fields(doc.fields)
            normalized_type = "tax.us.w2"
        elif doc_type.startswith("tax.us.1099NEC"):
            extracted_data = map_1099nec_fields(doc.fields)
            normalized_type = "tax.us.1099NEC"
        elif doc_type.startswith("tax.us.1099INT"):
            extracted_data = map_1099int_fields(doc.fields)
            normalized_type = "tax.us.1099INT"
        else:
            raise ValueError(f"Unsupported document type: {doc_type_raw}")
    except Exception as e:
        raise ValueError(f"Error mapping fields for {doc_type_raw}: {str(e)}")
    
    return normalized_type, extracted_data, warnings

