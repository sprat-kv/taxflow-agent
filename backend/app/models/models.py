from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from app.db.session import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Relationship to documents
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("upload_sessions.id"))
    filename = Column(String)
    file_path = Column(String)  # Path on disk
    file_size = Column(Integer)
    upload_timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    status = Column(String, default="uploaded")

    session = relationship("UploadSession", back_populates="documents")
    extraction_result = relationship("ExtractionResult", back_populates="document", uselist=False, cascade="all, delete-orphan")

class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), unique=True)
    document_type = Column(String)
    structured_data = Column(JSON)
    warnings = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    document = relationship("Document", back_populates="extraction_result")

