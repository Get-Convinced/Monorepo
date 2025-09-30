# Backend Authentication Setup

This document explains how the backend handles Frontegg authentication.

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_knowledge_agent
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_knowledge_agent
DB_USER=postgres
DB_PASSWORD=postgres

# Frontegg Configuration
# Get these values from your Frontegg dashboard
FRONTEGG_CLIENT_ID=your-client-id-here
FRONTEGG_CLIENT_SECRET=your-client-secret-here
FRONTEGG_BASE_URL=https://app.frontegg.com

# Frontend Configuration
FRONTEND_ORIGIN=http://localhost:3000

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6380

# Application Configuration
APP_ENV=local
```

## Database Setup

### 1. Start PostgreSQL
```bash
cd /Users/gauthamgsabahit/workspace/convinced/Monorepo
docker-compose up -d postgres
```

### 2. Run Database Migrations
```bash
cd packages/database
alembic upgrade head
```

### 3. Test Database Connection
```bash
cd packages/database
python test_db.py
```

## Architecture Overview

### Frontend (Next.js) Responsibilities
- ✅ Handle Frontegg OAuth flow
- ✅ Store and manage authentication tokens
- ✅ Include Bearer tokens in API requests
- ✅ Redirect unauthenticated users

### Backend (FastAPI) Responsibilities
- ✅ Validate Frontegg JWT tokens
- ✅ Extract user information from tokens
- ✅ Implement authorization logic
- ✅ Store/retrieve user data from database
- ✅ Handle business logic

## Authentication Flow

1. **User Login**: Frontend redirects to Frontegg hosted login
2. **Token Exchange**: Frontegg returns JWT token to frontend
3. **API Requests**: Frontend includes Bearer token in API requests
4. **Token Validation**: Backend validates JWT token with Frontegg public key
5. **User Creation**: Backend creates user in database if first time login
6. **Authorization**: Backend checks user permissions for protected endpoints

## Protected Endpoints

All endpoints that require authentication use the `get_current_user` dependency:

```python
from ..auth.frontegg_auth import get_current_user

@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    # current_user contains the decoded JWT payload
    user_email = current_user.get("email")
    # ... your logic here
```

## New Endpoints

- `GET /users/me` - Get current user's profile (auto-creates user if first login)
- All existing endpoints now require authentication

## Installation

Install the new dependencies:

```bash
cd apps/backend
pip install -r requirements.txt
```

## Testing

1. Start the backend server
2. Login through the frontend
3. Use the API test component to verify authentication works
4. Check that Bearer tokens are properly validated
