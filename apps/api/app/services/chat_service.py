from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import asyncio
from app.models.repository import Repository, Conversation, Message
from app.core.config import get_settings
from app.agents.orchestrator import AgentOrchestrator

settings = get_settings()


class ChatService:
    """Service for handling chat interactions with the multi-agent system."""
    
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.orchestrator = AgentOrchestrator()
    
    async def process_message(
        self,
        message: str,
        repo_id: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Process a message and stream the response."""
        
        # Get or create conversation
        conversation = await self._get_or_create_conversation(repo_id, conversation_id)
        
        # Save user message
        user_msg = Message(
            role="user",
            content=message,
            conversation_id=conversation.id
        )
        self.db.add(user_msg)
        await self.db.commit()
        
        # Get repository context if available
        repo_context = None
        if repo_id:
            result = await self.db.execute(
                select(Repository).where(Repository.id == repo_id)
            )
            repo = result.scalar_one_or_none()
            if repo:
                repo_context = {
                    "name": repo.name,
                    "id": repo.id,
                    "languages": repo.languages
                }
        
        # Process through agent pipeline
        full_response = ""
        citations = []
        risk_analysis = None
        
        async for chunk in self.orchestrator.process(message, repo_context):
            chunk_type = chunk.get("type", "content")
            
            if chunk_type == "content":
                full_response += chunk.get("content", "")
                yield chunk
                
            elif chunk_type == "citation":
                citations.append(chunk.get("citation"))
                yield chunk
                
            elif chunk_type == "risk":
                risk_analysis = chunk.get("risk")
                yield chunk
                
            elif chunk_type == "status":
                yield chunk
        
        # Save assistant message
        assistant_msg = Message(
            role="assistant",
            content=full_response,
            citations=citations if citations else None,
            risk_analysis=risk_analysis,
            conversation_id=conversation.id
        )
        self.db.add(assistant_msg)
        await self.db.commit()
        
        # Update conversation title if first message
        if not conversation.title:
            conversation.title = message[:50] + ("..." if len(message) > 50 else "")
            await self.db.commit()
    
    async def process_message_sync(
        self,
        message: str,
        repo_id: Optional[int] = None,
        conversation_id: Optional[str] = None
    ) -> dict:
        """Process a message and return full response (non-streaming)."""
        full_response = ""
        citations = []
        risk_analysis = None
        
        async for chunk in self.process_message(message, repo_id, conversation_id):
            chunk_type = chunk.get("type", "content")
            
            if chunk_type == "content":
                full_response += chunk.get("content", "")
            elif chunk_type == "citation":
                citations.append(chunk.get("citation"))
            elif chunk_type == "risk":
                risk_analysis = chunk.get("risk")
        
        return {
            "id": str(datetime.utcnow().timestamp()),
            "content": full_response,
            "citations": citations if citations else None,
            "risk": risk_analysis
        }
    
    async def _get_or_create_conversation(
        self,
        repo_id: Optional[int],
        conversation_id: Optional[str]
    ) -> Conversation:
        """Get existing or create new conversation."""
        if conversation_id and conversation_id != "new":
            try:
                conv_id = int(conversation_id)
                result = await self.db.execute(
                    select(Conversation)
                    .where(Conversation.id == conv_id)
                    .where(Conversation.user_id == self.user_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    return conversation
            except ValueError:
                pass
        
        # Create new conversation
        conversation = Conversation(
            user_id=self.user_id,
            repository_id=repo_id
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        
        return conversation
