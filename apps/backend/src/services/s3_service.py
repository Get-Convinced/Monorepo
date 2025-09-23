"""
S3 Service for file storage operations.

This service provides class-based S3 operations for uploading, downloading,
and managing files in organization-specific buckets.
"""

import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, BinaryIO, Tuple
from uuid import UUID
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import UploadFile

from shared_database.models import Organization, User, S3File


class S3ServiceError(Exception):
    """Custom exception for S3 service errors."""
    pass


class S3Service:
    """Class-based S3 service for file operations."""
    
    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        endpoint_url: Optional[str] = None
    ):
        """
        Initialize S3 service.
        
        Args:
            aws_access_key_id: AWS access key ID (optional, uses env vars if not provided)
            aws_secret_access_key: AWS secret access key (optional, uses env vars if not provided)
            aws_region: AWS region
            endpoint_url: Custom S3 endpoint URL (for local development)
        """
        self.aws_region = aws_region
        self.endpoint_url = endpoint_url
        
        # Initialize S3 client
        session_kwargs = {"region_name": aws_region}
        if endpoint_url:
            session_kwargs["endpoint_url"] = endpoint_url
        
        try:
            if aws_access_key_id and aws_secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=aws_region
                )
            else:
                # Use default credential chain (env vars, IAM roles, etc.)
                session = boto3.Session(region_name=aws_region)
            
            self.s3_client = session.client('s3', **session_kwargs)
            
        except NoCredentialsError:
            raise S3ServiceError("AWS credentials not found. Please configure AWS credentials.")
        except Exception as e:
            raise S3ServiceError(f"Failed to initialize S3 client: {str(e)}")
    
    async def create_bucket_if_not_exists(self, bucket_name: str) -> bool:
        """
        Create S3 bucket if it doesn't exist.
        
        Args:
            bucket_name: Name of the bucket to create
            
        Returns:
            True if bucket was created or already exists, False otherwise
        """
        try:
            # Check if bucket exists
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    if self.aws_region == 'us-east-1':
                        # us-east-1 doesn't need LocationConstraint
                        self.s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                        )
                    return True
                except ClientError as create_error:
                    raise S3ServiceError(f"Failed to create bucket {bucket_name}: {str(create_error)}")
            else:
                raise S3ServiceError(f"Error checking bucket {bucket_name}: {str(e)}")
    
    def generate_file_hash(self, file_content: bytes) -> str:
        """Generate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def generate_s3_key(
        self,
        organization_slug: str,
        user_id: str,
        file_name: str,
        subfolder: str = "documents"
    ) -> str:
        """
        Generate S3 key for file storage.
        
        Args:
            organization_slug: Organization slug
            user_id: User ID
            file_name: Original file name
            subfolder: Subfolder within user directory
            
        Returns:
            S3 key path
        """
        # Sanitize file name
        safe_file_name = "".join(c for c in file_name if c.isalnum() or c in "._-")
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        return f"org-{organization_slug}/users/{user_id}/{subfolder}/{timestamp}_{safe_file_name}"
    
    async def upload_file(
        self,
        organization: Organization,
        user: User,
        upload_file: UploadFile,
        subfolder: str = "documents",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Tuple[S3File, str]:
        """
        Upload file to S3 and return S3File record.
        
        Args:
            organization: Organization object
            user: User object
            upload_file: FastAPI UploadFile object
            subfolder: Subfolder within user directory
            metadata: Additional file metadata
            tags: File tags
            
        Returns:
            Tuple of (S3File record, S3 key)
        """
        try:
            # Ensure bucket exists
            await self.create_bucket_if_not_exists(organization.s3_bucket_name)
            
            # Read file content
            file_content = await upload_file.read()
            await upload_file.seek(0)  # Reset file pointer
            
            # Generate file hash
            file_hash = self.generate_file_hash(file_content)
            
            # Generate S3 key
            s3_key = self.generate_s3_key(
                organization.slug,
                str(user.id),
                upload_file.filename,
                subfolder
            )
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(upload_file.filename)
            if not content_type:
                content_type = "application/octet-stream"
            
            # Prepare S3 metadata
            s3_metadata = {
                "original_filename": upload_file.filename,
                "uploaded_by": user.email,
                "organization": organization.name,
                "upload_timestamp": datetime.utcnow().isoformat(),
            }
            
            if metadata:
                s3_metadata.update(metadata)
            
            # Upload to S3
            upload_kwargs = {
                "Bucket": organization.s3_bucket_name,
                "Key": s3_key,
                "Body": file_content,
                "ContentType": content_type,
                "Metadata": {k: str(v) for k, v in s3_metadata.items()}
            }
            
            if tags:
                upload_kwargs["Tagging"] = "&".join([f"{i+1}={tag}" for i, tag in enumerate(tags)])
            
            self.s3_client.put_object(**upload_kwargs)
            
            # Create S3File record
            s3_file = S3File(
                organization_id=organization.id,
                user_id=user.id,
                file_name=upload_file.filename,
                original_file_name=upload_file.filename,
                file_path=f"org-{organization.slug}/users/{user.id}/{subfolder}",
                s3_key=s3_key,
                s3_bucket=organization.s3_bucket_name,
                file_size_bytes=len(file_content),
                content_type=content_type,
                file_hash=file_hash,
                file_metadata=s3_metadata,
                tags=tags or []
            )
            
            return s3_file, s3_key
            
        except Exception as e:
            raise S3ServiceError(f"Failed to upload file {upload_file.filename}: {str(e)}")
    
    async def download_file(self, s3_file: S3File) -> bytes:
        """
        Download file content from S3.
        
        Args:
            s3_file: S3File record
            
        Returns:
            File content as bytes
        """
        try:
            response = self.s3_client.get_object(
                Bucket=s3_file.s3_bucket,
                Key=s3_file.s3_key
            )
            return response['Body'].read()
        except ClientError as e:
            raise S3ServiceError(f"Failed to download file {s3_file.s3_key}: {str(e)}")
    
    async def delete_file(self, s3_file: S3File) -> bool:
        """
        Delete file from S3.
        
        Args:
            s3_file: S3File record
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=s3_file.s3_bucket,
                Key=s3_file.s3_key
            )
            return True
        except ClientError as e:
            raise S3ServiceError(f"Failed to delete file {s3_file.s3_key}: {str(e)}")
    
    async def generate_presigned_url(
        self,
        s3_file: S3File,
        expiration: int = 3600,
        operation: str = "get_object"
    ) -> str:
        """
        Generate presigned URL for file access.
        
        Args:
            s3_file: S3File record
            expiration: URL expiration time in seconds
            operation: S3 operation (get_object, put_object, etc.)
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={
                    'Bucket': s3_file.s3_bucket,
                    'Key': s3_file.s3_key
                },
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise S3ServiceError(f"Failed to generate presigned URL for {s3_file.s3_key}: {str(e)}")
    
    async def list_files(
        self,
        organization: Organization,
        user: Optional[User] = None,
        prefix: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List files in organization bucket.
        
        Args:
            organization: Organization object
            user: Optional user filter
            prefix: S3 key prefix filter
            limit: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            # Build prefix
            if user and not prefix:
                prefix = f"org-{organization.slug}/users/{user.id}/"
            elif not prefix:
                prefix = f"org-{organization.slug}/"
            
            response = self.s3_client.list_objects_v2(
                Bucket=organization.s3_bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
            
        except ClientError as e:
            raise S3ServiceError(f"Failed to list files: {str(e)}")
    
    async def get_file_metadata(self, s3_file: S3File) -> Dict[str, Any]:
        """
        Get file metadata from S3.
        
        Args:
            s3_file: S3File record
            
        Returns:
            File metadata dictionary
        """
        try:
            response = self.s3_client.head_object(
                Bucket=s3_file.s3_bucket,
                Key=s3_file.s3_key
            )
            
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {}),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }
            
        except ClientError as e:
            raise S3ServiceError(f"Failed to get metadata for {s3_file.s3_key}: {str(e)}")
    
    async def copy_file(
        self,
        source_s3_file: S3File,
        target_organization: Organization,
        target_user: User,
        new_filename: Optional[str] = None
    ) -> Tuple[S3File, str]:
        """
        Copy file to another organization/user.
        
        Args:
            source_s3_file: Source S3File record
            target_organization: Target organization
            target_user: Target user
            new_filename: Optional new filename
            
        Returns:
            Tuple of (new S3File record, new S3 key)
        """
        try:
            # Ensure target bucket exists
            await self.create_bucket_if_not_exists(target_organization.s3_bucket_name)
            
            # Generate new S3 key
            filename = new_filename or source_s3_file.original_file_name
            new_s3_key = self.generate_s3_key(
                target_organization.slug,
                str(target_user.id),
                filename
            )
            
            # Copy object in S3
            copy_source = {
                'Bucket': source_s3_file.s3_bucket,
                'Key': source_s3_file.s3_key
            }
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=target_organization.s3_bucket_name,
                Key=new_s3_key
            )
            
            # Create new S3File record
            new_s3_file = S3File(
                organization_id=target_organization.id,
                user_id=target_user.id,
                file_name=filename,
                original_file_name=filename,
                file_path=f"org-{target_organization.slug}/users/{target_user.id}/documents",
                s3_key=new_s3_key,
                s3_bucket=target_organization.s3_bucket_name,
                file_size_bytes=source_s3_file.file_size_bytes,
                content_type=source_s3_file.content_type,
                file_hash=source_s3_file.file_hash,
                file_metadata={
                    **source_s3_file.file_metadata,
                    "copied_from": str(source_s3_file.id),
                    "copy_timestamp": datetime.utcnow().isoformat()
                },
                tags=source_s3_file.tags
            )
            
            return new_s3_file, new_s3_key
            
        except Exception as e:
            raise S3ServiceError(f"Failed to copy file {source_s3_file.s3_key}: {str(e)}")


def get_s3_service() -> S3Service:
    """
    Factory function to create S3Service instance.
    
    Returns:
        Configured S3Service instance
    """
    return S3Service(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
        endpoint_url=os.getenv("AWS_S3_ENDPOINT_URL")  # For local development
    )


