from typing import Union, Tuple, List
from pathlib import Path
from app.services.document_intelligence import get_document_intelligence_service
from app.schemas.schemas import W2Data, NEC1099Data, INT1099Data

def _get_field_value(fields: dict, field_name: str, value_attr: str = "content"):
    if field_name not in fields:
        return None
    field = fields[field_name]
    if value_attr == "value_number":
        return getattr(field, "value_number", None)
    elif value_attr == "value_string":
        return getattr(field, "value_string", None)
    elif value_attr == "value_object":
        return getattr(field, "value_object", None)
    return getattr(field, "content", None)

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
    first_transaction = transactions[0].value_object if transactions and len(transactions) > 0 else {}
    
    return INT1099Data(
        tax_year=_get_field_value(fields, "TaxYear", "value_string"),
        payer_tin=_get_field_value(payer, "TIN", "value_string") if payer else None,
        payer_name=_get_field_value(payer, "Name", "value_string") if payer else None,
        recipient_tin=_get_field_value(recipient, "TIN", "value_string") if recipient else None,
        recipient_name=_get_field_value(recipient, "Name", "value_string") if recipient else None,
        interest_income=_get_field_value(first_transaction, "Box1", "value_number"),
        early_withdrawal_penalty=_get_field_value(first_transaction, "Box2", "value_number"),
        interest_on_us_savings_bonds=_get_field_value(first_transaction, "Box3", "value_number"),
        federal_income_tax_withheld=_get_field_value(first_transaction, "Box4", "value_number"),
        investment_expenses=_get_field_value(first_transaction, "Box5", "value_number"),
        foreign_tax_paid=_get_field_value(first_transaction, "Box6", "value_number")
    )

def process_document(pdf_path: str | Path) -> Tuple[str, Union[W2Data, NEC1099Data, INT1099Data], List[str]]:
    warnings = []
    
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    service = get_document_intelligence_service()
    result = service.analyze_tax_document(pdf_bytes)
    
    if not result.documents:
        raise ValueError("No documents detected in PDF")
    
    doc = result.documents[0]
    doc_type = doc.doc_type
    
    if doc_type == "tax.us.w2":
        extracted_data = map_w2_fields(doc.fields)
    elif doc_type == "tax.us.1099NEC":
        extracted_data = map_1099nec_fields(doc.fields)
    elif doc_type == "tax.us.1099INT":
        extracted_data = map_1099int_fields(doc.fields)
    else:
        raise ValueError(f"Unsupported document type: {doc_type}")
    
    return doc_type, extracted_data, warnings

