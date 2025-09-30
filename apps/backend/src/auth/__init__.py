# Authentication module - Frontegg SDK with Redis caching

from .frontegg_sdk_auth import (
    # Main auth instance
    frontegg_sdk_auth,
    
    # FastAPI dependencies
    get_current_user_sdk as get_current_user,
    get_current_user_optional_sdk as get_current_user_optional,
    require_auth_sdk as require_auth,
    get_organization_id_sdk as get_organization_id,
    
    # Health check
    sdk_auth_health_check as auth_health_check
)
