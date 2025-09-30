import { useMemo } from 'react';
import axios from 'axios';

// Health check (no auth required)
export const useHealthApi = () => {
    return useMemo(() => ({
        async checkHealth(): Promise<{ status: string; service: string }> {
            const response = await axios.get(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'}/health`);
            return response.data;
        },

        async getApiStatus(): Promise<any> {
            const response = await axios.get(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'}/api/status`);
            return response.data;
        }
    }), []);
};
