from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
import uuid
from app.db.session import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    status = Column(String, default="pending")
    
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    tax_result = relationship("TaxResult", back_populates="session", uselist=False, cascade="all, delete-orphan")

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

class TaxResult(Base):
    __tablename__ = "tax_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("upload_sessions.id"), unique=True)
    filing_status = Column(String)
    gross_income = Column(JSON)
    standard_deduction = Column(JSON)
    taxable_income = Column(JSON)
    tax_liability = Column(JSON)
    total_withholding = Column(JSON)
    refund_or_owed = Column(JSON)
    status = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    session = relationship("UploadSession")

class WorkflowState(Base):
    __tablename__ = "workflow_states"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("upload_sessions.id"), unique=True)
    state_data = Column(JSON)
    status = Column(String)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    session = relationship("UploadSession")

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("upload_sessions.id"))
    report_type = Column(String)  # e.g., "form_1040"
    file_path = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    session = relationship("UploadSession")

