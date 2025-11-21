from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_size: int

class DocumentRead(DocumentBase):
    id: str
    status: str
    upload_timestamp: datetime
    
    class Config:
        from_attributes = True

class UploadSessionBase(BaseModel):
    pass

class UploadSessionRead(UploadSessionBase):
    id: str
    created_at: datetime
    status: str
    documents: List[DocumentRead] = []

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    session_id: str
    documents: List[DocumentRead]

class W2Data(BaseModel):
    tax_year: Optional[str] = None
    employee_ssn: Optional[str] = None
    employee_name: Optional[str] = None
    employer_ein: Optional[str] = None
    employer_name: Optional[str] = None
    wages_tips_other_compensation: Optional[float] = None
    federal_income_tax_withheld: Optional[float] = None
    social_security_wages: Optional[float] = None
    social_security_tax_withheld: Optional[float] = None
    medicare_wages_and_tips: Optional[float] = None
    medicare_tax_withheld: Optional[float] = None

class NEC1099Data(BaseModel):
    tax_year: Optional[str] = None
    payer_tin: Optional[str] = None
    payer_name: Optional[str] = None
    recipient_tin: Optional[str] = None
    recipient_name: Optional[str] = None
    nonemployee_compensation: Optional[float] = None
    federal_income_tax_withheld: Optional[float] = None

class INT1099Data(BaseModel):
    tax_year: Optional[str] = None
    payer_tin: Optional[str] = None
    payer_name: Optional[str] = None
    recipient_tin: Optional[str] = None
    recipient_name: Optional[str] = None
    interest_income: Optional[float] = None
    early_withdrawal_penalty: Optional[float] = None
    interest_on_us_savings_bonds: Optional[float] = None
    federal_income_tax_withheld: Optional[float] = None
    investment_expenses: Optional[float] = None
    foreign_tax_paid: Optional[float] = None

class ExtractionResultRead(BaseModel):
    id: str
    document_id: str
    document_type: str
    structured_data: dict
    warnings: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaxInput(BaseModel):
    total_wages: float = 0.0
    total_interest: float = 0.0
    total_nec_income: float = 0.0
    total_withholding: float = 0.0
    
class TaxCalculationResult(BaseModel):
    gross_income: float
    standard_deduction: float
    taxable_income: float
    tax_liability: float
    total_withholding: float
    refund_or_owed: float
    status: str

class PersonalInfo(BaseModel):
    """
    Personal information for tax processing.
    
    **Mandatory fields for aggregator function:**
    - filer_name: Full name of the tax filer
    - filer_ssn: Social Security Number
    - home_address: Complete home address
    - occupation: Occupation/employment
    - digital_assets: Answer about digital assets (yes/no/other)
    
    **Optional fields:**
    - phone: Phone number
    """
    filer_name: Optional[str] = None
    filer_ssn: Optional[str] = None
    home_address: Optional[str] = None
    occupation: Optional[str] = None
    digital_assets: Optional[str] = None
    phone: Optional[str] = None

class UserInputs(BaseModel):
    """Optional user inputs to override extracted values"""
    total_wages: Optional[float] = None
    total_interest: Optional[float] = None
    total_nec_income: Optional[float] = None
    total_withholding: Optional[float] = None

class ProcessSessionRequest(BaseModel):
    """
    Request structure for processing a tax session.
    
    All fields are optional to support incremental updates, but for a complete initial request,
    the following fields are mandatory for the aggregator function to proceed:
    
    **Mandatory Fields for Initial Request:**
    - filing_status: Tax filing status - Valid values: "single", "married_filing_jointly", "head_of_household"
    - tax_year: Tax year (currently only "2024" is supported)
    - personal_info.filer_name: Full name of the tax filer
    - personal_info.filer_ssn: Social Security Number of the filer (format: XXX-XX-XXXX)
    - personal_info.home_address: Complete home address (street, city, state, ZIP)
    - personal_info.occupation: Occupation/employment description
    - personal_info.digital_assets: Answer regarding digital assets - Valid values: "yes", "no", or other descriptive text
    
    **Optional Fields:**
    - personal_info.phone: Phone number (format: XXX-XXX-XXXX or (XXX) XXX-XXXX)
    - user_inputs.total_wages: Override total wages from W2 forms (float)
    - user_inputs.total_interest: Override total interest income from 1099-INT forms (float)
    - user_inputs.total_nec_income: Override total non-employee compensation from 1099-NEC forms (float)
    - user_inputs.total_withholding: Override total federal tax withheld (float)
    
    **Complete Example Request (All Fields):**
    {
        "filing_status": "single",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "John Michael Doe",
            "filer_ssn": "123-45-6789",
            "home_address": "123 Main Street, Apt 4B, New York, NY 10001",
            "occupation": "Software Engineer",
            "digital_assets": "no",
            "phone": "(555) 123-4567"
        },
        "user_inputs": {
            "total_wages": 75000.50,
            "total_interest": 125.75,
            "total_nec_income": 5000.00,
            "total_withholding": 8500.25
        }
    }
    
    **Minimal Initial Request (Only Mandatory Fields):**
    {
        "filing_status": "single",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "Jane Smith",
            "filer_ssn": "987-65-4321",
            "home_address": "456 Oak Avenue, Los Angeles, CA 90001",
            "occupation": "Teacher",
            "digital_assets": "yes"
        }
    }
    
    **Example Incremental Update (to provide missing fields):**
    {
        "personal_info": {
            "filer_ssn": "123-45-6789",
            "home_address": "123 Main Street, New York, NY 10001"
        }
    }
    
    **Example with Different Filing Status:**
    {
        "filing_status": "married_filing_jointly",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "Robert and Sarah Johnson",
            "filer_ssn": "111-22-3333",
            "home_address": "789 Elm Drive, Chicago, IL 60601",
            "occupation": "Accountant",
            "digital_assets": "no",
            "phone": "312-555-7890"
        }
    }
    """
    filing_status: Optional[str] = None
    tax_year: Optional[str] = None
    personal_info: Optional[PersonalInfo] = None
    user_inputs: Optional[UserInputs] = None

class AgentLog(BaseModel):
    timestamp: str
    node: str
    message: str
    type: str

class ProcessSessionResponse(BaseModel):
    status: str
    message: Optional[str] = None
    missing_fields: Optional[List[str]] = None
    aggregated_data: Optional[dict] = None
    calculation_result: Optional[dict] = None
    validation_result: Optional[str] = None
    warnings: Optional[List[str]] = None
    logs: Optional[List[AgentLog]] = None
    current_step: Optional[str] = None

