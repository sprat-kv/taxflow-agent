from pathlib import Path
from pypdf import PdfReader, PdfWriter
from typing import Dict
from sqlalchemy.orm import Session
from app.models.models import WorkflowState

class Form1040Service:
    TEMPLATE_PATH = Path("storage/forms/f1040.pdf")
    OUTPUT_DIR = Path("storage/reports")
    
    FIELD_MAPPING = {
        "filer_first_name": "f1_04[0]",
        "filer_last_name": "f1_05[0]",
        "filer_ssn": "f1_06[0]",
        "home_address": "f1_10[0]",
        "city": "f1_12[0]",
        "state": "f1_13[0]",
        "zip": "f1_14[0]",
        "line_1a": "f1_32[0]",
        "line_1z": "f1_41[0]",
        "line_2b": "f1_43[0]",
        "line_8": "f1_53[0]",
        "line_9": "f1_54[0]",
        "line_11": "f1_56[0]",
        "line_12": "f1_57[0]",
        "line_15": "f1_60[0]",
        "line_16": "f2_02[0]",
        "line_24": "f2_10[0]",
        "line_25a": "f2_11[0]",
        "line_33": "f2_22[0]",
        "line_34": "f2_23[0]",
        "line_37": "f2_28[0]",
        "occupation": "f2_33[0]",
        "phone": "f2_37[0]",
    }
    
    @classmethod
    def generate_1040(cls, session_id: str, db: Session) -> Path:
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
        
        form_data = cls._prepare_form_data(
            personal_info, 
            calc_result, 
            aggregated_data,
            filing_status
        )
        
        return cls._fill_pdf(session_id, form_data, filing_status)
    
    @classmethod
    def _prepare_form_data(
        cls, 
        personal_info: Dict, 
        calc_result: Dict, 
        aggregated_data: Dict,
        filing_status: str
    ) -> Dict[str, str]:
        full_name = personal_info.get("filer_name", "")
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        full_address = personal_info.get("home_address", "")
        street = ""
        city = ""
        state = ""
        zip_code = ""
        
        if "," in full_address:
            parts = full_address.split(",")
            street = parts[0].strip() if len(parts) > 0 else ""
            if len(parts) > 1:
                city = parts[1].strip()
            if len(parts) > 2:
                state_zip = parts[2].strip().split()
                if len(state_zip) > 0:
                    state = state_zip[0]
                if len(state_zip) > 1:
                    zip_code = state_zip[1]
        else:
            street = full_address
        
        total_wages = aggregated_data.get("total_wages", 0)
        total_interest = aggregated_data.get("total_interest", 0)
        total_nec_income = aggregated_data.get("total_nec_income", 0)
        gross_income = calc_result.get("gross_income", 0)
        
        field_values = {
            cls.FIELD_MAPPING["filer_first_name"]: first_name,
            cls.FIELD_MAPPING["filer_last_name"]: last_name,
            cls.FIELD_MAPPING["filer_ssn"]: personal_info.get("filer_ssn", ""),
            cls.FIELD_MAPPING["home_address"]: street,
            cls.FIELD_MAPPING["city"]: city,
            cls.FIELD_MAPPING["state"]: state,
            cls.FIELD_MAPPING["zip"]: zip_code,
            cls.FIELD_MAPPING["line_1a"]: f"{total_wages:,.2f}" if total_wages > 0 else "",
            cls.FIELD_MAPPING["line_1z"]: f"{total_wages:,.2f}" if total_wages > 0 else "",
            cls.FIELD_MAPPING["line_2b"]: f"{total_interest:,.2f}" if total_interest > 0 else "",
            cls.FIELD_MAPPING["line_8"]: f"{total_nec_income:,.2f}" if total_nec_income > 0 else "",
            cls.FIELD_MAPPING["line_9"]: f"{gross_income:,.2f}",
            cls.FIELD_MAPPING["line_11"]: f"{gross_income:,.2f}",
            cls.FIELD_MAPPING["line_12"]: f"{calc_result.get('standard_deduction', 0):,.2f}",
            cls.FIELD_MAPPING["line_15"]: f"{calc_result.get('taxable_income', 0):,.2f}",
            cls.FIELD_MAPPING["line_16"]: f"{calc_result.get('tax_liability', 0):,.2f}",
            cls.FIELD_MAPPING["line_24"]: f"{calc_result.get('tax_liability', 0):,.2f}",
            cls.FIELD_MAPPING["line_25a"]: f"{calc_result.get('total_withholding', 0):,.2f}",
            cls.FIELD_MAPPING["line_33"]: f"{calc_result.get('total_withholding', 0):,.2f}",
            cls.FIELD_MAPPING["occupation"]: personal_info.get("occupation", ""),
            cls.FIELD_MAPPING["phone"]: personal_info.get("phone", ""),
        }
        
        status = calc_result.get("status", "")
        refund_or_owed = calc_result.get("refund_or_owed", 0)
        
        if status == "refund":
            field_values[cls.FIELD_MAPPING["line_34"]] = f"{refund_or_owed:,.2f}"
        elif status == "owed":
            field_values[cls.FIELD_MAPPING["line_37"]] = f"{refund_or_owed:,.2f}"
        
        return field_values
    
    @classmethod
    def _fill_pdf(cls, session_id: str, field_values: Dict[str, str], filing_status: str) -> Path:
        reader = PdfReader(cls.TEMPLATE_PATH)
        writer = PdfWriter()
        writer.clone_reader_document_root(reader)
        
        if field_values:
            writer.update_page_form_field_values(writer.pages[0], field_values)
            if len(writer.pages) > 1:
                writer.update_page_form_field_values(writer.pages[1], field_values)
        
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        session_dir = cls.OUTPUT_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        
        output_path = session_dir / "Form_1040.pdf"
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return output_path

