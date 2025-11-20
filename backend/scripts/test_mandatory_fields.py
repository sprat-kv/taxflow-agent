"""
Test script for mandatory 1040 field collection.
Tests the agent's ability to extract and request personal information.
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_mandatory_fields_extraction():
    """Test that agent extracts Name/SSN from W-2 and asks for missing fields."""
    print_section("TEST: Mandatory Field Extraction & Validation")
    
    sample_docs_dir = Path("../sample_docs")
    w2_file = sample_docs_dir / "PYW224S_EE.pdf"
    
    if not w2_file.exists():
        print(f"❌ W-2 sample file not found: {w2_file}")
        return
    
    # Step 1: Upload document
    print("\n📤 Step 1: Upload W-2 document")
    with open(w2_file, "rb") as f:
        files = {"files": (w2_file.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/sessions", files=files)
        response.raise_for_status()
        data = response.json()
        session_id = data["session_id"]
        document_id = data["documents"][0]["id"]
    print(f"   ✅ Session created: {session_id}")
    
    # Step 2: Extract document data
    print("\n📄 Step 2: Extract document data")
    response = requests.post(f"{BASE_URL}/documents/{document_id}/extract")
    response.raise_for_status()
    extraction = response.json()
    print(f"   ✅ Extracted: {extraction['document_type']}")
    
    # Show extracted personal info if available
    structured_data = extraction.get("structured_data", {})
    if structured_data.get("employee_name"):
        print(f"   📝 Extracted Name: {structured_data['employee_name']}")
    if structured_data.get("employee_ssn"):
        print(f"   📝 Extracted SSN: {structured_data['employee_ssn']}")
    if structured_data.get("tax_year"):
        print(f"   📝 Extracted Tax Year: {structured_data['tax_year']}")
    
    # Step 3: Process without any user input
    print("\n🤖 Step 3: Process session (no personal info provided)")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/process",
        json={}
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"   Status: {result['status']}")
    if result["status"] == "waiting_for_user":
        print(f"   ⚠️  Missing fields: {result.get('missing_fields', [])}")
        print(f"   Message: {result.get('message', '')}")
        
        # Verify expected mandatory fields are requested
        missing = result.get('missing_fields', [])
        expected_mandatory = ["filer_name", "filer_ssn", "home_address", "digital_assets", "occupation", "filing_status"]
        
        print(f"\n   Expected mandatory fields to be requested:")
        for field in expected_mandatory:
            if field in missing:
                print(f"      ✅ {field} - correctly requested")
            else:
                print(f"      ⚠️  {field} - NOT requested (may be auto-extracted)")
        
        return session_id, result
    else:
        print(f"   ❌ Expected 'waiting_for_user', got '{result['status']}'")
        return session_id, result

def test_provide_mandatory_fields(session_id: str):
    """Test providing mandatory fields to complete the workflow."""
    print_section("TEST: Providing Mandatory Fields")
    
    # Prepare personal info payload
    personal_info = {
        "filer_name": "D KERTHI VENKATA",
        "filer_ssn": "123-45-6789",
        "home_address": "123 Main St, Anytown, CA 12345",
        "occupation": "Software Engineer",
        "digital_assets": "No"
    }
    
    filing_status = "single"
    
    print(f"\n📥 Providing personal information:")
    for key, value in personal_info.items():
        masked_value = value if key != "filer_ssn" else "***-**-" + value.split("-")[-1]
        print(f"   {key}: {masked_value}")
    print(f"   filing_status: {filing_status}")
    
    # Process with complete information
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/process",
        json={
            "personal_info": personal_info,
            "filing_status": filing_status
        }
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"\n   Status: {result['status']}")
    
    if result["status"] == "complete":
        print("   ✅ Workflow completed successfully!")
        
        if result.get("calculation_result"):
            calc = result["calculation_result"]
            print(f"\n   Tax Calculation:")
            print(f"      Gross Income: ${calc.get('gross_income', 0):,.2f}")
            print(f"      Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
            print(f"      Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
            print(f"      Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
            print(f"      Result: {calc.get('status', 'unknown').upper()} ${calc.get('refund_or_owed', 0):,.2f}")
        
        if result.get("validation_result"):
            print(f"\n   Validation: {result['validation_result']}")
        
        return True
    elif result["status"] == "waiting_for_user":
        print(f"   ⚠️  Still waiting for: {result.get('missing_fields', [])}")
        return False
    else:
        print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"      Warning: {warning}")
        return False

def test_partial_info():
    """Test providing only some mandatory fields."""
    print_section("TEST: Partial Information Handling")
    
    sample_docs_dir = Path("../sample_docs")
    w2_file = sample_docs_dir / "PYW223S_EE.pdf"
    
    if not w2_file.exists():
        print(f"❌ W-2 sample file not found: {w2_file}")
        return
    
    # Upload and extract
    with open(w2_file, "rb") as f:
        files = {"files": (w2_file.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/sessions", files=files)
        session_id = response.json()["session_id"]
        document_id = response.json()["documents"][0]["id"]
    
    requests.post(f"{BASE_URL}/documents/{document_id}/extract")
    
    # Provide only partial info (missing digital_assets and occupation)
    print("\n📥 Providing partial information (missing some fields):")
    partial_info = {
        "filer_name": "Jane Smith",
        "home_address": "456 Oak Ave, Springfield, IL 67890"
    }
    
    for key, value in partial_info.items():
        print(f"   {key}: {value}")
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/process",
        json={
            "personal_info": partial_info,
            "filing_status": "single"
        }
    )
    result = response.json()
    
    print(f"\n   Status: {result['status']}")
    
    if result["status"] == "waiting_for_user":
        missing = result.get('missing_fields', [])
        print(f"   ⚠️  Still missing: {missing}")
        
        # Verify expected fields are still requested
        expected_still_missing = ["filer_ssn", "digital_assets", "occupation"]
        print(f"\n   Verification:")
        for field in expected_still_missing:
            if field in missing:
                print(f"      ✅ {field} - correctly identified as missing")
            else:
                print(f"      ❌ {field} - should be missing but wasn't flagged")
        
        return session_id
    else:
        print(f"   ❌ Expected 'waiting_for_user', got '{result['status']}'")
        return None

def main():
    """Run all mandatory field tests."""
    print("\n" + "=" * 60)
    print("  MANDATORY 1040 FIELD COLLECTION TESTS")
    print("=" * 60)
    
    try:
        health_response = requests.get("http://localhost:8000/health")
        health_response.raise_for_status()
        print("✅ API server is running\n")
    except Exception as e:
        print(f"\n❌ API server is not running: {e}")
        print("   Please start the server with: uvicorn app.main:app --reload")
        return
    
    print("-" * 60)
    
    # Test 1: Extract and validate mandatory fields
    session_id, result = test_mandatory_fields_extraction()
    
    if session_id and result.get("status") == "waiting_for_user":
        # Test 2: Provide complete mandatory fields
        success = test_provide_mandatory_fields(session_id)
        
        if success:
            print("\n" + "=" * 60)
            print("  ✅ COMPLETE WORKFLOW TEST PASSED")
            print("=" * 60)
    
    # Test 3: Partial information handling
    test_partial_info()
    
    print("\n" + "=" * 60)
    print("  ALL MANDATORY FIELD TESTS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

