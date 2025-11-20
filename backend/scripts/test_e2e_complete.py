"""
End-to-end test script for complete tax processing workflow.
Tests: Upload → Extract → Process → Generate Form 1040 PDF

Usage:
    cd backend
    uv run python scripts/test_e2e_complete.py
"""
import requests
import json
from pathlib import Path
from typing import Optional

BASE_URL = "http://localhost:8000/api"

def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num: int, description: str):
    """Print a step header."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 70)

def upload_documents(files: list[Path]) -> Optional[dict]:
    """
    Upload multiple PDF documents.
    
    Args:
        files: List of PDF file paths
        
    Returns:
        Upload response data or None if failed
    """
    print_step(1, "Uploading Documents")
    
    upload_files = []
    for file_path in files:
        if not file_path.exists():
            print(f"   ❌ File not found: {file_path}")
            return None
        upload_files.append(("files", (file_path.name, open(file_path, "rb"), "application/pdf")))
    
    try:
        response = requests.post(f"{BASE_URL}/sessions", files=upload_files)
        response.raise_for_status()
        data = response.json()
        
        session_id = data["session_id"]
        documents = data["documents"]
        
        print(f"   ✅ Session created: {session_id}")
        print(f"   ✅ Documents uploaded: {len(documents)}")
        for doc in documents:
            print(f"      - {doc['filename']} (ID: {doc['id']})")
        
        return {"session_id": session_id, "documents": documents}
        
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return None
    finally:
        for _, file_tuple in upload_files:
            file_tuple[1].close()

def extract_all_documents(session_id: str, document_ids: list[str]) -> bool:
    """
    Extract data from all documents in a session.
    
    Args:
        session_id: Session ID
        document_ids: List of document IDs to extract
        
    Returns:
        True if all extractions successful, False otherwise
    """
    print_step(2, "Extracting Document Data")
    
    success_count = 0
    extraction_results = []
    
    for doc_id in document_ids:
        try:
            print(f"   Extracting document {doc_id[:8]}...")
            response = requests.post(f"{BASE_URL}/documents/{doc_id}/extract")
            response.raise_for_status()
            result = response.json()
            
            doc_type = result.get("document_type", "unknown")
            print(f"      ✅ Extracted: {doc_type}")
            
            # Show key extracted data
            structured_data = result.get("structured_data", {})
            if doc_type == "tax.us.w2":
                if structured_data.get("employee_name"):
                    print(f"         Name: {structured_data['employee_name']}")
                if structured_data.get("wages_tips_other_compensation"):
                    print(f"         Wages: ${structured_data['wages_tips_other_compensation']:,.2f}")
                if structured_data.get("federal_income_tax_withheld"):
                    print(f"         Withholding: ${structured_data['federal_income_tax_withheld']:,.2f}")
            elif doc_type == "tax.us.1099INT":
                if structured_data.get("interest_income"):
                    print(f"         Interest: ${structured_data['interest_income']:,.2f}")
                if structured_data.get("federal_income_tax_withheld"):
                    print(f"         Withholding: ${structured_data['federal_income_tax_withheld']:,.2f}")
            elif doc_type == "tax.us.1099NEC":
                if structured_data.get("nonemployee_compensation"):
                    print(f"         NEC Income: ${structured_data['nonemployee_compensation']:,.2f}")
                if structured_data.get("federal_income_tax_withheld"):
                    print(f"         Withholding: ${structured_data['federal_income_tax_withheld']:,.2f}")
            
            print(f"\n         Complete Structured Data (JSON):")
            print(f"            {json.dumps(structured_data, indent=13, default=str)}")
            
            if result.get("warnings"):
                print(f"\n         ⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"            - {warning}")
            
            extraction_results.append(result)
            success_count += 1
            
        except Exception as e:
            print(f"      ❌ Extraction failed: {e}")
    
    print(f"\n   Summary: {success_count}/{len(document_ids)} documents extracted successfully")
    return success_count == len(document_ids)

def process_session(session_id: str, personal_info: dict, filing_status: str) -> Optional[dict]:
    """
    Process session through agent workflow.
    
    Args:
        session_id: Session ID
        personal_info: Personal information dictionary
        filing_status: Filing status
        
    Returns:
        Process result or None if failed
    """
    print_step(3, "Processing Session (Agent Workflow)")
    
    # First call - check what's missing
    print("\n   [3a] Initial processing (checking for missing info)...")
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/process",
            json={}
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"      Status: {result['status']}")
        
        if result["status"] == "waiting_for_user":
            missing = result.get("missing_fields", [])
            print(f"      ⚠️  Missing fields: {missing}")
            
            # Second call - provide all required info
            print("\n   [3b] Providing required information...")
            print(f"      Filing Status: {filing_status}")
            print(f"      Personal Info:")
            for key, value in personal_info.items():
                masked = value if key != "filer_ssn" else "***-**-" + value.split("-")[-1]
                print(f"         {key}: {masked}")
            
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/process",
                json={
                    "personal_info": personal_info,
                    "filing_status": filing_status
                }
            )
            response.raise_for_status()
            result = response.json()
        
        print(f"\n      Final Status: {result['status']}")
        
        if result["status"] == "complete":
            print("      ✅ Tax calculation completed successfully!")
            
            # Display aggregated data
            if result.get("aggregated_data"):
                agg = result["aggregated_data"]
                print(f"\n      📊 Aggregated Financial Data:")
                print(f"         Wages: ${agg.get('total_wages', 0):,.2f}")
                print(f"         Interest: ${agg.get('total_interest', 0):,.2f}")
                print(f"         NEC Income: ${agg.get('total_nec_income', 0):,.2f}")
                print(f"         Total Withholding: ${agg.get('total_withholding', 0):,.2f}")
                print(f"\n      Complete Aggregated Data (JSON):")
                print(f"         {json.dumps(agg, indent=10)}")
            
            # Display calculation results
            if result.get("calculation_result"):
                calc = result["calculation_result"]
                print(f"\n      💰 Tax Calculation Results:")
                print(f"         Gross Income: ${calc.get('gross_income', 0):,.2f}")
                print(f"         Standard Deduction: ${calc.get('standard_deduction', 0):,.2f}")
                print(f"         Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
                print(f"         Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
                print(f"         Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
                print(f"         Result: {calc.get('status', 'unknown').upper()} ${calc.get('refund_or_owed', 0):,.2f}")
                print(f"\n      Complete Calculation Result (JSON):")
                print(f"         {json.dumps(calc, indent=10)}")
            
            if result.get("validation_result"):
                validation = result["validation_result"]
                print(f"\n      ✅ Validation Result:")
                print(f"         {validation}")
            
            if result.get("warnings"):
                print(f"\n      ⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"         - {warning}")
            
            return result
        else:
            print(f"      ❌ Workflow did not complete")
            print(f"      Status: {result.get('status', 'unknown')}")
            print(f"      Message: {result.get('message', 'No message')}")
            
            if result.get("missing_fields"):
                print(f"      Missing Fields: {result['missing_fields']}")
            
            if result.get("warnings"):
                print(f"\n      ⚠️  Warnings:")
                for warning in result["warnings"]:
                    print(f"         - {warning}")
            
            # Show partial results if available
            if result.get("aggregated_data"):
                agg = result["aggregated_data"]
                print(f"\n      Partial Aggregated Data:")
                print(f"         {json.dumps(agg, indent=10)}")
            
            if result.get("calculation_result"):
                calc = result["calculation_result"]
                print(f"\n      Partial Calculation Result:")
                print(f"         {json.dumps(calc, indent=10)}")
            
            return None
            
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)} - {e.response.text}"
            except:
                error_detail = f"{str(e)} - Status: {e.response.status_code}"
        print(f"      ❌ Processing failed: {error_detail}")
        return None
    except Exception as e:
        import traceback
        print(f"      ❌ Processing failed: {e}")
        print(f"      Traceback: {traceback.format_exc()}")
        return None

def generate_form_1040(session_id: str) -> Optional[Path]:
    """
    Generate Form 1040 PDF.
    
    Args:
        session_id: Session ID
        
    Returns:
        Path to generated PDF or None if failed
    """
    print_step(4, "Generating Form 1040 PDF")
    
    try:
        print(f"   Requesting PDF generation for session {session_id}...")
        response = requests.post(f"{BASE_URL}/reports/{session_id}/1040")
        response.raise_for_status()
        
        # Save PDF
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"Form_1040_{session_id}.pdf"
        
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        file_size = len(response.content)
        print(f"   ✅ PDF generated successfully!")
        print(f"   📁 Saved to: {output_file.absolute()}")
        print(f"   📄 File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        
        return output_file
        
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)}\n   Response: {e.response.text}"
            except:
                error_detail = f"{str(e)} - Status: {e.response.status_code}"
        print(f"   ❌ PDF generation failed: {error_detail}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return None
    except Exception as e:
        import traceback
        print(f"   ❌ PDF generation failed: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return None

def main():
    """Run complete end-to-end test."""
    print_section("COMPLETE END-TO-END TAX PROCESSING TEST")
    
    # Check API server
    try:
        health_response = requests.get("http://localhost:8000/health")
        health_response.raise_for_status()
        print("✅ API server is running\n")
    except Exception as e:
        print(f"\n❌ API server is not running: {e}")
        print("   Please start the server with: uvicorn app.main:app --reload")
        return
    
    # Define test documents
    sample_docs_dir = Path("../sample_docs")
    test_files = {
        "w2": sample_docs_dir / "PYW224S_EE.pdf",
        "1099_int": sample_docs_dir / "1099-int3.pdf",
        "1099_nec": sample_docs_dir / "1099_nec_3.pdf"
    }
    
    # Verify all files exist
    print("\n📋 Test Documents:")
    all_exist = True
    for doc_type, file_path in test_files.items():
        if file_path.exists():
            print(f"   ✅ {doc_type}: {file_path.name}")
        else:
            print(f"   ❌ {doc_type}: NOT FOUND - {file_path}")
            all_exist = False
    
    if not all_exist:
        print("\n❌ Some test documents are missing. Please check file paths.")
        return
    
    # Prepare personal information
    personal_info = {
        "filer_name": "John Doe",
        "filer_ssn": "123-45-6789",
        "home_address": "123 Main Street, Anytown, CA 12345",
        "occupation": "Software Engineer",
        "digital_assets": "No"
    }
    filing_status = "single"
    
    print(f"\n👤 Test Configuration:")
    print(f"   Filing Status: {filing_status}")
    print(f"   Filer Name: {personal_info['filer_name']}")
    print(f"   Address: {personal_info['home_address']}")
    
    # Execute workflow
    upload_result = upload_documents(list(test_files.values()))
    if not upload_result:
        print("\n❌ Test failed at upload step")
        return
    
    session_id = upload_result["session_id"]
    document_ids = [doc["id"] for doc in upload_result["documents"]]
    
    if not extract_all_documents(session_id, document_ids):
        print("\n⚠️  Some documents failed extraction, continuing anyway...")
    
    process_result = process_session(session_id, personal_info, filing_status)
    if not process_result:
        print("\n❌ Test failed at processing step")
        return
    
    pdf_path = generate_form_1040(session_id)
    if not pdf_path:
        print("\n❌ Test failed at PDF generation step")
        return
    
    # Final summary
    print_section("TEST SUMMARY")
    print("✅ All steps completed successfully!")
    print(f"\n📊 Session ID: {session_id}")
    print(f"📄 Generated PDF: {pdf_path}")
    
    # Show final calculation summary
    if process_result:
        print(f"\n📋 Final Calculation Summary:")
        if process_result.get("calculation_result"):
            calc = process_result["calculation_result"]
            print(f"   Gross Income: ${calc.get('gross_income', 0):,.2f}")
            print(f"   Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
            print(f"   Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
            print(f"   Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
            print(f"   Final Result: {calc.get('status', 'unknown').upper()} ${calc.get('refund_or_owed', 0):,.2f}")
    
    print(f"\n🎉 End-to-end test PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    main()

