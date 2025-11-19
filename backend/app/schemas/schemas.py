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

