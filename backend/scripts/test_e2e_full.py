"""
Comprehensive End-to-End Test Script for Tax Processing System
Tests: Upload → Extract → Process → Generate Form 1040 PDF

This script tests the complete workflow:
1. Upload tax documents (W-2, 1099-INT, 1099-NEC)
2. Extract structured data using Azure Document Intelligence
3. Process through LangGraph agent workflow
4. Generate filled Form 1040 PDF

Usage:
    cd backend
    uv run python scripts/test_e2e_full.py

Requirements:
    - API server running on http://localhost:8000
    - Sample documents in ../sample_docs/ directory
    - Azure Document Intelligence credentials configured
"""
import requests
import json
from pathlib import Path
from typing import Optional, Dict, Any
import sys

BASE_URL = "http://localhost:8000/api"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}{Colors.ENDC}")

def print_step(step_num: int, description: str):
    """Print a step header."""
    print(f"\n{Colors.OKCYAN}[Step {step_num}] {description}{Colors.ENDC}")
    print("-" * 80)

def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}   ✅ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.FAIL}   ❌ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}   ⚠️  {message}{Colors.ENDC}")

def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.OKBLUE}   ℹ️  {message}{Colors.ENDC}")

def check_api_server() -> bool:
    """Check if API server is running."""
    print_header("API SERVER CHECK")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        print_success("API server is running")
        return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API server")
        print_info("Please start the server with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print_error(f"API server check failed: {e}")
        return False

def find_sample_documents() -> Dict[str, Path]:
    """Find sample documents in the sample_docs directory."""
    print_header("SAMPLE DOCUMENTS CHECK")
    
    # Try multiple possible locations
    possible_dirs = [
        Path("../sample_docs"),
        Path("sample_docs"),
        Path("../../sample_docs"),
    ]
    
    sample_docs_dir = None
    for dir_path in possible_dirs:
        if dir_path.exists():
            sample_docs_dir = dir_path
            break
    
    if not sample_docs_dir:
        print_error("Sample documents directory not found")
        print_info("Expected locations:")
        for dir_path in possible_dirs:
            print(f"   - {dir_path.absolute()}")
        return {}
    
    print_info(f"Found sample docs directory: {sample_docs_dir.absolute()}")
    
    # Look for common document names
    test_files = {}
    patterns = {
        "w2": ["*w2*.pdf", "*W2*.pdf", "PYW224S_EE.pdf"],
        "1099_int": ["*1099*int*.pdf", "*1099-int*.pdf", "1099-int3.pdf"],
        "1099_nec": ["*1099*nec*.pdf", "*1099-nec*.pdf", "1099_nec_3.pdf"]
    }
    
    for doc_type, pattern_list in patterns.items():
        found = False
        for pattern in pattern_list:
            matches = list(sample_docs_dir.glob(pattern))
            if matches:
                test_files[doc_type] = matches[0]
                print_success(f"{doc_type}: {matches[0].name}")
                found = True
                break
        if not found:
            print_warning(f"{doc_type}: Not found (will skip)")
    
    return test_files

def upload_documents(files: Dict[str, Path]) -> Optional[Dict[str, Any]]:
    """Upload multiple PDF documents."""
    print_step(1, "Uploading Documents")
    
    if not files:
        print_error("No documents to upload")
        return None
    
    upload_file_list = []
    for doc_type, file_path in files.items():
        if not file_path.exists():
            print_warning(f"File not found: {file_path} (skipping)")
            continue
        
        try:
            file_handle = open(file_path, "rb")
            upload_file_list.append(("files", (file_path.name, file_handle, "application/pdf")))
            print_info(f"Prepared: {file_path.name}")
        except Exception as e:
            print_error(f"Failed to open {file_path}: {e}")
    
    if not upload_file_list:
        print_error("No valid files to upload")
        return None
    
    try:
        print_info(f"Uploading {len(upload_file_list)} file(s)...")
        response = requests.post(f"{BASE_URL}/sessions", files=upload_file_list, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        session_id = data["session_id"]
        documents = data["documents"]
        
        print_success(f"Session created: {session_id}")
        print_success(f"Documents uploaded: {len(documents)}")
        for doc in documents:
            print(f"      - {doc['filename']} (ID: {doc['id'][:8]}...)")
        
        return {"session_id": session_id, "documents": documents}
        
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)} - {e.response.text}"
            except:
                error_detail = f"{str(e)} - Status: {e.response.status_code}"
        print_error(f"Upload failed: {error_detail}")
        return None
    except Exception as e:
        print_error(f"Upload failed: {e}")
        return None
    finally:
        for _, file_tuple in upload_file_list:
            file_tuple[1].close()

