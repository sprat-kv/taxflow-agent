"""
Test script for Form 1040 PDF generation with updated field mappings.
"""
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app.db.session import SessionLocal
from app.services.form_1040_service import Form1040Service
from app.models.models import WorkflowState, UploadSession
import json

def test_1040_generation():
    """Test Form 1040 PDF generation."""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("FORM 1040 PDF GENERATION TEST")
        print("=" * 80)
        
        # Get a completed session
        print("\n1. Finding a completed session...")
        workflow_state = db.query(WorkflowState).filter(
            WorkflowState.status == "validated"
        ).first()
        
        if not workflow_state:
            print("   ERROR: No validated sessions found.")
            print("   Please run the complete workflow first (upload -> extract -> process)")
            return
        
        session_id = workflow_state.session_id
        print(f"   Found session: {session_id}")
        print(f"   Status: {workflow_state.status}")
        
        # Display the state data
        state_data = workflow_state.state_data
        print("\n2. State Data:")
        print(f"   Filing Status: {state_data.get('filing_status')}")
        print(f"   Tax Year: {state_data.get('tax_year')}")
        
        personal_info = state_data.get("personal_info", {})
        print("\n3. Personal Information:")
        print(f"   Name: {personal_info.get('filer_name')}")
        print(f"   SSN: {personal_info.get('filer_ssn')}")
        print(f"   Address: {personal_info.get('home_address')}")
        print(f"   Occupation: {personal_info.get('occupation')}")
        
        aggregated_data = state_data.get("aggregated_data", {})
        print("\n4. Aggregated Financial Data:")
        print(f"   Total Wages: ${aggregated_data.get('total_wages', 0):,.2f}")
        print(f"   Total Interest: ${aggregated_data.get('total_interest', 0):,.2f}")
        print(f"   Total 1099-NEC: ${aggregated_data.get('total_nec_income', 0):,.2f}")
        print(f"   Total Withholding: ${aggregated_data.get('total_withholding', 0):,.2f}")
        
        calc_result = state_data.get("calculation_result", {})
        print("\n5. Tax Calculation Results:")
        print(f"   Gross Income: ${calc_result.get('gross_income', 0):,.2f}")
        print(f"   Standard Deduction: ${calc_result.get('standard_deduction', 0):,.2f}")
        print(f"   Taxable Income: ${calc_result.get('taxable_income', 0):,.2f}")
        print(f"   Tax Liability: ${calc_result.get('tax_liability', 0):,.2f}")
        print(f"   Total Withholding: ${calc_result.get('total_withholding', 0):,.2f}")
        print(f"   Refund/Owed: ${calc_result.get('refund_or_owed', 0):,.2f}")
        print(f"   Status: {calc_result.get('status')}")
        
        # Generate the PDF
        print("\n6. Generating Form 1040 PDF...")
        try:
            output_path = Form1040Service.generate_1040(session_id, db)
            print(f"   SUCCESS! PDF generated at:")
            print(f"   {output_path.absolute()}")
            print(f"   File size: {output_path.stat().st_size:,} bytes")
        except Exception as e:
            print(f"   ERROR generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
        # Display field mapping summary
        print("\n7. Field Mapping Summary:")
        print("   The following fields were mapped:")
        print("   - Personal: Name (f1_04, f1_05), SSN (f1_06)")
        print("   - Address: Street (f1_10), City (f1_12), State (f1_13), ZIP (f1_14)")
        print("   - Income: Wages (f1_32), Interest (f1_43), 1099-NEC (f1_53), Total (f1_54)")
        print("   - Deductions: AGI (f1_56), Std Deduction (f1_57), Taxable (f1_60)")
        print("   - Tax: Tax Amount (f2_02), Total Tax (f2_10)")
        print("   - Payments: Withholding (f2_11), Total (f2_22)")
        print("   - Result: Refund (f2_23) or Owed (f2_28)")
        print("   - Other: Occupation (f2_33), Phone (f2_37)")
        
        print("\n" + "=" * 80)
        print("INSTRUCTIONS:")
        print("=" * 80)
        print("1. Open the generated PDF")
        print("2. Verify all text fields are filled correctly")
        print("3. Check that values match the amounts shown above")
        print("4. Note: Filing status checkbox is NOT filled (skipped as requested)")
        print("=" * 80)
        
    finally:
        db.close()

if __name__ == "__main__":
    test_1040_generation()

