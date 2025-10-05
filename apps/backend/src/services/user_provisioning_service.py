"""
User and Organization Auto-Provisioning Service.

This service automatically creates user and organization records in our database
when a user authenticates via Frontegg for the first time.
"""

import logging
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func

from shared_database.models import User, Organization, OrganizationMember, UserRole

logger = logging.getLogger(__name__)


class UserProvisioningService:
    """Service for auto-provisioning users and organizations from Frontegg."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_user_and_org(
        self, 
        frontegg_user: Dict[str, Any]
    ) -> Tuple[User, Organization]:
        """
        Get or create user and organization from Frontegg user info.
        
        This is called on every authenticated request to ensure the user/org
        exist in our database before proceeding with business logic.
        
        Args:
            frontegg_user: User info from Frontegg JWT token
            
        Returns:
            Tuple of (User, Organization)
        """
        # Extract Frontegg data
        user_id = uuid.UUID(frontegg_user["id"])
        email = frontegg_user.get("email", "")
        name = frontegg_user.get("name", email)
        tenant_id = uuid.UUID(frontegg_user["tenantId"])
        tenant_ids = frontegg_user.get("tenantIds", [frontegg_user["tenantId"]])
        roles = frontegg_user.get("roles", [])
        
        # Get or create organization
        organization = await self._get_or_create_organization(tenant_id, name)
        
        # Get or create user
        user = await self._get_or_create_user(
            user_id=user_id,
            email=email,
            name=name,
            frontegg_data=frontegg_user
        )
        
        # Ensure user is member of organization
        await self._ensure_organization_membership(
            user=user,
            organization=organization,
            roles=roles
        )
        
        return user, organization
    
    async def _get_or_create_organization(
        self, 
        tenant_id: uuid.UUID,
        default_name: str
    ) -> Organization:
        """Get or create organization."""
        # Try to get existing organization
        result = await self.session.execute(
            select(Organization).where(Organization.id == tenant_id)
        )
        organization = result.scalar_one_or_none()
        
        if organization:
            logger.debug(f"Found existing organization: {organization.id}")
            return organization
        
        # Create new organization
        # Generate a slug from the org ID (first 8 chars)
        slug = str(tenant_id)[:8]
        
        # Create S3 bucket name (lowercase, alphanumeric)
        s3_bucket = f"org-{slug}"
        
        organization = Organization(
            id=tenant_id,
            name=default_name or f"Organization {slug}",
            slug=slug,
            s3_bucket_name=s3_bucket,
            settings={
                "auto_provisioned": True,
                "frontegg_tenant_id": str(tenant_id)
            }
        )
        
        self.session.add(organization)
        await self.session.commit()
        await self.session.refresh(organization)
        
        logger.info(f"Created new organization: {organization.id} ({organization.name})")
        return organization
    
    async def _get_or_create_user(
        self,
        user_id: uuid.UUID,
        email: str,
        name: str,
        frontegg_data: Dict[str, Any]
    ) -> User:
        """Get or create user."""
        # Try to get existing user
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update last login and profile if needed
            user.last_login_at = func.now()
            if user.email != email:
                user.email = email
            if user.name != name:
                user.name = name
            
            await self.session.commit()
            await self.session.refresh(user)
            logger.debug(f"Found existing user: {user.id}")
            return user
        
        # Create new user
        user = User(
            id=user_id,
            email=email,
            name=name,
            is_active=True,
            email_verified=frontegg_data.get("emailVerified", False),
            avatar_url=frontegg_data.get("profilePictureUrl"),
            profile_data={
                "frontegg_sub": frontegg_data.get("sub"),
                "frontegg_roles": frontegg_data.get("roles", []),
                "frontegg_permissions": frontegg_data.get("permissions", []),
                "auto_provisioned": True
            }
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        logger.info(f"Created new user: {user.id} ({user.email})")
        return user
    
    async def _ensure_organization_membership(
        self,
        user: User,
        organization: Organization,
        roles: list
    ) -> OrganizationMember:
        """Ensure user is a member of the organization."""
        # Check if membership exists
        result = await self.session.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == organization.id
            )
        )
        membership = result.scalar_one_or_none()
        
        if membership:
            logger.debug(f"User {user.id} already member of org {organization.id}")
            return membership
        
        # Determine role from Frontegg roles
        role = UserRole.MEMBER.value
        if "Admin" in roles or "admin" in roles:
            role = UserRole.ADMIN.value
        elif "Viewer" in roles or "viewer" in roles:
            role = UserRole.VIEWER.value
        
        # Create membership
        membership = OrganizationMember(
            organization_id=organization.id,
            user_id=user.id,
            role=role,
            is_active=True,
            permissions={
                "frontegg_roles": roles,
                "auto_provisioned": True
            }
        )
        
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(membership)
        
        logger.info(
            f"Created membership: user {user.id} → org {organization.id} (role: {role})"
        )
        return membership


# Dependency for FastAPI
async def get_user_provisioning_service(
    session: AsyncSession
) -> UserProvisioningService:
    """Get user provisioning service instance."""
    return UserProvisioningService(session)

