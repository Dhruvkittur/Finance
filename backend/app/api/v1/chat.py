"""
FinPilot AI — Chat API Routes
================================
Endpoints:
  POST /api/v1/chat/sessions            — Create chat session
  GET  /api/v1/chat/sessions            — List user sessions
  GET  /api/v1/chat/sessions/{id}       — Get session with messages
  DELETE /api/v1/chat/sessions/{id}     — Delete session
  POST /api/v1/chat/sessions/{id}/messages — Send message (streaming)
  WS   /api/v1/chat/ws/{session_id}     — WebSocket for real-time streaming
  POST /api/v1/chat/sessions/{id}/export — Export chat
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import redis_client
from app.core.security import get_current_user_payload, sanitize_user_input
from app.graph.state import create_initial_state
from app.graph.workflow import run_finpilot_pipeline
from app.models.chat import ChatMessage, ChatSession, MessageRole
from app.services.llm_service import llm_service

router = APIRouter(prefix="/chat")
logger = logging.getLogger(__name__)


# ── Schemas ────────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: Optional[str] = "New Conversation"
    active_document_ids: Optional[list[str]] = []


class SendMessageRequest(BaseModel):
    content: str
    active_document_ids: Optional[list[str]] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    citations: Optional[list] = None
    agent_timeline: Optional[list] = None
    charts: Optional[list] = None
    confidence_score: Optional[float] = None
    tokens_used: int = 0
    created_at: str


# ── Session Endpoints ──────────────────────────────────────────────────────────

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    user_id = uuid.UUID(payload["sub"])
    session = ChatSession(
        id=uuid.uuid4(),
        user_id=user_id,
        title=request.title or "New Conversation",
        active_documents=request.active_document_ids or [],
    )
    db.add(session)
    await db.flush()

    return {
        "id": str(session.id),
        "title": session.title,
        "user_id": str(session.user_id),
        "active_documents": session.active_documents,
        "message_count": 0,
        "created_at": session.created_at.isoformat(),
    }


@router.get("/sessions")
async def list_sessions(
    page: int = 1,
    per_page: int = 20,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the current user."""
    user_id = uuid.UUID(payload["sub"])
    offset = (page - 1) * per_page

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id, ChatSession.is_archived == False)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    sessions = result.scalars().all()

    total_result = await db.execute(
        select(func.count(ChatSession.id))
        .where(ChatSession.user_id == user_id, ChatSession.is_archived == False)
    )
    total = total_result.scalar() or 0

    return {
        "sessions": [
            {
                "id": str(s.id),
                "title": s.title,
                "message_count": s.message_count,
                "total_tokens_used": s.total_tokens_used,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            }
            for s in sessions
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Get a session with all its messages."""
    user_id = uuid.UUID(payload["sub"])

    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = messages_result.scalars().all()

    return {
        "id": str(session.id),
        "title": session.title,
        "active_documents": session.active_documents,
        "message_count": session.message_count,
        "total_tokens_used": session.total_tokens_used,
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "citations": m.citations,
                "agent_timeline": m.agent_timeline,
                "charts": m.charts,
                "tables": m.tables,
                "confidence_score": m.confidence_score,
                "tokens_used": m.tokens_used,
                "agents_used": m.agents_used,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """Delete (archive) a chat session."""
    user_id = uuid.UUID(payload["sub"])
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_archived = True


# ── Message Sending (SSE Streaming) ───────────────────────────────────────────

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message and receive a streaming response via SSE.
    The pipeline runs all required AI agents and streams the final response.
    """
    user_id = payload["sub"]

    # Validate session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == uuid.UUID(session_id),
            ChatSession.user_id == uuid.UUID(user_id),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Store user message
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        session_id=session.id,
        role=MessageRole.USER,
        content=request.content,
    )
    db.add(user_msg)
    await db.flush()

    # Determine active documents
    active_doc_ids = request.active_document_ids or session.active_documents or []

    async def generate_stream():
        """SSE generator that runs the pipeline and streams chunks."""
        try:
            # Send initial event
            yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

            # Build initial state
            initial_state = create_initial_state(
                user_query=request.content,
                user_id=user_id,
                session_id=session_id,
                active_document_ids=active_doc_ids,
                workflow_type="chat",
            )

            # Stream agent progress events
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': 'PlannerAgent', 'message': 'Analyzing your query...'})}\n\n"

            # Run the complete pipeline
            final_state = await run_finpilot_pipeline(initial_state, thread_id=session_id)

            # Stream agent timeline events
            for step in final_state.get("agent_steps", []):
                yield f"data: {json.dumps({'type': 'agent_step', 'step': step})}\n\n"

            # Stream the final response in chunks
            final_response = final_state.get("final_response", "")
            if final_response:
                # Split into chunks and stream
                words = final_response.split(" ")
                chunk_size = 5
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i + chunk_size]) + " "
                    yield f"data: {json.dumps({'type': 'content', 'chunk': chunk})}\n\n"

            # Save assistant response to DB
            async with db.begin_nested():
                assistant_msg = ChatMessage(
                    id=uuid.uuid4(),
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=final_response,
                    citations=final_state.get("citations", []),
                    agent_timeline=final_state.get("agent_steps", []),
                    charts=final_state.get("charts", []),
                    tables=final_state.get("tables", []),
                    confidence_score=final_state.get("confidence_score", 0),
                    hallucination_score=final_state.get("hallucination_score", 0),
                    agents_used=final_state.get("required_agents", []),
                    tokens_used=final_state.get("total_tokens_used", 0),
                    model_used=final_state.get("llm_provider_used", ""),
                    cost_usd=final_state.get("total_cost_usd", 0),
                )
                db.add(assistant_msg)

                # Update session stats
                session.message_count += 2
                session.total_tokens_used += final_state.get("total_tokens_used", 0)
                session.total_cost_usd += final_state.get("total_cost_usd", 0)

            # Send completion event
            yield f"data: {json.dumps({'type': 'complete', 'message_id': str(assistant_msg.id), 'citations': final_state.get('citations', []), 'charts': final_state.get('charts', []), 'confidence_score': final_state.get('confidence_score', 0), 'tokens_used': final_state.get('total_tokens_used', 0), 'agents_used': final_state.get('required_agents', [])})}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── WebSocket Real-time Chat ───────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for real-time bidirectional chat.
    Handles streaming responses and live agent status updates.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: session {session_id}")

    try:
        while True:
            # Receive user message
            data = await websocket.receive_json()
            query = data.get("content", "")
            user_id = data.get("user_id", "anonymous")
            doc_ids = data.get("document_ids", [])

            if not query:
                continue

            # Send acknowledgment
            await websocket.send_json({
                "type": "ack",
                "session_id": session_id,
            })

            # Build and run pipeline
            initial_state = create_initial_state(
                user_query=query,
                user_id=user_id,
                session_id=session_id,
                active_document_ids=doc_ids,
            )

            # Stream agent steps as they complete
            await websocket.send_json({
                "type": "agent_start",
                "agent": "PlannerAgent",
            })

            final_state = await run_finpilot_pipeline(initial_state, thread_id=session_id)

            # Send agent timeline
            for step in final_state.get("agent_steps", []):
                await websocket.send_json({
                    "type": "agent_step",
                    "step": step,
                })

            # Send final response
            await websocket.send_json({
                "type": "response",
                "content": final_state.get("final_response", ""),
                "citations": final_state.get("citations", []),
                "charts": final_state.get("charts", []),
                "confidence_score": final_state.get("confidence_score", 0),
                "agents_used": final_state.get("required_agents", []),
                "tokens_used": final_state.get("total_tokens_used", 0),
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
