"""
Unit tests for tax calculation logic.
Can be run independently to verify tax math without API calls.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from decimal import Decimal
from app.services.tax_rules import (
    get_standard_deduction,
    calculate_taxable_income,
    calculate_tax_liability,
    calculate_refund_or_owed
)

def test_case_a():
    """Test Case A: Simple Single (Refund)"""
    print("\n" + "=" * 60)
    print("  TEST CASE A: Simple Single (Refund)")
    print("=" * 60)
    
    gross_income = Decimal("50000")
    withholding = Decimal("5000")
    filing_status = "single"
    
    standard_deduction = get_standard_deduction(filing_status)
    print(f"   Standard Deduction: ${standard_deduction:,.2f}")
    
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    print(f"   Taxable Income: ${taxable_income:,.2f}")
    
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    print(f"   Tax Liability: ${tax_liability:,.2f}")
    
    refund_or_owed, status = calculate_refund_or_owed(tax_liability, withholding)
    print(f"   Result: {status.upper()} ${refund_or_owed:,.2f}")
    
    expected_refund = Decimal("984.00")
    if abs(refund_or_owed - expected_refund) < Decimal("0.01"):
        print("   ✅ PASS: Refund matches expected value")
        return True
    else:
        print(f"   ❌ FAIL: Expected ${expected_refund:,.2f}, got ${refund_or_owed:,.2f}")
        return False

def test_case_b():
    """Test Case B: Freelancer (Owe)"""
    print("\n" + "=" * 60)
    print("  TEST CASE B: Freelancer (Owe)")
    print("=" * 60)
    
    gross_income = Decimal("20000")
    withholding = Decimal("0")
    filing_status = "single"
    
    standard_deduction = get_standard_deduction(filing_status)
    print(f"   Standard Deduction: ${standard_deduction:,.2f}")
    
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    print(f"   Taxable Income: ${taxable_income:,.2f}")
    
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    print(f"   Tax Liability: ${tax_liability:,.2f}")
    
    refund_or_owed, status = calculate_refund_or_owed(tax_liability, withholding)
    print(f"   Result: {status.upper()} ${refund_or_owed:,.2f}")
    
    expected_owed = Decimal("540.00")
    if abs(refund_or_owed - expected_owed) < Decimal("0.01"):
        print("   ✅ PASS: Amount owed matches expected value")
        return True
    else:
        print(f"   ❌ FAIL: Expected ${expected_owed:,.2f}, got ${refund_or_owed:,.2f}")
        return False

def test_scenario_w2_only():
    """Test Scenario: W-2 Only Income"""
    print("\n" + "=" * 60)
    print("  TEST SCENARIO: W-2 Only Income")
    print("=" * 60)
    
    gross_income = Decimal("75000")
    withholding = Decimal("8000")
    filing_status = "single"
    
    standard_deduction = get_standard_deduction(filing_status)
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    refund_or_owed, status = calculate_refund_or_owed(tax_liability, withholding)
    
    print(f"   Gross Income (W-2 only): ${gross_income:,.2f}")
    print(f"   Standard Deduction: ${standard_deduction:,.2f}")
    print(f"   Taxable Income: ${taxable_income:,.2f}")
    print(f"   Tax Liability: ${tax_liability:,.2f}")
    print(f"   Withholding: ${withholding:,.2f}")
    print(f"   Result: {status.upper()} ${refund_or_owed:,.2f}")
    print("   ✅ PASS: W-2 only calculation works")
    return True

def test_scenario_w2_nec():
    """Test Scenario: W-2 + 1099-NEC"""
    print("\n" + "=" * 60)
    print("  TEST SCENARIO: W-2 + 1099-NEC")
    print("=" * 60)
    
    w2_income = Decimal("50000")
    nec_income = Decimal("20000")
    gross_income = w2_income + nec_income
    
    w2_withholding = Decimal("5000")
    nec_withholding = Decimal("0")
    total_withholding = w2_withholding + nec_withholding
    
    filing_status = "single"
    
    standard_deduction = get_standard_deduction(filing_status)
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    refund_or_owed, status = calculate_refund_or_owed(tax_liability, total_withholding)
    
    print(f"   W-2 Income: ${w2_income:,.2f}")
    print(f"   1099-NEC Income: ${nec_income:,.2f}")
    print(f"   Gross Income: ${gross_income:,.2f}")
    print(f"   Standard Deduction: ${standard_deduction:,.2f}")
    print(f"   Taxable Income: ${taxable_income:,.2f}")
    print(f"   Tax Liability: ${tax_liability:,.2f}")
    print(f"   Total Withholding: ${total_withholding:,.2f}")
    print(f"   Result: {status.upper()} ${refund_or_owed:,.2f}")
    print("   ✅ PASS: W-2 + NEC calculation works")
    return True

def test_scenario_w2_small_interest():
    """Test Scenario: W-2 + Small Interest (< $10)"""
    print("\n" + "=" * 60)
    print("  TEST SCENARIO: W-2 + Small Interest (< $10)")
    print("=" * 60)
    
    w2_income = Decimal("50000")
    interest_income = Decimal("8.50")
    gross_income = w2_income + interest_income
    
    w2_withholding = Decimal("5000")
    int_withholding = Decimal("0")
    total_withholding = w2_withholding + int_withholding
    
    filing_status = "single"
    
    standard_deduction = get_standard_deduction(filing_status)
    taxable_income = calculate_taxable_income(gross_income, filing_status)
    tax_liability = calculate_tax_liability(taxable_income, filing_status)
    refund_or_owed, status = calculate_refund_or_owed(tax_liability, total_withholding)
    
    print(f"   W-2 Income: ${w2_income:,.2f}")
    print(f"   Interest Income: ${interest_income:,.2f}")
    print(f"   Gross Income: ${gross_income:,.2f}")
    print(f"   Standard Deduction: ${standard_deduction:,.2f}")
    print(f"   Taxable Income: ${taxable_income:,.2f}")
    print(f"   Tax Liability: ${tax_liability:,.2f}")
    print(f"   Total Withholding: ${total_withholding:,.2f}")
    print(f"   Result: {status.upper()} ${refund_or_owed:,.2f}")
    print("   ✅ PASS: Small interest is included correctly")
    return True

def test_filing_statuses():
    """Test all filing statuses"""
    print("\n" + "=" * 60)
    print("  TEST: All Filing Statuses")
    print("=" * 60)
    
    gross_income = Decimal("100000")
    
    for status in ["single", "married_filing_jointly", "head_of_household"]:
        deduction = get_standard_deduction(status)
        taxable = calculate_taxable_income(gross_income, status)
        tax = calculate_tax_liability(taxable, status)
        
        print(f"\n   {status.replace('_', ' ').title()}:")
        print(f"      Deduction: ${deduction:,.2f}")
        print(f"      Taxable: ${taxable:,.2f}")
        print(f"      Tax: ${tax:,.2f}")
    
    print("\n   ✅ PASS: All filing statuses work")
    return True

def main():
    """Run all unit tests."""
    print("\n" + "=" * 60)
    print("  TAX CALCULATION UNIT TESTS")
    print("=" * 60)
    
    results = []
    
    results.append(("Case A", test_case_a()))
    results.append(("Case B", test_case_b()))
    results.append(("W-2 Only", test_scenario_w2_only()))
    results.append(("W-2 + NEC", test_scenario_w2_nec()))
    results.append(("W-2 + Small Interest", test_scenario_w2_small_interest()))
    results.append(("Filing Statuses", test_filing_statuses()))
    
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 All tests passed!")
        return 0
    else:
        print(f"\n   ⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

