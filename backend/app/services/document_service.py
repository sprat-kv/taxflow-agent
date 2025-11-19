import os
from sqlalchemy.orm import Session
from app.models.models import Document, ExtractionResult
from app.schemas.schemas import ExtractionResultRead
from app.services.extraction import process_document

class DocumentService:
    """Service for document processing and extraction."""
    
    @staticmethod
    def extract_document_data(db: Session, document_id: str) -> ExtractionResultRead:
        """
        Extract structured data from a tax document.
        
        Args:
            db: Database session
            document_id: UUID of the document
            
        Returns:
            ExtractionResultRead containing extracted data
            
        Raises:
            ValueError: If document not found or extraction fails
        """
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if not db_doc:
            raise ValueError("Document not found")
        
        if not os.path.exists(db_doc.file_path):
            raise ValueError("PDF file not found on disk")
        
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
        
        except Exception as e:
            db_doc.status = "error"
            db.commit()
            raise ValueError(f"Extraction failed: {str(e)}")

