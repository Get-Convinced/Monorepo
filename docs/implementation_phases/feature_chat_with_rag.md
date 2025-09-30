# Feature Implementation: RAG-Powered Chat with Source Citations

## 🎯 **Feature Overview**

Implement a conversational AI chat interface that uses Retrieval-Augmented Generation (RAG) to answer questions based on uploaded documents, with transparent source citations and persistent chat history.

**Status**: 🟢 Ready for Implementation  
**Priority**: P0 (Core Feature)  
**Estimated Effort**: 2-3 weeks  
**Target**: MVP Launch

---

## 📋 **MVP Scope**

### **What We're Building**

#### **Core Functionality**
- ✅ Chat interface with message history
- ✅ RAG-powered responses using Ragie retrieval + OpenAI LLM
- ✅ Source citations showing document name and page numbers
- ✅ Persistent chat sessions stored in PostgreSQL
- ✅ Active session management (resume on return)
- ✅ Chat history sidebar (collapsible)
- ✅ Streaming responses (token-by-token)
- ✅ Error handling with retry capability
- ✅ Rate limiting (50 msg/user/hour, 1000 msg/org/day)
- ✅ Response mode selection (Strict/Balanced/Creative)

#### **User Experience**
- User opens chat → Resumes active session OR starts new empty chat
- User asks question → See "thinking" animation → Response streams in
- Response shows source cards (document icon, name, page number)
- User can create new chat, view history, archive/delete old chats
- Settings dropdown to change response mode (controls temperature)

#### **Technical Architecture**
```
Frontend (Next.js + shadcn/ui)
    ↓
Backend FastAPI (/api/v1/chat/*)
    ↓
Chat Service → Ragie Service (retrieve chunks)
             → LLM Service (OpenAI GPT-4o)
             → Database (save messages)
    ↓
Response with sources
```

---

## 🚫 **Post-MVP: Deferred Features**

### **Why Deferred & When to Add**

| Feature | Rationale for Deferring | Add When |
|---------|-------------------------|----------|
| **Smart Context Selection** | Simple chronological context (last 5 messages) is sufficient for MVP | Users report context issues or need longer conversations |
| **Document Filtering** | Users can already filter via all uploaded docs in their partition | Users request ability to chat with specific document subsets |
| **Shared Organization Chats** | Private sessions reduce complexity; collaboration not core to MVP | Multi-user collaboration becomes a requirement |
| **Response Caching** | Adds complexity; low traffic expected initially | API costs become significant (>$500/month) |
| **Smart Title Generation** | Simple truncation is fast and clear | Users complain about unclear session titles |
| **Multi-modal Responses** | Current text-only sufficient for document Q&A | Need to display images, tables, charts in responses |
| **Tool Use / Function Calling** | Not needed for document Q&A use case | Need to integrate with external APIs, calculations |
| **Chain-of-Thought Reasoning** | GPT-4o is capable without explicit CoT prompting | Quality issues arise that CoT would solve |
| **Feedback Loop (👍👎)** | No active learning pipeline yet | Want to improve model based on user feedback |
| **Per-User/Session Preferences** | Organization-wide settings sufficient for MVP | Users request personalized tone, language, format |
| **Configurable Rate Limits** | Fixed limits prevent abuse without complexity | Need tiered pricing or custom enterprise limits |
| **Retrieval Optimization** | Current Ragie search is fast enough (<500ms) | Search becomes bottleneck (>2s P95) |
| **Message Retention Policies** | Keep-forever is simplest; storage is cheap | Database size becomes an issue (>100GB) |

### **Code Extensibility for Future Features**

The implementation will include hooks for future features:
- **Temperature field in DB** → Easy to add per-session temperature
- **Session metadata JSON field** → Store future preferences
- **Message metadata JSON field** → Add feedback scores, citations
- **Rate limit service abstraction** → Swap fixed limits for dynamic
- **Prompt template system** → Easy to modify system prompts

---

## 💾 **Database Schema**

### **New Tables**

