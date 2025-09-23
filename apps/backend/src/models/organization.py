"""
Organization API models.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class OrganizationCreateRequest(BaseModel):
    """Request model for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(..., min_length=1, max_length=100, description="URL-friendly identifier")
    description: Optional[str] = Field(None, description="Organization description")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Organization settings")


class OrganizationUpdateRequest(BaseModel):
    """Request model for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings")


class OrganizationResponse(BaseModel):
    """Response model for organization data."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    settings: Dict[str, Any]
    s3_bucket_name: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrganizationMemberResponse(BaseModel):
    """Response model for organization member data."""
    id: UUID
    user_id: UUID
    role: str
    permissions: Dict[str, Any]
    is_active: bool
    joined_at: datetime
    updated_at: datetime
    user: Optional["UserResponse"] = None
    
    class Config:
        from_attributes = True


class OrganizationListResponse(BaseModel):
    """Response model for organization list."""
    organizations: List[OrganizationResponse]
    total: int
    limit: int
    offset: int


class OrganizationMemberCreateRequest(BaseModel):
    """Request model for adding a member to an organization."""
    user_id: UUID = Field(..., description="User ID to add")
    role: str = Field(default="member", description="Member role")
    permissions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional permissions")


class OrganizationMemberUpdateRequest(BaseModel):
    """Request model for updating organization member."""
    role: Optional[str] = Field(None, description="Member role")
    permissions: Optional[Dict[str, Any]] = Field(None, description="Additional permissions")


class OrganizationMemberListResponse(BaseModel):
    """Response model for organization member list."""
    members: List[OrganizationMemberResponse]
    total: int
    organization_id: UUID


