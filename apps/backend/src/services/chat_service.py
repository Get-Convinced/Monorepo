"""
Chat service for RAG-powered conversational AI.

This service orchestrates the RAG flow: session management, retrieval from Ragie,
LLM generation with OpenAI, and persistence to PostgreSQL.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database.models import (
    ChatSession as DBChatSession,
    ChatMessage as DBChatMessage,
    ChatSource as DBChatSource,
)
from ..models.chat import (
    ChatSession, ChatMessage, ChatSource, MessageRole, 
    MessageStatus, ResponseMode
)
from .ragie_service import RagieService
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ChatServiceError(Exception):
    """Base exception for chat service errors."""
    pass


class RateLimitExceededError(ChatServiceError):
    """Rate limit exceeded."""
    pass


class SessionNotFoundError(ChatServiceError):
    """Session not found."""
    pass


class ChatService:
    """Service for chat session and message management with RAG."""
    
    # Rate limits
    USER_HOURLY_LIMIT = 50
    ORG_DAILY_LIMIT = 1000
    
    def __init__(
        self,
        session: AsyncSession,
        ragie_service: RagieService,
        llm_service: LLMService
    ):
        """
        Initialize chat service.
        
        Args:
            session: Database session
            ragie_service: Service for document retrieval
            llm_service: Service for LLM generation
        """
        self.session = session
        self.ragie_service = ragie_service
        self.llm_service = llm_service
    
    async def check_rate_limits(
        self,
        user_id: str,
        organization_id: str
    ) -> None:
        """
        Check if user/org has exceeded rate limits.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            
        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        # Check user hourly limit
        user_hour_start = datetime.utcnow() - timedelta(hours=1)
        user_count_query = select(func.count(DBChatMessage.id)).join(
            DBChatSession
        ).where(
            and_(
                DBChatSession.user_id == user_id,
                DBChatMessage.created_at >= user_hour_start,
                DBChatMessage.role == MessageRole.USER.value
            )
        )
        user_result = await self.session.execute(user_count_query)
        user_count = user_result.scalar() or 0
        
        if user_count >= self.USER_HOURLY_LIMIT:
            raise RateLimitExceededError(
                f"User hourly limit exceeded ({self.USER_HOURLY_LIMIT} messages/hour)"
            )
        
        # Check org daily limit
        org_day_start = datetime.utcnow() - timedelta(days=1)
        org_count_query = select(func.count(DBChatMessage.id)).join(
            DBChatSession
        ).where(
            and_(
                DBChatSession.organization_id == organization_id,
                DBChatMessage.created_at >= org_day_start,
                DBChatMessage.role == MessageRole.USER.value
            )
        )
        org_result = await self.session.execute(org_count_query)
        org_count = org_result.scalar() or 0
        
        if org_count >= self.ORG_DAILY_LIMIT:
            raise RateLimitExceededError(
                f"Organization daily limit exceeded ({self.ORG_DAILY_LIMIT} messages/day)"
            )
    
    async def get_or_create_active_session(
        self,
        user_id: str,
        organization_id: str
    ) -> ChatSession:
        """
        Get active session or create new one.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            
        Returns:
            Active chat session
        """
        # Try to get active session
        query = select(DBChatSession).where(
            and_(
                DBChatSession.user_id == user_id,
                DBChatSession.is_active == True
            )
        )
        result = await self.session.execute(query)
        db_session = result.scalar_one_or_none()
        
        if db_session:
            return self._db_session_to_pydantic(db_session)
        
        # Create new session
        new_session = DBChatSession(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            organization_id=uuid.UUID(organization_id),
            title="New Chat",  # Will be updated with first message
            is_active=True,
            temperature=0.1,  # Default: Strict
            model_name="gpt-4o"
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        
        logger.info(f"Created new active session for user {user_id}")
        return self._db_session_to_pydantic(new_session)
    
    async def create_new_session(
        self,
        user_id: str,
        organization_id: str
    ) -> ChatSession:
        """
        Create new session and deactivate old active session.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            
        Returns:
            New chat session
        """
        # Deactivate current active session
        deactivate_query = update(DBChatSession).where(
            and_(
                DBChatSession.user_id == user_id,
                DBChatSession.is_active == True
            )
        ).values(is_active=False)
        await self.session.execute(deactivate_query)
        await self.session.commit()
        
        # Create new session
        logger.info(f"Creating new session for user {user_id}")
        return await self.get_or_create_active_session(user_id, organization_id)
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        organization_id: str,
        question: str,
        mode: ResponseMode = ResponseMode.STRICT,
        model: str = "gpt-4o"
    ) -> ChatMessage:
        """
        Process user message and generate AI response using RAG.
        
        Steps:
        1. Check rate limits
        2. Save user message
        3. Retrieve relevant chunks from Ragie
        4. Get conversation history
        5. Generate LLM response
        6. Save AI message with sources
        7. Update session
        
        Args:
            session_id: Chat session ID
            user_id: User ID
            organization_id: Organization ID
            question: User question
            mode: Response generation mode
            model: LLM model to use
            
        Returns:
            AI assistant message with sources
            
        Raises:
            RateLimitExceededError: If rate limit exceeded
            ChatServiceError: If processing fails
        """
        try:
            # 1. Check rate limits
            await self.check_rate_limits(user_id, organization_id)
            
            # 2. Save user message
            user_message = DBChatMessage(
                id=uuid.uuid4(),
                session_id=uuid.UUID(session_id),
                role=MessageRole.USER.value,
                content=question,
                status=MessageStatus.COMPLETED.value
            )
            self.session.add(user_message)
            await self.session.commit()
            
            logger.info(
                "Processing user message",
                extra={
                    "session_id": session_id,
                    "user_id": user_id,
                    "question_length": len(question)
                }
            )
            
            # 3. Retrieve from Ragie with enhanced features
            # Detect if query is time-sensitive
            is_time_sensitive = any(word in question.lower() for word in [
                "latest", "recent", "new", "update", "current", "today", "yesterday",
                "this week", "this month", "now", "2025", "2024"
            ])
            
            retrieval_result = await self.ragie_service.retrieve_chunks(
                query=question,
                organization_id=organization_id,
                max_chunks=20,  # Increased from 15 for better coverage
                rerank=True,  # Enable reranking for better relevance
                recency_bias=is_time_sensitive,  # Favor recent docs for time-sensitive queries
                max_chunks_per_document=5,  # Ensure diversity across documents
                min_score=0.5,  # Filter low-quality chunks
                use_cache=True  # Cache for 5 minutes
            )
            
            # Build sources directly from scored_chunks (no extra GETs)
            chunks_with_names = []
            for chunk in retrieval_result.scored_chunks:
                chunks_with_names.append({
                    "document_id": chunk.document_id,
                    "document_name": getattr(chunk, "document_name", None) or "Unknown Document",
                    "text": chunk.text,
                    "score": chunk.score,
                    "page_number": chunk.metadata.get("page") if hasattr(chunk, "metadata") and chunk.metadata else None,
                    "chunk_id": chunk.id
                })
            
            # 4. Get conversation history
            history_query = select(DBChatMessage).where(
                DBChatMessage.session_id == uuid.UUID(session_id)
            ).order_by(DBChatMessage.created_at.desc()).limit(10)
            history_result = await self.session.execute(history_query)
            history_messages = history_result.scalars().all()
            
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history_messages)
            ]
            
            # 5. Generate LLM response with source tracking
            llm_result = await self.llm_service.generate_response_with_sources(
                question=question,
                chunks=chunks_with_names,
                mode=mode,
                model=model,
                conversation_history=conversation_history
            )
            
            # Parse sources_used from LLM
            sources_used_map = {}  # source_num -> reason
            for source_info in llm_result.get("sources_used", []):
                source_num = source_info.get("source_num")
                reason = source_info.get("reason", "")
                if source_num and 1 <= source_num <= len(chunks_with_names):
                    sources_used_map[source_num] = reason
            
            # 6. Save AI message
            ai_message = DBChatMessage(
                id=uuid.uuid4(),
                session_id=uuid.UUID(session_id),
                role=MessageRole.ASSISTANT.value,
                content=llm_result["content"],
                status=MessageStatus.COMPLETED.value,
                model_used=llm_result["model"],
                temperature_used=llm_result["temperature"],
                tokens_prompt=llm_result["tokens_prompt"],
                tokens_completion=llm_result["tokens_completion"],
                tokens_total=llm_result["tokens_total"],
                processing_time_ms=llm_result["processing_time_ms"]
            )
            self.session.add(ai_message)
            await self.session.commit()
            await self.session.refresh(ai_message)
            
            # 7. Save sources with usage tracking
            sources = []
            for idx, chunk in enumerate(chunks_with_names, 1):
                source_num = idx
                is_used = source_num in sources_used_map
                usage_reason = sources_used_map.get(source_num)
                
                db_source = DBChatSource(
                    id=uuid.uuid4(),
                    message_id=ai_message.id,
                    ragie_document_id=chunk["document_id"],
                    ragie_chunk_id=chunk.get("chunk_id"),
                    document_name=chunk["document_name"],
                    page_number=chunk.get("page_number"),
                    chunk_text=chunk["text"][:500] if chunk["text"] else None,  # First 500 chars
                    relevance_score=chunk["score"],
                    is_used=is_used,  # NEW: Track if LLM used this source
                    usage_reason=usage_reason,  # NEW: Why LLM used it
                    source_number=source_num  # NEW: Original retrieval order
                )
                self.session.add(db_source)
                sources.append(self._db_source_to_pydantic(db_source))
            
            await self.session.commit()
            
            logger.info(
                "Sources saved with usage tracking",
                extra={
                    "total_sources": len(sources),
                    "used_sources": len(sources_used_map),
                    "used_function_calling": llm_result.get("used_function_calling", False)
                }
            )
            
            # 8. Update session
            await self._update_session_after_message(session_id, question)
            
            logger.info(
                "Message processed successfully",
                extra={
                    "session_id": session_id,
                    "sources_count": len(sources),
                    "tokens_total": llm_result["tokens_total"]
                }
            )
            
            return self._db_message_to_pydantic(ai_message, sources)
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Message processing failed: {e}", exc_info=True)
            
            # Save failed message
            try:
                error_message = DBChatMessage(
                    id=uuid.uuid4(),
                    session_id=uuid.UUID(session_id),
                    role=MessageRole.ASSISTANT.value,
                    content="I encountered an error processing your question.",
                    status=MessageStatus.FAILED.value,
                    error_message=str(e)
                )
                self.session.add(error_message)
                await self.session.commit()
            except Exception as save_error:
                logger.error(f"Failed to save error message: {save_error}")
            
            raise ChatServiceError(f"Failed to process message: {e}")
    
    async def _update_session_after_message(
        self,
        session_id: str,
        first_message_content: Optional[str] = None
    ) -> None:
        """Update session title and timestamp."""
        update_values = {
            "updated_at": datetime.utcnow(),
            "last_message_at": datetime.utcnow()
        }
        
        # Update title if this is first message
        if first_message_content:
            session_query = select(DBChatSession).where(
                DBChatSession.id == uuid.UUID(session_id)
            )
            result = await self.session.execute(session_query)
            session = result.scalar_one_or_none()
            
            if session and session.title == "New Chat":
                # Truncate first message for title
                title = first_message_content[:50]
                if len(first_message_content) > 50:
                    title += "..."
                update_values["title"] = title
        
        update_query = update(DBChatSession).where(
            DBChatSession.id == uuid.UUID(session_id)
        ).values(**update_values)
        await self.session.execute(update_query)
        await self.session.commit()
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum messages to return
            
        Returns:
            List of messages with sources
        """
        query = select(DBChatMessage).where(
            DBChatMessage.session_id == uuid.UUID(session_id)
        ).order_by(DBChatMessage.created_at.asc()).limit(limit)
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        # Load sources for each message
        pydantic_messages = []
        for msg in messages:
            sources = await self._get_message_sources(str(msg.id))
            pydantic_messages.append(self._db_message_to_pydantic(msg, sources))
        
        return pydantic_messages
    
    async def _get_message_sources(self, message_id: str) -> List[ChatSource]:
        """Get sources for a message."""
        query = select(DBChatSource).where(
            DBChatSource.message_id == uuid.UUID(message_id)
        )
        result = await self.session.execute(query)
        sources = result.scalars().all()
        return [self._db_source_to_pydantic(s) for s in sources]
    
    async def get_user_sessions(
        self,
        user_id: str,
        include_archived: bool = False,
        limit: int = 50
    ) -> List[ChatSession]:
        """
        Get user's chat sessions.
        
        Args:
            user_id: User ID
            include_archived: Include archived sessions
            limit: Maximum sessions to return
            
        Returns:
            List of chat sessions
        """
        conditions = [DBChatSession.user_id == user_id]
        if not include_archived:
            conditions.append(DBChatSession.is_archived == False)
        
        query = select(DBChatSession).where(
            and_(*conditions)
        ).order_by(DBChatSession.updated_at.desc()).limit(limit)
        
        result = await self.session.execute(query)
        sessions = result.scalars().all()
        return [self._db_session_to_pydantic(s) for s in sessions]
    
    async def archive_session(self, session_id: str) -> None:
        """Archive a session."""
        update_query = update(DBChatSession).where(
            DBChatSession.id == uuid.UUID(session_id)
        ).values(is_archived=True, is_active=False)
        await self.session.execute(update_query)
        await self.session.commit()
        
        logger.info(f"Archived session {session_id}")
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages."""
        session_query = select(DBChatSession).where(
            DBChatSession.id == uuid.UUID(session_id)
        )
        result = await self.session.execute(session_query)
        session = result.scalar_one_or_none()
        
        if session:
            await self.session.delete(session)
            await self.session.commit()
            logger.info(f"Deleted session {session_id}")
    
    # Helper methods for DB <-> Pydantic conversion
    def _db_session_to_pydantic(self, db_session: DBChatSession) -> ChatSession:
        """Convert DB session to Pydantic model."""
        return ChatSession(
            id=str(db_session.id),
            user_id=str(db_session.user_id),
            organization_id=str(db_session.organization_id),
            title=db_session.title,
            is_active=db_session.is_active,
            is_archived=db_session.is_archived,
            temperature=db_session.temperature,
            model_name=db_session.model_name,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            last_message_at=db_session.last_message_at,
            max_context_messages=db_session.max_context_messages,
            session_metadata=db_session.session_metadata
        )
    
    def _db_message_to_pydantic(
        self,
        db_message: DBChatMessage,
        sources: List[ChatSource] = None
    ) -> ChatMessage:
        """Convert DB message to Pydantic model."""
        return ChatMessage(
            id=str(db_message.id),
            session_id=str(db_message.session_id),
            role=MessageRole(db_message.role),
            content=db_message.content,
            status=MessageStatus(db_message.status),
            sources=sources,
            error_message=db_message.error_message,
            error_details=db_message.error_details,
            created_at=db_message.created_at,
            model_used=db_message.model_used,
            temperature_used=db_message.temperature_used,
            tokens_prompt=db_message.tokens_prompt,
            tokens_completion=db_message.tokens_completion,
            tokens_total=db_message.tokens_total,
            processing_time_ms=db_message.processing_time_ms,
            message_metadata=db_message.message_metadata,
            updated_at=db_message.updated_at
        )
    
    def _db_source_to_pydantic(self, db_source: DBChatSource) -> ChatSource:
        """Convert DB source to Pydantic model."""
        return ChatSource(
            id=str(db_source.id),
            ragie_document_id=db_source.ragie_document_id,
            document_name=db_source.document_name,
            page_number=db_source.page_number,
            chunk_text=db_source.chunk_text or "",
            relevance_score=db_source.relevance_score or 0.0,
            is_used=db_source.is_used if hasattr(db_source, 'is_used') else False,  # NEW
            usage_reason=db_source.usage_reason if hasattr(db_source, 'usage_reason') else None,  # NEW
            source_number=db_source.source_number if hasattr(db_source, 'source_number') else None,  # NEW
            ragie_chunk_id=db_source.ragie_chunk_id,
            source_metadata=db_source.source_metadata,
            created_at=db_source.created_at
        )