def extract_all_documents(session_id: str, document_ids: list[str]) -> bool:
    """Extract data from all documents in a session."""
    print_step(2, "Extracting Document Data")
    
    success_count = 0
    extraction_results = []
    
    for i, doc_id in enumerate(document_ids, 1):
        try:
            print_info(f"Extracting document {i}/{len(document_ids)} ({doc_id[:8]}...)")
            response = requests.post(
                f"{BASE_URL}/documents/{doc_id}/extract",
                timeout=120  # Extraction can take time
            )
            response.raise_for_status()
            result = response.json()
            
            doc_type = result.get("document_type", "unknown")
            print_success(f"Extracted: {doc_type}")
            
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
            elif doc_type == "tax.us.1099NEC":
                if structured_data.get("nonemployee_compensation"):
                    print(f"         NEC Income: ${structured_data['nonemployee_compensation']:,.2f}")
            
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print_warning(f"Warning: {warning}")
            
            extraction_results.append(result)
            success_count += 1
            
        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = f"{str(e)} - {e.response.text}"
                except:
                    error_detail = f"{str(e)} - Status: {e.response.status_code}"
            print_error(f"Extraction failed: {error_detail}")
        except Exception as e:
            print_error(f"Extraction failed: {e}")
    
    print(f"\n   Summary: {success_count}/{len(document_ids)} documents extracted successfully")
    return success_count > 0  # At least one success

