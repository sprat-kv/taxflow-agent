"""
Test script for Azure Document Intelligence unified tax model (prebuilt-tax.us).
This model automatically classifies and extracts data from W-2, 1099-NEC, and 1099-INT forms.

Usage:
    uv run python backend/scripts/test_azure_tax.py <path_to_pdf>
    uv run python backend/scripts/test_azure_tax.py samples/*.pdf
"""

import os
import sys
from pathlib import Path
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv

def analyze_tax_document(pdf_path: str, client: DocumentIntelligenceClient):
    """
    Analyze a tax document using Azure's unified prebuilt-tax.us model.
    
    Args:
        pdf_path: Path to the PDF file
        client: Azure DocumentIntelligenceClient instance
    """
    print(f"\n{'='*80}")
    print(f"Analyzing: {pdf_path}")
    print(f"{'='*80}")
    
    # Read PDF file
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    
    # Analyze using unified tax model
    poller = client.begin_analyze_document(
        "prebuilt-tax.us",
        pdf_bytes
    )
    result = poller.result()
    
    # Print results
    if not result.documents:
        print("⚠️  No documents detected")
        return
    
    for idx, doc in enumerate(result.documents):
        print(f"\n--- Document #{idx + 1} ---")
        print(f"Document Type: {doc.doc_type}")
        print(f"Confidence: {doc.confidence:.2%}")
        
        if doc.fields:
            print(f"\nExtracted Fields ({len(doc.fields)} total):")
            
            # Print key fields based on document type
            if doc.doc_type == "tax.us.w2":
                print_w2_fields(doc.fields)
            elif doc.doc_type == "tax.us.1099NEC":
                print_1099nec_fields(doc.fields)
            elif doc.doc_type == "tax.us.1099INT":
                print_1099int_fields(doc.fields)
            else:
                # Print all fields for unknown types
                for name, field in doc.fields.items():
                    print(f"  {name}: {field.content} (confidence: {field.confidence:.2%})")
        else:
            print("⚠️  No fields extracted")

def print_w2_fields(fields):
    """Print key W-2 fields."""
    key_fields = [
        "Wages", "FederalIncomeTaxWithheld", 
        "SocialSecurityWages", "SocialSecurityTaxWithheld",
        "MedicareWagesAndTips", "MedicareTaxWithheld"
    ]
    
    for field_name in key_fields:
        if field_name in fields:
            field = fields[field_name]
            value = field.value_number if hasattr(field, 'value_number') else field.content
            print(f"  {field_name}: ${value:,.2f}" if isinstance(value, (int, float)) else f"  {field_name}: {value}")
            print(f"    (confidence: {field.confidence:.2%})")
    
    # Print Employee info
    if "Employee" in fields and fields["Employee"].value_object:
        print("\n  Employee:")
        for item_name, item_field in fields["Employee"].value_object.items():
            if item_name == "SocialSecurityNumber":
                value = item_field.value_string if hasattr(item_field, 'value_string') else item_field.content
                print(f"    {item_name}: {value} (confidence: {item_field.confidence:.2%})")
    
    # Print Employer info
    if "Employer" in fields and fields["Employer"].value_object:
        print("\n  Employer:")
        for item_name, item_field in fields["Employer"].value_object.items():
            if item_name in ["Name", "IdNumber"]:
                value = item_field.value_string if hasattr(item_field, 'value_string') else item_field.content
                print(f"    {item_name}: {value} (confidence: {item_field.confidence:.2%})")

def print_1099nec_fields(fields):
    """Print key 1099-NEC fields."""
    key_fields = ["NonemployeeCompensation"]
    
    for field_name in key_fields:
        if field_name in fields:
            field = fields[field_name]
            value = field.value_number if hasattr(field, 'value_number') else field.content
            print(f"  {field_name}: ${value:,.2f}" if isinstance(value, (int, float)) else f"  {field_name}: {value}")
            print(f"    (confidence: {field.confidence:.2%})")
    
    # Print Payer info
    if "Payer" in fields and hasattr(fields["Payer"], 'value_object') and fields["Payer"].value_object:
        print("\n  Payer:")
        for item_name, item_field in fields["Payer"].value_object.items():
            if item_name in ["Name", "TaxIdNumber"]:
                value = item_field.value_string if hasattr(item_field, 'value_string') else item_field.content
                print(f"    {item_name}: {value} (confidence: {item_field.confidence:.2%})")

def print_1099int_fields(fields):
    """Print key 1099-INT fields."""
    key_fields = ["InterestIncome"]
    
    for field_name in key_fields:
        if field_name in fields:
            field = fields[field_name]
            value = field.value_number if hasattr(field, 'value_number') else field.content
            print(f"  {field_name}: ${value:,.2f}" if isinstance(value, (int, float)) else f"  {field_name}: {value}")
            print(f"    (confidence: {field.confidence:.2%})")
    
    # Print Payer info
    if "Payer" in fields and hasattr(fields["Payer"], 'value_object') and fields["Payer"].value_object:
        print("\n  Payer:")
        for item_name, item_field in fields["Payer"].value_object.items():
            if item_name in ["Name", "TaxIdNumber"]:
                value = item_field.value_string if hasattr(item_field, 'value_string') else item_field.content
                print(f"    {item_name}: {value} (confidence: {item_field.confidence:.2%})")

def main():
    # Load environment variables
    load_dotenv()
    
    endpoint = os.environ.get("DOCUMENTINTELLIGENCE_ENDPOINT")
    key = os.environ.get("DOCUMENTINTELLIGENCE_API_KEY")
    
    if not endpoint or not key:
        print("❌ Error: DOCUMENTINTELLIGENCE_ENDPOINT and DOCUMENTINTELLIGENCE_API_KEY must be set in .env")
        sys.exit(1)
    
    # Initialize client
    client = DocumentIntelligenceClient(
        endpoint=endpoint, 
        credential=AzureKeyCredential(key)
    )
    
    # Get PDF paths from command line
    if len(sys.argv) < 2:
        print("Usage: python test_azure_tax.py <pdf_path> [<pdf_path> ...]")
        sys.exit(1)
    
    pdf_paths = sys.argv[1:]
    
    # Process each PDF
    for pdf_path in pdf_paths:
        if not Path(pdf_path).exists():
            print(f"⚠️  File not found: {pdf_path}")
            continue
        
        try:
            analyze_tax_document(pdf_path, client)
        except Exception as e:
            print(f"❌ Error analyzing {pdf_path}: {e}")
    
    print(f"\n{'='*80}")
    print(f"✅ Analysis complete")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()

