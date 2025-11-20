"""
Script to list all Form 1040 PDF fields for mapping verification.
Run this and provide the correct field-to-description mapping.
"""
from pypdf import PdfReader
from pathlib import Path
import json

def main():
    """List all form fields in a clear format."""
    # Try both possible paths
    form_path = Path("storage/forms/f1040.pdf")
    if not form_path.exists():
        form_path = Path("../storage/forms/f1040.pdf")
    if not form_path.exists():
        print(f"❌ Form not found. Tried:")
        print(f"   storage/forms/f1040.pdf")
        print(f"   ../storage/forms/f1040.pdf")
        return
    
    print(f"Reading form from: {form_path.absolute()}\n")
    
    reader = PdfReader(form_path)
    fields = reader.get_form_text_fields()
    
    if not fields:
        print("❌ No form fields found in PDF")
        return
    
    print("=" * 80)
    print("FORM 1040 - ALL FIELD NAMES")
    print("=" * 80)
    print(f"\nTotal fields: {len(fields)}\n")
    
    # Group by prefix for easier reading
    groups = {
        "f1_01 to f1_09": [],
        "f1_10 to f1_20": [],
        "f1_21 to f1_30": [],
        "f1_31 to f1_40": [],
        "f1_41 to f1_50": [],
        "f1_51 to f1_60": [],
        "f2_* (Page 2)": [],
        "c1_* (Checkboxes)": [],
        "Other": []
    }
    
    for field_name in sorted(fields.keys()):
        if field_name.startswith("f1_"):
            num = int(field_name.split("_")[1].split("[")[0])
            if num <= 9:
                groups["f1_01 to f1_09"].append(field_name)
            elif num <= 20:
                groups["f1_10 to f1_20"].append(field_name)
            elif num <= 30:
                groups["f1_21 to f1_30"].append(field_name)
            elif num <= 40:
                groups["f1_31 to f1_40"].append(field_name)
            elif num <= 50:
                groups["f1_41 to f1_50"].append(field_name)
            else:
                groups["f1_51 to f1_60"].append(field_name)
        elif field_name.startswith("f2_"):
            groups["f2_* (Page 2)"].append(field_name)
        elif field_name.startswith("c1_"):
            groups["c1_* (Checkboxes)"].append(field_name)
        else:
            groups["Other"].append(field_name)
    
    # Print grouped
    for group_name, field_list in groups.items():
        if field_list:
            print(f"\n{group_name} ({len(field_list)} fields):")
            print("-" * 80)
            for field in field_list:
                print(f"  {field}")
    
    # Create mapping template
    print("\n" + "=" * 80)
    print("MAPPING TEMPLATE")
    print("=" * 80)
    print("\nPlease provide the correct mapping in this format:\n")
    print("FIELD_MAPPING = {")
    for field_name in sorted(fields.keys()):
        print(f'    "{field_name}": "DESCRIPTION_HERE",')
    print("}\n")
    
    # Save to JSON
    template = {field: "TODO" for field in sorted(fields.keys())}
    output_file = Path("1040_field_mapping_template.json")
    if not output_file.exists():
        output_file = Path("../1040_field_mapping_template.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Template saved to: {output_file.absolute()}")
    print("\nPlease:")
    print("1. Open the generated PDF and identify what each field represents")
    print("2. Edit the JSON file or provide the mapping in the format shown above")
    print("=" * 80)

if __name__ == "__main__":
    main()

