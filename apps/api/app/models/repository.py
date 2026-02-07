from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Repository(Base):
    """Repository model for indexed codebases."""
    
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Indexing status
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, cloning, indexing, ready, error
    indexed_files: Mapped[int] = mapped_column(default=0)
    total_files: Mapped[int] = mapped_column(default=0)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # For change detection
    
    # Metadata
    languages: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # {"python": 45, "javascript": 30}
    
    # Relations
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    def __repr__(self) -> str:
        return f"<Repository {self.name}>"


class Conversation(Base):
    """Conversation model for chat history."""
    
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Relations
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    repository_id: Mapped[Optional[int]] = mapped_column(ForeignKey("repositories.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationship
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation")
    
    def __repr__(self) -> str:
        return f"<Conversation {self.id}>"


class Message(Base):
    """Message model for individual chat messages."""
    
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Metadata
    citations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_analysis: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relations
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message {self.id} ({self.role})>"
