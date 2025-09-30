import { useMemo } from 'react';
import { useApiClient, ApiResponse } from '@/lib/api-client';

export const useFileApi = () => {
    const apiClient = useApiClient();

    return useMemo(() => ({
        async uploadFile(file: File, organizationId?: string): Promise<any> {
            const formData = new FormData();
            formData.append('file', file);
            if (organizationId) {
                formData.append('organization_id', organizationId);
            }

            const response = await apiClient.post<ApiResponse<any>>('/files/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                }
            });
            return response.data.data;
        },

        async getFiles(organizationId?: string, limit: number = 100, offset: number = 0): Promise<any[]> {
            const response = await apiClient.get<ApiResponse<any[]>>('/files/', {
                params: { organization_id: organizationId, limit, offset }
            });
            return response.data.data;
        },

        async getFileById(fileId: string): Promise<any> {
            const response = await apiClient.get<ApiResponse<any>>(`/files/${fileId}`);
            return response.data.data;
        },

        async deleteFile(fileId: string): Promise<void> {
            await apiClient.delete(`/files/${fileId}`);
        }
    }), [apiClient]);
};
