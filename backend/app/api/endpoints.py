from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.schemas import UploadResponse, ExtractionResultRead
from app.services.session_service import SessionService
from app.services.document_service import DocumentService

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

