from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    file_size: int

class DocumentRead(DocumentBase):
    id: str
    status: str
    upload_timestamp: datetime
    
    class Config:
        from_attributes = True

class UploadSessionBase(BaseModel):
    pass

class UploadSessionRead(UploadSessionBase):
    id: str
    created_at: datetime
    status: str
    documents: List[DocumentRead] = []

    class Config:
        from_attributes = True

class UploadResponse(BaseModel):
    session_id: str
    documents: List[DocumentRead]

