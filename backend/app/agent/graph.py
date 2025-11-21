from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from typing import Literal
from app.agent.state import TaxState
from app.agent.nodes import aggregator_node, calculator_node, validator_node

def should_continue(state: TaxState) -> Literal["calculate", "end"]:
    if state["status"] == "waiting_for_user":
        return "end"
    elif state["status"] == "error":
        return "end"
    else:
        return "calculate"

def create_tax_graph(db: Session) -> StateGraph:
    workflow = StateGraph(TaxState)
    
    workflow.add_node("aggregate", lambda state: aggregator_node(state, db))
    workflow.add_node("calculate", lambda state: calculator_node(state, db))
    workflow.add_node("validate", lambda state: validator_node(state))
    
    workflow.set_entry_point("aggregate")
    
    workflow.add_conditional_edges(
        "aggregate",
        should_continue,
        {
            "calculate": "calculate",
            "end": END
        }
    )
    
    workflow.add_edge("calculate", "validate")
    workflow.add_edge("validate", END)
    
    return workflow.compile()

def run_tax_workflow(
    session_id: str, 
    filing_status: str = None,
    tax_year: str = None,
    personal_info: dict = None,
    user_inputs: dict = None,
    db: Session = None
) -> TaxState:
    from app.services.workflow_state_service import WorkflowStateService
    
    existing_state = WorkflowStateService.get_state(db, session_id)
    
    if existing_state:
        if filing_status:
            existing_state["filing_status"] = filing_status
        if tax_year:
            existing_state["tax_year"] = tax_year
        if personal_info:
            # Ensure personal_info dict exists
            if "personal_info" not in existing_state:
                existing_state["personal_info"] = {}
            existing_state["personal_info"].update(personal_info)
        if user_inputs:
            existing_state["user_inputs"].update(user_inputs)
        initial_state = existing_state
    else:
        initial_state: TaxState = {
            "session_id": session_id,
            "filing_status": filing_status,
            "tax_year": tax_year,
            "personal_info": personal_info or {},
            "user_inputs": user_inputs or {},
            "aggregated_data": None,
            "calculation_result": None,
            "validation_result": None,
            "missing_fields": [],
            "warnings": [],
            "status": "initialized",
            "current_step": "initialized",
            "logs": []
        }
    
    graph = create_tax_graph(db)
    final_state = graph.invoke(initial_state)
    
    WorkflowStateService.save_state(db, session_id, final_state)
    
    return final_state

