# Chat API Endpoints - Frontend Integration Guide

**Status**: ✅ Ready for Integration  
**Backend Version**: 1.0.0  
**Last Updated**: 2025-01-30  
**OpenAI Model**: GPT-4o  
**Database**: PostgreSQL (migration required)

---

## 🎯 Overview

The Chat API provides RAG-powered (Retrieval-Augmented Generation) conversational AI that answers questions based on documents uploaded to Ragie. Each response includes source citations showing which documents were used.

### **Key Features**
- ✅ Persistent chat sessions (stored in PostgreSQL)
- ✅ RAG pipeline: Ragie retrieval → OpenAI GPT-4o → Source citations
- ✅ Active session management (resume on return)
- ✅ Conversation history (last 5 messages)
- ✅ Response modes: Strict (0.1), Balanced (0.5), Creative (0.9)
- ✅ Rate limiting: 50 msg/user/hour, 1000 msg/org/day
- ✅ Source citations with document names and page numbers

---

## 🔧 Prerequisites

### **1. Database Migration (REQUIRED)**
```bash
cd packages/database
alembic upgrade head
```

This creates 4 new tables:
- `chat_sessions` - Chat sessions
- `chat_messages` - Messages with LLM metadata
- `chat_sources` - Source citations
- `chat_rate_limits` - Rate limiting tracking

### **2. Environment Variables**
```bash
# Backend .env
OPENAI_API_KEY=sk-...  # Required for LLM generation
OPENAI_MODEL=gpt-4o    # Default model
```

### **3. Dependencies**
Already installed in backend:
- `openai>=1.0.0` - OpenAI client
- `tiktoken>=0.5.0` - Token counting

---

## 📋 API Endpoints

Base URL: `http://localhost:8082` (local) or production URL

All endpoints require:
- **Authorization**: `Bearer <token>` (Frontegg JWT)
- **X-Organization-ID**: `<organization_id>` (UUID)

---

## 1️⃣ Get Active Session

**Get or create active chat session for current user.**

### Request
```http
GET /api/v1/chat/session
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Response (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-uuid",
  "organization_id": "org-uuid",
  "title": "New Chat",
  "is_active": true,
  "is_archived": false,
  "temperature": 0.1,
  "model_name": "gpt-4o",
  "created_at": "2025-01-30T12:00:00Z",
  "updated_at": "2025-01-30T12:00:00Z",
  "last_message_at": null,
  "message_count": 0
}
```

### Behavior
- Returns existing active session if one exists
- Creates new session if no active session exists
- **Only one active session per user** at a time
- Title updates from first message (truncated to 50 chars)

---

## 2️⃣ Create New Session

**Create new chat session and deactivate current active session.**

### Request
```http
POST /api/v1/chat/session/new
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Response (200 OK)
```json
{
  "id": "new-session-uuid",
  "user_id": "user-uuid",
  "organization_id": "org-uuid",
  "title": "New Chat",
  "is_active": true,
  "is_archived": false,
  "temperature": 0.1,
  "model_name": "gpt-4o",
  "created_at": "2025-01-30T12:05:00Z",
  "updated_at": "2025-01-30T12:05:00Z",
  "last_message_at": null,
  "message_count": 0
}
```

### Use Case
When user clicks "New Chat" button in UI.

---

## 3️⃣ Send Message

**Send message and get AI response with sources.**

This is the main RAG endpoint that:
1. Checks rate limits
2. Saves user message
3. Retrieves relevant chunks from Ragie
4. Generates response with OpenAI
5. Saves AI response with sources
6. Updates session metadata

### Request
```http
POST /api/v1/chat/message?session_id=<session_id>
Authorization: Bearer <token>
X-Organization-ID: <org_id>
Content-Type: application/json

