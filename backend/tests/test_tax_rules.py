"""
Unit tests for tax calculation logic.
Tests verify 2024 tax rules against known scenarios.
"""
import pytest
from decimal import Decimal
from app.services.tax_rules import (
    get_standard_deduction,
    calculate_taxable_income,
    calculate_tax_liability,
    calculate_refund_or_owed,
)

def test_standard_deductions():
    """Test standard deduction amounts for each filing status."""
    assert get_standard_deduction("single") == Decimal("14600")
    assert get_standard_deduction("married_filing_jointly") == Decimal("29200")
    assert get_standard_deduction("head_of_household") == Decimal("21900")

def test_taxable_income_calculation():
    """Test taxable income calculation with standard deduction."""
    assert calculate_taxable_income(Decimal("50000"), "single") == Decimal("35400")
    assert calculate_taxable_income(Decimal("10000"), "single") == Decimal("0")
    assert calculate_taxable_income(Decimal("100000"), "married_filing_jointly") == Decimal("70800")

def test_case_a_simple_single_refund():
    """
    Test Case A from TAX_CALCULATOR.md
    Single, W-2 Wages: $50,000, Withholding: $5,000
    Expected: Refund of $984
    """
    gross_income = Decimal("50000")
    withholding = Decimal("5000")
    filing_status = "single"
    
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    assert taxable_income == Decimal("35400")
    
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    assert tax_liability == Decimal("4016.00")
    
    amount, status = calculate_refund_or_owed(tax_liability, withholding)
    assert status == "refund"
    assert amount == Decimal("984.00")

def test_case_b_freelancer_owe():
    """
    Test Case B from TAX_CALCULATOR.md
    Single, 1099-NEC: $20,000, No Withholding
    Expected: Owe $540
    """
    gross_income = Decimal("20000")
    withholding = Decimal("0")
    filing_status = "single"
    
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    assert taxable_income == Decimal("5400")
    
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    assert tax_liability == Decimal("540.00")
    
    amount, status = calculate_refund_or_owed(tax_liability, withholding)
    assert status == "owed"
    assert amount == Decimal("540.00")

def test_progressive_brackets_single():
    """Test progressive bracket calculation for single filer."""
    taxable_income = Decimal("100000")
    tax = calculate_tax_liability(taxable_income, "single")
    
    expected = (
        Decimal("11600") * Decimal("0.10") +
        (Decimal("47150") - Decimal("11600")) * Decimal("0.12") +
        (Decimal("100000") - Decimal("47150")) * Decimal("0.22")
    )
    assert tax == expected.quantize(Decimal("0.01"))

def test_zero_taxable_income():
    """Test that zero or negative taxable income results in zero tax."""
    assert calculate_tax_liability(Decimal("0"), "single") == Decimal("0")
    assert calculate_taxable_income(Decimal("5000"), "single") == Decimal("0")

def test_refund_owed_edge_cases():
    """Test edge cases for refund/owed calculation."""
    amount, status = calculate_refund_or_owed(Decimal("1000"), Decimal("1000"))
    assert status == "even"
    assert amount == Decimal("0.00")
    
    amount, status = calculate_refund_or_owed(Decimal("1000"), Decimal("1500"))
    assert status == "refund"
    assert amount == Decimal("500.00")
    
    amount, status = calculate_refund_or_owed(Decimal("1500"), Decimal("1000"))
    assert status == "owed"
    assert amount == Decimal("500.00")

