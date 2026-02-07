from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncGenerator
import json
import asyncio
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.repository import Conversation, Message
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/stream")
async def chat_stream(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Stream chat response using Server-Sent Events."""
    
    async def generate() -> AsyncGenerator[str, None]:
        chat_service = ChatService(db, current_user.id)
        
        try:
            async for chunk in chat_service.process_message(
                message=request.message,
                repo_id=request.repo_id,
                conversation_id=request.conversation_id
            ):
                # Format as SSE
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            error_chunk = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
        
        # Signal completion
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ChatMessageResponse:
    """Send a message and get a non-streaming response."""
    chat_service = ChatService(db, current_user.id)
    
    response = await chat_service.process_message_sync(
        message=request.message,
        repo_id=request.repo_id,
        conversation_id=request.conversation_id
    )
    
    return ChatMessageResponse(
        id=str(response["id"]),
        role="assistant",
        content=response["content"],
        citations=response.get("citations"),
        risk=response.get("risk"),
        timestamp=datetime.utcnow()
    )


@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's conversations."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .limit(50)
    )
    conversations = result.scalars().all()
    
    return [
        {
            "id": conv.id,
            "title": conv.title or "New Chat",
            "repository_id": conv.repository_id,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a conversation."""
    # Verify ownership
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user.id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "citations": msg.citations,
            "risk": msg.risk_analysis,
            "timestamp": msg.created_at.isoformat()
        }
        for msg in messages
    ]
