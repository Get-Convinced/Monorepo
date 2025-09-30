"""
Pydantic models for chat functionality.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    """Chat message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message processing status enumeration."""
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseMode(str, Enum):
    """Response generation mode (controls temperature)."""
    STRICT = "strict"        # Temperature 0.1 - factual only
    BALANCED = "balanced"    # Temperature 0.5 - balanced
    CREATIVE = "creative"    # Temperature 0.9 - more creative


class ChatSource(BaseModel):
    """Source citation for chat message."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    ragie_document_id: str
    document_name: str
    page_number: Optional[int] = None
    chunk_text: str
    relevance_score: float
    
    # Optional fields
    ragie_chunk_id: Optional[str] = None
    source_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    """Chat message with processing metadata."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_id: str
    role: MessageRole
    content: str
    status: MessageStatus
    created_at: datetime
    
    # Optional fields
    sources: Optional[List[ChatSource]] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # LLM metadata
    model_used: Optional[str] = None
    temperature_used: Optional[float] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    tokens_total: Optional[int] = None
    processing_time_ms: Optional[int] = None
    message_metadata: Optional[Dict[str, Any]] = None
    updated_at: Optional[datetime] = None


class ChatSession(BaseModel):
    """Chat session for conversations."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    organization_id: str
    title: str
    is_active: bool
    is_archived: bool
    temperature: float
    model_name: str
    created_at: datetime
    updated_at: datetime
    
    # Optional fields
    max_context_messages: int = 5
    session_metadata: Optional[Dict[str, Any]] = None
    last_message_at: Optional[datetime] = None
    message_count: int = 0  # Calculated field, not in DB


# Request/Response models for API endpoints

class SendMessageRequest(BaseModel):
    """Request to send a message."""
    question: str = Field(..., min_length=1, max_length=5000, description="User question")
    mode: ResponseMode = Field(ResponseMode.STRICT, description="Response generation mode")
    model: str = Field("gpt-4o", pattern="^(gpt-4o|gpt-3.5-turbo)$", description="LLM model to use")


class SendMessageResponse(BaseModel):
    """Response after sending a message."""
    user_message: ChatMessage
    assistant_message: ChatMessage


class CreateSessionRequest(BaseModel):
    """Request to create a new chat session."""
    # No fields needed, user/org from auth context
    pass


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""
    session: ChatSession


class GetSessionResponse(BaseModel):
    """Response for getting a session."""
    session: ChatSession


class GetSessionMessagesResponse(BaseModel):
    """Response for getting session messages."""
    messages: List[ChatMessage]
    total: int


class GetUserSessionsResponse(BaseModel):
    """Response for getting user's sessions."""
    sessions: List[ChatSession]
    total: int


class ArchiveSessionResponse(BaseModel):
    """Response after archiving a session."""
    success: bool = True
    message: str = "Session archived successfully"


class DeleteSessionResponse(BaseModel):
    """Response after deleting a session."""
    success: bool = True
    message: str = "Session deleted successfully"


class RateLimitInfo(BaseModel):
    """Rate limit information."""
    user_messages_remaining: int
    user_messages_total: int
    user_window_reset_at: datetime
    org_messages_remaining: int
    org_messages_total: int
    org_window_reset_at: datetime
