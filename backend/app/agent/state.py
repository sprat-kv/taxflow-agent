from typing import TypedDict, Optional, List, Dict, Any

class AgentLog(TypedDict):
    timestamp: str
    node: str
    message: str
    type: str

class TaxState(TypedDict):
    session_id: str
    filing_status: Optional[str]
    tax_year: Optional[str]
    personal_info: Dict[str, Any]
    user_inputs: Dict[str, Any]
    aggregated_data: Optional[Dict[str, float]]
    calculation_result: Optional[Dict[str, Any]]
    validation_result: Optional[str]
    
    missing_fields: List[str]
    warnings: List[str]
    status: str
    current_step: str
    logs: List[AgentLog]

