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

@router.post("/sessions", response_model=UploadResponse)
async def create_upload_session(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Create a new upload session and upload PDF files."""
    try:
        return SessionService.create_session_with_files(db, files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=UploadResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get upload session by ID."""
    try:
        return SessionService.get_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@router.post("/documents/{document_id}/extract", response_model=ExtractionResultRead)
async def extract_document(document_id: str, db: Session = Depends(get_db)):
    """
    Extract structured data from a tax document using Azure Document Intelligence.
    
    Args:
        document_id: UUID of the uploaded document
        db: Database session
        
    Returns:
        ExtractionResultRead containing extracted tax data
        
    Raises:
        HTTPException: If document not found or extraction fails
    """
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
    """
    Calculate tax for a session (direct calculation without agent).
    
    Args:
        session_id: Upload session ID
        filing_status: Filing status (single, married_filing_jointly, head_of_household)
        db: Database session
        
    Returns:
        TaxCalculationResult with calculated tax data
        
    Raises:
        HTTPException: If session not found or calculation fails
    """
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
    """
    Process a session through the complete tax workflow using LangGraph agent.
    
    This endpoint supports a chat-like experience:
    1. First call: Agent checks for missing info and returns what's needed
    2. Subsequent calls: User provides missing data, agent continues processing
    
    Workflow: Aggregate → Check Missing → Calculate → Validate
    
    Args:
        session_id: Upload session ID
        request: ProcessSessionRequest with optional filing_status and user_inputs
        db: Database session
        
    Returns:
        ProcessSessionResponse with status and results or missing fields
        
    Raises:
        HTTPException: If processing fails
    """
    try:
        final_state = run_tax_workflow(
            session_id=session_id,
            filing_status=request.filing_status,
            tax_year=request.tax_year,
            personal_info=request.personal_info,
            user_inputs=request.user_inputs,
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
    """
    Generate Form 1040 PDF for a completed session.
    
    Args:
        session_id: Upload session ID
        db: Database session
        
    Returns:
        FileResponse with the filled Form 1040 PDF
        
    Raises:
        HTTPException: If session not found or PDF generation fails
    """
    try:
        # Generate the PDF
        pdf_path = Form1040Service.generate_1040(session_id, db)
        
        # Save report record to database
        report = Report(
            session_id=session_id,
            report_type="form_1040",
            file_path=str(pdf_path)
        )
        db.add(report)
        db.commit()
        
        # Return PDF as downloadable file
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename="Form_1040.pdf"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