#### **1. `chat_sessions` Table**
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Session metadata
    title VARCHAR(255) NOT NULL,  -- Truncated from first message
    is_active BOOLEAN DEFAULT true,  -- Only one active per user
    is_archived BOOLEAN DEFAULT false,
    
    -- Configuration (extensible for future)
    temperature FLOAT DEFAULT 0.1,  -- 0.1=Strict, 0.5=Balanced, 0.9=Creative
    model_name VARCHAR(100) DEFAULT 'gpt-4o',
    max_context_messages INTEGER DEFAULT 5,
    session_metadata JSONB,  -- Future: document filters, preferences
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT unique_active_session_per_user 
        UNIQUE (user_id, is_active) 
        WHERE is_active = true
);

CREATE INDEX idx_chat_sessions_user_updated 
    ON chat_sessions(user_id, updated_at DESC);
CREATE INDEX idx_chat_sessions_org_updated 
    ON chat_sessions(organization_id, updated_at DESC);
CREATE INDEX idx_chat_sessions_active 
    ON chat_sessions(user_id, is_active) 
    WHERE is_active = true;
```

#### **2. `chat_messages` Table**
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Processing metadata
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'streaming', 'completed', 'failed')),
    error_message TEXT,
    error_details JSONB,
    
    -- LLM metadata (for assistant messages)
    model_used VARCHAR(100),
    temperature_used FLOAT,
    tokens_prompt INTEGER,
    tokens_completion INTEGER,
    tokens_total INTEGER,
    processing_time_ms INTEGER,
    
    -- Message metadata (extensible)
    message_metadata JSONB,  -- Future: feedback scores, edit history
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_created 
    ON chat_messages(session_id, created_at ASC);
CREATE INDEX idx_chat_messages_role 
    ON chat_messages(session_id, role);
```

#### **3. `chat_sources` Table**
```sql
CREATE TABLE chat_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    
    -- Ragie document reference
    ragie_document_id VARCHAR(255) NOT NULL,
    ragie_chunk_id VARCHAR(255),
    
    -- Source metadata
    document_name VARCHAR(500) NOT NULL,
    page_number INTEGER,
    chunk_text TEXT,  -- Denormalized for fast display
    relevance_score FLOAT,
    
    -- Additional metadata
    source_metadata JSONB,  -- Future: section, paragraph, confidence
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_sources_message 
    ON chat_sources(message_id);
CREATE INDEX idx_chat_sources_ragie_doc 
    ON chat_sources(ragie_document_id);
```

#### **4. `chat_rate_limits` Table**
```sql
CREATE TABLE chat_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Rate limit scope
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Limits (at least one must be set)
    messages_count INTEGER DEFAULT 0,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_duration_hours INTEGER DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT check_scope CHECK (
        (user_id IS NOT NULL AND organization_id IS NULL) OR
        (user_id IS NULL AND organization_id IS NOT NULL)
    )
);

CREATE INDEX idx_rate_limits_user_window 
    ON chat_rate_limits(user_id, window_start) 
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_rate_limits_org_window 
    ON chat_rate_limits(organization_id, window_start) 
    WHERE organization_id IS NOT NULL;
```

### **Migration Plan**

```bash
# Create migration
cd packages/database
alembic revision --autogenerate -m "add_chat_tables"

# Review migration file
# Edit: alembic/versions/XXX_add_chat_tables.py

# Apply migration
alembic upgrade head

# Verify
psql -d ai_knowledge_agent -c "\dt chat_*"
```

---

## 🔧 **Backend Implementation**

### **Phase 1: Dependencies & Models**

#### **1.1 Add Dependencies**
```toml
# apps/backend/pyproject.toml
[project]
dependencies = [
    # ... existing ...
    "openai>=1.0.0",  # OpenAI client
    "tiktoken>=0.5.0",  # Token counting
]
```

#### **1.2 Update Database Models**
```python
# packages/database/shared_database/models.py
# Add new models: ChatSession, ChatMessage, ChatSource, ChatRateLimit
# (Follow existing patterns)
```

