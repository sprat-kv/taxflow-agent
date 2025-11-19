import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.session import get_db
from app.models.models import UploadSession, Document, ExtractionResult
from app.schemas.schemas import UploadResponse, DocumentRead, ExtractionResultRead
from app.core.config import settings
from app.services.extraction import process_document

router = APIRouter()

UPLOAD_DIR = "storage/uploads"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/sessions", response_model=UploadResponse)
async def create_upload_session(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    # 1. Create a new session
    session_id = str(uuid.uuid4())
    db_session = UploadSession(id=session_id, status="pending")
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    uploaded_documents = []

    for file in files:
        # Validation
        if file.content_type != "application/pdf":
            continue # Skip non-PDFs or raise error? For now skipping.
        
        # Generate secure filename/ID
        doc_id = str(uuid.uuid4())
        file_path = os.path.join(session_dir, f"{doc_id}.pdf")
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            # Create Document record
            db_doc = Document(
                id=doc_id,
                session_id=session_id,
                filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                status="uploaded"
            )
            db.add(db_doc)
            uploaded_documents.append(db_doc)
            
        except Exception as e:
            # Log error here
            print(f"Error saving file {file.filename}: {e}")
            continue

    db.commit()
    
    # Refresh session to get documents relationship
    db.refresh(db_session)
    
    return UploadResponse(
        session_id=db_session.id,
        documents=[DocumentRead.model_validate(doc) for doc in uploaded_documents]
    )

@router.get("/sessions/{session_id}", response_model=UploadResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    db_session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return UploadResponse(
        session_id=db_session.id,
        documents=[DocumentRead.model_validate(doc) for doc in db_session.documents]
    )

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
    db_doc = db.query(Document).filter(Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(db_doc.file_path):
        raise HTTPException(status_code=404, detail="PDF file not found on disk")
    
    try:
        doc_type, extracted_data, warnings = process_document(db_doc.file_path)
        
        extraction_result = ExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            structured_data=extracted_data.model_dump(),
            warnings="; ".join(warnings) if warnings else None
        )
        db.add(extraction_result)
        db_doc.status = "parsed"
        db.commit()
        db.refresh(extraction_result)
        
        return ExtractionResultRead.model_validate(extraction_result)
    
    except ValueError as e:
        db_doc.status = "error"
        db.commit()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db_doc.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

