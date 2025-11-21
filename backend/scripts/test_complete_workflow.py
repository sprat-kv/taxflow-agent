"""
End-to-End Test Script for Complete Tax Processing Workflow with PDF Generation
Tests: Upload → Extract → Agent Process → Calculate → Generate 1040 PDF
"""
import requests
import json
import time
from pathlib import Path
import sys

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# Sample documents to upload
SAMPLE_DOCS = [
    "sample_docs/PYW224S_EE.pdf",  # W-2
    "sample_docs/1099-int3.pdf",    # 1099-INT
    "sample_docs/1099_nec_3.pdf"    # 1099-NEC
]

# Personal information for the agent
PERSONAL_INFO = {
    "filer_name": "John Doe",
    "filer_ssn": "123-45-6789",
    "home_address": "123 Main Street, Anytown, CA 12345",
    "occupation": "Software Engineer",
    "phone": "555-123-4567",
    "digital_assets": "No"
}

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_result(label, value, indent=0):
    """Print a labeled result."""
    spacing = "  " * indent
    if isinstance(value, (dict, list)):
        print(f"{spacing}{label}:")
        print(f"{spacing}  {json.dumps(value, indent=2)}")
    else:
        print(f"{spacing}{label}: {value}")

def check_server():
    """Check if the server is running."""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def create_session():
    """Step 1: Create a new upload session."""
    print_section("STEP 1: CREATE SESSION")
    
    response = requests.post(f"{API_BASE}/sessions")
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["id"]
        print_result("✓ Session Created", session_id)
        print_result("  Created At", data["created_at"])
        print_result("  Status", data["status"])
        return session_id
    else:
        print(f"✗ Failed to create session: {response.status_code}")
        print(f"  Error: {response.text}")
        return None

def upload_documents(session_id):
    """Step 2: Upload tax documents."""
    print_section("STEP 2: UPLOAD DOCUMENTS")
    
    uploaded_docs = []
    
    for doc_path in SAMPLE_DOCS:
        file_path = Path(doc_path)
        
        if not file_path.exists():
            print(f"✗ File not found: {doc_path}")
            continue
        
        print(f"\nUploading: {file_path.name}")
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/pdf")}
            response = requests.post(
                f"{API_BASE}/sessions/{session_id}/upload",
                files=files
            )
        
        if response.status_code == 200:
            doc_data = response.json()
            print(f"  ✓ Uploaded successfully")
            print_result("    Document ID", doc_data["id"], indent=1)
            print_result("    Size", f"{doc_data['file_size']:,} bytes", indent=1)
            uploaded_docs.append(doc_data["id"])
        else:
            print(f"  ✗ Upload failed: {response.status_code}")
            print(f"    Error: {response.text}")
    
    print(f"\n✓ Total documents uploaded: {len(uploaded_docs)}")
    return uploaded_docs

def extract_documents(session_id, document_ids):
    """Step 3: Extract data from documents."""
    print_section("STEP 3: EXTRACT DOCUMENT DATA")
    
    extracted_data = []
    
    for doc_id in document_ids:
        print(f"\nExtracting: {doc_id}")
        
        response = requests.post(f"{API_BASE}/documents/{doc_id}/extract")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Extraction successful")
            print_result("    Document Type", result["document_type"], indent=1)
            print_result("    Structured Data", "See below...", indent=1)
            
            # Display key extracted fields
            data = result["structured_data"]
            if "wages_tips_other_compensation" in data:
                print(f"      Wages: ${data.get('wages_tips_other_compensation', 0):,.2f}")
                print(f"      Withholding: ${data.get('federal_income_tax_withheld', 0):,.2f}")
            elif "interest_income" in data:
                print(f"      Interest: ${data.get('interest_income', 0):,.2f}")
            elif "nonemployee_compensation" in data:
                print(f"      1099-NEC: ${data.get('nonemployee_compensation', 0):,.2f}")
            
            extracted_data.append(result)
        else:
            print(f"  ✗ Extraction failed: {response.status_code}")
            print(f"    Error: {response.text}")
    
    print(f"\n✓ Total documents extracted: {len(extracted_data)}")
    return extracted_data