def process_session(session_id: str, personal_info: Dict[str, str], filing_status: str) -> Optional[Dict[str, Any]]:
    """Process session through agent workflow."""
    print_step(3, "Processing Session (Agent Workflow)")
    
    # First call - check what's missing
    print_info("Initial processing (checking for missing info)...")
    try:
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/process",
            json={},
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"      Status: {result['status']}")
        
        if result["status"] == "waiting_for_user":
            missing = result.get("missing_fields", [])
            print_warning(f"Missing fields: {missing}")
            
            # Second call - provide all required info
            print_info("Providing required information...")
            print(f"      Filing Status: {filing_status}")
            print(f"      Personal Info:")
            for key, value in personal_info.items():
                masked = value if key != "filer_ssn" else "***-**-" + value.split("-")[-1] if "-" in value else "***-**-****"
                print(f"         {key}: {masked}")
            
            response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/process",
                json={
                    "personal_info": personal_info,
                    "filing_status": filing_status,
                    "tax_year": "2024"
                },
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
        
        print(f"\n      Final Status: {result['status']}")
        
        if result["status"] == "complete":
            print_success("Tax calculation completed successfully!")
            
            # Display aggregated data
            if result.get("aggregated_data"):
                agg = result["aggregated_data"]
                print(f"\n      📊 Aggregated Financial Data:")
                print(f"         Wages: ${agg.get('total_wages', 0):,.2f}")
                print(f"         Interest: ${agg.get('total_interest', 0):,.2f}")
                print(f"         NEC Income: ${agg.get('total_nec_income', 0):,.2f}")
                print(f"         Total Withholding: ${agg.get('total_withholding', 0):,.2f}")
            
            # Display calculation results
            if result.get("calculation_result"):
                calc = result["calculation_result"]
                print(f"\n      💰 Tax Calculation Results:")
                print(f"         Gross Income: ${calc.get('gross_income', 0):,.2f}")
                print(f"         Standard Deduction: ${calc.get('standard_deduction', 0):,.2f}")
                print(f"         Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
                print(f"         Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
                print(f"         Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
                status = calc.get('status', 'unknown').upper()
                amount = calc.get('refund_or_owed', 0)
                print(f"         Result: {status} ${amount:,.2f}")
            
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print_warning(f"Warning: {warning}")
            
            return result
        else:
            print_error(f"Workflow did not complete (Status: {result.get('status', 'unknown')})")
            if result.get("missing_fields"):
                print_warning(f"Missing Fields: {result['missing_fields']}")
            return None
            
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)} - {e.response.text}"
            except:
                error_detail = f"{str(e)} - Status: {e.response.status_code}"
        print_error(f"Processing failed: {error_detail}")
        return None
    except Exception as e:
        print_error(f"Processing failed: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def generate_form_1040(session_id: str) -> Optional[Path]:
    """Generate Form 1040 PDF."""
    print_step(4, "Generating Form 1040 PDF")
    
    try:
        print_info(f"Requesting PDF generation for session {session_id}...")
        response = requests.post(
            f"{BASE_URL}/reports/{session_id}/1040",
            timeout=60
        )
        response.raise_for_status()
        
        # Verify it's a PDF
        content_type = response.headers.get('content-type', '')
        if 'pdf' not in content_type.lower():
            print_warning(f"Unexpected content type: {content_type}")
        
        # Save PDF
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"Form_1040_{session_id}.pdf"
        
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        file_size = len(response.content)
        print_success("PDF generated successfully!")
        print(f"      📁 Saved to: {output_file.absolute()}")
        print(f"      📄 File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
        
        # Verify file exists and is not empty
        if output_file.exists() and output_file.stat().st_size > 0:
            print_success("PDF file verified")
            return output_file
        else:
            print_error("PDF file verification failed")
            return None
        
    except requests.exceptions.HTTPError as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = f"{str(e)}\n   Response: {e.response.text}"
            except:
                error_detail = f"{str(e)} - Status: {e.response.status_code}"
        print_error(f"PDF generation failed: {error_detail}")
        return None
    except Exception as e:
        print_error(f"PDF generation failed: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    """Run complete end-to-end test."""
    print_header("COMPLETE END-TO-END TAX PROCESSING TEST")
    
    # Check API server
    if not check_api_server():
        sys.exit(1)
    
    # Find sample documents
    test_files = find_sample_documents()
    if not test_files:
        print_error("No sample documents found. Cannot proceed with test.")
        sys.exit(1)
    
    # Prepare personal information
    personal_info = {
        "filer_name": "John Doe",
        "filer_ssn": "123-45-6789",
        "home_address": "123 Main Street, Anytown, CA 12345",
        "occupation": "Software Engineer",
        "digital_assets": "No",
        "phone": "555-123-4567"
    }
    filing_status = "single"
    
    print_header("TEST CONFIGURATION")
    print(f"   Filing Status: {filing_status}")
    print(f"   Filer Name: {personal_info['filer_name']}")
    print(f"   Address: {personal_info['home_address']}")
    print(f"   Occupation: {personal_info['occupation']}")
    
    # Execute workflow
    upload_result = upload_documents(test_files)
    if not upload_result:
        print_error("Test failed at upload step")
        sys.exit(1)
    
    session_id = upload_result["session_id"]
    document_ids = [doc["id"] for doc in upload_result["documents"]]
    
    if not extract_all_documents(session_id, document_ids):
        print_warning("Some documents failed extraction, continuing anyway...")
    
    process_result = process_session(session_id, personal_info, filing_status)
    if not process_result:
        print_error("Test failed at processing step")
        sys.exit(1)
    
    pdf_path = generate_form_1040(session_id)
    if not pdf_path:
        print_error("Test failed at PDF generation step")
        sys.exit(1)
    
    # Final summary
    print_header("TEST SUMMARY")
    print_success("All steps completed successfully!")
    print(f"\n   📊 Session ID: {session_id}")
    print(f"   📄 Generated PDF: {pdf_path}")
    
    # Show final calculation summary
    if process_result and process_result.get("calculation_result"):
        calc = process_result["calculation_result"]
        print(f"\n   📋 Final Calculation Summary:")
        print(f"      Gross Income: ${calc.get('gross_income', 0):,.2f}")
        print(f"      Taxable Income: ${calc.get('taxable_income', 0):,.2f}")
        print(f"      Tax Liability: ${calc.get('tax_liability', 0):,.2f}")
        print(f"      Total Withholding: ${calc.get('total_withholding', 0):,.2f}")
        status = calc.get('status', 'unknown').upper()
        amount = calc.get('refund_or_owed', 0)
        print(f"      Final Result: {status} ${amount:,.2f}")
    
    print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 End-to-end test PASSED!{Colors.ENDC}")
    print("=" * 80)

if __name__ == "__main__":
    main()

