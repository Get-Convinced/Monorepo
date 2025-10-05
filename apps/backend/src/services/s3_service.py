"""
S3 Upload Service for document management via S3 + URL approach.

This service handles uploading files to organization-specific S3 buckets,
generating pre-signed URLs, and sending those URLs to Ragie for processing.
Each organization gets its own S3 bucket which serves as the Ragie partition.
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, Callable, List
from pathlib import Path
import threading

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from ..adapters.ragie_client import RagieClient, RagieError
from ..models.ragie import RagieDocument
from .redis_service import redis_service
from ..models.ragie import UploadProgress

logger = logging.getLogger(__name__)


class S3UploadProgressCallback:
    """Callback class to track S3 upload progress."""
    
    def __init__(self, upload_id: str, filename: str, total_size: int):
        self.upload_id = upload_id
        self.filename = filename
        self.total_size = total_size
        self.uploaded_size = 0
        self._lock = threading.Lock()
    
    def __call__(self, bytes_transferred: int):
        """Called by boto3 during upload with bytes transferred."""
        with self._lock:
            self.uploaded_size += bytes_transferred
            progress_percent = min(int((self.uploaded_size / self.total_size) * 95), 95)  # S3 upload is 0-95%
            
            # Update Redis progress asynchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, schedule the update
                    asyncio.create_task(self._update_progress(progress_percent))
                else:
                    # If not in async context, run it
                    loop.run_until_complete(self._update_progress(progress_percent))
            except RuntimeError:
                # No event loop, create a new one
                asyncio.run(self._update_progress(progress_percent))
    
    async def _update_progress(self, progress_percent: int):
        """Update progress in Redis."""
        try:
            await redis_service.set_upload_progress(self.upload_id, UploadProgress(
                upload_id=self.upload_id,
                filename=self.filename,
                status="uploading",
                upload_progress=progress_percent,
                processing_progress=0,
                stage_description=f"Uploading... {progress_percent}%"
            ))
        except Exception as e:
            logger.warning(f"Failed to update S3 upload progress: {e}")


class S3ServiceError(Exception):
    """Custom exception for S3 service errors."""
    pass


class S3Service:
    """Service for handling Ragie document uploads via S3 + URL approach."""
    
    def __init__(
        self,
        ragie_client: RagieClient,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        bucket_prefix: str = "ragie-docs"
    ):
        """
        Initialize Ragie S3 service.
        
        Args:
            ragie_client: Configured Ragie client
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region
            bucket_prefix: Prefix for organization buckets
        """
        self.ragie_client = ragie_client
        self.aws_region = aws_region
        self.bucket_prefix = bucket_prefix
        
        # Initialize S3 client
        try:
            if aws_access_key_id and aws_secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=aws_region
                )
            else:
                # Use default credential chain
                session = boto3.Session(region_name=aws_region)
            
            self.s3_client = session.client(
                's3',
                region_name=aws_region,
                config=Config(
                    signature_version='s3v4',
                    s3={
                        'addressing_style': 'virtual'
                    }
                )
            )
            
        except NoCredentialsError:
            raise S3ServiceError("AWS credentials not found. Please configure AWS credentials.")
        except Exception as e:
            raise S3ServiceError(f"Failed to initialize S3 client: {str(e)}")
    
    def get_organization_bucket_name(self, organization_id: str) -> str:
        """
        Get the main S3 bucket name (single bucket for all organizations).
        
        Args:
            organization_id: Organization ID (not used, kept for compatibility)
            
        Returns:
            Main S3 bucket name from environment
        """
        # Use the main bucket from environment variable
        import os
        bucket_name = os.getenv("S3_BUCKET", "get-convinced-dev")
        return bucket_name
    
    async def ensure_organization_bucket(self, organization_id: str) -> str:
        """
        Ensure main bucket exists (no longer creates buckets, just checks).
        
        Args:
            organization_id: Organization ID (for compatibility)
            
        Returns:
            Bucket name
        """
        bucket_name = self.get_organization_bucket_name(organization_id)
        
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Main bucket exists: {bucket_name}")
            return bucket_name
            
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                raise S3ServiceError(f"Main bucket '{bucket_name}' does not exist. Please create it manually in AWS console.")
            else:
                raise S3ServiceError(f"Error checking bucket {bucket_name}: {str(e)}")
    
    def generate_s3_key(
        self,
        organization_id: str,
        user_id: str,
        filename: str,
        version: Optional[int] = None
    ) -> str:
        """
        Generate S3 key for Ragie document upload with version control.
        
        Args:
            organization_id: Organization ID
            user_id: User ID
            filename: Original filename
            version: Version number (if None, will be determined automatically)
            
        Returns:
            S3 key path with organization prefix and version
        """
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # If version is provided, use it; otherwise it will be determined later
        if version is not None:
            version_str = f"v{version:03d}"  # v001, v002, etc.
        else:
            version_str = "v001"  # Default version
        
        # Use bucket prefix and organization ID to create versioned folder structure
        # Format: {bucket_prefix}/{organization_id}/{user_id}/{safe_filename}/{version_str}_{timestamp}
        return f"{self.bucket_prefix}/{organization_id}/{user_id}/{safe_filename}/{version_str}_{timestamp}"
    
    def get_next_version_number(
        self,
        bucket_name: str,
        organization_id: str,
        user_id: str,
        filename: str
    ) -> int:
        """
        Get the next version number for a file.
        
        Args:
            bucket_name: S3 bucket name
            organization_id: Organization ID
            user_id: User ID
            filename: Original filename
            
        Returns:
            Next version number (starting from 1)
        """
        try:
            # Search for existing versions of the same filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            prefix = f"{self.bucket_prefix}/{organization_id}/{user_id}/{safe_filename}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            versions = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    # Extract version number from key like: .../v001_20241229_143022
                    try:
                        version_part = key.split('/')[-1]  # Get the last part
                        if version_part.startswith('v') and '_' in version_part:
                            version_str = version_part.split('_')[0]  # Get v001 part
                            version_num = int(version_str[1:])  # Remove 'v' and convert to int
                            versions.append(version_num)
                    except (ValueError, IndexError):
                        continue  # Skip malformed keys
            
            if versions:
                latest_version = max(versions)
                next_version = latest_version + 1
                logger.info(f"Found {len(versions)} existing versions, next version: v{next_version:03d}")
                return next_version
            else:
                logger.info(f"No existing versions found, starting with v001")
                return 1
                
        except Exception as e:
            logger.warning(f"Error checking for existing versions: {e}")
            return 1  # Default to version 1 if error
    
    def list_file_versions(
        self,
        bucket_name: str,
        organization_id: str,
        user_id: str,
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a file.
        
        Args:
            bucket_name: S3 bucket name
            organization_id: Organization ID
            user_id: User ID
            filename: Original filename
            
        Returns:
            List of version information dictionaries
        """
        try:
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
            prefix = f"{self.bucket_prefix}/{organization_id}/{user_id}/{safe_filename}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            versions = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    try:
                        version_part = key.split('/')[-1]
                        if version_part.startswith('v') and '_' in version_part:
                            version_str = version_part.split('_')[0]
                            version_num = int(version_str[1:])
                            
                            versions.append({
                                "version": version_num,
                                "version_str": version_str,
                                "s3_key": key,
                                "size": obj['Size'],
                                "last_modified": obj['LastModified'].isoformat(),
                                "etag": obj['ETag'].strip('"')
                            })
                    except (ValueError, IndexError):
                        continue
            
            # Sort by version number (newest first)
            versions.sort(key=lambda x: x['version'], reverse=True)
            
            logger.info(f"Found {len(versions)} versions of file: {filename}")
            return versions
            
        except Exception as e:
            logger.error(f"Error listing file versions: {e}")
            return []
    
    async def upload_document_for_ragie(
        self,
        file_content: bytes,
        filename: str,
        organization_id: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        upload_id: Optional[str] = None
    ) -> Tuple[RagieDocument, str]:
        """
        Upload document to S3 and send URL to Ragie for processing.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            organization_id: Organization ID (used as Ragie partition)
            user_id: User ID
            metadata: Optional metadata for the document
            upload_id: Optional upload ID for progress tracking
            
        Returns:
            Tuple of (RagieDocument object, S3 URL)
        """
        try:
            # Ensure organization bucket exists
            bucket_name = await self.ensure_organization_bucket(organization_id)
            
            # Get next version number for this file
            next_version = self.get_next_version_number(bucket_name, organization_id, user_id, filename)
            
            # Generate S3 key with version
            s3_key = self.generate_s3_key(organization_id, user_id, filename, version=next_version)
            
            # Determine content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # Prepare S3 metadata
            s3_metadata = {
                "original_filename": filename,
                "uploaded_by": user_id,
                "organization_id": organization_id,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "ragie_upload": "true"
            }
            
            if metadata:
                # Add custom metadata with ragie_ prefix to avoid conflicts
                for key, value in metadata.items():
                    s3_metadata[f"ragie_{key}"] = str(value)
            
            logger.info(f"Uploading to S3 with version control", extra={
                "bucket_name": bucket_name,
                "s3_key": s3_key,
                "file_name": filename,
                "version": f"v{next_version:03d}",
                "file_size_bytes": len(file_content),
                "content_type": content_type,
                "organization_id": organization_id,
                "user_id": user_id
            })
            
            # Upload to S3 with progress tracking
            if upload_id:
                # Create progress callback for tracking
                progress_callback = S3UploadProgressCallback(
                    upload_id=upload_id,
                    filename=filename,
                    total_size=len(file_content)
                )
                
                # Use multipart upload for progress tracking on larger files
                if len(file_content) > 5 * 1024 * 1024:  # 5MB threshold
                    logger.info(f"Using multipart upload for large file: {len(file_content)} bytes")
                    self._multipart_upload_with_progress(
                        bucket_name=bucket_name,
                        s3_key=s3_key,
                        file_content=file_content,
                        content_type=content_type,
                        metadata=s3_metadata,
                        progress_callback=progress_callback
                    )
                else:
                    # For smaller files, use regular put_object (progress will be 0% then 80%)
                    logger.info(f"Using regular upload for small file: {len(file_content)} bytes")
                    self.s3_client.put_object(
                        Bucket=bucket_name,
                        Key=s3_key,
                        Body=file_content,
                        ContentType=content_type,
                        Metadata=s3_metadata
                    )
                    # Manually trigger progress completion
                    progress_callback(len(file_content))
            else:
                # No progress tracking, use simple upload
                self.s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata=s3_metadata
                )
            
            # Generate pre-signed URL for Ragie access (valid for 24 hours)
            s3_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': s3_key},
                ExpiresIn=86400  # 24 hours
            )
            
            logger.info(f"S3 upload successful", extra={
                "s3_url": s3_url,
                "bucket_name": bucket_name,
                "s3_key": s3_key
            })
            
            # Update progress: S3 upload complete, sending to Ragie
            if upload_id:
                await redis_service.set_upload_progress(upload_id, UploadProgress(
                    upload_id=upload_id,
                    filename=filename,
                    status="uploading",
                    upload_progress=98,  # Almost done
                    processing_progress=0,
                    stage_description="Finalizing upload..."
                ))
            
            # Send URL to Ragie for processing
            logger.info(f"[RAGIE] Sending URL to Ragie", extra={
                "s3_url": s3_url,
                "partition": organization_id,
                "file_name": filename
            })
            
            document = await self.ragie_client.create_document_from_url(
                url=s3_url,
                partition=organization_id,
                metadata=metadata,
                name=filename  # Pass original filename with extension
            )
            
            logger.info(f"Ragie document created successfully", extra={
                "document_id": document.id,
                "document_status": document.status,
                "document_name": document.name,
                "s3_url": s3_url
            })
            
            # Update progress: Upload complete! Document sent to Ragie for processing
            if upload_id:
                await redis_service.set_upload_progress(upload_id, UploadProgress(
                    upload_id=upload_id,
                    filename=filename,
                    status="completed",  # Upload is complete from user perspective
                    upload_progress=100,
                    processing_progress=100,  # Show as complete
                    processing_status=document.status,
                    document_id=document.id,
                    stage_description="Upload complete! Document is being processed by Ragie."
                ))
            
            return document, s3_url
            
        except RagieError as e:
            logger.error(f"Ragie API error during document creation", extra={
                "error": str(e),
                "s3_url": s3_url if 's3_url' in locals() else "not_created",
                "organization_id": organization_id
            })
            # Clean up S3 file if Ragie fails
            if 'bucket_name' in locals() and 's3_key' in locals():
                try:
                    self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
                    logger.info(f"Cleaned up S3 file after Ragie failure: {s3_key}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup S3 file: {cleanup_error}")
            raise S3ServiceError(f"Ragie document creation failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Unexpected error during S3+Ragie upload", extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "organization_id": organization_id,
                "file_name": filename
            })
            raise S3ServiceError(f"Upload failed: {str(e)}")
    
    async def cleanup_s3_file(self, s3_url: str, organization_id: str) -> bool:
        """
        Clean up S3 file when document is deleted from Ragie.
        
        Args:
            s3_url: S3 URL of the file
            organization_id: Organization ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract bucket and key from URL
            # Format: https://bucket-name.s3.region.amazonaws.com/key
            url_parts = s3_url.replace("https://", "").split("/", 1)
            if len(url_parts) != 2:
                logger.warning(f"Invalid S3 URL format: {s3_url}")
                return False
            
            bucket_part = url_parts[0]
            s3_key = url_parts[1]
            
            # Extract bucket name (remove .s3.region.amazonaws.com)
            bucket_name = bucket_part.split(".")[0]
            
            # Verify this is the correct bucket
            expected_bucket = self.get_organization_bucket_name(organization_id)
            if bucket_name != expected_bucket:
                logger.warning(f"Bucket mismatch: {bucket_name} != {expected_bucket}")
                return False
            
            # Verify the key starts with the expected organization prefix
            expected_prefix = f"{self.bucket_prefix}/{organization_id}/"
            if not s3_key.startswith(expected_prefix):
                logger.warning(f"Key prefix mismatch: {s3_key} doesn't start with {expected_prefix}")
                return False
            
            # Delete the file
            self.s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            
            logger.info(f"S3 file cleaned up successfully", extra={
                "s3_url": s3_url,
                "bucket_name": bucket_name,
                "s3_key": s3_key
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup S3 file", extra={
                "s3_url": s3_url,
                "error": str(e)
            })
            return False
    
    def _multipart_upload_with_progress(
        self,
        bucket_name: str,
        s3_key: str,
        file_content: bytes,
        content_type: str,
        metadata: Dict[str, str],
        progress_callback: S3UploadProgressCallback
    ) -> None:
        """
        Perform multipart upload with progress tracking.
        
        Args:
            bucket_name: S3 bucket name
            s3_key: S3 object key
            file_content: File content as bytes
            content_type: MIME content type
            metadata: S3 metadata
            progress_callback: Progress callback function
        """
        try:
            # Initialize multipart upload
            response = self.s3_client.create_multipart_upload(
                Bucket=bucket_name,
                Key=s3_key,
                ContentType=content_type,
                Metadata=metadata
            )
            
            upload_id = response['UploadId']
            parts = []
            
            # Split file into 5MB chunks
            chunk_size = 5 * 1024 * 1024  # 5MB
            part_number = 1
            
            for i in range(0, len(file_content), chunk_size):
                chunk = file_content[i:i + chunk_size]
                
                # Upload part
                part_response = self.s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=chunk
                )
                
                parts.append({
                    'ETag': part_response['ETag'],
                    'PartNumber': part_number
                })
                
                # Update progress
                progress_callback(len(chunk))
                
                part_number += 1
            
            # Complete multipart upload
            self.s3_client.complete_multipart_upload(
                Bucket=bucket_name,
                Key=s3_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            logger.info(f"Multipart upload completed: {len(parts)} parts")
            
        except Exception as e:
            # Abort multipart upload on error
            try:
                self.s3_client.abort_multipart_upload(
                    Bucket=bucket_name,
                    Key=s3_key,
                    UploadId=upload_id
                )
            except:
                pass  # Ignore cleanup errors
            
            logger.error(f"Multipart upload failed: {e}")
            raise


# Singleton instance to avoid repeated initialization
_s3_service_instance: Optional[S3Service] = None

def get_s3_service() -> S3Service:
    """
    Factory function to create S3Service instance (singleton).
    
    Returns:
        Configured S3Service instance
    """
    global _s3_service_instance
    
    if _s3_service_instance is None:
        # Import here to avoid circular import
        from ..api.ragie import get_ragie_client
        
        # Get shared Ragie client singleton
        ragie_client = get_ragie_client()
        
        # Get AWS credentials
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("AWS_REGION", "us-east-1")
        bucket_prefix = os.getenv("RAGIE_S3_BUCKET_PREFIX", "ragie-docs")
        
        # S3 configuration
        s3_bucket = os.getenv("S3_BUCKET", "get-convinced-dev")
        
        _s3_service_instance = S3Service(
            ragie_client=ragie_client,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_region=region,
            bucket_prefix=bucket_prefix
        )
        logger.info("S3 service initialized")
    
    return _s3_service_instance
