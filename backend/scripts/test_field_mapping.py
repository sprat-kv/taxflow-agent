"""
Visual test script to fill Form 1040 fields one at a time.
This helps identify which field corresponds to which textbox on the form.
"""
from pypdf import PdfReader, PdfWriter
from pathlib import Path

def test_field(field_name: str, test_value: str = "TEST_VALUE"):
    """
    Fill a single field with a test value and save PDF.
    
    Args:
        field_name: PDF field name (e.g., "f1_01[0]")
        test_value: Value to fill in the field
    """
    # Find template
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    # Create output directory
    output_dir = Path("test_output/field_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate PDF with single field filled
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)
    
    writer.update_page_form_field_values(
        writer.pages[0],
        {field_name: test_value}
    )
    
    # Save with descriptive filename
    safe_name = field_name.replace("[", "_").replace("]", "")
    output_file = output_dir / f"{safe_name}_{test_value}.pdf"
    
    with open(output_file, "wb") as f:
        writer.write(f)
    
    print(f"✅ Created: {output_file.name}")
    print(f"   Field: {field_name}")
    print(f"   Value: {test_value}")
    print()

def test_key_fields():
    """Test the key fields we're currently using."""
    print("=" * 80)
    print("TESTING KEY FIELDS")
    print("=" * 80)
    print("\nGenerating test PDFs with individual fields filled...")
    print("Open each PDF to see which textbox the field corresponds to.\n")
    
    test_fields = {
        # Personal Info
        "f1_01[0]": "FIRST_NAME_TEST",
        "f1_02[0]": "LAST_NAME_TEST",
        "f1_03[0]": "123-45-6789",
        "f1_04[0]": "STREET_ADDRESS_TEST",
        "f1_05[0]": "CITY_STATE_ZIP_TEST",
        
        # Income
        "f1_10[0]": "50000.00",  # Line 1a - Wages
        "f1_12[0]": "1000.00",   # Line 2b - Interest
        "f1_19[0]": "20000.00",  # Line 8 - Other Income
        "f1_20[0]": "71000.00",  # Line 9 - Total Income
        
        # Deductions
        "f1_22[0]": "71000.00",  # Line 11 - AGI
        "f1_23[0]": "14600.00",  # Line 12 - Standard Deduction
        "f1_26[0]": "56400.00",  # Line 15 - Taxable Income
        
        # Tax
        "f1_27[0]": "5000.00",   # Line 16 - Tax
        "f1_35[0]": "5000.00",   # Line 24 - Total Tax
        
        # Payments
        "f1_36[0]": "6000.00",   # Line 25a - Withholding
        "f1_44[0]": "6000.00",   # Line 33 - Total Payments
        
        # Refund/Owe
        "f1_45[0]": "1000.00",   # Line 34 - Refund
        "f1_48[0]": "500.00",    # Line 37 - Amount Owed
        
        # Page 2
        "f2_08[0]": "OCCUPATION_TEST",
    }
    
    for field_name, test_value in test_fields.items():
        test_field(field_name, test_value)
    
    print("=" * 80)
    print("✅ All test PDFs generated!")
    print(f"📁 Location: {Path('test_output/field_tests').absolute()}")
    print("\nNext steps:")
    print("1. Open each PDF and identify which textbox contains the test value")
    print("2. Note the correct field-to-textbox mapping")
    print("3. Provide the corrected mapping")
    print("=" * 80)

if __name__ == "__main__":
    test_key_fields()

