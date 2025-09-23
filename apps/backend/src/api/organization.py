"""
Organization API endpoints.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database import DatabaseClient
from shared_database.database import get_async_session
from ..models.organization import (
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
    OrganizationListResponse,
    OrganizationMemberResponse,
    OrganizationMemberCreateRequest,
    OrganizationMemberUpdateRequest,
    OrganizationMemberListResponse
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_db_client() -> DatabaseClient:
    """Dependency to get database client."""
    return DatabaseClient()


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new organization."""
    try:
        # Check if slug already exists
        existing_org = await db_client.get_organization_by_slug(session, request.slug)
        if existing_org:
            raise HTTPException(
                status_code=400,
                detail=f"Organization with slug '{request.slug}' already exists"
            )
        
        # Create organization
        organization = await db_client.create_organization(
            session=session,
            name=request.name,
            slug=request.slug,
            description=request.description,
            settings=request.settings
        )
        
        await session.commit()
        return OrganizationResponse.model_validate(organization)
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")


@router.get("/", response_model=OrganizationListResponse)
async def list_organizations(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """List organizations with pagination."""
    try:
        from shared_database.services import OrganizationService
        service = OrganizationService(session)
        organizations = await service.list_organizations(limit=limit, offset=offset)
        
        # Get total count (simplified - in production you'd want a proper count query)
        total = len(organizations)  # This is not accurate for pagination
        
        return OrganizationListResponse(
            organizations=[OrganizationResponse.model_validate(org) for org in organizations],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list organizations: {str(e)}")


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(
    organization_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get organization by ID."""
    try:
        organization = await db_client.get_organization_by_id(session, organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return OrganizationResponse.model_validate(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization: {str(e)}")


@router.get("/slug/{slug}", response_model=OrganizationResponse)
async def get_organization_by_slug(
    slug: str,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get organization by slug."""
    try:
        organization = await db_client.get_organization_by_slug(session, slug)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        return OrganizationResponse.model_validate(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get organization: {str(e)}")


@router.put("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: UUID,
    request: OrganizationUpdateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Update organization."""
    try:
        from shared_database.services import OrganizationService
        service = OrganizationService(session)
        
        organization = await service.update_organization(
            org_id=organization_id,
            name=request.name,
            description=request.description,
            settings=request.settings
        )
        
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        await session.commit()
        return OrganizationResponse.model_validate(organization)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update organization: {str(e)}")


@router.post("/{organization_id}/members", response_model=OrganizationMemberResponse)
async def add_organization_member(
    organization_id: UUID,
    request: OrganizationMemberCreateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Add a member to an organization."""
    try:
        # Verify organization exists
        organization = await db_client.get_organization_by_id(session, organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Verify user exists
        user = await db_client.get_user_by_id(session, request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Add member
        member = await db_client.add_organization_member(
            session=session,
            organization_id=organization_id,
            user_id=request.user_id,
            role=request.role,
            permissions=request.permissions
        )
        
        await session.commit()
        return OrganizationMemberResponse.model_validate(member)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add member: {str(e)}")


@router.get("/{organization_id}/members", response_model=OrganizationMemberListResponse)
async def get_organization_members(
    organization_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get organization members."""
    try:
        # Verify organization exists
        organization = await db_client.get_organization_by_id(session, organization_id)
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        members = await db_client.get_organization_members(session, organization_id)
        
        return OrganizationMemberListResponse(
            members=[OrganizationMemberResponse.model_validate(member) for member in members],
            total=len(members),
            organization_id=organization_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get members: {str(e)}")


@router.put("/{organization_id}/members/{user_id}", response_model=OrganizationMemberResponse)
async def update_organization_member(
    organization_id: UUID,
    user_id: UUID,
    request: OrganizationMemberUpdateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Update organization member role and permissions."""
    try:
        from shared_database.services import OrganizationMemberService
        service = OrganizationMemberService(session)
        
        member = await service.update_member_role(
            organization_id=organization_id,
            user_id=user_id,
            role=request.role,
            permissions=request.permissions
        )
        
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        
        await session.commit()
        return OrganizationMemberResponse.model_validate(member)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update member: {str(e)}")


@router.delete("/{organization_id}/members/{user_id}")
async def remove_organization_member(
    organization_id: UUID,
    user_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Remove a member from an organization."""
    try:
        from shared_database.services import OrganizationMemberService
        service = OrganizationMemberService(session)
        
        success = await service.remove_member(organization_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Member not found")
        
        await session.commit()
        return {"message": "Member removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove member: {str(e)}")