{
  "question": "What is the main topic of the uploaded documents?",
  "mode": "strict",
  "model": "gpt-4o"
}
```

### Request Body
```typescript
{
  question: string;     // 1-5000 characters
  mode: "strict" | "balanced" | "creative";  // Response mode
  model: "gpt-4o" | "gpt-3.5-turbo";        // LLM model
}
```

### Response (200 OK)
```json
{
  "id": "message-uuid",
  "session_id": "session-uuid",
  "role": "assistant",
  "content": "Based on the uploaded documents, the main topics include...",
  "status": "completed",
  "sources": [
    {
      "id": "source-1",
      "ragie_document_id": "ragie-doc-id",
      "document_name": "Q4 Financial Report.pdf",
      "page_number": 3,
      "chunk_text": "The quarterly revenue increased by 25%...",
      "relevance_score": 0.95
    },
    {
      "id": "source-2",
      "ragie_document_id": "ragie-doc-id-2",
      "document_name": "Product Roadmap.pdf",
      "page_number": 1,
      "chunk_text": "Key initiatives for next quarter include...",
      "relevance_score": 0.87
    }
  ],
  "created_at": "2025-01-30T12:10:00Z",
  "tokens_total": 345,
  "processing_time_ms": 1850
}
```

### Response Modes
| Mode | Temperature | Behavior |
|------|-------------|----------|
| `strict` | 0.1 | Factual only, no assumptions, says "I don't know" if context insufficient |
| `balanced` | 0.5 | Balanced, reasonable inferences clearly stated |
| `creative` | 0.9 | Broader context, may use general knowledge beyond documents |

### Error Responses

#### 429 - Rate Limit Exceeded
```json
{
  "detail": "User hourly limit exceeded (50 messages/hour)"
}
```
or
```json
{
  "detail": "Organization daily limit exceeded (1000 messages/day)"
}
```

#### 422 - Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "question"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

#### 400 - Processing Error
```json
{
  "detail": "Failed to process message: <error details>"
}
```

### Performance
- **P95 Response Time**: < 5 seconds (target)
- **Ragie Retrieval**: < 500ms
- **OpenAI Generation**: 1-3 seconds
- **Database Operations**: < 100ms

---

## 4️⃣ Get Session Messages

**Get all messages for a specific session.**

### Request
```http
GET /api/v1/chat/session/{session_id}/messages?limit=50
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Query Parameters
- `limit` (optional): Number of messages to return (default: 50, max: 100)

### Response (200 OK)
```json
[
  {
    "id": "msg-1",
    "session_id": "session-uuid",
    "role": "user",
    "content": "What is in the documents?",
    "status": "completed",
    "sources": null,
    "created_at": "2025-01-30T12:10:00Z"
  },
  {
    "id": "msg-2",
    "session_id": "session-uuid",
    "role": "assistant",
    "content": "Based on the documents...",
    "status": "completed",
    "sources": [
      {
        "id": "source-1",
        "document_name": "Report.pdf",
        "page_number": 1,
        "chunk_text": "...",
        "relevance_score": 0.95
      }
    ],
    "created_at": "2025-01-30T12:10:05Z",
    "tokens_total": 250,
    "processing_time_ms": 1500
  }
]
```

### Notes
- Messages ordered chronologically (oldest first)
- User messages have `sources: null`
- Assistant messages include sources array

---

## 5️⃣ Get User Sessions

**Get all chat sessions for current user.**

### Request
```http
GET /api/v1/chat/sessions?include_archived=false&limit=50
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Query Parameters
- `include_archived` (optional): Include archived sessions (default: false)
- `limit` (optional): Number of sessions to return (default: 50, max: 100)

### Response (200 OK)
```json
[
  {
    "id": "session-1",
    "title": "What is the Q4 revenue?",
    "is_active": true,
    "is_archived": false,
    "created_at": "2025-01-30T12:00:00Z",
    "updated_at": "2025-01-30T12:15:00Z",
    "last_message_at": "2025-01-30T12:15:00Z",
    "message_count": 6
  },
  {
    "id": "session-2",
    "title": "Tell me about the product roadmap...",
    "is_active": false,
    "is_archived": false,
    "created_at": "2025-01-29T10:00:00Z",
    "updated_at": "2025-01-29T10:30:00Z",
    "last_message_at": "2025-01-29T10:30:00Z",
    "message_count": 12
  }
]
```

### Notes
- Ordered by `updated_at` descending (most recent first)
- Only returns sessions for authenticated user
- Title is truncated from first message

---

## 6️⃣ Archive Session

**Archive a chat session (soft delete).**

### Request
```http
POST /api/v1/chat/session/{session_id}/archive
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Response (204 No Content)
```
(empty body)
```

### Behavior
- Sets `is_archived = true`
- Sets `is_active = false`
- Session won't appear in default session list
- Can still be retrieved with `include_archived=true`

---

## 7️⃣ Delete Session

**Permanently delete a chat session and all its messages.**

### Request
```http
DELETE /api/v1/chat/session/{session_id}
Authorization: Bearer <token>
X-Organization-ID: <org_id>
```

### Response (204 No Content)
```
(empty body)
```

### Behavior
- **Permanently deletes** session and all messages (CASCADE)
- Cannot be undone
- Sources are also deleted

---

## 🔄 Typical User Flow

