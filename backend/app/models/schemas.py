from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class DocumentType(str, Enum):
    CONTRACT = "contract"
    AGREEMENT = "agreement"
    REGULATION = "regulation"
    POLICY = "policy"
    TERMS = "terms"
    OTHER = "other"

class ExtractionField(BaseModel):
    field_id: UUID = Field(default_factory=uuid4)
    field_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    data_type: str = Field(default="text")
    required: bool = False
    description: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)
    
    @validator('field_name')
    def validate_field_name(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Field name must be alphanumeric with underscores only')
        return v.lower()
    
    @validator('data_type')
    def validate_data_type(cls, v):
        allowed_types = ['text', 'date', 'number', 'currency', 'boolean', 'percentage', 'duration']
        if v not in allowed_types:
            raise ValueError(f'Data type must be one of: {allowed_types}')
        return v

class Citation(BaseModel):
    text: str
    page: Optional[int] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

class ExtractedValue(BaseModel):
    value: Any
    normalized_value: Optional[Any] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)
    raw_text: Optional[str] = None
    page_number: Optional[int] = None
    validation_status: str = Field(default="valid")
    
    @validator('confidence')
    def round_confidence(cls, v):
        return round(v, 3)

class DocumentInfo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    filename: str
    original_filename: str
    file_path: str
    file_size: int = Field(..., ge=0)
    file_type: str
    doc_type: DocumentType = DocumentType.CONTRACT
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processed_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    extracted_fields: Dict[str, ExtractedValue] = Field(default_factory=dict)
    processing_status: str = Field(default="pending")
    error_message: Optional[str] = None
    
    @property
    def extraction_complete(self) -> bool:
        return self.processing_status == "completed"

class UploadResponse(BaseModel):
    success: bool
    message: str
    files: List[DocumentInfo]
    total_size: int

class CompareRequest(BaseModel):
    document_ids: list[str]