import os
import shutil
import uuid
from typing import List
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.models import UploadSession, Document
from app.schemas.schemas import UploadResponse, DocumentRead

UPLOAD_DIR = "storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SessionService:
    @staticmethod
    def create_session_with_files(db: Session, files: List[UploadFile]) -> UploadResponse:
        session_id = str(uuid.uuid4())
        db_session = UploadSession(id=session_id, status="pending")
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        session_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)

        uploaded_documents = []

        for file in files:
            header = file.file.read(5)
            file.file.seek(0)
            
            if header[:4] != b'%PDF':
                continue
            
            if file.content_type != "application/pdf":
                continue
            
            doc_id = str(uuid.uuid4())
            file_path = os.path.join(session_dir, f"{doc_id}.pdf")
            
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                file_size = os.path.getsize(file_path)
                
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
                
            except Exception:
                continue

        db.commit()
        db.refresh(db_session)
        
        return UploadResponse(
            session_id=db_session.id,
            documents=[DocumentRead.model_validate(doc) for doc in uploaded_documents]
        )
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> UploadResponse:
        db_session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
        if not db_session:
            raise ValueError("Session not found")
        
        return UploadResponse(
            session_id=db_session.id,
            documents=[DocumentRead.model_validate(doc) for doc in db_session.documents]
        )
    
    @staticmethod
    def delete_session(db: Session, session_id: str):
        session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
        if not session:
            return
        
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
        
        report_dir = os.path.join("storage/reports", session_id)
        if os.path.exists(report_dir):
            shutil.rmtree(report_dir)
        
        db.delete(session)
        db.commit()