#### **1.3 Create Pydantic Schemas**
```python
# apps/backend/src/models/chat.py

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageStatus(str, Enum):
    PENDING = "pending"
    STREAMING = "streaming"
    COMPLETED = "completed"
    FAILED = "failed"

class ResponseMode(str, Enum):
    STRICT = "strict"        # Temperature 0.1
    BALANCED = "balanced"    # Temperature 0.5
    CREATIVE = "creative"    # Temperature 0.9

class ChatSource(BaseModel):
    id: str
    ragie_document_id: str
    document_name: str
    page_number: Optional[int] = None
    chunk_text: str
    relevance_score: float

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    status: MessageStatus
    sources: Optional[List[ChatSource]] = None
    error_message: Optional[str] = None
    created_at: datetime
    
    # Metadata (optional)
    tokens_total: Optional[int] = None
    processing_time_ms: Optional[int] = None

class ChatSession(BaseModel):
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
    last_message_at: Optional[datetime] = None
    message_count: int = 0
```

---

### **Phase 2: Service Layer**

#### **2.1 LLM Service**
```python
# apps/backend/src/services/llm_service.py

import logging
import os
import time
from typing import List, Dict, Any, AsyncIterator
from openai import AsyncOpenAI, OpenAIError
import tiktoken

from ..models.chat import ResponseMode, MessageRole

logger = logging.getLogger(__name__)

class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass

class LLMService:
    """Service for OpenAI LLM interactions."""
    
    TEMPERATURE_MAP = {
        ResponseMode.STRICT: 0.1,
        ResponseMode.BALANCED: 0.5,
        ResponseMode.CREATIVE: 0.9
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def _build_system_prompt(self, mode: ResponseMode) -> str:
        """Build system prompt based on response mode."""
        base_prompt = """You are a helpful AI assistant that answers questions based on provided document context.

Instructions:
- Use ONLY the information from the provided context to answer questions
- Cite sources by referring to document names when possible
- Be accurate and precise
"""
        
        if mode == ResponseMode.STRICT:
            return base_prompt + """- If the context doesn't contain enough information, say "I don't have enough information to answer that."
- Do not make assumptions or infer beyond what's explicitly stated"""
        
        elif mode == ResponseMode.BALANCED:
            return base_prompt + """- If the context is insufficient, clearly state what information is missing
- You may make reasonable inferences if they're logical and clearly stated"""
        
        else:  # CREATIVE
            return base_prompt + """- Feel free to provide broader context and make reasonable inferences
- You may elaborate on topics using your general knowledge when helpful
- Always indicate when you're providing information beyond the source documents"""
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format Ragie chunks into context string."""
        if not chunks:
            return "No relevant documents found."
        
        context_parts = ["Relevant document excerpts:\n"]
        for i, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("document_name", "Unknown")
            page = chunk.get("page_number")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            
            page_info = f", Page {page}" if page else ""
            context_parts.append(
                f"\n[Source {i}] {doc_name}{page_info} (Relevance: {score:.2f})\n{text}\n"
            )
        
        return "\n".join(context_parts)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    async def generate_response(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        mode: ResponseMode = ResponseMode.STRICT,
        model: str = "gpt-4o",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using OpenAI.
        
        Returns:
            {
                "content": str,
                "tokens_prompt": int,
                "tokens_completion": int,
                "tokens_total": int,
                "model": str,
                "temperature": float,
                "processing_time_ms": int
            }
        """
        start_time = time.time()
        
        try:
            # Build messages
            system_prompt = self._build_system_prompt(mode)
            context = self._format_context(chunks)
            temperature = self.TEMPERATURE_MAP[mode]
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 messages)
            if conversation_history:
                messages.extend(conversation_history[-5:])
            
            # Add current question with context
            user_message = f"{context}\n\nQuestion: {question}"
            messages.append({"role": "user", "content": user_message})
            
            logger.info("Generating LLM response", extra={
                "model": model,
                "mode": mode.value,
                "chunks_count": len(chunks),
                "history_messages": len(conversation_history or [])
            })
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
                stream=False  # Non-streaming for MVP
            )
            
            content = response.choices[0].message.content
            usage = response.usage
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info("LLM response generated", extra={
                "tokens_total": usage.total_tokens,
                "processing_time_ms": processing_time_ms
            })
            
            return {
                "content": content,
                "tokens_prompt": usage.prompt_tokens,
                "tokens_completion": usage.completion_tokens,
                "tokens_total": usage.total_tokens,
                "model": model,
                "temperature": temperature,
                "processing_time_ms": processing_time_ms
            }
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(f"LLM generation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise LLMServiceError(f"Unexpected error: {e}")
    
    async def generate_response_stream(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        mode: ResponseMode = ResponseMode.STRICT,
        model: str = "gpt-4o",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncIterator[str]:
        """
        Generate streaming response (for post-MVP).
        
        Yields tokens as they're generated.
        """
        # Build messages (same as non-streaming)
        system_prompt = self._build_system_prompt(mode)
        context = self._format_context(chunks)
        temperature = self.TEMPERATURE_MAP[mode]
        
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history[-5:])
        
        user_message = f"{context}\n\nQuestion: {question}"
        messages.append({"role": "user", "content": user_message})
        
        # Stream response
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=1500,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

def get_llm_service() -> LLMService:
    """Dependency to get LLM service."""
    return LLMService()
```

