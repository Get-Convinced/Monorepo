/**
 * API Hooks - Centralized exports for all API-related hooks
 * 
 * This file provides a clean interface for importing API hooks throughout the app.
 * All hooks use Frontegg's useAuth for automatic authentication.
 */

// Core API client
export { useApiClient } from '@/lib/api-client';

// Domain-specific API hooks
export { useUserApi } from '../use-user-api';
export { useFileApi } from '../use-file-api';
export { useHealthApi } from '../use-health-api';

// React Query hooks (business logic + API calls)
export * from '../use-ragie-queries';
export * from '../use-organization-queries';
