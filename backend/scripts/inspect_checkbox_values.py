
import sys
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import NameObject, DictionaryObject, ArrayObject

def inspect_checkboxes():
    template_path = Path("storage/forms/f1040.pdf")
    if not template_path.exists():
        # Try relative path if run from backend root
        template_path = Path("../storage/forms/f1040.pdf")
    
    if not template_path.exists():
        # Try finding it
        print("Searching for f1040.pdf...")
        files = list(Path(".").glob("**/f1040.pdf"))
        if files:
            template_path = files[0]
        else:
            print("❌ f1040.pdf not found.")
            return

    print(f"Analyzing: {template_path.absolute()}")
    reader = PdfReader(template_path)
    fields = reader.get_fields()
    
    if not fields:
        print("No fields found via get_fields(). Checking /AcroForm directly...")
        # Fallback to direct AcroForm inspection if needed
        pass

    print(f"Found {len(fields) if fields else 0} fields total.")

    checkboxes = []
    
    for field_name, field_data in fields.items():
        field_type = field_data.get("/FT")
        
        # Check if it's a button/checkbox
        if field_type == "/Btn":
            print(f"\nFound Checkbox/Button: {field_name}")
            print(f"  Data: {field_data}")
            
            # Try to find the "On" value (Export Value)
            # Often in /AP (Appearance) -> /N (Normal)
            on_value = "Unknown"
            
            if "/AP" in field_data:
                ap = field_data["/AP"]
                if "/N" in ap:
                    n_dict = ap["/N"]
                    # If it's a dictionary, keys are states (e.g., /Yes, /Off)
                    if isinstance(n_dict, DictionaryObject):
                        states = list(n_dict.keys())
                        print(f"  States found in /AP/N: {states}")
                        # Usually one is /Off and the other is the "On" value
                        on_value = [s for s in states if s != "/Off"]
            
            checkboxes.append({
                "name": field_name,
                "on_values": on_value
            })

    print("\n" + "="*40)
    print(f"Found {len(checkboxes)} potential checkboxes.")
    print("="*40)
    for cb in checkboxes:
        print(f"Name: {cb['name']}, Possible 'On' values: {cb['on_values']}")

if __name__ == "__main__":
    inspect_checkboxes()

