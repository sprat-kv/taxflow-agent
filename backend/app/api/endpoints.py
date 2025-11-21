from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.schemas.schemas import (
    UploadResponse, 
    ExtractionResultRead, 
    TaxCalculationResult,
    ProcessSessionRequest,
    ProcessSessionResponse
)
from app.services.session_service import SessionService
from app.services.document_service import DocumentService
from app.services.tax_service import TaxService
from app.services.tax_rules import FilingStatus
from app.agent.graph import run_tax_workflow
from app.services.form_1040_service import Form1040Service
from app.models.models import Report

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024

@router.post("/sessions", response_model=UploadResponse)
async def create_upload_session(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    for file in files:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} exceeds maximum size of 10MB"
            )
    
    try:
        return SessionService.create_session_with_files(db, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=UploadResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    try:
        return SessionService.get_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.post("/documents/{document_id}/extract", response_model=ExtractionResultRead)
async def extract_document(document_id: str, db: Session = Depends(get_db)):
    try:
        return DocumentService.extract_document_data(db, document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/tax/calculate/{session_id}", response_model=TaxCalculationResult)
async def calculate_tax(
    session_id: str, 
    filing_status: FilingStatus,
    db: Session = Depends(get_db)
):
    try:
        return TaxService.calculate_tax(session_id, filing_status, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tax calculation failed: {str(e)}")

@router.post("/sessions/{session_id}/process", response_model=ProcessSessionResponse)
async def process_session(
    session_id: str,
    request: ProcessSessionRequest = Body(...),
    db: Session = Depends(get_db)
) -> ProcessSessionResponse:
    try:
        # Convert Pydantic models to dicts for the workflow
        personal_info_dict = request.personal_info.dict(exclude_none=True) if request.personal_info else None
        user_inputs_dict = request.user_inputs.dict(exclude_none=True) if request.user_inputs else None
        
        final_state = run_tax_workflow(
            session_id=session_id,
            filing_status=request.filing_status,
            tax_year=request.tax_year,
            personal_info=personal_info_dict,
            user_inputs=user_inputs_dict,
            db=db
        )
        
        if final_state["status"] == "waiting_for_user":
            return ProcessSessionResponse(
                status="waiting_for_user",
                message="Please provide the following information to continue",
                missing_fields=final_state.get("missing_fields", []),
                warnings=final_state.get("warnings", [])
            )
        elif final_state["status"] == "error":
            return ProcessSessionResponse(
                status="error",
                message="An error occurred during processing",
                warnings=final_state.get("warnings", [])
            )
        else:
            return ProcessSessionResponse(
                status="complete",
                message="Tax calculation completed successfully",
                aggregated_data=final_state.get("aggregated_data"),
                calculation_result=final_state.get("calculation_result"),
                validation_result=final_state.get("validation_result"),
                warnings=final_state.get("warnings", [])
            )
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

@router.post("/reports/{session_id}/1040")
async def generate_form_1040(
    session_id: str,
    db: Session = Depends(get_db)
):
    try:
        pdf_path = Form1040Service.generate_1040(session_id, db)
        
        report = Report(
            session_id=session_id,
            report_type="form_1040",
            file_path=str(pdf_path)
        )
        db.add(report)
        db.commit()
        
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename="Form_1040.pdf"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    try:
        SessionService.delete_session(db, session_id)
        return {"message": "Session data deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

