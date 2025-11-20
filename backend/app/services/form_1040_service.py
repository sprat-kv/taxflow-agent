"""
Form 1040 PDF generation service.
Fills the official IRS Form 1040 with calculated tax data.
"""
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.models import TaxResult, WorkflowState, UploadSession
import uuid

class Form1040Service:
    """Service for generating filled Form 1040 PDFs."""
    
    TEMPLATE_PATH = Path("storage/forms/f1040.pdf")
    OUTPUT_DIR = Path("storage/reports")
    
    # Field mapping: Our data keys → PDF field names
    # Based on 2024 Form 1040 structure
    FIELD_MAPPING = {
        # Personal Information (Page 1, Top)
        "filer_first_name": "f1_01[0]",
        "filer_last_name": "f1_02[0]",
        "filer_ssn": "f1_03[0]",
        
        # Address
        "home_address": "f1_04[0]",  # Street address
        "city_state_zip": "f1_05[0]",  # City, state, ZIP
        
        # Filing Status (Checkboxes - only one should be checked)
        # We'll handle checkboxes separately
        
        # Income Section
        "line_1a": "f1_10[0]",  # Wages (W-2 Box 1)
        "line_2b": "f1_12[0]",  # Taxable interest
        "line_8": "f1_19[0]",   # Other income (1099-NEC)
        "line_9": "f1_20[0]",   # Total income
        
        # Adjustments & Deductions
        "line_11": "f1_22[0]",  # Adjusted Gross Income
        "line_12": "f1_23[0]",  # Standard deduction
        "line_15": "f1_26[0]",  # Taxable income
        
        # Tax & Credits
        "line_16": "f1_27[0]",  # Tax
        "line_24": "f1_35[0]",  # Total tax
        
        # Payments
        "line_25a": "f1_36[0]",  # Federal income tax withheld
        "line_33": "f1_44[0]",  # Total payments
        
        # Refund or Amount Owed
        "line_34": "f1_45[0]",  # Overpayment (refund)
        "line_37": "f1_48[0]",  # Amount you owe
        
        # Signature Section (Page 2)
        "occupation": "f2_08[0]",
        "phone": "f2_09[0]",
    }
    
    @classmethod
    def generate_1040(cls, session_id: str, db: Session) -> Path:
        """
        Generate a filled Form 1040 PDF for a session.
        
        Args:
            session_id: Upload session ID
            db: Database session
            
        Returns:
            Path to the generated PDF file
            
        Raises:
            ValueError: If required data is missing
        """
        # Fetch workflow state and tax result
        workflow_state = db.query(WorkflowState).filter(
            WorkflowState.session_id == session_id
        ).first()
        
        if not workflow_state or workflow_state.status != "validated":
            raise ValueError(f"Session {session_id} has not completed tax calculation")
        
        state_data = workflow_state.state_data
        personal_info = state_data.get("personal_info", {})
        calc_result = state_data.get("calculation_result", {})
        aggregated_data = state_data.get("aggregated_data", {})
        filing_status = state_data.get("filing_status", "")
        
        # Prepare form data
        form_data = cls._prepare_form_data(
            personal_info, 
            calc_result, 
            aggregated_data,
            filing_status
        )
        
        # Fill the PDF
        output_path = cls._fill_pdf(session_id, form_data, filing_status)
        
        return output_path
    
    @classmethod
    def _prepare_form_data(
        cls, 
        personal_info: Dict, 
        calc_result: Dict, 
        aggregated_data: Dict,
        filing_status: str
    ) -> Dict[str, str]:
        """
        Map our data to PDF field values.
        
        Returns:
            Dictionary of PDF field names and their values
        """
        # Parse name
        full_name = personal_info.get("filer_name", "")
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        # Parse address
        full_address = personal_info.get("home_address", "")
        # Simple split: assume "Street, City, State ZIP" format
        address_parts = full_address.split(",", 1)
        street = address_parts[0] if address_parts else full_address
        city_state_zip = address_parts[1].strip() if len(address_parts) > 1 else ""
        
        # Calculate gross income (Line 9)
        total_wages = aggregated_data.get("total_wages", 0)
        total_interest = aggregated_data.get("total_interest", 0)
        total_nec_income = aggregated_data.get("total_nec_income", 0)
        gross_income = calc_result.get("gross_income", 0)
        
        # Prepare field values
        field_values = {
            cls.FIELD_MAPPING["filer_first_name"]: first_name,
            cls.FIELD_MAPPING["filer_last_name"]: last_name,
            cls.FIELD_MAPPING["filer_ssn"]: personal_info.get("filer_ssn", ""),
            cls.FIELD_MAPPING["home_address"]: street,
            cls.FIELD_MAPPING["city_state_zip"]: city_state_zip,
            
            # Income
            cls.FIELD_MAPPING["line_1a"]: f"{total_wages:,.2f}" if total_wages > 0 else "",
            cls.FIELD_MAPPING["line_2b"]: f"{total_interest:,.2f}" if total_interest > 0 else "",
            cls.FIELD_MAPPING["line_8"]: f"{total_nec_income:,.2f}" if total_nec_income > 0 else "",
            cls.FIELD_MAPPING["line_9"]: f"{gross_income:,.2f}",
            
            # Deductions
            cls.FIELD_MAPPING["line_11"]: f"{gross_income:,.2f}",  # AGI = Gross (no adjustments)
            cls.FIELD_MAPPING["line_12"]: f"{calc_result.get('standard_deduction', 0):,.2f}",
            cls.FIELD_MAPPING["line_15"]: f"{calc_result.get('taxable_income', 0):,.2f}",
            
            # Tax
            cls.FIELD_MAPPING["line_16"]: f"{calc_result.get('tax_liability', 0):,.2f}",
            cls.FIELD_MAPPING["line_24"]: f"{calc_result.get('tax_liability', 0):,.2f}",
            
            # Payments
            cls.FIELD_MAPPING["line_25a"]: f"{calc_result.get('total_withholding', 0):,.2f}",
            cls.FIELD_MAPPING["line_33"]: f"{calc_result.get('total_withholding', 0):,.2f}",
            
            # Refund or Owe
            cls.FIELD_MAPPING["occupation"]: personal_info.get("occupation", ""),
        }
        
        # Add refund or owed amount
        status = calc_result.get("status", "")
        refund_or_owed = calc_result.get("refund_or_owed", 0)
        
        if status == "refund":
            field_values[cls.FIELD_MAPPING["line_34"]] = f"{refund_or_owed:,.2f}"
        elif status == "owed":
            field_values[cls.FIELD_MAPPING["line_37"]] = f"{refund_or_owed:,.2f}"
        
        return field_values
    
    @classmethod
    def _fill_pdf(cls, session_id: str, field_values: Dict[str, str], filing_status: str) -> Path:
        """
        Fill the PDF template with provided values.
        
        Args:
            session_id: Session ID for output naming
            field_values: Dictionary of field names and values
            filing_status: Filing status for checkbox
            
        Returns:
            Path to filled PDF
        """
        reader = PdfReader(cls.TEMPLATE_PATH)
        writer = PdfWriter()
        
        # Clone document to preserve AcroForm structure
        writer.clone_reader_document_root(reader)
        
        # Handle filing status checkbox (c1_01[0] through c1_05[0])
        # Single=c1_01, MFJ=c1_02, MFS=c1_03, HOH=c1_04, QSS=c1_05
        checkbox_map = {
            "single": "c1_01[0]",
            "married_filing_jointly": "c1_02[0]",
            "married_filing_separately": "c1_03[0]",
            "head_of_household": "c1_04[0]",
            "qualifying_surviving_spouse": "c1_05[0]",
        }
        
        # Add checkbox to field_values if filing status is provided
        if filing_status in checkbox_map:
            checkbox_field = checkbox_map[filing_status]
            field_values[checkbox_field] = "/Yes"
        
        # Update all form fields at once
        if field_values:
            writer.update_page_form_field_values(
                writer.pages[0],  # Page 1
                field_values
            )
        
        # Save to output directory
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        session_dir = cls.OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        output_path = session_dir / "Form_1040.pdf"
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path

