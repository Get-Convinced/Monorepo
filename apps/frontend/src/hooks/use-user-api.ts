import { useMemo } from 'react';
import { useApiClient, ApiResponse } from '@/lib/api-client';

export const useUserApi = () => {
    const apiClient = useApiClient();

    return useMemo(() => ({
        async getUsers(limit: number = 100, offset: number = 0): Promise<any[]> {
            const response = await apiClient.get<ApiResponse<any[]>>('/users/', {
                params: { limit, offset }
            });
            return response.data.data;
        },

        async getUserById(userId: string): Promise<any> {
            const response = await apiClient.get<ApiResponse<any>>(`/users/${userId}`);
            return response.data.data;
        },

        async createUser(userData: {
            email: string;
            name: string;
            profile_data?: any;
            avatar_url?: string;
        }): Promise<any> {
            const response = await apiClient.post<ApiResponse<any>>('/users/', userData);
            return response.data.data;
        }
    }), [apiClient]);
};
