import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
from app.db.session import get_db
from app.models.models import UploadSession, Document
from app.schemas.schemas import UploadResponse, DocumentRead
from app.core.config import settings

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

