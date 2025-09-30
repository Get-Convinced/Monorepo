# Authentication module - Frontegg SDK with auto-provisioning

from .frontegg_sdk_auth import (
    # Main auth instance
    frontegg_sdk_auth,
    
    # FastAPI dependencies (base - without provisioning)
    get_current_user_sdk as get_current_user,
    get_current_user_optional_sdk as get_current_user_optional,
    require_auth_sdk as require_auth,
    get_organization_id_sdk as get_organization_id,
    
    # Health check
    sdk_auth_health_check as auth_health_check
)

from .provisioning_auth import (
    # Auto-provisioning dependencies (recommended for most endpoints)
    get_current_user_with_provisioning,
    get_provisioned_user,
    get_provisioned_organization,
    get_user_and_org_ids,
)