#### **2.2 Chat Service**
```python
# apps/backend/src/services/chat_service.py

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database.models import (
    ChatSession as DBChatSession,
    ChatMessage as DBChatMessage,
    ChatSource as DBChatSource,
    ChatRateLimit
)
from ..models.chat import (
    ChatSession, ChatMessage, ChatSource, MessageRole, 
    MessageStatus, ResponseMode
)
from ..services.ragie_service import RagieService
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ChatServiceError(Exception):
    """Base exception for chat service errors."""
    pass

class RateLimitExceededError(ChatServiceError):
    """Rate limit exceeded."""
    pass

class ChatService:
    """Service for chat session and message management."""
    
    # Rate limits
    USER_HOURLY_LIMIT = 50
    ORG_DAILY_LIMIT = 1000
    
    def __init__(
        self,
        session: AsyncSession,
        ragie_service: RagieService,
        llm_service: LLMService
    ):
        self.session = session
        self.ragie_service = ragie_service
        self.llm_service = llm_service
    
    async def check_rate_limits(
        self,
        user_id: str,
        organization_id: str
    ) -> None:
        """Check if user/org has exceeded rate limits."""
        # Check user hourly limit
        user_hour_start = datetime.utcnow() - timedelta(hours=1)
        user_count_query = select(ChatMessage).join(ChatSession).where(
            and_(
                ChatSession.user_id == user_id,
                ChatMessage.created_at >= user_hour_start,
                ChatMessage.role == MessageRole.USER
            )
        )
        user_result = await self.session.execute(user_count_query)
        user_count = len(user_result.scalars().all())
        
        if user_count >= self.USER_HOURLY_LIMIT:
            raise RateLimitExceededError(
                f"User hourly limit exceeded ({self.USER_HOURLY_LIMIT} messages/hour)"
            )
        
        # Check org daily limit
        org_day_start = datetime.utcnow() - timedelta(days=1)
        org_count_query = select(ChatMessage).join(ChatSession).where(
            and_(
                ChatSession.organization_id == organization_id,
                ChatMessage.created_at >= org_day_start,
                ChatMessage.role == MessageRole.USER
            )
        )
        org_result = await self.session.execute(org_count_query)
        org_count = len(org_result.scalars().all())
        
        if org_count >= self.ORG_DAILY_LIMIT:
            raise RateLimitExceededError(
                f"Organization daily limit exceeded ({self.ORG_DAILY_LIMIT} messages/day)"
            )
    
    async def get_or_create_active_session(
        self,
        user_id: str,
        organization_id: str
    ) -> ChatSession:
        """Get active session or create new one."""
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
            user_id=user_id,
            organization_id=organization_id,
            title="New Chat",  # Will be updated with first message
            is_active=True,
            temperature=0.1,  # Default: Strict
            model_name="gpt-4o"
        )
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        
        return self._db_session_to_pydantic(new_session)
    
    async def create_new_session(
        self,
        user_id: str,
        organization_id: str
    ) -> ChatSession:
        """Create new session and deactivate old active session."""
        # Deactivate current active session
        deactivate_query = update(DBChatSession).where(
            and_(
                DBChatSession.user_id == user_id,
                DBChatSession.is_active == True
            )
        ).values(is_active=False)
        await self.session.execute(deactivate_query)
        
        # Create new session
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
        Process user message and generate AI response.
        
        Steps:
        1. Check rate limits
        2. Save user message
        3. Retrieve relevant chunks from Ragie
        4. Get conversation history
        5. Generate LLM response
        6. Save AI message with sources
        7. Update session
        """
        try:
            # 1. Check rate limits
            await self.check_rate_limits(user_id, organization_id)
            
            # 2. Save user message
            user_message = DBChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=MessageRole.USER,
                content=question,
                status=MessageStatus.COMPLETED
            )
            self.session.add(user_message)
            await self.session.commit()
            
            # 3. Retrieve from Ragie
            logger.info(f"Retrieving chunks for question", extra={
                "session_id": session_id,
                "question_length": len(question)
            })
            
            retrieval_result = await self.ragie_service.retrieve_chunks(
                query=question,
                organization_id=organization_id,
                max_chunks=5
            )
            
            # Get document names
            chunks_with_names = []
            for chunk in retrieval_result.chunks:
                try:
                    doc = await self.ragie_service.get_document(
                        document_id=chunk.document_id,
                        organization_id=organization_id
                    )
                    chunks_with_names.append({
                        "document_id": chunk.document_id,
                        "document_name": doc.name,
                        "text": chunk.text,
                        "score": chunk.score,
                        "page_number": chunk.metadata.get("page"),
                        "chunk_id": chunk.id
                    })
                except Exception as e:
                    logger.warning(f"Failed to get doc name: {e}")
                    chunks_with_names.append({
                        "document_id": chunk.document_id,
                        "document_name": "Unknown Document",
                        "text": chunk.text,
                        "score": chunk.score,
                        "page_number": chunk.metadata.get("page"),
                        "chunk_id": chunk.id
                    })
            
            # 4. Get conversation history
            history_query = select(DBChatMessage).where(
                DBChatMessage.session_id == session_id
            ).order_by(DBChatMessage.created_at.desc()).limit(10)
            history_result = await self.session.execute(history_query)
            history_messages = history_result.scalars().all()
            
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in reversed(history_messages)
            ]
            
            # 5. Generate LLM response
            llm_result = await self.llm_service.generate_response(
                question=question,
                chunks=chunks_with_names,
                mode=mode,
                model=model,
                conversation_history=conversation_history
            )
            
            # 6. Save AI message
            ai_message = DBChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content=llm_result["content"],
                status=MessageStatus.COMPLETED,
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
            
            # 7. Save sources
            sources = []
            for chunk in chunks_with_names:
                db_source = DBChatSource(
                    id=uuid.uuid4(),
                    message_id=ai_message.id,
                    ragie_document_id=chunk["document_id"],
                    ragie_chunk_id=chunk.get("chunk_id"),
                    document_name=chunk["document_name"],
                    page_number=chunk.get("page_number"),
                    chunk_text=chunk["text"][:500],  # First 500 chars
                    relevance_score=chunk["score"]
                )
                self.session.add(db_source)
                sources.append(self._db_source_to_pydantic(db_source))
            
            await self.session.commit()
            
            # 8. Update session
            await self._update_session_after_message(session_id, question)
            
            return self._db_message_to_pydantic(ai_message, sources)
            
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            
            # Save failed message
            error_message = DBChatMessage(
                id=uuid.uuid4(),
                session_id=session_id,
                role=MessageRole.ASSISTANT,
                content="I encountered an error processing your question.",
                status=MessageStatus.FAILED,
                error_message=str(e)
            )
            self.session.add(error_message)
            await self.session.commit()
            
            raise ChatServiceError(f"Failed to process message: {e}")
    
    async def _update_session_after_message(
        self,
        session_id: str,
        first_message_content: Optional[str] = None
    ):
        """Update session title and timestamp."""
        update_values = {
            "updated_at": datetime.utcnow(),
            "last_message_at": datetime.utcnow()
        }
        
        # Update title if this is first message
        if first_message_content:
            session_query = select(DBChatSession).where(
                DBChatSession.id == session_id
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
            DBChatSession.id == session_id
        ).values(**update_values)
        await self.session.execute(update_query)
        await self.session.commit()
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Get messages for a session."""
        query = select(DBChatMessage).where(
            DBChatMessage.session_id == session_id
        ).order_by(DBChatMessage.created_at.asc()).limit(limit)
        
        result = await self.session.execute(query)
        messages = result.scalars().all()
        
        # Load sources for each message
        pydantic_messages = []
        for msg in messages:
            sources = await self._get_message_sources(msg.id)
            pydantic_messages.append(self._db_message_to_pydantic(msg, sources))
        
        return pydantic_messages
    
    async def _get_message_sources(self, message_id: str) -> List[ChatSource]:
        """Get sources for a message."""
        query = select(DBChatSource).where(
            DBChatSource.message_id == message_id
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
        """Get user's chat sessions."""
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
            DBChatSession.id == session_id
        ).values(is_archived=True, is_active=False)
        await self.session.execute(update_query)
        await self.session.commit()
    
    async def delete_session(self, session_id: str) -> None:
        """Delete a session and all its messages."""
        session_query = select(DBChatSession).where(
            DBChatSession.id == session_id
        )
        result = await self.session.execute(session_query)
        session = result.scalar_one_or_none()
        
        if session:
            await self.session.delete(session)
            await self.session.commit()
    
    # Helper methods for DB <-> Pydantic conversion
    def _db_session_to_pydantic(self, db_session: DBChatSession) -> ChatSession:
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
            last_message_at=db_session.last_message_at
        )
    
    def _db_message_to_pydantic(
        self,
        db_message: DBChatMessage,
        sources: List[ChatSource] = None
    ) -> ChatMessage:
        return ChatMessage(
            id=str(db_message.id),
            session_id=str(db_message.session_id),
            role=db_message.role,
            content=db_message.content,
            status=db_message.status,
            sources=sources,
            error_message=db_message.error_message,
            created_at=db_message.created_at,
            tokens_total=db_message.tokens_total,
            processing_time_ms=db_message.processing_time_ms
        )
    
    def _db_source_to_pydantic(self, db_source: DBChatSource) -> ChatSource:
        return ChatSource(
            id=str(db_source.id),
            ragie_document_id=db_source.ragie_document_id,
            document_name=db_source.document_name,
            page_number=db_source.page_number,
            chunk_text=db_source.chunk_text,
            relevance_score=db_source.relevance_score
        )
```

