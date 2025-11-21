from typing import Literal
from decimal import Decimal

FilingStatus = Literal["single", "married_filing_jointly", "head_of_household"]

STANDARD_DEDUCTIONS = {
    "single": Decimal("14600"),
    "married_filing_jointly": Decimal("29200"),
    "head_of_household": Decimal("21900"),
}

TAX_BRACKETS = {
    "single": [
        (Decimal("0.10"), Decimal("11600")),
        (Decimal("0.12"), Decimal("47150")),
        (Decimal("0.22"), Decimal("100525")),
        (Decimal("0.24"), Decimal("191950")),
        (Decimal("0.32"), Decimal("243725")),
        (Decimal("0.35"), Decimal("609350")),
        (Decimal("0.37"), None),  # No upper limit for highest bracket
    ],
    "married_filing_jointly": [
        (Decimal("0.10"), Decimal("23200")),
        (Decimal("0.12"), Decimal("94300")),
        (Decimal("0.22"), Decimal("201050")),
        (Decimal("0.24"), Decimal("383900")),
        (Decimal("0.32"), Decimal("487450")),
        (Decimal("0.35"), Decimal("731200")),
        (Decimal("0.37"), None),
    ],
    "head_of_household": [
        (Decimal("0.10"), Decimal("16550")),
        (Decimal("0.12"), Decimal("63100")),
        (Decimal("0.22"), Decimal("100500")),
        (Decimal("0.24"), Decimal("191950")),
        (Decimal("0.32"), Decimal("243700")),
        (Decimal("0.35"), Decimal("609350")),
        (Decimal("0.37"), None),
    ],
}

def get_standard_deduction(filing_status: FilingStatus) -> Decimal:
    if filing_status not in STANDARD_DEDUCTIONS:
        raise ValueError(f"Invalid filing status: {filing_status}")
    
    return STANDARD_DEDUCTIONS[filing_status]

def calculate_taxable_income(gross_income: Decimal, filing_status: FilingStatus) -> Decimal:
    standard_deduction = get_standard_deduction(filing_status)
    taxable_income = gross_income - standard_deduction
    
    return max(Decimal("0"), taxable_income)

def calculate_tax_liability(taxable_income: Decimal, filing_status: FilingStatus) -> Decimal:
    if filing_status not in TAX_BRACKETS:
        raise ValueError(f"Invalid filing status: {filing_status}")
    
    if taxable_income <= 0:
        return Decimal("0")
    
    brackets = TAX_BRACKETS[filing_status]
    total_tax = Decimal("0")
    remaining_income = taxable_income
    previous_limit = Decimal("0")
    
    for rate, upper_limit in brackets:
        if remaining_income <= 0:
            break
        
        if upper_limit is None:
            chunk = remaining_income
        else:
            chunk = min(remaining_income, upper_limit - previous_limit)
        
        tax_for_chunk = chunk * rate
        total_tax += tax_for_chunk
        remaining_income -= chunk
        
        if upper_limit is not None:
            previous_limit = upper_limit
    
    return total_tax.quantize(Decimal("0.01"))

def calculate_refund_or_owed(tax_liability: Decimal, total_withholding: Decimal) -> tuple[Decimal, str]:
    balance = tax_liability - total_withholding
    
    if balance < 0:
        return (abs(balance).quantize(Decimal("0.01")), "refund")
    elif balance > 0:
        return (balance.quantize(Decimal("0.01")), "owed")
    else:
        return (Decimal("0.00"), "even")

