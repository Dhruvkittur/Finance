"""
FinPilot AI — Document Intelligence API Routes
================================================
Endpoints:
  POST /api/v1/documents/upload   — Upload and process documents
  GET  /api/v1/documents          — List documents
  GET  /api/v1/documents/{id}     — Get document details
  DELETE /api/v1/documents/{id}   — Delete document
  GET  /api/v1/documents/{id}/status — Processing status
  POST /api/v1/documents/search   — Semantic search
"""

import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.models.document import Document, DocumentStatus, DocumentType
from app.services.document_service import DocumentProcessingService
from app.tasks.document_tasks import process_document_task

router = APIRouter(prefix="/documents")
logger = logging.getLogger(__name__)

document_service = DocumentProcessingService()


class SearchRequest(BaseModel):
    query: str
    document_ids: Optional[list[str]] = None
    n_results: int = 10
    search_type: str = "hybrid"  # semantic | hybrid


def doc_to_dict(doc: Document) -> dict:
    return {
        "id": str(doc.id),
        "filename": doc.filename,
        "original_filename": doc.original_filename,
        "doc_type": doc.doc_type,
        "category": doc.category,
        "title": doc.title,
        "file_size": doc.file_size,
        "file_size_mb": doc.file_size_mb,
        "page_count": doc.page_count,
        "status": doc.status,
        "chunks_count": doc.chunks_count,
        "embeddings_generated": doc.embeddings_generated,
        "tables_extracted": doc.tables_extracted,
        "summary": doc.summary,
        "tags": doc.tags or [],
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a financial document for AI processing.
    Processing runs asynchronously via Celery.
    Returns immediately with document ID and status 'pending'.
    """
    user_id = payload["sub"]

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file
    try:
        document_service.validate_file(
            filename=file.filename or "unknown",
            file_size=file_size,
            content_type=file.content_type or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Determine document type
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    doc_type_map = {
        "pdf": DocumentType.PDF,
        "docx": DocumentType.DOCX, "doc": DocumentType.DOCX,
        "pptx": DocumentType.PPTX, "ppt": DocumentType.PPTX,
        "xlsx": DocumentType.XLSX, "xls": DocumentType.XLSX,
        "csv": DocumentType.CSV,
        "txt": DocumentType.TXT,
        "png": DocumentType.IMAGE, "jpg": DocumentType.IMAGE,
        "jpeg": DocumentType.IMAGE, "tiff": DocumentType.IMAGE,
    }
    doc_type = doc_type_map.get(ext, DocumentType.UNKNOWN)

    # Save file to disk
    saved_filename, file_path, file_hash = await document_service.save_file(
        file_content=file_content,
        original_filename=file.filename or "unknown",
        user_id=user_id,
    )

    # Create DB record
    document = Document(
        id=uuid.uuid4(),
        filename=saved_filename,
        original_filename=file.filename or "unknown",
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        file_hash=file_hash,
        doc_type=doc_type,
        title=title or file.filename,
        status=DocumentStatus.PENDING,
        user_id=uuid.UUID(user_id),
        tags=tags.split(",") if tags else [],
    )
    db.add(document)
    await db.flush()
    doc_id = str(document.id)

    # Process document synchronously in local dev mode
    logger.info(f"Processing document synchronously: {doc_id}")
    result = await document_service.process_document(
        document_id=doc_id,
        file_path=file_path,
        doc_type=doc_type,
        user_id=user_id,
    )
    document.status = result["status"]
    document.chunks_count = result.get("chunks_count", 0)
    document.embeddings_generated = result["status"] == "processed"
    document.page_count = result.get("page_count")
    document.tables_extracted = result.get("tables_count", 0)
    if result.get("raw_text"):
        document.raw_text = result["raw_text"]

    logger.info(f"Document uploaded: {doc_id} by user {user_id}")

    return {
        "id": doc_id,
        "filename": saved_filename,
        "original_filename": file.filename,
        "status": document.status,
        "file_size_mb": round(file_size / 1024 / 1024, 2),
        "doc_type": doc_type,
        "message": "Document uploaded and queued for processing",
    }


@router.get("")
async def list_documents(
    page: int = 1,
    per_page: int = 20,
    status_filter: Optional[str] = None,
    doc_type: Optional[str] = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the current user."""
    user_id = uuid.UUID(payload["sub"])
    offset = (page - 1) * per_page

    query = select(Document).where(Document.user_id == user_id)
    if status_filter:
        query = query.where(Document.status == status_filter)
    if doc_type:
        query = query.where(Document.doc_type == doc_type)

    result = await db.execute(
        query.order_by(Document.created_at.desc()).offset(offset).limit(per_page)
    )
    documents = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == user_id)
    )
    total = count_result.scalar() or 0

    return {
        "documents": [doc_to_dict(d) for d in documents],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Get full document details."""
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(Document).where(
            Document.id == uuid.UUID(document_id),
            Document.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_to_dict(doc)


@router.get("/{document_id}/status")
async def get_processing_status(
    document_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Poll document processing status."""
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(Document).where(
            Document.id == uuid.UUID(document_id),
            Document.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document_id,
        "status": doc.status,
        "chunks_count": doc.chunks_count,
        "embeddings_generated": doc.embeddings_generated,
        "ocr_applied": doc.ocr_applied,
        "processing_error": doc.processing_error,
        "processing_time_seconds": doc.processing_time_seconds,
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its vector embeddings."""
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(Document).where(
            Document.id == uuid.UUID(document_id),
            Document.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from ChromaDB
    from app.services.vector_service import VectorService
    vs = VectorService()
    await vs.initialize_collections()
    await vs.delete_document_chunks(document_id)

    # Delete file from disk
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except Exception:
        pass

    await db.delete(doc)


@router.post("/search")
async def semantic_search(
    request: SearchRequest,
    payload: dict = Depends(get_current_user_payload),
):
    """
    Perform semantic search across all processed documents.
    Returns ranked chunks with similarity scores.
    """
    from app.services.vector_service import VectorService

    vs = VectorService()
    await vs.initialize_collections()

    if request.search_type == "hybrid":
        results = await vs.hybrid_search(
            query=request.query,
            n_results=request.n_results,
            document_ids=request.document_ids,
        )
    else:
        results = await vs.semantic_search(
            query=request.query,
            n_results=request.n_results,
            document_ids=request.document_ids,
        )

    return {
        "query": request.query,
        "results": results,
        "total": len(results),
        "search_type": request.search_type,
    }
