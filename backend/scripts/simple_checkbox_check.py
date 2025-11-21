"""
Simple script to generate a numbered checkbox reference PDF.
Each checkbox will be checked in order from 01 to 37.
"""
from pypdf import PdfReader, PdfWriter
from pathlib import Path

def create_numbered_checkbox_pdf():
    """Generate a single PDF with all checkboxes checked and numbered."""
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        print(f"Error: Template not found at {template_path}")
        return
    
    print(f"Reading template: {template_path.absolute()}")
    reader = PdfReader(template_path)
    
    # Read the checkbox manifest to get all checkbox names and their On values
    manifest_path = Path("test_output/checkbox_tests/checkbox_manifest.txt")
    
    checkboxes = []
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line and line[0].isdigit() and '. ' in line:
                    # Parse number and name
                    num_str, name = line.split('. ', 1)
                    num = int(num_str)
                    
                    # Get the On Value from next line
                    on_value = "/1"  # default
                    if i + 1 < len(lines) and "On Value:" in lines[i + 1]:
                        on_value = lines[i + 1].split("On Value:")[1].strip()
                    
                    checkboxes.append({
                        "num": num,
                        "name": name,
                        "on_value": on_value
                    })
                i += 1
    else:
        print(f"Warning: Manifest not found at {manifest_path}")
        return
    
    print(f"Found {len(checkboxes)} checkboxes from manifest\n")
    
    # Create writer
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)
    
    # Prepare values: all checkboxes checked with their proper On values
    field_values = {}
    for cb in checkboxes:
        field_values[cb["name"]] = cb["on_value"]
    
    # Update all pages
    for page in writer.pages:
        writer.update_page_form_field_values(page, field_values)
    
    # Save output
    output_dir = Path("test_output/checkbox_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "ALL_CHECKBOXES_NUMBERED.pdf"
    
    with open(output_file, "wb") as f:
        writer.write(f)
    
    print(f"[OK] Generated: {output_file.name}")
    print(f"[OK] Location: {output_file.absolute()}")
    print("\nINSTRUCTIONS:")
    print("1. Open the PDF to see ALL checkboxes checked")
    print("2. Use the checkbox_manifest.txt to match numbers to field names")
    print("3. Update 1040_field_mapping_template.json with descriptions")
    print("\nCheckbox list:")
    for cb in checkboxes:
        print(f"  {cb['num']:02d}. {cb['name']}")

if __name__ == "__main__":
    create_numbered_checkbox_pdf()

