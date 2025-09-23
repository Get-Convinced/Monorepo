# Backend Responsibilities

## 🎯 **Core Role**
The backend (API Gateway) serves as the **central orchestrator** and **security layer** for the AI Knowledge Agent system. It handles authentication verification, database operations, request routing, and business logic coordination.

---

## 🔐 **Authentication & Authorization**

### **Primary Responsibilities**
- ✅ **Token Verification**: Verify Frontegg JWT tokens received from frontend
- ✅ **Token Caching**: Cache verified tokens in Redis for faster subsequent requests
- ✅ **Session Management**: Maintain user session state and handle token refresh
- ✅ **Organization Context**: Extract and validate organization membership from tokens

### **Authority Level**: 🔴 **FULL CONTROL**
```typescript
// Authentication Flow
Frontend → Frontegg Login → JWT Token → Backend Verification → Cached Session
```

### **Implementation Details**
- **Token Validation**: Direct API calls to Frontegg for token verification
- **Cache Strategy**: Redis-based caching with TTL matching token expiry
- **Middleware**: JWT validation middleware for all protected routes
- **Fallback**: Graceful degradation if Frontegg is temporarily unavailable

---

## 🗄️ **Database Operations**

### **Primary Responsibilities**
- ✅ **User Management**: CRUD operations for user profiles and preferences
- ✅ **Organization Management**: Multi-tenant organization data isolation
- ✅ **Document Metadata**: Store document metadata, processing status, and ownership
- ✅ **Chat History**: Persist chat conversations and message threading
- ✅ **Analytics Data**: Store evaluation metrics, usage statistics, and performance data
- ✅ **System Configuration**: Manage application settings and feature flags

### **Authority Level**: 🔴 **FULL CONTROL**
```sql
-- Database Schema Ownership
Users, Organizations, Documents, ChatSessions, 
Messages, Evaluations, Analytics, SystemConfig
```

### **Data Access Patterns**
- **Read Operations**: User profiles, document lists, chat history, analytics dashboards
- **Write Operations**: User updates, document uploads, chat messages, evaluation scores
- **Batch Operations**: Analytics aggregation, data cleanup, migration scripts

---

## 🌐 **API Orchestration**

### **Primary Responsibilities**
- ✅ **Request Routing**: Route requests to appropriate microservices
- ✅ **Response Aggregation**: Combine responses from multiple services
- ✅ **Error Handling**: Centralized error handling and user-friendly error messages
- ✅ **Rate Limiting**: Implement per-user and per-organization rate limits
- ✅ **Request Validation**: Input validation and sanitization
- ✅ **API Versioning**: Manage API versions and backward compatibility

### **Authority Level**: 🟡 **COORDINATION CONTROL**
```typescript
// Service Orchestration
Frontend Request → Backend Validation → Service Routing → Response Aggregation
```

---

## 💬 **Chat Flow Management**

### **Primary Responsibilities**
- ✅ **Session Management**: Create and manage chat sessions
- ✅ **Message Persistence**: Store chat messages and metadata
- ✅ **Context Preparation**: Prepare user context for document-processor
- ✅ **Response Handling**: Process and format responses from RAG system
- ✅ **Thread Management**: Handle conversation threading and history

### **Authority Level**: 🟡 **COORDINATION CONTROL**
```typescript
// Chat Flow
User Message → Backend Session → Document-Processor RAG → Backend Response → Frontend
```

### **Chat Responsibilities**
- **Input Processing**: Message validation, context extraction, user intent analysis
- **Service Communication**: Forward queries to document-processor with user context
- **Output Processing**: Format RAG responses, add metadata, handle citations
- **History Management**: Maintain conversation context and message threading

---

## 📊 **Analytics & Evaluation**

### **Primary Responsibilities**
- ✅ **Metrics Collection**: Aggregate usage metrics and performance data
- ✅ **Evaluation Orchestration**: Coordinate evaluation workflows
- ✅ **Report Generation**: Generate analytics reports and dashboards
- ✅ **Data Export**: Handle data export requests and formatting

### **Authority Level**: 🟡 **COORDINATION CONTROL**
```typescript
// Analytics Flow
Usage Events → Backend Aggregation → Database Storage → Dashboard APIs
```

---

## 🔄 **Integration Management**

### **Primary Responsibilities**
- ✅ **Document-Processor Communication**: Manage document processing workflows
- ✅ **External API Integration**: Handle third-party service integrations
- ✅ **Webhook Handling**: Process webhooks from external services
- ✅ **Queue Management**: Manage background job queues and processing

### **Authority Level**: 🟡 **COORDINATION CONTROL**

---

## 🛡️ **Security & Compliance**

### **Primary Responsibilities**
- ✅ **Data Encryption**: Encrypt sensitive data at rest and in transit
- ✅ **Audit Logging**: Log all user actions and system events
- ✅ **Access Control**: Implement role-based access control (RBAC)
- ✅ **Data Privacy**: Ensure GDPR/CCPA compliance for user data

### **Authority Level**: 🔴 **FULL CONTROL**

---

## 📋 **API Endpoints Overview**

### **Authentication**
```typescript
POST /auth/verify          // Verify Frontegg token
POST /auth/refresh         // Refresh user session
DELETE /auth/logout        // Invalidate session
```

### **User Management**
```typescript
GET /users/profile         // Get user profile
PUT /users/profile         // Update user profile
GET /users/organizations   // Get user organizations
```

### **Document Management**
```typescript
GET /documents             // List user documents
POST /documents/upload     // Upload document
DELETE /documents/:id      // Delete document
GET /documents/:id/status  // Get processing status
```

### **Chat System**
```typescript
POST /chat/sessions        // Create chat session
GET /chat/sessions         // List chat sessions
POST /chat/messages        // Send message
GET /chat/sessions/:id     // Get chat history
```

### **Analytics**
```typescript
GET /analytics/dashboard   // Get dashboard data
GET /analytics/usage       // Get usage statistics
POST /analytics/evaluate   // Trigger evaluation
GET /analytics/reports     // Get evaluation reports
```

---

## 🔧 **Technical Stack**

### **Framework & Libraries**
- **Fastify**: High-performance web framework
- **TypeScript**: Type-safe development
- **Prisma/Drizzle**: Database ORM
- **Redis**: Caching and session storage
- **Bull/BullMQ**: Job queue management

### **Infrastructure**
- **PostgreSQL**: Primary database
- **Redis**: Cache and session store
- **Docker**: Containerization
- **AWS ALB**: Load balancing

---

## 🚫 **What Backend Does NOT Handle**

- ❌ **Document Processing**: Delegated to document-processor service
- ❌ **Vector Operations**: Handled by document-processor + QDrant
- ❌ **RAG Implementation**: Managed by document-processor
- ❌ **UI State Management**: Frontend responsibility
- ❌ **Client-side Authentication**: Frontend + Frontegg handles initial auth
- ❌ **File Storage**: Direct uploads to S3 (signed URLs)

---

## 🔄 **Service Dependencies**

### **Upstream Dependencies**
- **Frontend**: Receives authenticated requests
- **Frontegg**: Token verification service

### **Downstream Dependencies**
- **Document-Processor**: Document operations and RAG
- **PostgreSQL**: Data persistence
- **Redis**: Caching and sessions
- **S3**: File storage (via signed URLs)

### **Critical Path**
```
Frontend Auth → Backend Verification → Service Routing → Response Delivery
```

This backend architecture ensures secure, scalable, and maintainable API orchestration while maintaining clear separation of concerns with other system components.
