# JWT Token Caching Strategy

## 🎯 **Why Token Caching?**

### **Problem**
- Every API request requires validating JWT token with Frontegg
- Network latency adds ~100-500ms per request
- Frontegg API rate limits and availability issues
- Poor user experience with slow API responses

### **Solution: Smart Token Caching**
- Cache validated tokens locally for 5 minutes
- Fallback to Frontegg validation when cache miss
- Automatic cache invalidation on token expiration
- Redis + local memory for high availability

## 🏗️ **Architecture**

```
Request → Cache Check → Frontegg (if needed) → Response
    ↓           ↓              ↓
  Fast      Redis/Local    Network Call
```

### **Cache Layers**
1. **Redis Cache** (Primary): Shared across backend instances
2. **Local Memory** (Fallback): Per-instance cache
3. **Frontegg API** (Source of Truth): When cache miss

## ⚡ **Performance Benefits**

| Scenario | Without Cache | With Cache | Improvement |
|----------|---------------|------------|-------------|
| Cache Hit | 200-500ms | 1-5ms | **99% faster** |
| Cache Miss | 200-500ms | 200-500ms | Same |
| Frontegg Down | Request fails | Works (cached) | **100% uptime** |

## 🔒 **Security Considerations**

### **Token Revocation**
- **Immediate**: Tokens revoked in Frontegg are cached for up to 5 minutes
- **Mitigation**: Short cache TTL (5 minutes) + local expiration check
- **Critical Actions**: Force re-validation for sensitive operations

### **Cache Security**
- Tokens hashed for cache keys (no plaintext storage)
- Automatic cleanup of expired entries
- Redis authentication (if configured)

## 🛠️ **Configuration**

### **Environment Variables**
```env
# Redis Configuration (optional)
REDIS_URL=redis://localhost:6380

# Cache Settings
TOKEN_CACHE_TTL=300  # 5 minutes
PUBLIC_KEY_CACHE_TTL=3600  # 1 hour
```

### **Cache TTL Strategy**
- **Token Cache**: 5 minutes (balance of performance vs security)
- **Public Key Cache**: 1 hour (rarely changes)
- **Local Fallback**: Same TTL as Redis

## 📊 **Monitoring & Metrics**

### **Key Metrics to Track**
- Cache hit rate (target: >80%)
- Average response time
- Frontegg API call frequency
- Cache invalidation events

### **Health Checks**
- Redis connectivity
- Cache performance
- Token validation success rate

## 🚀 **Usage Examples**

### **Automatic Caching**
```python
# No code changes needed - caching is automatic
@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    # First call: validates with Frontegg + caches
    # Subsequent calls: uses cache (5x faster)
    return {"user": current_user}
```

### **Manual Cache Management**
```python
from src.auth.token_cache import token_cache

# Invalidate specific token (e.g., on logout)
token_cache.invalidate_token(user_token)

# Invalidate all user tokens (e.g., password change)
token_cache.invalidate_user_tokens(user_id)
```

## 🔄 **Cache Invalidation Strategies**

### **Automatic Invalidation**
- Token expiration (JWT `exp` claim)
- Cache TTL expiration (5 minutes)
- Local expiration check

### **Manual Invalidation**
- User logout
- Password change
- Account suspension
- Security incidents

## 🎛️ **Tuning Recommendations**

### **For High Traffic**
- Increase Redis memory
- Use Redis clustering
- Monitor cache hit rates

### **For High Security**
- Reduce cache TTL (1-2 minutes)
- Force re-validation for sensitive endpoints
- Implement cache warming

### **For Development**
- Use local cache only (no Redis)
- Longer TTL for testing
- Disable cache for debugging

## 🚨 **Fallback Behavior**

### **Redis Unavailable**
- Falls back to local memory cache
- No performance degradation
- Automatic Redis reconnection

### **Frontegg Unavailable**
- Uses cached tokens only
- Graceful degradation
- Health check endpoints

## 📈 **Expected Results**

- **90%+ cache hit rate** for active users
- **5-10x faster** API responses
- **Reduced Frontegg API calls** by 90%
- **Better user experience** with faster loading
- **Higher reliability** with fallback mechanisms
