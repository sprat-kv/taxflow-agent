import requests
from pathlib import Path
from pprint import pprint
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

BASE_URL = "http://localhost:8000/api"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_DIR = PROJECT_ROOT / "sample_docs"
OUTPUT_DIR = PROJECT_ROOT / "backend" / "test_output"

DOCUMENT_FILES = [
    SAMPLE_DIR / "PYW224S_EE.pdf",      # W-2
    SAMPLE_DIR / "1099-int3.pdf",       # 1099-INT
    SAMPLE_DIR / "1099_nec_3.pdf",      # 1099-NEC
]


def upload_documents():
    files = []
    open_files = []
    try:
        for path in DOCUMENT_FILES:
            fh = open(path, "rb")
            open_files.append(fh)
            files.append(("files", (path.name, fh, "application/pdf")))

        response = requests.post(f"{BASE_URL}/sessions", files=files)
        response.raise_for_status()
        data = response.json()
        print(f"Session created: {data['session_id']}")
        print(f"Uploaded {len(data['documents'])} documents")
        return data
    finally:
        for fh in open_files:
            fh.close()


def extract_all(documents):
    for doc in documents:
        doc_id = doc["id"]
        print(f"Extracting {doc['filename']} ({doc_id}) ...")
        response = requests.post(f"{BASE_URL}/documents/{doc_id}/extract")
        response.raise_for_status()
    print("Extraction complete for all documents.\n")


def process_session(session_id):
    payload = {
        "filing_status": "single",
        "tax_year": "2024",
        "personal_info": {
            "filer_name": "Alex Rivers",
            "filer_ssn": "222-33-4444",
            "home_address": "456 Maple Ave, Austin, TX 73301",
            "occupation": "Product Manager",
            "digital_assets": "no",
            "phone": "555-987-6543"
        }
    }

    print("Running agent workflow...")
    response = requests.post(
        f"{BASE_URL}/sessions/{session_id}/process",
        json=payload
    )
    response.raise_for_status()
    data = response.json()

    status = data["status"]
    print(f"Workflow status: {status}")

    if status == "waiting_for_user":
        print("Missing fields:", data.get("missing_fields"))
    elif status == "error":
        print("Warnings:", data.get("warnings"))
    else:
        print("\nAggregated Data:")
        pprint(data.get("aggregated_data"))
        print("\nCalculation Result:")
        pprint(data.get("calculation_result"))
        if data.get("advisor_feedback"):
            print("\nAdvisor Feedback:\n")
            print(data["advisor_feedback"])

    return data


def generate_form_1040(session_id):
    print("\nGenerating Form 1040 PDF...")
    response = requests.post(f"{BASE_URL}/reports/{session_id}/1040")
    response.raise_for_status()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pdf_path = OUTPUT_DIR / f"Form_1040_{session_id}.pdf"
    with open(pdf_path, "wb") as pdf_file:
        pdf_file.write(response.content)

    print(f"Form 1040 saved to {pdf_path}")


def run_e2e_test():
    session_data = upload_documents()
    session_id = session_data["session_id"]

    try:
        extract_all(session_data["documents"])
        workflow_result = process_session(session_id)

        if workflow_result["status"] == "complete":
            generate_form_1040(session_id)
        else:
            print("Skipping PDF generation due to incomplete workflow.")

    finally:
        # optional cleanup
        requests.delete(f"{BASE_URL}/sessions/{session_id}")
        print(f"\nSession {session_id} cleaned up.")


if __name__ == "__main__":
    run_e2e_test()

