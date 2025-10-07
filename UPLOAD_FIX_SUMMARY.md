# Upload Fix Summary - Ragie 415 Error Resolution

## 🎯 **Root Cause**
The 415 "Unsupported Media Type" error was caused by using the wrong Ragie API endpoint:
- ❌ **Before**: Using `/documents` POST with `multipart/form-data` (direct file upload)
- ✅ **After**: Using `/documents/url` POST with JSON (URL-based upload)

## 🔄 **Solution: S3 + URL Upload Method**

### **How it works now:**
1. **Upload to S3**: File is first uploaded to our S3 bucket
2. **Generate presigned URL**: Create a temporary public URL for the file
3. **Send URL to Ragie**: Use `/documents/url` endpoint with JSON payload
4. **Ragie fetches**: Ragie downloads the file from the S3 URL
5. **Process**: Ragie processes the document normally

### **Benefits:**
- ✅ Avoids `multipart/form-data` complexity and 415 errors
- ✅ Uses simple JSON requests (easier to debug)
- ✅ Better for large files (no timeout issues)
- ✅ S3 provides reliable file storage
- ✅ Presigned URLs are temporary and secure

## 📝 **Code Changes**

### **1. Re-enabled S3 Service** (`apps/backend/src/api/ragie.py`)
```python
def get_ragie_service() -> RagieService:
    """Get configured Ragie service instance with S3 support (singleton)."""
    global _ragie_service_instance
    
    if _ragie_service_instance is None:
        ragie_client = get_ragie_client()
        
        # Use S3+URL approach (avoids multipart/form-data 415 errors)
        try:
            s3_service = get_s3_service(ragie_client)
            logger.info("Initializing Ragie service with S3+URL upload method")
            _ragie_service_instance = RagieService(
                ragie_client=ragie_client,
                ragie_s3_service=s3_service
            )
        except Exception as e:
            logger.warning(f"Failed to initialize S3 service, falling back to direct upload: {e}")
            _ragie_service_instance = RagieService(ragie_client=ragie_client)
    
    return _ragie_service_instance
```

### **2. Service Already Supports Both Methods** (`apps/backend/src/services/ragie_service.py`)
The `RagieService.upload_document()` method already had logic to:
- Use S3+URL method if `ragie_s3_service` is provided
- Fall back to direct upload if S3 service is not available

### **3. Added Debug Logging** (`apps/backend/src/adapters/ragie_client.py`)
- Logs form data keys and values
- Logs file information (filename, size, content-type)
- Generates equivalent curl command for debugging
- Logs full error response body

## 🧪 **Testing**

### **Upload a file:**
1. Go to frontend: https://get-convinced-kb.vercel.app/
2. Upload a PDF or other supported file
3. Check the logs for success

### **Extract debug info (if needed):**
```bash
cd /Users/gauthamgsabahit/workspace/convinced/Monorepo
./extract-ragie-debug.sh
```

### **Monitor logs in real-time:**
```bash
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --follow | grep -iE "(upload|ragie|s3)"
```

## 📊 **Expected Log Flow**

### **Successful Upload:**
```
INFO: Initializing Ragie service with S3+URL upload method
INFO: Starting document upload file_name=test.pdf upload_method=s3_url
INFO: Using S3+URL upload method
INFO: Uploading file to S3 bucket
INFO: File uploaded to S3 successfully
INFO: Creating Ragie document from URL
INFO: Making POST request to Ragie API url=https://api.ragie.ai/documents/url
INFO: Ragie API response status_code=201
INFO: Document uploaded via S3+URL successfully
```

### **If S3 fails (fallback to direct):**
```
WARNING: Failed to initialize S3 service, falling back to direct upload
INFO: Using direct upload method (fallback)
INFO: Making POST request to Ragie API url=https://api.ragie.ai/documents
```

## 🔑 **Required Secrets**
All secrets are configured in AWS Secrets Manager (`get-convinced-prod-app-secrets`):
- ✅ `RAGIE_API_KEY` - For Ragie API authentication
- ✅ `AWS_ACCESS_KEY_ID` - For S3 uploads
- ✅ `AWS_SECRET_ACCESS_KEY` - For S3 uploads
- ✅ `RAGIE_S3_BUCKET_PREFIX` - S3 bucket prefix for uploads

## 📚 **Related Files**
- `apps/backend/src/api/ragie.py` - API endpoints and service initialization
- `apps/backend/src/services/ragie_service.py` - Upload logic (S3 vs direct)
- `apps/backend/src/services/s3_service.py` - S3 upload and presigned URL generation
- `apps/backend/src/adapters/ragie_client.py` - Ragie API client with debug logging
- `apps/backend/tests/openAPI/ragie.json` - Ragie API specification
- `extract-ragie-debug.sh` - Debug log extraction script

## 🚀 **Deployment Status**
- **Deployed**: October 6, 2025 at 14:00 IST
- **Task Definition**: `get-convinced-prod-backend:3`
- **Method**: S3 + URL upload
- **Status**: ✅ Active and healthy

## 📧 **If Issues Persist**
1. Run `./extract-ragie-debug.sh` to get curl command
2. Test the curl command locally
3. Share with Ragie support team with:
   - The curl command (with your API key)
   - The error response body
   - The request details from logs

---

**Last Updated**: October 6, 2025
**Author**: AI Assistant
**Status**: ✅ Deployed and ready for testing
