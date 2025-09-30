# Ragie API Endpoints - Frontend Integration Guide

## 🎯 **Overview**
This document provides the complete API specification for the Ragie integration endpoints. The backend implementation is complete and ready for frontend integration.

## 🆕 **Latest Updates**

### **Upload Progress Tracking** ✅
- Real-time upload progress tracking with Redis storage
- Tracks both file upload and Ragie processing status
- Polling-based progress updates for live feedback

### **Document Analytics** ✅  
- Usage insights and document statistics
- File type distribution and processing status
- Upload trends and organizational metrics

### **Enhanced Error Handling** ✅
- Temporary storage for failed uploads with Redis
- Detailed error messages and structured logging
- Recovery mechanisms for interrupted uploads

## 🔐 **Authentication**
All endpoints require:
- **Authorization Header**: `Bearer <token>`
- **Organization Header**: `X-Organization-ID: <organization-id>`

```typescript
const headers = {
  'Authorization': `Bearer ${userToken}`,
  'X-Organization-ID': organizationId,
  'Content-Type': 'application/json' // except for file uploads
};
```

## 📄 **Document Management Endpoints**

### 1. Upload Document
Upload documents to the organization's knowledge base.

```http
POST /api/v1/ragie/documents/upload
```

**Headers:**
```
Authorization: Bearer <token>
X-Organization-ID: <org-id>
Content-Type: multipart/form-data
```

**Body (Form Data):**
```typescript
{
  file: File,                    // Required: The document file
  metadata?: string             // Optional: JSON string with metadata
}
```

**Metadata Format:**
```typescript
{
  title?: string,               // Document title
  description?: string,         // Document description  
  tags?: string[]              // User-defined tags (flexible, not enum)
}
```

**Supported File Types:**
- **Documents**: `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`
- **Size Limit**: 50MB maximum

**Success Response (201):**
```typescript
{
  success: true,
  data: {
    id: string,                 // Ragie document ID
    name: string,              // Original filename
    status: "ready" | "processing" | "failed",
    created_at: string,        // ISO timestamp
    updated_at: string,        // ISO timestamp
    metadata: {
      title?: string,
      description?: string,
      tags?: string[]
    }
  }
}
```

**Error Responses:**
```typescript
// 422 - Invalid file
{
  success: false,
  error: {
    code: "VALIDATION_ERROR",
    message: "File must have a filename"
  }
}

// 400 - Upload failed
{
  success: false,
  error: {
    code: "UPLOAD_ERROR", 
    message: "File type not supported. Supported types: .pdf, .doc, ..."
  }
}
```

### 2. List Documents
Get paginated list of organization's documents.

```http
GET /api/v1/ragie/documents?limit=20&cursor=<cursor>
```

**Query Parameters:**
- `limit` (optional): Number of documents (1-100, default: 20)
- `cursor` (optional): Pagination cursor from previous response

**Success Response (200):**
```typescript
{
  success: true,
  data: {
    documents: Array<{
      id: string,
      name: string,
      status: "ready" | "processing" | "failed",
      created_at: string,
      updated_at: string,
      metadata: {
        title?: string,
        description?: string,
        tags?: string[]
      }
    }>,
    cursor?: string,           // Next page cursor (if has_more = true)
    has_more: boolean         // Whether more documents exist
  }
}
```

### 3. Get Document Details
Get specific document information.

```http
GET /api/v1/ragie/documents/{document_id}
```

**Success Response (200):**
```typescript
{
  success: true,
  data: {
    id: string,
    name: string,
    status: "ready" | "processing" | "failed",
    created_at: string,
    updated_at: string,
    metadata: {
      title?: string,
      description?: string,
      tags?: string[]
    }
  }
}
```

**Error Response (404):**
```typescript
{
  success: false,
  error: {
    code: "NOT_FOUND",
    message: "Document not found"
  }
}
```

### 4. Update Document Metadata
Update document tags and metadata.

```http
PATCH /api/v1/ragie/documents/{document_id}/metadata
```

**Request Body:**
```typescript
{
  metadata: {
    title?: string,           // Optional: Update title
    description?: string,     // Optional: Update description
    tags?: string[]          // Optional: Update tags (replaces existing)
  }
}
```

**Success Response (200):**
```typescript
{
  success: true,
  data: {
    id: string,
    name: string,
    status: "ready" | "processing" | "failed",
    created_at: string,
    updated_at: string,
    metadata: {              // Updated metadata
      title?: string,
      description?: string,
      tags?: string[]
    }
  }
}
```

### 5. Delete Document
Remove document from knowledge base.

```http
DELETE /api/v1/ragie/documents/{document_id}
```

**Success Response (204):**
```
No content (empty response body)
```

**Error Response (404):**
```typescript
{
  success: false,
  error: {
    code: "NOT_FOUND",
    message: "Document not found"
  }
}
```

### 6. Get Document Source File
Download the original document file.

```http
GET /api/v1/ragie/documents/{document_id}/source
```

**Success Response (200):**
```
Content-Type: <original-file-type>
Body: <binary-file-content>
```

Use this for document preview or download functionality.

## 📊 **Enhanced Features**

### 9. Upload Progress Tracking
Track real-time upload progress for documents.

```http
GET /api/v1/ragie/upload-progress/{upload_id}
```

**Headers:**
```
Authorization: Bearer <token>
X-Organization-ID: <organization-id>
```

**Response:**
```typescript
interface UploadProgressResponse {
  success: true;
  data: {
    upload_id: string;
    filename: string;
    status: "uploading" | "processing" | "completed" | "failed";
    upload_progress: number;      // 0-100
    processing_progress: number;  // 0-100
    processing_status?: string;   // Ragie processing stage
    document_id?: string;         // Available when completed
    error_message?: string;       // Available when failed
    stage_description?: string;   // Human-readable status
  };
}
```

