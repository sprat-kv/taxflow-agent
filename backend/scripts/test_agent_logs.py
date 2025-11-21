import requests
import json
import os
from pathlib import Path
import time

# Configuration
BASE_URL = "http://localhost:8000/api"
SAMPLE_DOCS_DIR = Path("sample_docs")
W2_FILE = SAMPLE_DOCS_DIR / "PYW224S_EE.pdf"

def test_agent_logs():
    print("Starting Agent Log Test...")
    
    # 1. Create Session & Upload File
    if not W2_FILE.exists():
        print(f"Error: Sample file not found at {W2_FILE}")
        return

    print(f"Uploading {W2_FILE.name}...")
    files = [('files', ('w2.pdf', open(W2_FILE, 'rb'), 'application/pdf'))]
    
    try:
        resp = requests.post(f"{BASE_URL}/sessions", files=files)
        resp.raise_for_status()
        data = resp.json()
        session_id = data["session_id"]
        document_id = data["documents"][0]["id"]
        print(f"Session created: {session_id}")
    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return

    # 1.5 Trigger Extraction
    print(f"Extracting document {document_id}...")
    try:
        resp = requests.post(f"{BASE_URL}/documents/{document_id}/extract")
        resp.raise_for_status()
        print("Extraction complete.")
    except Exception as e:
        print(f"Extraction failed: {str(e)}")
        # Cleanup
        requests.delete(f"{BASE_URL}/sessions/{session_id}")
        return

    # 2. Run Process (Agent Workflow)
    print("\nRunning Agent Workflow...")
    # Minimal payload that should satisfy mandatory fields combined with the W2
    payload = {
        "filing_status": "single",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "Test User",
            "filer_ssn": "000-00-0000",
            "home_address": "123 Test Lane",
            "occupation": "Tester",
            "digital_assets": "no"
        }
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/sessions/{session_id}/process", json=payload)
        resp.raise_for_status()
        result = resp.json()
        
        # 3. Analyze Logs
        logs = result.get("logs", [])
        status = result.get("status")
        
        print(f"\nWorkflow Status: {status}")
        print(f"Logs Received: {len(logs)}\n")
        
        print("-" * 100)
        print(f"{'TIMESTAMP':<12} | {'NODE':<12} | {'TYPE':<8} | MESSAGE")
        print("-" * 100)
        
        for log in logs:
            # Format timestamp to show time only
            time_str = log['timestamp'].split('T')[1][:8]
            print(f"{time_str:<12} | {log['node']:<12} | {log['type']:<8} | {log['message']}")
            
        print("-" * 100)
        
        # 4. Verify specific log content
        has_aggregator = any(l['node'] == 'aggregator' for l in logs)
        has_calculator = any(l['node'] == 'calculator' for l in logs)
        has_validator = any(l['node'] == 'validator' for l in logs)
        
        if has_aggregator and has_calculator and has_validator:
            print("\nSUCCESS: Logs from all nodes (aggregator, calculator, validator) detected!")
        else:
            print("\nWARNING: Missing logs from some nodes.")
            if not has_aggregator: print("   - Missing Aggregator logs")
            if not has_calculator: print("   - Missing Calculator logs")
            if not has_validator: print("   - Missing Validator logs")
            
        # Cleanup
        requests.delete(f"{BASE_URL}/sessions/{session_id}")
        print(f"\nSession {session_id} cleaned up.")
            
    except Exception as e:
        print(f"Processing failed: {str(e)}")
        if 'resp' in locals():
            print(resp.text)

if __name__ == "__main__":
    test_agent_logs()

