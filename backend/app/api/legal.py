from fastapi import APIRouter, UploadFile, File, Body
from app.models.schemas import (
    DocumentInfo, CompareRequest,
    UploadResponse, DocumentType
)
from typing import List
from app.core.config import settings
from fastapi import UploadFile, File, HTTPException, status
from pathlib import Path
import uuid
import asyncio
import shutil
from app.services.logger import logger
from app.services.document_parser import DocumentParser
from app.services.field_extractor import FieldExtractor
from app.services.normalizer import FieldNormalizer
from datetime import datetime


router = APIRouter()

documents_store = {}
comparison_tables_store = {}

document_parser = DocumentParser()
field_extractor = FieldExtractor()
startup_time = datetime.utcnow()

@router.post("/api/documents/upload", response_model=UploadResponse)
async def upload_documents(
    files: List[UploadFile] = File(..., description="Legal documents to upload")
):
    uploaded_files = []
    total_size = 0
    
    for file in files:
        try:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file_ext} not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}"
                )
            
            file_id = str(uuid.uuid4())
            unique_filename = f"{file_id}{file_ext}"
            file_path = settings.UPLOAD_DIR / unique_filename
            
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = file_path.stat().st_size
            total_size += file_size
            
            doc_type = DocumentType.CONTRACT
            if "policy" in file.filename.lower():
                doc_type = DocumentType.POLICY
            elif "agreement" in file.filename.lower():
                doc_type = DocumentType.AGREEMENT
            elif "regulation" in file.filename.lower():
                doc_type = DocumentType.REGULATION
            
            doc_info = DocumentInfo(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file_size,
                file_type=file_ext[1:],  
                doc_type=doc_type
            )
            
            documents_store[str(doc_info.id)] = doc_info
            uploaded_files.append(doc_info)
            
            logger.info(f"Uploaded document: {file.filename} ({file_size} bytes)")
            
        except Exception as e:
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    return UploadResponse(
        success=True,
        message=f"Successfully uploaded {len(uploaded_files)} file(s)",
        files=uploaded_files,
        total_size=total_size
    )

@router.get("/api/documents")
async def list_documents():
    documents = []
    for doc_id, doc in documents_store.items():
        documents.append({
            "id": doc_id,
            "filename": doc.original_filename,
            "size": doc.file_size,
            "type": doc.doc_type.value,
            "status": doc.processing_status,
            "upload_date": doc.upload_date,
            "extracted_fields_count": len(doc.extracted_fields),
            "has_errors": doc.error_message is not None
        })
    
    return {
        "count": len(documents),
        "documents": documents
    }

@router.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    if document_id not in documents_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = documents_store[document_id]
    return doc.dict()

@router.post("/api/compare")
async def compare_documents(request: CompareRequest):
    results = []
    for doc_id in request.document_ids:
        if doc_id not in documents_store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found"
            )
        results.append(documents_store[doc_id])
    return results

@router.post("/api/documents/{document_id}/extract")
async def extract_document_fields(document_id: str):
    if document_id not in documents_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = documents_store[document_id]

    if doc.extraction_complete and len(doc.extracted_fields) > 0:
        return {
            "message": "Document already processed",
            "document_id": document_id,
            "extracted_fields": doc.extracted_fields
        }
    
    try:
        doc.processing_status = "processing"
        doc.error_message = None
        
        file_path = Path(doc.file_path)
        parsed_content = await document_parser.parse(file_path)
        
        extracted_fields = field_extractor.extract_all_fields(parsed_content['text'])
        
        for field_name, extracted_value in extracted_fields.items():
            if extracted_value.value:
                normalized = FieldNormalizer.normalize(
                    extracted_value.value,
                    field_extractor._infer_data_type(field_name)
                )
                extracted_value.normalized_value = normalized
        
        doc.extracted_fields = extracted_fields
        doc.processed_date = datetime.utcnow()
        doc.processing_status = "completed"
        doc.metadata.update(parsed_content.get('metadata', {}))
        
        logger.info(f"Extracted {len(extracted_fields)} fields from {doc.original_filename}")
        
        return {
            "message": "Extraction completed successfully",
            "document_id": document_id,
            "extracted_fields_count": len(extracted_fields),
            "word_count": len(parsed_content['text'].split()),
            "page_count": len(parsed_content.get('pages', [])),
            "extracted_fields": extracted_fields
        }
        
    except Exception as e:
        doc.processing_status = "error"
        doc.error_message = str(e)
        
        logger.error(f"Error extracting fields from {doc.original_filename}: {str(e)}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract fields: {str(e)}"
        )
