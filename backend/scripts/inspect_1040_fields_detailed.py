"""
Script to inspect Form 1040 PDF fields and their locations.
Helps identify the correct field-to-textbox mapping.
"""
from pypdf import PdfReader
from pathlib import Path
import json

def inspect_form_fields_detailed():
    """Extract and display all form fields with detailed information."""
    # Handle both running from backend/ and project root
    form_path = Path("storage/forms/f1040.pdf")
    if not form_path.exists():
        form_path = Path("backend/storage/forms/f1040.pdf")
    
    if not form_path.exists():
        print(f"❌ Form not found: {form_path}")
        return
    
    reader = PdfReader(form_path)
    
    if reader.get_form_text_fields() is None:
        print("❌ No form fields found in PDF")
        return
    
    fields = reader.get_form_text_fields()
    
    print("\n" + "=" * 80)
    print("FORM 1040 PDF FIELD INSPECTION")
    print("=" * 80)
    print(f"\nTotal fields found: {len(fields)}\n")
    
    # Get all pages to check field locations
    num_pages = len(reader.pages)
    print(f"Total pages: {num_pages}\n")
    
    # Group fields by likely sections based on naming
    field_groups = {
        "Personal Info (f1_01-f1_09)": [],
        "Income Lines (f1_10-f1_20)": [],
        "Deductions (f1_21-f1_26)": [],
        "Tax Lines (f1_27-f1_35)": [],
        "Payments (f1_36-f1_44)": [],
        "Refund/Owe (f1_45-f1_48)": [],
        "Page 2 Fields (f2_*)": [],
        "Checkboxes (c1_*)": [],
        "Other": []
    }
    
    for field_name, field_value in fields.items():
        if field_name.startswith("f1_0") or field_name.startswith("f1_1"):
            if int(field_name.split("_")[1].split("[")[0]) <= 9:
                field_groups["Personal Info (f1_01-f1_09)"].append((field_name, field_value))
            elif int(field_name.split("_")[1].split("[")[0]) <= 20:
                field_groups["Income Lines (f1_10-f1_20)"].append((field_name, field_value))
            elif int(field_name.split("_")[1].split("[")[0]) <= 26:
                field_groups["Deductions (f1_21-f1_26)"].append((field_name, field_value))
            elif int(field_name.split("_")[1].split("[")[0]) <= 35:
                field_groups["Tax Lines (f1_27-f1_35)"].append((field_name, field_value))
            elif int(field_name.split("_")[1].split("[")[0]) <= 44:
                field_groups["Payments (f1_36-f1_44)"].append((field_name, field_value))
            elif int(field_name.split("_")[1].split("[")[0]) <= 48:
                field_groups["Refund/Owe (f1_45-f1_48)"].append((field_name, field_value))
        elif field_name.startswith("f2_"):
            field_groups["Page 2 Fields (f2_*)"].append((field_name, field_value))
        elif field_name.startswith("c1_"):
            field_groups["Checkboxes (c1_*)"].append((field_name, field_value))
        else:
            field_groups["Other"].append((field_name, field_value))
    
    # Print grouped fields
    for group_name, field_list in field_groups.items():
        if field_list:
            print(f"\n{group_name} ({len(field_list)} fields)")
            print("-" * 80)
            for field_name, field_value in sorted(field_list, key=lambda x: x[0]):
                value_str = f" = '{field_value}'" if field_value else ""
                print(f"  {field_name}{value_str}")
    
    # Create mapping template for user to fill
    print("\n" + "=" * 80)
    print("FIELD MAPPING TEMPLATE")
    print("=" * 80)
    print("\nPlease provide the correct mapping. Format:")
    print("  'field_name': 'description/location'")
    print("\nExample:")
    print("  'f1_01[0]': 'First Name'")
    print("  'f1_02[0]': 'Last Name'")
    print("  'f1_10[0]': 'Line 1a - Wages'")
    print("\n" + "-" * 80)
    
    # Generate template
    template = {}
    for field_name in sorted(fields.keys()):
        template[field_name] = "TODO: Describe what this field is"
    
    # Save to JSON file
    output_file = Path("backend/1040_field_mapping_template.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2)
    
    print(f"\nTemplate saved to: {output_file}")
    print("Please edit this file with the correct field descriptions.")
    
    # Also create a simple list for easy reference
    list_file = Path("backend/1040_fields_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        f.write("FORM 1040 FIELD NAMES\n")
        f.write("=" * 80 + "\n\n")
        f.write("Fill in the description for each field:\n\n")
        for field_name in sorted(fields.keys()):
            f.write(f"{field_name}: [DESCRIPTION HERE]\n")
    
    print(f"Field list saved to: {list_file}")
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Open the generated PDF and identify what each field represents")
    print("2. Edit 1040_field_mapping_template.json with correct descriptions")
    print("3. Or provide the mapping in a format like:")
    print("   f1_01[0] = First Name")
    print("   f1_02[0] = Last Name")
    print("   etc.")
    print("=" * 80 + "\n")

def create_test_fill_script():
    """Create a script to test filling individual fields."""
    script_content = '''"""
Script to test filling individual Form 1040 fields.
Use this to verify field mappings one at a time.
"""
from pypdf import PdfReader, PdfWriter
from pathlib import Path

def test_single_field(field_name: str, test_value: str):
    """Fill a single field and save for inspection."""
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        template_path = Path("backend/storage/forms/f1040.pdf")
    output_path = Path(f"backend/test_output/test_field_{field_name.replace('[', '_').replace(']', '')}.pdf")
    
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.clone_reader_document_root(reader)
    
    writer.update_page_form_field_values(
        writer.pages[0],
        {field_name: test_value}
    )
    
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    
    print(f"✅ Created test PDF: {output_path}")
    print(f"   Field: {field_name}")
    print(f"   Value: {test_value}")

if __name__ == "__main__":
    # Test a few key fields
    test_fields = {
        "f1_01[0]": "TEST_FIRST",
        "f1_02[0]": "TEST_LAST",
        "f1_03[0]": "123-45-6789",
        "f1_10[0]": "50000.00",
        "f1_12[0]": "1000.00",
    }
    
    for field, value in test_fields.items():
        test_single_field(field, value)
'''
    
    script_path = Path("backend/scripts/test_single_fields.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print(f"✅ Test script created: {script_path}")
    print("   Run this to test individual field mappings")

if __name__ == "__main__":
    inspect_form_fields_detailed()
    create_test_fill_script()

