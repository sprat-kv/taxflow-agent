"""
Test script for Form 1040 PDF generation.
Tests the end-to-end flow: Upload → Extract → Process → Generate PDF
"""
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def test_full_1040_workflow():
    """Test complete workflow from upload to PDF generation."""
    print("\n" + "=" * 60)
    print("  FORM 1040 PDF GENERATION TEST")
    print("=" * 60)
    
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
    
    # Step 2: Extract document
    print("\n📄 Step 2: Extract document data")
    response = requests.post(f"{BASE_URL}/documents/{document_id}/extract")
    response.raise_for_status()
    extraction = response.json()
    print(f"   ✅ Extracted: {extraction['document_type']}")
    
    # Step 3: Process session with complete info
    print("\n🤖 Step 3: Process session (complete workflow)")
    personal_info = {
        "filer_name": "John Doe",
        "filer_ssn": "123-45-6789",
        "home_address": "123 Main St, Anytown, CA 12345",
        "occupation": "Software Engineer",
        "digital_assets": "No"
    }
    
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/process",
        json={
            "personal_info": personal_info,
            "filing_status": "single"
        }
    )
    response.raise_for_status()
    result = response.json()
    
    print(f"   Status: {result['status']}")
    
    if result["status"] != "complete":
        print(f"   ❌ Workflow did not complete successfully")
        print(f"   Message: {result.get('message', '')}")
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"   Warning: {warning}")
        return
    
    print("   ✅ Tax calculation completed")
    
    # Show calculation results
    if result.get("calculation_result"):
        calc = result["calculation_result"]
        print(f"\n   Tax Summary:")
        print(f"      Gross Income: ${calc.get('gross_income', 0):,.2f}")
        print(f"      Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
        print(f"      Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
        print(f"      Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
        print(f"      Result: {calc.get('status', 'unknown').upper()} ${calc.get('refund_or_owed', 0):,.2f}")
    
    # Step 4: Generate Form 1040 PDF
    print("\n📝 Step 4: Generate Form 1040 PDF")
    response = requests.post(f"{BASE_URL}/reports/{session_id}/1040")
    response.raise_for_status()
    
    # Save the PDF
    output_dir = Path("../test_output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"Form_1040_{session_id}.pdf"
    
    with open(output_file, "wb") as f:
        f.write(response.content)
    
    print(f"   ✅ PDF generated successfully!")
    print(f"   📁 Saved to: {output_file.absolute()}")
    print(f"   📄 File size: {len(response.content):,} bytes")
    
    print("\n" + "=" * 60)
    print("  ✅ FORM 1040 GENERATION TEST PASSED")
    print("=" * 60)

def main():
    """Run Form 1040 generation test."""
    try:
        health_response = requests.get("http://localhost:8000/health")
        health_response.raise_for_status()
        print("✅ API server is running\n")
    except Exception as e:
        print(f"\n❌ API server is not running: {e}")
        print("   Please start the server with: uvicorn app.main:app --reload")
        return
    
    test_full_1040_workflow()

if __name__ == "__main__":
    main()

