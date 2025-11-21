
"""
Script to create a visual reference PDF showing checkbox locations.
Refined to automatically detect checkboxes and their correct 'On' values.
"""
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from pathlib import Path
import json

def get_checkbox_export_value(field_data):
    """
    Determine the export value (On value) for a checkbox field.
    Returns the value to set to make it 'checked'.
    """
    # Method 1: Check /_States_ (pypdf helper)
    if '/_States_' in field_data:
        states = field_data['/_States_']
        for state in states:
            if state != '/Off':
                return state
                
    # Method 2: Check /AP /N dictionary keys
    if '/AP' in field_data and '/N' in field_data['/AP']:
        n_dict = field_data['/AP']['/N']
        if hasattr(n_dict, 'keys'): # It's a dictionary
            for key in n_dict.keys():
                if key != '/Off':
                    return key
                    
    # Method 3: Check /Opt (Options)
    if '/Opt' in field_data:
        opts = field_data['/Opt']
        if len(opts) > 0:
            return opts[0] # Return first option
            
    # Default fallback
    return '/Yes'

def create_checkbox_reference():
    """Create PDFs with checkboxes checked one at a time for identification."""
    # Find template
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"Reading template from: {template_path.absolute()}")
    reader = PdfReader(template_path)
    
    # 1. Discover all checkboxes and their values
    print("Scanning for checkboxes...")
    fields = reader.get_fields()
    checkboxes = []
    
    if fields:
        for field_name, field_data in fields.items():
            if field_data.get('/FT') == '/Btn':
                # Exclude push buttons if any (usually don't have on/off states like this)
                on_value = get_checkbox_export_value(field_data)
                
                # Simplify name for display if needed, but keep full name for filling
                short_name = field_name.split('.')[-1]
                
                checkboxes.append({
                    "full_name": field_name,
                    "short_name": short_name,
                    "on_value": on_value,
                    "page": 0 if "Page1" in field_name else (1 if "Page2" in field_name else -1)
                })
    
    print(f"Found {len(checkboxes)} checkboxes.")
    
    # Sort by page then name
    checkboxes.sort(key=lambda x: (x['page'], x['full_name']))
    
    output_dir = Path("test_output/checkbox_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Create "ALL CHECKED" PDF
    print("\nGenerating 'ALL_CHECKBOXES_CHECKED.pdf'...")
    writer_all = PdfWriter()
    writer_all.clone_reader_document_root(reader)
    
    # Prepare map of {full_name: on_value}
    all_values = {cb["full_name"]: cb["on_value"] for cb in checkboxes}
    
    # Update all pages
    for page in writer_all.pages:
        writer_all.update_page_form_field_values(page, all_values)
        
    output_all = output_dir / "ALL_CHECKBOXES_CHECKED.pdf"
    with open(output_all, "wb") as f:
        writer_all.write(f)
    print(f"[OK] Created: {output_all.name}")
    
    # 3. Create Manifest File
    manifest_path = output_dir / "checkbox_manifest.txt"
    with open(manifest_path, "w") as f:
        f.write("CHECKBOX MANIFEST\n")
        f.write("=================\n\n")
        for i, cb in enumerate(checkboxes, 1):
            f.write(f"{i:02d}. {cb['full_name']}\n")
            f.write(f"    On Value: {cb['on_value']}\n")
            f.write(f"    Short Name: {cb['short_name']}\n\n")
    print(f"[OK] Created manifest: {manifest_path.name}")
    
    # 4. Create Individual PDFs
    print(f"\nCreating {len(checkboxes)} individual PDFs...")
    
    for i, cb in enumerate(checkboxes, 1):
        writer = PdfWriter()
        writer.clone_reader_document_root(reader)
        
        # Update field
        # Note: We must update the correct page, or just try updating the field on the page object
        # Since update_page_form_field_values scans the page's annotations, we can run it on all pages
        # or just the one if we know it. To be safe, we'll run on all (it's fast enough).
        
        target_value = {cb["full_name"]: cb["on_value"]}
        
        for page in writer.pages:
            writer.update_page_form_field_values(page, target_value)
            
        # Create a safe filename
        safe_name = cb["short_name"].replace("[", "_").replace("]", "")
        filename = f"{i:02d}_{safe_name}.pdf"
        output_file = output_dir / filename
        
        with open(output_file, "wb") as f:
            writer.write(f)
            
        # Print progress every 5 files
        if i % 5 == 0:
            print(f"   Created {i}/{len(checkboxes)}...")

    print(f"\n[OK] Process complete. Check {output_dir.absolute()}")
    print("\nINSTRUCTIONS:")
    print("1. Open 'ALL_CHECKBOXES_CHECKED.pdf' to see if they are working.")
    print("2. If they are working, open individual files to identify specific fields.")
    print("3. Use 'checkbox_manifest.txt' to see the full field names.")

if __name__ == "__main__":
    create_checkbox_reference.py = create_checkbox_reference # Self-reference fix if needed? No.
    create_checkbox_reference()