### Flow 1: First Time User
```typescript
// 1. User opens chat page
const session = await GET('/api/v1/chat/session');
// → Returns new session with title "New Chat"

// 2. Load messages (empty for new session)
const messages = await GET(`/api/v1/chat/session/${session.id}/messages`);
// → Returns []

// 3. User asks question
const response = await POST(`/api/v1/chat/message?session_id=${session.id}`, {
  question: "What's in my documents?",
  mode: "strict",
  model: "gpt-4o"
});
// → Returns AI response with sources

// 4. Session title auto-updates
// Backend updates title to "What's in my documents?" (truncated if needed)
```

### Flow 2: Returning User
```typescript
// 1. User returns to chat page
const session = await GET('/api/v1/chat/session');
// → Returns EXISTING active session (resumes conversation)

// 2. Load message history
const messages = await GET(`/api/v1/chat/session/${session.id}/messages`);
// → Returns all previous messages

// 3. User continues conversation
// Questions include last 5 messages as context
```

### Flow 3: Create New Chat
```typescript
// 1. User clicks "New Chat" button
const newSession = await POST('/api/v1/chat/session/new');
// → Deactivates old session, creates new one

// 2. UI switches to new session
// Old session is saved and can be accessed from history
```

### Flow 4: View Chat History
```typescript
// 1. User opens history sidebar
const sessions = await GET('/api/v1/chat/sessions?limit=50');
// → Returns all sessions (most recent first)

// 2. User clicks old session
const messages = await GET(`/api/v1/chat/session/${oldSessionId}/messages`);
// → Load that session's messages

// 3. User continues old conversation
// Send new messages to that session
```

---

## ⚠️ Rate Limiting

### Limits
- **User**: 50 messages per hour (rolling window)
- **Organization**: 1000 messages per day (rolling window)

### Rate Limit Response
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "User hourly limit exceeded (50 messages/hour)"
}
```

### Frontend Handling
```typescript
try {
  const response = await sendMessage(question);
} catch (error) {
  if (error.response?.status === 429) {
    // Show user-friendly message
    showToast("You've reached your message limit. Please try again in an hour.");
    // Optionally disable input temporarily
  }
}
```

### Recommendations
- Show remaining messages in UI (call backend for count)
- Disable send button when limit reached
- Show countdown timer for rate limit reset

---

## 🎨 UI/UX Recommendations

### Message Display
```typescript
interface MessageProps {
  message: ChatMessage;
}

const MessageBubble: React.FC<MessageProps> = ({ message }) => {
  return (
    <div className={message.role === 'user' ? 'user-message' : 'ai-message'}>
      <div className="message-content">
        {message.content}
      </div>
      
      {message.sources && message.sources.length > 0 && (
        <div className="sources">
          <div className="sources-label">Sources:</div>
          {message.sources.map(source => (
            <SourceCard key={source.id} source={source} />
          ))}
        </div>
      )}
      
      <div className="message-meta">
        {formatTime(message.created_at)}
        {message.tokens_total && ` • ${message.tokens_total} tokens`}
      </div>
    </div>
  );
};
```

### Source Citation Card
```typescript
const SourceCard: React.FC<{ source: ChatSource }> = ({ source }) => {
  return (
    <div className="source-card">
      <div className="source-icon">📄</div>
      <div className="source-info">
        <div className="source-name">{source.document_name}</div>
        {source.page_number && (
          <div className="source-page">Page {source.page_number}</div>
        )}
        <div className="source-relevance">
          Relevance: {(source.relevance_score * 100).toFixed(0)}%
        </div>
      </div>
    </div>
  );
};
```

### Settings Dropdown
```typescript
const [mode, setMode] = useState<ResponseMode>('strict');
const [model, setModel] = useState<Model>('gpt-4o');

<SettingsDropdown>
  <Select value={mode} onChange={setMode}>
    <Option value="strict">Strict (Factual Only)</Option>
    <Option value="balanced">Balanced (Recommended)</Option>
    <Option value="creative">Creative (Broader Context)</Option>
  </Select>
  
  <Select value={model} onChange={setModel}>
    <Option value="gpt-4o">GPT-4o (Recommended)</Option>
    <Option value="gpt-3.5-turbo">GPT-3.5 Turbo (Faster)</Option>
  </Select>