**Usage Example:**
```typescript
// Start upload and get upload_id from upload response
const uploadResponse = await uploadDocument(file);
const uploadId = uploadResponse.upload_id;

// Poll for progress
const interval = setInterval(async () => {
  const progress = await getUploadProgress(uploadId);
  
  if (progress.status === 'completed' || progress.status === 'failed') {
    clearInterval(interval);
  }
  
  updateProgressBar(progress.upload_progress);
}, 1000);
```

### 10. Document Analytics
Get usage insights and document statistics.

```http
GET /api/v1/ragie/documents/analytics
```

**Headers:**
```
Authorization: Bearer <token>
X-Organization-ID: <organization-id>
```

**Response:**
```typescript
interface AnalyticsResponse {
  success: true;
  data: {
    total_documents: number;
    total_size_bytes: number;
    by_file_type: {
      [extension: string]: {
        count: number;
        size_bytes: number;
      };
    };
    by_status: {
      [status: string]: number;
    };
    upload_trends: {
      last_7_days: number;
      last_30_days: number;
    };
  };
}
```

**Usage Example:**
```typescript
const analytics = await getDocumentAnalytics();

// Display file type distribution
analytics.by_file_type.forEach(([type, data]) => {
  console.log(`${type}: ${data.count} files`);
});

// Show processing status
console.log(`Ready: ${analytics.by_status.ready || 0}`);
console.log(`Processing: ${analytics.by_status.processing || 0}`);
```

## 🔍 **Query & Retrieval Endpoints**

### 7. Query Documents (RAG)
Search and retrieve relevant document chunks.

```http
POST /api/v1/ragie/query
```

**Request Body:**
```typescript
{
  query: string,                    // Required: Search query
  max_chunks?: number,              // Optional: Max chunks to return (default: 10)
  document_ids?: string[],          // Optional: Filter by specific documents
  metadata_filter?: {               // Optional: Filter by metadata
    tags?: string[],
    // Any other metadata fields
  }
}
```

**Success Response (200):**
```typescript
{
  success: true,
  data: {
    chunks: Array<{
      id: string,                   // Chunk ID
      document_id: string,          // Source document ID
      text: string,                 // Chunk content
      score: number,                // Relevance score (0-1)
      metadata: {                   // Chunk metadata
        page?: number,
        // Other metadata
      }
    }>,
    document_ids?: string[],        // Documents that had matches
    average_score?: number          // Average relevance score
  }
}
```

## 🚨 **Error Handling**

### Common Error Codes
- `UNAUTHORIZED` (401): Missing or invalid auth token
- `MISSING_ORGANIZATION` (400): Missing X-Organization-ID header
- `VALIDATION_ERROR` (422): Invalid request data
- `NOT_FOUND` (404): Resource not found
- `UPLOAD_ERROR` (400): File upload failed
- `INTERNAL_ERROR` (500): Server error

### Error Response Format
```typescript
{
  success: false,
  error: {
    code: string,               // Error code for programmatic handling
    message: string,            // Human-readable error message
    details?: object           // Additional error details (optional)
  }
}
```

## 📝 **Frontend Implementation Examples**

### Upload Document with Progress
```typescript
const uploadDocument = async (file: File, metadata?: any) => {
  const formData = new FormData();
  formData.append('file', file);
  
  if (metadata) {
    formData.append('metadata', JSON.stringify(metadata));
  }

  try {
    const response = await fetch('/api/v1/ragie/documents/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-Organization-ID': organizationId,
        // Don't set Content-Type for FormData
      },
      body: formData
    });

    const result = await response.json();
    
    if (!result.success) {
      throw new Error(result.error.message);
    }
    
    return result.data;
  } catch (error) {
    console.error('Upload failed:', error);
    throw error;
  }
};
```

### List Documents with Pagination
```typescript
const listDocuments = async (cursor?: string, limit = 20) => {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  if (cursor) params.append('cursor', cursor);

  const response = await fetch(`/api/v1/ragie/documents?${params}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Organization-ID': organizationId,
    }
  });

  const result = await response.json();
  return result.data;
};
```

### Query Documents
```typescript
const queryDocuments = async (query: string, options?: {
  maxChunks?: number;
  documentIds?: string[];
}) => {
  const response = await fetch('/api/v1/ragie/query', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'X-Organization-ID': organizationId,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      max_chunks: options?.maxChunks || 10,
      document_ids: options?.documentIds,
    })
  });

  const result = await response.json();
  return result.data;
};
```

## 🎯 **Key Implementation Notes**

### Organization Isolation
- Each organization's documents are completely isolated
- The `X-Organization-ID` header determines data partition
- Users can only access their organization's documents

### File Type Support
- **Supported**: PDFs, Word docs, PowerPoint, Excel, common images
- **Not supported yet**: Videos (coming later), text files, archives
- **Size limit**: 50MB per file

### Metadata & Tags
- Tags are completely user-defined (not enums)
- Users can create any tags they want
- Metadata is flexible JSON structure
- Title and description are optional

### Status Tracking
- Documents have status: `ready`, `processing`, `failed`
- Most documents will be `ready` immediately after upload
- Some may show `processing` briefly for large files

### Error Handling
- All errors follow consistent format
- Use `error.code` for programmatic handling
- Use `error.message` for user display
- Always check `success` field in responses

## 🚀 **Ready for Frontend Integration**

The backend implementation is complete and tested. All endpoints are functional and ready for frontend integration. The API follows RESTful conventions and provides comprehensive error handling.

For questions or issues during integration, refer to the test files in `apps/backend/tests/api/test_ragie_routes.py` for additional usage examples.

---

*Last Updated: January 2025*
*Backend Status: ✅ Complete and Ready*
