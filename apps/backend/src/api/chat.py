"""
Chat API endpoints for RAG-powered conversations.

This module provides FastAPI endpoints for chat session management,
message sending, and conversation history retrieval.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database.database import get_async_session
from ..services.chat_service import (
    ChatService, ChatServiceError, RateLimitExceededError, SessionNotFoundError
)
from ..services.ragie_service import RagieService
from ..services.llm_service import LLMService, get_llm_service
from ..api.ragie import get_ragie_service
from ..auth import require_auth, get_organization_id, get_user_and_org_ids
from ..models.chat import (
    ChatSession, ChatMessage, SendMessageRequest, ResponseMode
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


# Dependencies
def get_chat_service(
    session: AsyncSession = Depends(get_async_session),
    ragie_service: RagieService = Depends(get_ragie_service),
    llm_service: LLMService = Depends(get_llm_service)
) -> ChatService:
    """
    Get configured chat service instance.
    
    Args:
        session: Database session
        ragie_service: Ragie service for retrieval
        llm_service: LLM service for generation
        
    Returns:
        Configured chat service
    """
    return ChatService(
        session=session,
        ragie_service=ragie_service,
        llm_service=llm_service
    )


# Endpoints

@router.get(
    "/session",
    response_model=ChatSession,
    summary="Get Active Session",
    description="Get or create active chat session for current user"
)
async def get_active_session(
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatSession:
    user_id, organization_id = ids
    """
    Get or create active chat session for the authenticated user.
    
    Returns:
        Active chat session
    """
    try:
        session = await chat_service.get_or_create_active_session(
            user_id=user_id,
            organization_id=organization_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to get active session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/session/new",
    response_model=ChatSession,
    summary="Create New Session",
    description="Create new chat session and deactivate current"
)
async def create_new_session(
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatSession:
    user_id, organization_id = ids
    """
    Create a new chat session and deactivate the current active session.
    
    Returns:
        New chat session
    """
    try:
        session = await chat_service.create_new_session(
            user_id=user_id,
            organization_id=organization_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/message",
    response_model=ChatMessage,
    summary="Send Message",
    description="Send message and get AI response with source citations"
)
async def send_message(
    request: SendMessageRequest,
    session_id: str = Query(..., description="Chat session ID"),
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatMessage:
    user_id, organization_id = ids
    """
    Send a message to the chat and get an AI-generated response with sources.
    
    This endpoint:
    1. Checks rate limits
    2. Retrieves relevant document chunks from Ragie
    3. Generates response using OpenAI with conversation context
    4. Returns response with source citations
    
    Args:
        request: Message request with question, mode, and model
        session_id: Chat session ID (query parameter)
        
    Returns:
        AI assistant message with sources
        
    Raises:
        HTTPException: 
            - 429 if rate limit exceeded
            - 400 if invalid request
            - 500 if processing fails
    """
    try:
        logger.info("send_message received", extra={
            "session_id": session_id,
            "user_id": user_id,
            "org_id": organization_id,
            "model": request.model,
            "mode": request.mode.value,
            "question_length": len(request.question),
            "question_preview": request.question[:500]
        })
        message = await chat_service.send_message(
            session_id=session_id,
            user_id=user_id,
            organization_id=organization_id,
            question=request.question,
            mode=request.mode,
            model=request.model
        )
        return message
        
    except RateLimitExceededError as e:
        logger.warning(f"Rate limit exceeded for user {user_id}: {e}")
        raise HTTPException(status_code=429, detail=str(e))
        
    except ChatServiceError as e:
        # Surface OpenAI quota/rate errors as 429 if present
        detail = str(e)
        if 'insufficient_quota' in detail or '429' in detail.lower():
            logger.warning("LLM quota/rate limit error", extra={"user_id": user_id, "org_id": organization_id})
            raise HTTPException(status_code=429, detail="LLM rate limit or quota exceeded. Please try again later.")
        logger.error(f"Chat service error: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Failed to send message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/session/{session_id}/messages",
    response_model=List[ChatMessage],
    summary="Get Session Messages",
    description="Get all messages for a chat session"
)
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100, description="Maximum messages to return"),
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> List[ChatMessage]:
    user_id, organization_id = ids
    """
    Get messages for a chat session with their sources.
    
    Args:
        session_id: Chat session ID
        limit: Maximum number of messages to return (1-100)
        
    Returns:
        List of messages with sources
    """
    try:
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            limit=limit
        )
        return messages
        
    except Exception as e:
        logger.error(f"Failed to get messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sessions",
    response_model=List[ChatSession],
    summary="Get User Sessions",
    description="Get all chat sessions for current user"
)
async def get_user_sessions(
    include_archived: bool = Query(False, description="Include archived sessions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum sessions to return"),
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> List[ChatSession]:
    user_id, organization_id = ids
    """
    Get all chat sessions for the authenticated user.
    
    Args:
        include_archived: Whether to include archived sessions
        limit: Maximum number of sessions to return (1-100)
        
    Returns:
        List of chat sessions
    """
    try:
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            include_archived=include_archived,
            limit=limit
        )
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/session/{session_id}/archive",
    status_code=204,
    summary="Archive Session",
    description="Archive a chat session"
)
async def archive_session(
    session_id: str,
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> None:
    user_id, organization_id = ids
    """
    Archive a chat session.
    
    Args:
        session_id: Session ID to archive
    """
    try:
        await chat_service.archive_session(session_id)
        
    except Exception as e:
        logger.error(f"Failed to archive session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/session/{session_id}",
    status_code=204,
    summary="Delete Session",
    description="Permanently delete a chat session and all its messages"
)
async def delete_session(
    session_id: str,
    ids: tuple[str, str] = Depends(get_user_and_org_ids),
    chat_service: ChatService = Depends(get_chat_service)
) -> None:
    user_id, organization_id = ids
    """
    Permanently delete a chat session and all its messages.
    
    Args:
        session_id: Session ID to delete
    """
    try:
        await chat_service.delete_session(session_id)
        
    except Exception as e:
        logger.error(f"Failed to delete session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
