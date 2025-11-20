"""
Script to create a visual reference PDF showing checkbox locations.
Since checkboxes don't show text, this creates a numbered reference.
"""
from pypdf import PdfReader, PdfWriter
from pathlib import Path

def create_checkbox_reference():
    """Create PDFs with checkboxes checked one at a time for identification."""
    # Find template
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    reader = PdfReader(template_path)
    
    # Known checkbox fields (filing status and others)
    known_checkboxes = [
        "c1_01[0]",  # Likely Single
        "c1_02[0]",  # Likely Married Filing Jointly
        "c1_03[0]",  # Likely Married Filing Separately
        "c1_04[0]",  # Likely Head of Household
        "c1_05[0]",  # Likely Qualifying Surviving Spouse
    ]
    
    output_dir = Path("test_output/checkbox_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("CREATING CHECKBOX REFERENCE PDFs")
    print("=" * 80)
    print(f"\nCreating individual PDFs for each checkbox...\n")
    
    for i, cb_name in enumerate(known_checkboxes, 1):
        writer = PdfWriter()
        writer.clone_reader_document_root(reader)
        
        # Check only this checkbox
        writer.update_page_form_field_values(
            writer.pages[0],
            {cb_name: "/Yes"}
        )
        
        output_file = output_dir / f"checkbox_{i:02d}_{cb_name.replace('[', '_').replace(']', '')}.pdf"
        
        with open(output_file, "wb") as f:
            writer.write(f)
        
        print(f"✅ Created: {output_file.name}")
        print(f"   Checkbox: {cb_name}")
        print(f"   This checkbox will be CHECKED in this PDF")
        print()
    
    # Also create one with ALL checkboxes checked
    writer_all = PdfWriter()
    writer_all.clone_reader_document_root(reader)
    
    all_checkboxes = {cb: "/Yes" for cb in known_checkboxes}
    writer_all.update_page_form_field_values(writer_all.pages[0], all_checkboxes)
    
    output_all = output_dir / "ALL_CHECKBOXES_CHECKED.pdf"
    with open(output_all, "wb") as f:
        writer_all.write(f)
    
    print(f"✅ Created: {output_all.name}")
    print(f"   All checkboxes are checked in this PDF")
    print(f"   Use this to see all checkbox locations at once")
    
    print("\n" + "=" * 80)
    print("INSTRUCTIONS:")
    print("=" * 80)
    print("1. Open each individual checkbox PDF")
    print("2. Note which checkbox is checked (it will be marked with ☑️)")
    print("3. Identify what that checkbox represents on the form")
    print("4. Map it in your 1040_field_mapping_template.json")
    print("\nExample:")
    print('  "c1_01[0]": "Filing Status - Single"')
    print('  "c1_02[0]": "Filing Status - Married Filing Jointly"')
    print("=" * 80)

if __name__ == "__main__":
    create_checkbox_reference()

