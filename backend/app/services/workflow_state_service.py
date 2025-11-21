from sqlalchemy.orm import Session
from app.models.models import WorkflowState
from app.agent.state import TaxState
from datetime import datetime, UTC

class WorkflowStateService:
    @staticmethod
    def save_state(db: Session, session_id: str, state: TaxState) -> WorkflowState:
        existing = db.query(WorkflowState).filter(
            WorkflowState.session_id == session_id
        ).first()
        
        if existing:
            existing.state_data = dict(state)
            existing.status = state["status"]
            existing.updated_at = datetime.now(UTC)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            workflow_state = WorkflowState(
                session_id=session_id,
                state_data=dict(state),
                status=state["status"]
            )
            db.add(workflow_state)
            db.commit()
            db.refresh(workflow_state)
            return workflow_state
    
    @staticmethod
    def get_state(db: Session, session_id: str) -> TaxState:
        workflow_state = db.query(WorkflowState).filter(
            WorkflowState.session_id == session_id
        ).first()
        
        if workflow_state:
            return workflow_state.state_data
        return None

