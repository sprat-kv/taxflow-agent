"""
End-to-end test script for the complete tax processing workflow.
Tests upload → extraction → agent workflow → calculation.
"""
import requests
import json
import time
from pathlib import Path
from typing import Optional

BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def upload_documents(files: list[str]) -> Optional[str]:
    """
    Upload PDF documents and create a session.
    
    Args:
        files: List of PDF file paths
        
    Returns:
        Session ID or None if failed
    """
    print_section("Step 1: Upload Documents")
    
    upload_files = []
    for file_path in files:
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return None
        upload_files.append(("files", (Path(file_path).name, open(file_path, "rb"), "application/pdf")))
    
    try:
        response = requests.post(f"{BASE_URL}/sessions", files=upload_files)
        response.raise_for_status()
        data = response.json()
        session_id = data["session_id"]
        print(f"✅ Session created: {session_id}")
        print(f"   Documents uploaded: {len(data['documents'])}")
        for doc in data["documents"]:
            print(f"   - {doc['filename']} (ID: {doc['id']})")
        return session_id
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None
    finally:
        for _, file_tuple in upload_files:
            file_tuple[1].close()

def extract_documents(session_id: str) -> list[str]:
    """
    Extract data from all documents in a session.
    
    Args:
        session_id: Session ID
        
    Returns:
        List of document IDs that were extracted
    """
    print_section("Step 2: Extract Document Data")
    
    session_response = requests.get(f"{BASE_URL}/sessions/{session_id}")
    session_response.raise_for_status()
    session_data = session_response.json()
    
    document_ids = [doc["id"] for doc in session_data["documents"]]
    extracted_ids = []
    
    for doc_id in document_ids:
        try:
            print(f"   Extracting document {doc_id}...")
            response = requests.post(f"{BASE_URL}/documents/{doc_id}/extract")
            response.raise_for_status()
            result = response.json()
            print(f"   ✅ Extracted: {result['document_type']}")
            if result.get("warnings"):
                print(f"      Warnings: {result['warnings']}")
            extracted_ids.append(doc_id)
        except Exception as e:
            print(f"   ❌ Extraction failed for {doc_id}: {e}")
    
    return extracted_ids