#### **2.3 Chat API Endpoints**
```python
# apps/backend/src/api/chat.py

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database.database import get_async_session
from ..services.chat_service import ChatService, ChatServiceError, RateLimitExceededError
from ..services.ragie_service import RagieService
from ..services.llm_service import LLMService, get_llm_service
from ..api.ragie import get_ragie_service
from ..auth import require_auth, get_organization_id
from ..models.chat import (
    ChatSession, ChatMessage, ResponseMode, MessageRole
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Request/Response Models
class SendMessageRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=5000)
    mode: ResponseMode = ResponseMode.STRICT
    model: str = Field("gpt-4o", pattern="^(gpt-4o|gpt-3.5-turbo)$")

class CreateSessionRequest(BaseModel):
    """Request to create new chat session."""
    pass  # No fields needed, will use auth context

# Dependencies
def get_chat_service(
    session: AsyncSession = Depends(get_async_session),
    ragie_service: RagieService = Depends(get_ragie_service),
    llm_service: LLMService = Depends(get_llm_service)
) -> ChatService:
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
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatSession:
    """Get or create active session."""
    try:
        session = await chat_service.get_or_create_active_session(
            user_id=user_id,
            organization_id=organization_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to get active session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/session/new",
    response_model=ChatSession,
    summary="Create New Session",
    description="Create new chat session and deactivate current"
)
async def create_new_session(
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatSession:
    """Create new session."""
    try:
        session = await chat_service.create_new_session(
            user_id=user_id,
            organization_id=organization_id
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/message",
    response_model=ChatMessage,
    summary="Send Message",
    description="Send message and get AI response with sources"
)
async def send_message(
    request: SendMessageRequest,
    session_id: str = Query(..., description="Chat session ID"),
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatMessage:
    """Send message to chat."""
    try:
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
        raise HTTPException(status_code=429, detail=str(e))
    except ChatServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/session/{session_id}/messages",
    response_model=List[ChatMessage],
    summary="Get Session Messages",
    description="Get all messages for a session"
)
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(require_auth),
    chat_service: ChatService = Depends(get_chat_service)
) -> List[ChatMessage]:
    """Get messages for session."""
    try:
        messages = await chat_service.get_session_messages(
            session_id=session_id,
            limit=limit
        )
        return messages
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/sessions",
    response_model=List[ChatSession],
    summary="Get User Sessions",
    description="Get all chat sessions for current user"
)
async def get_user_sessions(
    include_archived: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(require_auth),
    chat_service: ChatService = Depends(get_chat_service)
) -> List[ChatSession]:
    """Get user's sessions."""
    try:
        sessions = await chat_service.get_user_sessions(
            user_id=user_id,
            include_archived=include_archived,
            limit=limit
        )
        return sessions
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/session/{session_id}/archive",
    status_code=204,
    summary="Archive Session",
    description="Archive a chat session"
)
async def archive_session(
    session_id: str,
    user_id: str = Depends(require_auth),
    chat_service: ChatService = Depends(get_chat_service)
) -> None:
    """Archive session."""
    try:
        await chat_service.archive_session(session_id)
    except Exception as e:
        logger.error(f"Failed to archive session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete(
    "/session/{session_id}",
    status_code=204,
    summary="Delete Session",
    description="Permanently delete a chat session"
)
async def delete_session(
    session_id: str,
    user_id: str = Depends(require_auth),
    chat_service: ChatService = Depends(get_chat_service)
) -> None:
    """Delete session."""
    try:
        await chat_service.delete_session(session_id)
    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### **2.4 Register Router**
```python
# apps/backend/src/main.py
from .api.chat import router as chat_router

