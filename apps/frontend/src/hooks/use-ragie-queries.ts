import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useMemo } from 'react';
import { useApiClient } from '@/lib/api-client';

// Simplified types - only what we actually need
export interface RagieDocument {
    id: string;
    name: string;
    status: "ready" | "processing" | "failed";
    created_at: string;
    updated_at: string;
    metadata: {
        title?: string;
        description?: string;
        tags?: string[];
    };
}

export interface UploadProgress {
    upload_id: string;
    filename: string;
    status: "uploading" | "processing" | "completed" | "failed";
    upload_progress: number;
    processing_progress: number;
    processing_status?: string;
    document_id?: string;
    error_message?: string;
    stage_description?: string;
}

export interface DocumentAnalytics {
    total_documents: number;
    total_size_bytes: number;
    by_file_type: Record<string, { count: number; size_bytes: number }>;
    by_status: Record<string, number>;
    upload_trends: Record<string, number>;
}

// Internal API hook for Ragie operations
const useRagieApi = () => {
    const apiClient = useApiClient();

    return useMemo(() => ({
        async uploadDocument(file: File, metadata?: { title?: string; description?: string; tags?: string[] }) {
            const formData = new FormData();
            formData.append('file', file);
            if (metadata) {
                formData.append('metadata', JSON.stringify(metadata));
            }

            const response = await apiClient.post('/api/v1/ragie/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            // Upload endpoint returns DocumentUploadResponse directly, not wrapped in {success: true, data: ...}
            // Response: {upload_id, filename, status, message}
            return response.data;
        },

        async getDocuments() {
            const response = await apiClient.get('/api/v1/ragie/documents');
            // Documents endpoint returns {documents: [], cursor: null, has_more: false}
            // NOT the standard {success: true, data: ...} format
            return response.data.documents || [];
        },

        async deleteDocument(documentId: string) {
            await apiClient.delete(`/api/v1/ragie/documents/${documentId}`);
        },

        async updateMetadata(documentId: string, metadata: Record<string, any>) {
            const response = await apiClient.patch(`/api/v1/ragie/documents/${documentId}/metadata`, { metadata });
            // Metadata endpoint returns {success: true, data: {...}} format
            if (!response.data?.data) {
                throw new Error('Invalid response: missing data');
            }
            return response.data.data;
        },

        async getUploadProgress(uploadId: string) {
            const response = await apiClient.get(`/api/v1/ragie/upload-progress/${uploadId}`);
            // Upload progress endpoint returns {success: true, data: {...}} format
            if (!response.data?.data) {
                throw new Error('Invalid response: missing data');
            }
            return response.data.data;
        },

        async getAnalytics() {
            const response = await apiClient.get('/api/v1/ragie/documents/analytics');
            // Analytics endpoint returns {success: true, data: {...}} format
            if (!response.data?.data) {
                throw new Error('Invalid response: missing data');
            }
            return response.data.data;
        },

        async downloadDocument(documentId: string) {
            const response = await apiClient.get(`/api/v1/ragie/documents/${documentId}/source`, {
                responseType: 'blob',
            });
            return response.data;
        },
    }), [apiClient]);
};

// Query keys for React Query
const ragieKeys = {
    all: ['ragie'] as const,
    documents: () => [...ragieKeys.all, 'documents'] as const,
    analytics: () => [...ragieKeys.all, 'analytics'] as const,
    uploadProgress: (uploadId: string) => [...ragieKeys.all, 'upload-progress', uploadId] as const,
};

// Hook-based queries with built-in error handling
export function useRagieDocuments() {
    console.log('🔄 [QUERY] useRagieDocuments hook called');
    const ragieApi = useRagieApi();

    return useQuery({
        queryKey: ragieKeys.documents(),
        queryFn: async () => {
            console.log('🔄 [QUERY] Executing ragieApi.getDocuments query function');
            const result = await ragieApi.getDocuments();
            console.log('🔄 [QUERY] getDocuments result:', result);
            // Ensure we always return an array, never undefined
            return Array.isArray(result) ? result : [];
        },
        staleTime: 30 * 1000, // 30 seconds
    });
}

export function useUploadDocument() {
    const queryClient = useQueryClient();
    const ragieApi = useRagieApi();

    return useMutation({
        mutationFn: ({ file, metadata }: { file: File; metadata?: { title?: string; description?: string; tags?: string[] } }) =>
            ragieApi.uploadDocument(file, metadata),
        onSuccess: (data) => {
            toast.success(`Upload started for "${data.filename}"`);
        },
        onError: (error: any) => {
            const message = error.response?.data?.error?.message || 'Upload failed';
            toast.error(message);
        },
    });
}

export function useDeleteDocument() {
    const queryClient = useQueryClient();
    const ragieApi = useRagieApi();

    return useMutation({
        mutationFn: ragieApi.deleteDocument,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ragieKeys.documents() });
            toast.success('Document deleted successfully');
        },
        onError: (error: any) => {
            const message = error.response?.data?.error?.message || 'Delete failed';
            toast.error(message);
        },
    });
}

export function useUpdateMetadata() {
    const queryClient = useQueryClient();
    const ragieApi = useRagieApi();

    return useMutation({
        mutationFn: ({ documentId, metadata }: { documentId: string; metadata: Record<string, any> }) =>
            ragieApi.updateMetadata(documentId, metadata),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ragieKeys.documents() });
            toast.success('Metadata updated successfully');
        },
        onError: (error: any) => {
            const message = error.response?.data?.error?.message || 'Update failed';
            toast.error(message);
        },
    });
}

export function useUploadProgress(uploadId: string, enabled: boolean = true) {
    const ragieApi = useRagieApi();

    return useQuery({
        queryKey: ragieKeys.uploadProgress(uploadId),
        queryFn: () => ragieApi.getUploadProgress(uploadId),
        enabled: enabled && !!uploadId,
        refetchInterval: (query) => {
            const data = query.state.data;
            if (data && (data.status === 'completed' || data.status === 'failed')) {
                return false; // Stop polling
            }
            return 1000; // Poll every second
        },
    });
}

export function useDocumentAnalytics() {
    const ragieApi = useRagieApi();

    return useQuery({
        queryKey: ragieKeys.analytics(),
        queryFn: ragieApi.getAnalytics,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

export function useDownloadDocument() {
    const ragieApi = useRagieApi();

    return useMutation({
        mutationFn: async ({ documentId, filename }: { documentId: string; filename: string }) => {
            const blob = await ragieApi.downloadDocument(documentId);

            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        },
        onSuccess: () => {
            toast.success('Download started');
        },
        onError: (error: any) => {
            const message = error.response?.data?.error?.message || 'Download failed';
            toast.error(message);
        },
    });
}

// Bulk operations simplified - just loop through individual operations
export function useBulkDelete() {
    const queryClient = useQueryClient();
    const ragieApi = useRagieApi();

    return useMutation({
        mutationFn: async (documentIds: string[]) => {
            const results = await Promise.allSettled(
                documentIds.map(id => ragieApi.deleteDocument(id))
            );

            const successful = results.filter(r => r.status === 'fulfilled').length;
            const failed = results.filter(r => r.status === 'rejected').length;

            return { successful, failed, total: documentIds.length };
        },
        onSuccess: (result) => {
            queryClient.invalidateQueries({ queryKey: ragieKeys.documents() });
            if (result.failed > 0) {
                toast.warning(`${result.successful} deleted, ${result.failed} failed`);
            } else {
                toast.success(`${result.successful} documents deleted`);
            }
        },
        onError: () => {
            toast.error('Bulk delete failed');
        },
    });
}