</SettingsDropdown>
```

---

## 🔍 Testing Checklist

### Functional Tests
- [ ] User can create new session
- [ ] User can send message and get response
- [ ] Sources display correctly
- [ ] Conversation history loads
- [ ] User can switch between sessions
- [ ] User can create new chat
- [ ] User can archive session
- [ ] User can delete session
- [ ] Rate limit shows appropriate error

### Edge Cases
- [ ] Empty message validation
- [ ] Very long messages (>5000 chars)
- [ ] No documents uploaded (what does Ragie return?)
- [ ] Network timeout handling
- [ ] Concurrent message sending
- [ ] Session switching during message processing

### Performance Tests
- [ ] Large message history (50+ messages) loads quickly
- [ ] Rapid session switching doesn't cause UI lag
- [ ] Source cards render efficiently

---

## 🐛 Known Issues & Warnings

### Pydantic Warnings (Non-blocking)
```
UserWarning: Field "model_used" in ChatMessage has conflict with protected namespace "model_".
```
- **Impact**: None - informational warning only
- **Can be ignored** - doesn't affect functionality

### Rate Limit Edge Cases
- Rate limits are per-user and per-org
- If user switches orgs, limits are independent
- Limits are rolling windows (not fixed hourly/daily resets)

### OpenAI Errors
If OpenAI API fails:
```json
{
  "id": "message-uuid",
  "role": "assistant",
  "content": "I encountered an error processing your question.",
  "status": "failed",
  "error_message": "LLM generation failed: <details>"
}
```

Frontend should:
- Show error message to user
- Offer retry button
- Log error for debugging

---

## 📊 Monitoring & Analytics

### Metrics to Track
- **Usage**: Messages per user/org per day
- **Performance**: P50, P95, P99 response times
- **Errors**: OpenAI failures, rate limit hits
- **Cost**: OpenAI tokens used (track `tokens_total`)
- **Quality**: Session length, message count per session

### Logging
Backend logs include:
- `user_id`, `organization_id`, `session_id` for tracing
- `processing_time_ms` for performance monitoring
- `tokens_total` for cost tracking

---

## 🔧 Environment-Specific URLs

### Local Development
```typescript
const API_BASE_URL = 'http://localhost:8082';
```

### Staging
```typescript
const API_BASE_URL = 'https://api-staging.yourapp.com';
```

### Production
```typescript
const API_BASE_URL = 'https://api.yourapp.com';
```

---

## 📚 Additional Resources

### Backend Documentation
- **Implementation Spec**: `docs/implementation_phases/feature_chat_with_rag.md`
- **Test Suite**: `apps/backend/tests/CHAT_TESTS_SUMMARY.md`
- **LLM Service**: `apps/backend/src/services/llm_service.py`
- **Chat Service**: `apps/backend/src/services/chat_service.py`
- **Chat API**: `apps/backend/src/api/chat.py`
- **Pydantic Models**: `apps/backend/src/models/chat.py`

### Database Schema
```sql
-- See: packages/database/alembic/versions/003_add_chat_tables.py
chat_sessions
chat_messages
chat_sources
chat_rate_limits
```

---

## 🤝 Support & Questions

### Common Questions

**Q: How many sources are returned per response?**
A: Up to 5 chunks from Ragie (configurable in backend).

**Q: What happens if no relevant documents found?**
A: LLM responds with "I couldn't find relevant information..." and `sources = []`.

**Q: Can users search within a specific document?**
A: Not in MVP. Ragie searches all documents in the organization partition.

**Q: How are conversation history managed?**
A: Last 5 messages are included in LLM context automatically.

**Q: Can users export chat history?**
A: Not in MVP. Can be added by fetching all messages and exporting.

**Q: What's the max message length?**
A: 5000 characters (enforced by API validation).

### Getting Help
- **Backend Issues**: Check `apps/backend/tests/CHAT_TESTS_SUMMARY.md`
- **API Questions**: See this document
- **Ragie Integration**: See `docs/handoff/ragie-api-endpoints.md`

---

## ✅ Integration Checklist

### Before You Start
- [ ] Database migration applied (`alembic upgrade head`)
- [ ] Backend running with `OPENAI_API_KEY` set
- [ ] Ragie documents uploaded (test with existing docs)
- [ ] Authentication working (Frontegg)

### During Development
- [ ] API client created with proper auth headers
- [ ] Session management implemented
- [ ] Message sending/receiving working
- [ ] Source citations displaying
- [ ] Rate limiting handled gracefully
- [ ] Error states handled
- [ ] Loading states implemented

### Before Deployment
- [ ] All endpoints tested with real backend
- [ ] Rate limiting tested (send 51 messages)
- [ ] Different modes tested (strict/balanced/creative)
- [ ] Session switching tested
- [ ] Chat history tested
- [ ] Error handling tested (network errors, OpenAI failures)

---

**Status**: ✅ Backend Ready - Integration Can Begin  
**Contact**: Backend Team  
**Version**: 1.0.0  
**Last Updated**: 2025-01-30
