"""
Test script to process sample tax documents through the API and save outputs.

Usage:
    uv run python backend/scripts/test_extraction_api.py
"""

import os
import sys
import json
from pathlib import Path
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
SAMPLE_DOCS_DIR = Path("../sample_docs")
OUTPUT_DIR = SAMPLE_DOCS_DIR / "outputs"

def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def upload_document(pdf_path: Path) -> Dict[str, Any]:
    """Upload a PDF document and return the session and document info."""
    with open(pdf_path, "rb") as f:
        files = {"files": (pdf_path.name, f, "application/pdf")}
        response = requests.post(f"{BASE_URL}/api/sessions", files=files)
        response.raise_for_status()
        return response.json()

def extract_document(document_id: str) -> Dict[str, Any]:
    """Extract data from a document."""
    response = requests.post(f"{BASE_URL}/api/documents/{document_id}/extract")
    response.raise_for_status()
    return response.json()

def process_sample_document(pdf_path: Path) -> Dict[str, Any]:
    """Process a single sample document through the full pipeline."""
    print(f"\nProcessing: {pdf_path.name}")
    
    try:
        upload_result = upload_document(pdf_path)
        session_id = upload_result["session_id"]
        documents = upload_result["documents"]
        
        if not documents:
            return {"error": "No documents uploaded", "file": pdf_path.name}
        
        document_id = documents[0]["id"]
        extraction_result = extract_document(document_id)
        
        return {
            "file": pdf_path.name,
            "session_id": session_id,
            "document_id": document_id,
            "extraction": extraction_result
        }
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if hasattr(e.response, 'text'):
            error_detail = f"{str(e)} - {e.response.text}"
        return {
            "file": pdf_path.name,
            "error": error_detail,
            "error_type": "api_error"
        }
    except Exception as e:
        return {
            "file": pdf_path.name,
            "error": str(e),
            "error_type": "processing_error"
        }

def main():
    ensure_output_dir()
    
    pdf_files = sorted(SAMPLE_DOCS_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {SAMPLE_DOCS_DIR}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files to process")
    print(f"API Base URL: {BASE_URL}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    results = []
    
    for pdf_path in pdf_files:
        result = process_sample_document(pdf_path)
        results.append(result)
        
        output_file = OUTPUT_DIR / f"{pdf_path.stem}_output.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2, default=str)
        
        if "error" in result:
            print(f"  ❌ Error: {result['error']}")
        else:
            doc_type = result.get("extraction", {}).get("document_type", "unknown")
            print(f"  ✅ Extracted as {doc_type}")
    
    summary_file = OUTPUT_DIR / "summary.json"
    summary = {
        "total_files": len(pdf_files),
        "successful": len([r for r in results if "error" not in r]),
        "failed": len([r for r in results if "error" in r]),
        "results": results
    }
    
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n{'='*80}")
    print(f"Processing complete!")
    print(f"Successful: {summary['successful']}/{summary['total_files']}")
    print(f"Failed: {summary['failed']}/{summary['total_files']}")
    print(f"Results saved to: {OUTPUT_DIR}")
    print(f"Summary saved to: {summary_file}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

