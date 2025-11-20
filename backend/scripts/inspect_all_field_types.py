"""
Script to inspect all Form 1040 form fields including checkboxes.
Identifies text fields vs checkboxes and their locations.
"""
from pypdf import PdfReader
from pathlib import Path
import json

def inspect_all_fields():
    """Inspect all form fields including checkboxes."""
    # Find template
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"Reading template from: {template_path.absolute()}\n")
    
    reader = PdfReader(template_path)
    
    # Get all form fields (text fields)
    text_fields = reader.get_form_text_fields() or {}
    
    # Get all form fields including checkboxes
    # We need to access the form fields directly from the PDF structure
    all_fields = {}
    checkboxes = {}
    text_fields_dict = {}
    
    if reader.metadata is not None and hasattr(reader, 'trailer'):
        # Access the AcroForm dictionary
        if '/AcroForm' in reader.trailer.get('/Root', {}):
            acro_form = reader.trailer['/Root']['/AcroForm']
            if '/Fields' in acro_form:
                fields_array = acro_form['/Fields']
                
                def extract_field_info(field_ref, prefix=""):
                    """Recursively extract field information."""
                    if hasattr(field_ref, 'get_object'):
                        field_obj = field_ref.get_object()
                    else:
                        field_obj = field_ref
                    
                    if '/T' in field_obj:  # Field name
                        field_name = str(field_obj['/T'])
                        full_name = f"{prefix}.{field_name}" if prefix else field_name
                        
                        # Check if it's a checkbox
                        if '/FT' in field_obj and field_obj['/FT'] == '/Btn':
                            # It's a button/checkbox
                            checkboxes[full_name] = {
                                'type': 'checkbox',
                                'name': full_name,
                                'value': str(field_obj.get('/V', '/Off'))
                            }
                        else:
                            # It's a text field
                            text_fields_dict[full_name] = {
                                'type': 'text',
                                'name': full_name,
                                'value': str(field_obj.get('/V', ''))
                            }
                        
                        all_fields[full_name] = field_obj
                    
                    # Check for kids (nested fields)
                    if '/Kids' in field_obj:
                        for kid in field_obj['/Kids']:
                            extract_field_info(kid, full_name if '/T' in field_obj else prefix)
                
                for field_ref in fields_array:
                    extract_field_info(field_ref)
    
    # Also get text fields using the simpler method
    simple_text_fields = reader.get_form_text_fields() or {}
    
    print("=" * 80)
    print("FORM 1040 FIELD INSPECTION (All Field Types)")
    print("=" * 80)
    
    print(f"\n📝 Text Fields (from get_form_text_fields): {len(simple_text_fields)}")
    print(f"📋 All Fields (from AcroForm): {len(all_fields)}")
    print(f"☑️  Checkboxes Found: {len(checkboxes)}")
    print(f"📄 Text Fields Found: {len(text_fields_dict)}")
    
    # Display checkboxes
    if checkboxes:
        print("\n" + "=" * 80)
        print("CHECKBOXES (☑️)")
        print("=" * 80)
        for cb_name, cb_info in sorted(checkboxes.items()):
            print(f"  {cb_name}")
            print(f"    Type: {cb_info['type']}")
            print(f"    Current Value: {cb_info['value']}")
            print()
    
    # Display text fields grouped
    print("=" * 80)
    print("TEXT FIELDS (📝)")
    print("=" * 80)
    
    # Group by prefix
    f1_fields = {k: v for k, v in sorted(simple_text_fields.items()) if k.startswith('f1_')}
    f2_fields = {k: v for k, v in sorted(simple_text_fields.items()) if k.startswith('f2_')}
    other_fields = {k: v for k, v in sorted(simple_text_fields.items()) if not (k.startswith('f1_') or k.startswith('f2_'))}
    
    if f1_fields:
        print(f"\nPage 1 Fields (f1_*): {len(f1_fields)}")
        for field_name in sorted(f1_fields.keys()):
            print(f"  {field_name}")
    
    if f2_fields:
        print(f"\nPage 2 Fields (f2_*): {len(f2_fields)}")
        for field_name in sorted(f2_fields.keys()):
            print(f"  {field_name}")
    
    if other_fields:
        print(f"\nOther Fields: {len(other_fields)}")
        for field_name in sorted(other_fields.keys()):
            print(f"  {field_name}")
    
    # Save to JSON for reference
    output = {
        "checkboxes": checkboxes,
        "text_fields": {k: {"type": "text", "value": v} for k, v in simple_text_fields.items()},
        "all_fields_simple": list(simple_text_fields.keys())
    }
    
    output_file = Path("1040_all_fields_inspection.json")
    if not output_file.exists():
        output_file = Path("../1040_all_fields_inspection.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Full inspection saved to: {output_file.absolute()}")
    print("\n" + "=" * 80)
    print("CHECKBOX HANDLING NOTES:")
    print("=" * 80)
    print("Checkboxes need to be set to '/Yes' or '/On' to be checked")
    print("Use '/Off' or False to uncheck them")
    print("=" * 80)

if __name__ == "__main__":
    inspect_all_fields()

