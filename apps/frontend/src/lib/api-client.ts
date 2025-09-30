/**
 * Hook-Only API Client for Backend Communication
 * 
 * Uses Frontegg's useAuth hook for reliable authentication.
 * All API calls must be made from within React components.
 */
import axios, { AxiosError } from 'axios';
import { useAuth } from '@frontegg/nextjs';
import { useMemo } from 'react';

// API Response Types
export interface ApiResponse<T> {
    success: boolean;
    data: T;
    meta?: {
        timestamp: string;
        requestId: string;
    };
}

export interface ApiError {
    success: false;
    error: {
        code: string;
        message: string;
        details?: Record<string, any>;
    };
}

// Hook-based authenticated API client
const useApiClient = () => {
    const { user } = useAuth();


    return useMemo(() => {
        const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

        const client = axios.create({
            baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Add auth headers to every request
        client.interceptors.request.use(
            (config) => {
                if (user?.accessToken) {
                    config.headers.Authorization = `Bearer ${user.accessToken}`;
                }

                if (user?.tenantId) {
                    config.headers['X-Organization-ID'] = user.tenantId;
                }

                return config;
            },
            (error) => {
                return Promise.reject(error);
            }
        );

        // Add response interceptor for error handling
        client.interceptors.response.use(
            (response) => {
                return response;
            },
            (error) => {
                // Only log actual errors, not debug info
                if (error.response?.status >= 500) {
                    console.error('Server error:', error.response?.status);
                }
                return Promise.reject(error);
            }
        );

        return client;
    }, [user?.accessToken, user?.tenantId]);
};

// Export the core useApiClient hook for other hooks to use
export { useApiClient };
