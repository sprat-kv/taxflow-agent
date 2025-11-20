"""
LangGraph state definition for tax processing workflow.
"""
from typing import TypedDict, Optional, List, Dict, Any

class TaxState(TypedDict):
    """State for tax processing graph."""
    session_id: str
    filing_status: Optional[str]
    tax_year: Optional[str]
    
    # Universally Mandatory 1040 Fields
    personal_info: Dict[str, Any]  # name, ssn, address, occupation, digital_assets
    
    user_inputs: Dict[str, Any]
    aggregated_data: Optional[Dict[str, float]]
    calculation_result: Optional[Dict[str, Any]]
    validation_result: Optional[str]
    
    missing_fields: List[str]
    warnings: List[str]
    status: str

