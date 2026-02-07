from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# === Repository Schemas ===

class RepositoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None


class RepositoryCreate(RepositoryBase):
    local_path: Optional[str] = None


class RepositoryResponse(RepositoryBase):
    id: int
    local_path: Optional[str] = None
    status: str
    indexed_files: int
    total_files: int
    languages: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Chat Schemas ===

class Citation(BaseModel):
    file: str
    lines: Optional[str] = None


class RiskAnalysis(BaseModel):
    level: str  # low, medium, high
    description: str


class ChatMessageRequest(BaseModel):
    message: str
    repo_id: Optional[int] = None
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    citations: Optional[List[Citation]] = None
    risk: Optional[RiskAnalysis] = None
    timestamp: datetime


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str] = None
    repository_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
