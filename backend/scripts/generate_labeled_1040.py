"""
Script to generate Form 1040 PDF with ALL fields labeled (text + checkboxes).
This helps identify which field corresponds to which element on the form.
"""
from pypdf import PdfReader, PdfWriter
from pathlib import Path
import json

def generate_complete_labeled_pdf():
    """Generate PDF with all fields (text + checkboxes) labeled."""
    # Find template
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"Reading template from: {template_path.absolute()}\n")
    
    reader = PdfReader(template_path)
    
    # Get text fields
    text_fields = reader.get_form_text_fields() or {}
    print(f"Found {len(text_fields)} text fields")
    
    # Get all form fields including checkboxes from AcroForm
    all_field_names = set(text_fields.keys())
    checkbox_fields = []
    
    # Try to find checkboxes by accessing form fields directly
    try:
        if hasattr(reader, 'trailer') and reader.trailer:
            root = reader.trailer.get('/Root', {})
            if '/AcroForm' in root:
                acro_form = root['/AcroForm']
                if '/Fields' in acro_form:
                    fields_array = acro_form['/Fields']
                    
                    def find_checkboxes(field_ref, parent_name=""):
                        """Recursively find all checkbox fields."""
                        if hasattr(field_ref, 'get_object'):
                            field_obj = field_ref.get_object()
                        else:
                            field_obj = field_ref
                        
                        field_type = field_obj.get('/FT')
                        field_name = str(field_obj.get('/T', ''))
                        
                        if field_type == '/Btn':  # Button/Checkbox
                            full_name = f"{parent_name}.{field_name}" if parent_name else field_name
                            # Also check if it's in the simple format we use
                            if field_name.startswith('c1_'):
                                checkbox_fields.append(field_name)
                            else:
                                checkbox_fields.append(full_name)
                        
                        # Check kids (nested fields)
                        if '/Kids' in field_obj:
                            new_parent = f"{parent_name}.{field_name}" if field_name else parent_name
                            for kid in field_obj['/Kids']:
                                find_checkboxes(kid, new_parent)
                    
                    for field_ref in fields_array:
                        find_checkboxes(field_ref)
    except Exception as e:
        print(f"Note: Could not fully inspect AcroForm structure: {e}")
        print("Will use known checkbox patterns (c1_*)")
    
    # Add known checkbox patterns if not found
    known_checkboxes = [f"c1_0{i}[0]" for i in range(1, 6)]  # c1_01 through c1_05
    for cb in known_checkboxes:
        if cb not in checkbox_fields:
            checkbox_fields.append(cb)
    
    print(f"Found {len(checkbox_fields)} checkbox fields")
    print(f"Checkboxes: {checkbox_fields}\n")
    
    # Create writer
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)
    
    # Prepare field values
    field_values = {}
    
    # Fill text fields with their field names
    for field_name in sorted(text_fields.keys()):
        field_values[field_name] = field_name
    
    # Fill checkboxes - check them all so you can see which ones are checkboxes
    # Since checkboxes don't display text, we'll check them all
    # You'll need to identify which checkbox corresponds to which field name
    # by checking the individual checkbox test PDFs
    for i, cb_name in enumerate(checkbox_fields, 1):
        # Set checkbox to checked state
        field_values[cb_name] = "/Yes"
    
    print(f"Filling {len(field_values)} total fields...")
    print(f"  - {len(text_fields)} text fields")
    print(f"  - {len(checkbox_fields)} checkboxes\n")
    
    # Update all pages
    num_pages = len(writer.pages)
    print(f"Updating fields on {num_pages} page(s)...\n")
    
    for page_num in range(num_pages):
        writer.update_page_form_field_values(
            writer.pages[page_num],
            field_values
        )
    
    # Save output
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "Form_1040_ALL_FIELDS_LABELED.pdf"
    
    with open(output_file, "wb") as f:
        writer.write(f)
    
    print("=" * 80)
    print("✅ PDF GENERATED SUCCESSFULLY!")
    print("=" * 80)
    print(f"\n📁 Output file: {output_file.absolute()}")
    print(f"📄 File size: {output_file.stat().st_size:,} bytes")
    print("\n📋 What to look for:")
    print("1. TEXT FIELDS: Each textbox shows its field name (e.g., 'f1_01[0]')")
    print("2. CHECKBOXES: All checkboxes will be CHECKED (☑️) in this PDF")
    print("   - To identify which checkbox is which, run:")
    print("     python scripts/create_checkbox_reference.py")
    print("   - This creates individual PDFs with one checkbox checked at a time")
    print("\n📝 Instructions:")
    print("1. Open the generated PDF to see text field names")
    print("2. Run create_checkbox_reference.py to identify checkboxes")
    print("3. Map each field to its description")
    print("4. Update 1040_field_mapping_template.json with descriptions")
    print("\n💡 Tip: Checkboxes use '/Yes' to check, '/Off' to uncheck")
    print("=" * 80)
    
    # Also create a checkbox mapping file
    checkbox_file = Path("1040_checkbox_mapping.json")
    if not checkbox_file.exists():
        checkbox_file = Path("../1040_checkbox_mapping.json")
    
    checkbox_info = {
        "known_checkboxes": checkbox_fields,
        "note": "Checkboxes are set to '/Yes' to be checked, '/Off' to be unchecked",
        "mapping_template": {cb: "TODO: Describe what this checkbox represents" for cb in checkbox_fields}
    }
    
    with open(checkbox_file, "w", encoding="utf-8") as f:
        json.dump(checkbox_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Checkbox info saved to: {checkbox_file.absolute()}")

if __name__ == "__main__":
    import json
    generate_complete_labeled_pdf()