def process_session(session_id: str, filing_status: Optional[str] = None, user_inputs: Optional[dict] = None) -> dict:
    """
    Process session through agent workflow.
    
    Args:
        session_id: Session ID
        filing_status: Optional filing status
        user_inputs: Optional user-provided inputs
        
    Returns:
        Process response data
    """
    print_section("Step 3: Process Session (Agent Workflow)")
    
    payload = {}
    if filing_status:
        payload["filing_status"] = filing_status
    if user_inputs:
        payload["user_inputs"] = user_inputs
    
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/process",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"   Status: {data['status']}")
        
        if data["status"] == "waiting_for_user":
            print(f"   ⚠️  Missing fields: {data.get('missing_fields', [])}")
            print(f"   Message: {data.get('message', '')}")
            if data.get("warnings"):
                for warning in data["warnings"]:
                    print(f"   Warning: {warning}")
        
        elif data["status"] == "complete":
            print("   ✅ Calculation complete!")
            if data.get("aggregated_data"):
                agg = data["aggregated_data"]
                print(f"   Aggregated Data:")
                print(f"      Wages: ${agg.get('total_wages', 0):,.2f}")
                print(f"      Interest: ${agg.get('total_interest', 0):,.2f}")
                print(f"      NEC Income: ${agg.get('total_nec_income', 0):,.2f}")
                print(f"      Withholding: ${agg.get('total_withholding', 0):,.2f}")
            
            if data.get("calculation_result"):
                calc = data["calculation_result"]
                print(f"   Tax Calculation:")
                print(f"      Gross Income: ${calc.get('gross_income', 0):,.2f}")
                print(f"      Standard Deduction: ${calc.get('standard_deduction', 0):,.2f}")
                print(f"      Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
                print(f"      Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
                print(f"      Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
                print(f"      Result: {calc.get('status', 'unknown').upper()} ${calc.get('refund_or_owed', 0):,.2f}")
            
            if data.get("validation_result"):
                print(f"   Validation: {data['validation_result']}")
        
        elif data["status"] == "error":
            print(f"   ❌ Error: {data.get('message', 'Unknown error')}")
            if data.get("warnings"):
                for warning in data["warnings"]:
                    print(f"   Warning: {warning}")
        
        return data
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        return {}

def test_scenario_1_w2_only(sample_docs_dir: Path):
    """Test Scenario 1: W-2 only income."""
    print_section("TEST SCENARIO 1: W-2 Only Income")
    
    w2_file = sample_docs_dir / "PYW224S_EE.pdf"
    if not w2_file.exists():
        print(f"❌ W-2 sample file not found: {w2_file}")
        return
    
    session_id = upload_documents([str(w2_file)])
    if not session_id:
        return
    
    extract_documents(session_id)
    
    print("\n   First call (no filing status):")
    result1 = process_session(session_id)
    
    if result1.get("status") == "waiting_for_user":
        print("\n   Second call (with filing status):")
        result2 = process_session(session_id, filing_status="single")
        print("\n✅ Scenario 1 test complete!")

def test_scenario_2_w2_nec(sample_docs_dir: Path):
    """Test Scenario 2: W-2 + 1099-NEC."""
    print_section("TEST SCENARIO 2: W-2 + 1099-NEC")
    
    w2_file = sample_docs_dir / "PYW224S_EE.pdf"
    nec_file = sample_docs_dir / "1099-nec_1.pdf"
    
    files = []
    if w2_file.exists():
        files.append(str(w2_file))
    if nec_file.exists():
        files.append(str(nec_file))
    
    if not files:
        print(f"❌ Sample files not found in {sample_docs_dir}")
        return
    
    session_id = upload_documents(files)
    if not session_id:
        return
    
    extract_documents(session_id)
    
    result = process_session(session_id, filing_status="single")
    
    if result.get("status") == "complete":
        print("\n✅ Scenario 2 test complete!")

def test_scenario_3_w2_small_interest(sample_docs_dir: Path):
    """Test Scenario 3: W-2 + Small Interest (< $10)."""
    print_section("TEST SCENARIO 3: W-2 + Small Interest")
    
    w2_file = sample_docs_dir / "PYW224S_EE.pdf"
    int_file = sample_docs_dir / "1099-int1.pdf"
    
    files = []
    if w2_file.exists():
        files.append(str(w2_file))
    if int_file.exists():
        files.append(str(int_file))
    
    if not files:
        print(f"❌ Sample files not found in {sample_docs_dir}")
        return
    
    session_id = upload_documents(files)
    if not session_id:
        return
    
    extract_documents(session_id)
    
    result = process_session(session_id, filing_status="single")
    
    if result.get("status") == "complete":
        print("\n✅ Scenario 3 test complete!")

def test_missing_info_handling(sample_docs_dir: Path):
    """Test missing information handling."""
    print_section("TEST: Missing Information Handling")
    
    w2_file = sample_docs_dir / "w2.pdf"
    if not w2_file.exists():
        print(f"❌ W-2 sample file not found: {w2_file}")
        return
    
    session_id = upload_documents([str(w2_file)])
    if not session_id:
        return
    
    extract_documents(session_id)
    
    print("\n   Test 1: No filing status provided")
    result1 = process_session(session_id)
    
    if result1.get("status") == "waiting_for_user":
        print("\n   Test 2: Provide filing status")
        result2 = process_session(session_id, filing_status="single")
        
        if result2.get("status") == "complete":
            print("\n   Test 3: Provide user inputs to override")
            user_inputs = {
                "total_wages": 60000,
                "total_withholding": 6000
            }
            result3 = process_session(session_id, filing_status="single", user_inputs=user_inputs)
            print("\n✅ Missing info handling test complete!")

def main():
    """Run all test scenarios."""
    print("\n" + "=" * 60)
    print("  TAX PROCESSING WORKFLOW - END-TO-END TESTS")
    print("=" * 60)
    
    sample_docs_dir = Path("../sample_docs")
    if not sample_docs_dir.exists():
        print(f"\n❌ Sample documents directory not found: {sample_docs_dir}")
        print("   Please ensure sample PDFs are in the 'sample_docs' directory")
        return
    
    print(f"\n📁 Using sample documents from: {sample_docs_dir.absolute()}")
    
    try:
        health_response = requests.get("http://localhost:8000/health")
        health_response.raise_for_status()
        print("✅ API server is running")
    except Exception as e:
        print(f"\n❌ API server is not running: {e}")
        print("   Please start the server with: uvicorn app.main:app --reload")
        return
    
    print("\n" + "-" * 60)
    print("Starting tests...")
    print("-" * 60)
    
    test_scenario_1_w2_only(sample_docs_dir)
    time.sleep(1)
    
    test_scenario_2_w2_nec(sample_docs_dir)
    time.sleep(1)
    
    test_scenario_3_w2_small_interest(sample_docs_dir)
    time.sleep(1)
    
    test_missing_info_handling(sample_docs_dir)
    
    print("\n" + "=" * 60)
    print("  ALL TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