def process_with_agent(session_id, filing_status="single", tax_year="2024"):
    """Step 4: Process through the LangGraph agent."""
    print_section("STEP 4: PROCESS WITH AGENT")
    
    print("Initial processing (without personal info)...")
    
    # First call - agent should ask for personal info
    payload = {
        "filing_status": filing_status,
        "tax_year": tax_year
    }
    
    response = requests.post(
        f"{API_BASE}/sessions/{session_id}/process",
        json=payload
    )
    
    if response.status_code != 200:
        print(f"✗ Agent processing failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None
    
    result = response.json()
    print_result("  Status", result["status"])
    print_result("  Message", result["message"])
    
    if result["status"] == "waiting_for_user":
        print_result("  Missing Fields", result.get("missing_fields", []))
        
        # Second call - provide personal info
        print("\nProviding personal information...")
        
        payload = {
            "filing_status": filing_status,
            "tax_year": tax_year,
            "personal_info": PERSONAL_INFO
        }
        
        response = requests.post(
            f"{API_BASE}/sessions/{session_id}/process",
            json=payload
        )
        
        if response.status_code != 200:
            print(f"✗ Agent processing failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
        
        result = response.json()
    
    print_result("  Final Status", result["status"])
    print_result("  Message", result["message"])
    
    if result.get("aggregated_data"):
        print("\n  Aggregated Financial Data:")
        agg = result["aggregated_data"]
        print(f"    Total Wages: ${agg.get('total_wages', 0):,.2f}")
        print(f"    Total Interest: ${agg.get('total_interest', 0):,.2f}")
        print(f"    Total 1099-NEC: ${agg.get('total_nec_income', 0):,.2f}")
        print(f"    Total Withholding: ${agg.get('total_withholding', 0):,.2f}")
    
    if result.get("calculation_result"):
        print("\n  Tax Calculation Results:")
        calc = result["calculation_result"]
        print(f"    Gross Income: ${calc.get('gross_income', 0):,.2f}")
        print(f"    Standard Deduction: ${calc.get('standard_deduction', 0):,.2f}")
        print(f"    Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
        print(f"    Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
        print(f"    Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
        print(f"    Refund/Owed: ${calc.get('refund_or_owed', 0):,.2f}")
        print(f"    Status: {calc.get('status', 'N/A').upper()}")
    
    if result.get("warnings"):
        print("\n  Warnings:")
        for warning in result["warnings"]:
            print(f"    ⚠ {warning}")
    
    return result

def generate_1040_pdf(session_id):
    """Step 5: Generate Form 1040 PDF."""
    print_section("STEP 5: GENERATE FORM 1040 PDF")
    
    print("Requesting PDF generation...")
    
    response = requests.post(
        f"{API_BASE}/reports/{session_id}/1040",
        stream=True
    )
    
    if response.status_code == 200:
        # Save the PDF
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"Form_1040_{session_id}.pdf"
        
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = output_file.stat().st_size
        
        print(f"✓ PDF generated successfully!")
        print_result("  Output File", output_file.absolute())
        print_result("  File Size", f"{file_size:,} bytes")
        
        return output_file
    else:
        print(f"✗ PDF generation failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return None

def verify_pdf(pdf_path):
    """Step 6: Verify PDF was created correctly."""
    print_section("STEP 6: VERIFY PDF")
    
    if not pdf_path or not pdf_path.exists():
        print("✗ PDF file not found")
        return False
    
    print("✓ PDF file exists")
    print_result("  Location", pdf_path.absolute())
    print_result("  Size", f"{pdf_path.stat().st_size:,} bytes")
    
    # Try to open with pypdf to verify it's a valid PDF
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        print_result("  Pages", num_pages)
        print_result("  Valid PDF", "Yes")
        
        # Check for form fields
        fields = reader.get_form_text_fields()
        if fields:
            print_result("  Form Fields", len(fields))
        
        return True
    except Exception as e:
        print(f"✗ PDF verification failed: {str(e)}")
        return False

def main():
    """Run the complete end-to-end test."""
    print("\n" + "=" * 80)
    print("  END-TO-END TAX PROCESSING WORKFLOW TEST")
    print("  With Form 1040 PDF Generation")
    print("=" * 80)
    
    # Check server
    print("\nChecking server status...")
    if not check_server():
        print("✗ Server is not running!")
        print("  Please start the server with: uvicorn app.main:app --reload")
        return False
    print("✓ Server is running")
    
    # Check sample documents
    print("\nChecking sample documents...")
    missing_docs = []
    for doc_path in SAMPLE_DOCS:
        if not Path(doc_path).exists():
            missing_docs.append(doc_path)
    
    if missing_docs:
        print("✗ Missing sample documents:")
        for doc in missing_docs:
            print(f"  - {doc}")
        print("\nPlease ensure sample documents are in the sample_docs/ directory")
        return False
    print(f"✓ Found all {len(SAMPLE_DOCS)} sample documents")
    
    # Run the workflow
    try:
        # Step 1: Create session
        session_id = create_session()
        if not session_id:
            return False
        
        # Step 2: Upload documents
        document_ids = upload_documents(session_id)
        if not document_ids:
            print("\n✗ No documents were uploaded")
            return False
        
        # Step 3: Extract data
        extracted_data = extract_documents(session_id, document_ids)
        if not extracted_data:
            print("\n✗ No data was extracted")
            return False
        
        # Step 4: Process with agent
        agent_result = process_with_agent(session_id)
        if not agent_result or agent_result["status"] != "complete":
            print("\n✗ Agent processing did not complete successfully")
            return False
        
        # Step 5: Generate PDF
        pdf_path = generate_1040_pdf(session_id)
        if not pdf_path:
            return False
        
        # Step 6: Verify PDF
        pdf_valid = verify_pdf(pdf_path)
        if not pdf_valid:
            return False
        
        # Success summary
        print_section("TEST RESULTS: SUCCESS ✓")
        print("\nWorkflow completed successfully!")
        print(f"\n  Session ID: {session_id}")
        print(f"  Documents Processed: {len(document_ids)}")
        print(f"  PDF Generated: {pdf_path.name}")
        print("\nNext Steps:")
        print("  1. Open the generated PDF to verify all fields are filled")
        print("  2. Check that financial data matches extracted documents")
        print("  3. Verify personal information is correct")
        print("\n" + "=" * 80)
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