app.include_router(chat_router)
```

---

## 🎨 **Frontend Implementation**

### **Phase 3: Frontend Components**

#### **3.1 API Client**
```typescript
// apps/frontend/src/lib/api/chat.ts

import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8082';

export enum ResponseMode {
  STRICT = 'strict',
  BALANCED = 'balanced',
  CREATIVE = 'creative'
}

export interface ChatSource {
  id: string;
  ragie_document_id: string;
  document_name: string;
  page_number?: number;
  chunk_text: string;
  relevance_score: number;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  status: 'pending' | 'streaming' | 'completed' | 'failed';
  sources?: ChatSource[];
  error_message?: string;
  created_at: string;
  tokens_total?: number;
  processing_time_ms?: number;
}

export interface ChatSession {
  id: string;
  user_id: string;
  organization_id: string;
  title: string;
  is_active: boolean;
  is_archived: boolean;
  temperature: number;
  model_name: string;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  message_count?: number;
}

export async function getActiveSession(
  token: string,
  organizationId: string
): Promise<ChatSession> {
  const response = await axios.get(`${API_BASE}/api/v1/chat/session`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Organization-ID': organizationId
    }
  });
  return response.data;
}

export async function createNewSession(
  token: string,
  organizationId: string
): Promise<ChatSession> {
  const response = await axios.post(
    `${API_BASE}/api/v1/chat/session/new`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
  return response.data;
}

export async function sendMessage(
  sessionId: string,
  question: string,
  mode: ResponseMode,
  model: string,
  token: string,
  organizationId: string
): Promise<ChatMessage> {
  const response = await axios.post(
    `${API_BASE}/api/v1/chat/message?session_id=${sessionId}`,
    { question, mode, model },
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
  return response.data;
}

export async function getSessionMessages(
  sessionId: string,
  token: string,
  organizationId: string
): Promise<ChatMessage[]> {
  const response = await axios.get(
    `${API_BASE}/api/v1/chat/session/${sessionId}/messages`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
  return response.data;
}

export async function getUserSessions(
  token: string,
  organizationId: string,
  includeArchived: boolean = false
): Promise<ChatSession[]> {
  const response = await axios.get(
    `${API_BASE}/api/v1/chat/sessions?include_archived=${includeArchived}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
  return response.data;
}

export async function archiveSession(
  sessionId: string,
  token: string,
  organizationId: string
): Promise<void> {
  await axios.post(
    `${API_BASE}/api/v1/chat/session/${sessionId}/archive`,
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
}

export async function deleteSession(
  sessionId: string,
  token: string,
  organizationId: string
): Promise<void> {
  await axios.delete(
    `${API_BASE}/api/v1/chat/session/${sessionId}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Organization-ID': organizationId
      }
    }
  );
}
```

#### **3.2 Update Chat Components**

**Key Components to Update:**
1. **ChatInterface** - Add session management, settings dropdown
2. **MessageArea** - Display sources as cards
3. **InputArea** - Send actual messages, handle loading
4. **ChatSidebar** (new) - Show session history
5. **SourceCard** (new) - Display source citations
6. **SettingsDropdown** (new) - Response mode + model selection

**Implementation files:**
- `apps/frontend/src/components/chat/chat-interface.tsx` - Update with real state
- `apps/frontend/src/components/chat/message-area.tsx` - Add source rendering
- `apps/frontend/src/components/chat/input-area.tsx` - Connect to API
- `apps/frontend/src/components/chat/chat-sidebar.tsx` - NEW: History
- `apps/frontend/src/components/chat/source-card.tsx` - NEW: Citations
- `apps/frontend/src/components/chat/settings-dropdown.tsx` - NEW: Settings

---

## 🧪 **Testing Strategy**

### **Backend Tests**
```bash
# Unit tests
tests/unit/services/test_llm_service.py       # Mock OpenAI
tests/unit/services/test_chat_service.py      # Mock DB & services

# Integration tests
tests/integration/test_chat_api.py            # Full API flow
tests/integration/test_rate_limiting.py       # Rate limit enforcement

# Run tests
cd apps/backend
pytest tests/ -v --cov=src
```

### **Frontend Tests**
```bash
# Component tests
tests/components/chat/chat-interface.test.tsx
tests/components/chat/source-card.test.tsx

# Integration tests
tests/e2e/chat-flow.spec.ts                   # Playwright E2E

# Run tests
cd apps/frontend
pnpm test
pnpm test:e2e
```

---

## 🚀 **Deployment Checklist**

### **Environment Variables**
```bash
# Backend .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # or gpt-3.5-turbo

# Frontend .env
NEXT_PUBLIC_API_BASE_URL=https://api.yourapp.com
```

### **Database Migration**
```bash
cd packages/database
alembic upgrade head
```

### **Deployment Steps**
1. ✅ Run database migration
2. ✅ Deploy backend with new chat endpoints
3. ✅ Deploy frontend with chat UI
4. ✅ Test active session creation
5. ✅ Test message sending end-to-end
6. ✅ Test rate limiting
7. ✅ Monitor OpenAI API costs
8. ✅ Monitor response times

---

## 📊 **Success Metrics**

### **Key Metrics to Track**
- **Adoption**: Daily/weekly active chat users
- **Engagement**: Messages per session, session duration
- **Quality**: Error rate, rate limit hits
- **Performance**: P95 response time, Ragie retrieval time, LLM latency
- **Cost**: OpenAI tokens used, cost per message

### **Target Metrics (MVP)**
- ✅ P95 response time < 5s
- ✅ Error rate < 5%
- ✅ User satisfaction > 70% (via future feedback)
- ✅ Cost per message < $0.05

---

## 📝 **Implementation Timeline**

| Phase | Tasks | Effort | Owner |
|-------|-------|--------|-------|
| **Week 1** | Backend setup, DB migration, LLM/Chat services | 5 days | Backend Dev |
| **Week 2** | Chat API endpoints, rate limiting, testing | 5 days | Backend Dev |
| **Week 3** | Frontend components, API integration, E2E tests | 5 days | Frontend Dev |
| **Week 4** | Integration testing, bug fixes, deployment | 3 days | Full Team |

**Total Estimated Effort**: 18 days = ~3.5 weeks

---

## ✅ **Definition of Done**

- [ ] Database migration applied successfully
- [ ] All backend tests passing (unit + integration)
- [ ] All frontend tests passing (component + E2E)
- [ ] User can send message and get response with sources
- [ ] User can view chat history and create new sessions
- [ ] Rate limiting enforced correctly
- [ ] Error states handled gracefully
- [ ] Settings dropdown works (mode + model selection)
- [ ] Source cards display correctly
- [ ] Performance metrics meet targets
- [ ] Documentation updated
- [ ] Deployed to production

---

**Created**: 2025-01-XX  
**Last Updated**: 2025-01-XX  
**Status**: 🟢 Ready for Implementation
