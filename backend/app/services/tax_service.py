from decimal import Decimal
from sqlalchemy.orm import Session
from app.schemas.schemas import TaxCalculationResult
from app.services.tax_aggregator import aggregate_tax_data
from app.services.tax_rules import (
    calculate_taxable_income,
    calculate_tax_liability,
    calculate_refund_or_owed,
    get_standard_deduction,
    FilingStatus
)

class TaxService:
    @staticmethod
    def calculate_tax(
        session_id: str, 
        filing_status: FilingStatus, 
        db: Session
    ) -> TaxCalculationResult:
        tax_input = aggregate_tax_data(session_id, db)
        
        gross_income = Decimal(str(
            tax_input.total_wages + 
            tax_input.total_interest + 
            tax_input.total_nec_income
        ))
        
        taxable_income = calculate_taxable_income(gross_income, filing_status)
        tax_liability = calculate_tax_liability(taxable_income, filing_status)
        total_withholding = Decimal(str(tax_input.total_withholding))
        refund_or_owed_amount, status = calculate_refund_or_owed(
            tax_liability, 
            total_withholding
        )
        standard_deduction = get_standard_deduction(filing_status)
        
        return TaxCalculationResult(
            gross_income=float(gross_income),
            standard_deduction=float(standard_deduction),
            taxable_income=float(taxable_income),
            tax_liability=float(tax_liability),
            total_withholding=float(total_withholding),
            refund_or_owed=float(refund_or_owed_amount),
            status=status
        )

