"""
User API models.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Request model for creating a user."""
    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    profile_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional profile data")
    avatar_url: Optional[str] = Field(None, max_length=500, description="User avatar URL")


class UserUpdateRequest(BaseModel):
    """Request model for updating a user."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User full name")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="Additional profile data")
    avatar_url: Optional[str] = Field(None, max_length=500, description="User avatar URL")


class UserResponse(BaseModel):
    """Response model for user data."""
    id: UUID
    email: str
    name: str
    profile_data: Dict[str, Any]
    avatar_url: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response model for user list."""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class UserOrganizationResponse(BaseModel):
    """Response model for user's organization membership."""
    organization_id: UUID
    organization_name: str
    organization_slug: str
    role: str
    permissions: Dict[str, Any]
    joined_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserOrganizationsResponse(BaseModel):
    """Response model for user's organizations."""
    organizations: List[UserOrganizationResponse]
    total: int


