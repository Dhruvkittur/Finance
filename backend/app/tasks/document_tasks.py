"""
FinPilot AI — Document Processing Celery Tasks
"""

import asyncio
import logging
from celery import shared_task
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.document_tasks.process_document_task",
    queue="documents",
    max_retries=3,
    soft_time_limit=300,
)
def process_document_task(
    self,
    document_id: str,
    file_path: str,
    doc_type: str,
    user_id: str,
):
    """
    Background task: process an uploaded document through the full pipeline.
    Updates document status in DB upon completion.
    """
    logger.info(f"Processing document {document_id}")

    try:
        # Run async code in sync Celery task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _process():
            from app.services.document_service import DocumentProcessingService
            from app.core.database import AsyncSessionFactory
            from app.models.document import Document, DocumentStatus
            from sqlalchemy import select
            import uuid

            service = DocumentProcessingService()
            result = await service.process_document(
                document_id=document_id,
                file_path=file_path,
                doc_type=doc_type,
                user_id=user_id,
            )

            # Update database
            async with AsyncSessionFactory() as db:
                db_result = await db.execute(
                    select(Document).where(Document.id == uuid.UUID(document_id))
                )
                document = db_result.scalar_one_or_none()
                if document:
                    document.status = result["status"]
                    document.chunks_count = result.get("chunks_count", 0)
                    document.embeddings_generated = result["status"] == DocumentStatus.PROCESSED
                    document.page_count = result.get("page_count")
                    document.tables_extracted = result.get("tables_count", 0)
                    document.processing_time_seconds = result.get("processing_time_seconds")
                    document.ocr_applied = result.get("ocr_applied", False)
                    if result.get("error"):
                        document.processing_error = result["error"]
                    if result.get("raw_text"):
                        document.raw_text = result["raw_text"][:10000]
                    await db.commit()

            return result

        result = loop.run_until_complete(_process())
        loop.close()

        logger.info(
            f"Document {document_id} processed: "
            f"status={result['status']}, chunks={result.get('chunks_count', 0)}"
        )
        return result

    except Exception as exc:
        logger.error(f"Document processing task failed: {exc}")
        self.retry(exc=exc, countdown=60)
