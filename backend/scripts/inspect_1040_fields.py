"""
Script to inspect Form 1040 PDF field names.
Outputs all form fields that can be filled programmatically.
"""
from pypdf import PdfReader
from pathlib import Path

def inspect_form_fields():
    """Extract and display all form field names from the 1040 PDF."""
    form_path = Path("storage/forms/f1040.pdf")
    
    if not form_path.exists():
        print(f"❌ Form not found: {form_path}")
        return
    
    reader = PdfReader(form_path)
    
    if reader.get_form_text_fields() is None:
        print("❌ No form fields found in PDF")
        return
    
    fields = reader.get_form_text_fields()
    
    print(f"\n{'='*80}")
    print(f"FORM 1040 PDF FIELDS ({len(fields)} total)")
    print(f"{'='*80}\n")
    
    # Group fields by page/section based on naming patterns
    grouped_fields = {
        "personal_info": [],
        "filing_status": [],
        "income": [],
        "deductions": [],
        "tax": [],
        "payments": [],
        "refund": [],
        "other": []
    }
    
    for field_name, field_value in fields.items():
        # Categorize based on field name patterns
        if "name" in field_name.lower() or "ssn" in field_name.lower() or "address" in field_name.lower():
            grouped_fields["personal_info"].append((field_name, field_value))
        elif "c1_" in field_name:  # Checkboxes typically start with c1_
            grouped_fields["filing_status"].append((field_name, field_value))
        elif any(x in field_name for x in ["f1_1", "f1_2", "f1_3", "f1_4", "f1_5", "f1_6", "f1_7", "f1_8", "f1_9"]):
            grouped_fields["income"].append((field_name, field_value))
        elif any(x in field_name for x in ["f1_10", "f1_11", "f1_12", "f1_13", "f1_14", "f1_15"]):
            grouped_fields["deductions"].append((field_name, field_value))
        elif any(x in field_name for x in ["f1_16", "f1_17", "f1_18", "f1_19", "f1_20", "f1_21", "f1_22", "f1_23", "f1_24"]):
            grouped_fields["tax"].append((field_name, field_value))
        elif any(x in field_name for x in ["f1_25", "f1_26", "f1_27", "f1_28", "f1_29", "f1_30", "f1_31", "f1_32", "f1_33"]):
            grouped_fields["payments"].append((field_name, field_value))
        elif any(x in field_name for x in ["f1_34", "f1_35", "f1_36", "f1_37"]):
            grouped_fields["refund"].append((field_name, field_value))
        else:
            grouped_fields["other"].append((field_name, field_value))
    
    # Print grouped fields
    for category, field_list in grouped_fields.items():
        if field_list:
            print(f"\n{category.upper().replace('_', ' ')} ({len(field_list)} fields)")
            print("-" * 80)
            for field_name, field_value in sorted(field_list):
                value_str = f" = '{field_value}'" if field_value else ""
                print(f"  {field_name}{value_str}")
    
    # Save to file for reference
    output_file = Path("1040_field_mapping.txt")
    with open(output_file, "w") as f:
        f.write("FORM 1040 PDF FIELD NAMES\n")
        f.write("="*80 + "\n\n")
        for field_name in sorted(fields.keys()):
            f.write(f"{field_name}\n")
    
    print(f"\n{'='*80}")
    print(f"Field names saved to: {output_file}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    inspect_form_fields()

