from typing import TypedDict, Optional, List, Dict, Any

class AgentLog(TypedDict):
    timestamp: str
    node: str
    message: str
    type: str  # "info", "success", "warning", "error"

class TaxState(TypedDict):
    session_id: str
    filing_status: Optional[str]
    tax_year: Optional[str]
    personal_info: Dict[str, Any]
    user_inputs: Dict[str, Any]
    aggregated_data: Optional[Dict[str, float]]
    calculation_result: Optional[Dict[str, Any]]
    validation_result: Optional[str]
    advisor_feedback: Optional[str]
    
    missing_fields: List[str]
    warnings: List[str]
    status: str
    
    logs: List[AgentLog]
    current_step: str

