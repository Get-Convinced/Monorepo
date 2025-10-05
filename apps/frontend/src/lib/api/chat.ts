/**
 * Chat API Client
 * Endpoints for RAG-powered chat with source citations
 */
import { useApiClient } from '../api-client';
import { useCallback, useMemo } from 'react';

// ============ Types ============

export enum ResponseMode {
    STRICT = 'strict',
    BALANCED = 'balanced',
    CREATIVE = 'creative'
}

export interface ChatSource {
    id: string;
    ragie_document_id: string;
    document_name: string;
    page_number?: number;
    chunk_text: string;
    relevance_score: number;
}

export interface ChatMessage {
    id: string;
    session_id: string;
    role: 'user' | 'assistant';
    content: string;
    status: 'pending' | 'streaming' | 'completed' | 'failed';
    sources?: ChatSource[];
    error_message?: string;
    created_at: string;
    tokens_total?: number;
    processing_time_ms?: number;
}

export interface ChatSession {
    id: string;
    user_id: string;
    organization_id: string;
    title: string;
    is_active: boolean;
    is_archived: boolean;
    temperature: number;
    model_name: string;
    created_at: string;
    updated_at: string;
    last_message_at?: string;
    message_count?: number;
}

export interface SendMessageRequest {
    question: string;
    mode: ResponseMode;
    model: 'gpt-4o' | 'gpt-3.5-turbo';
}

// ============ API Hook ============

export const useChatApi = () => {
    const apiClient = useApiClient();

    const getActiveSession = useCallback(async (): Promise<ChatSession> => {
        const response = await apiClient.get('/api/v1/chat/session');
        return response.data;
    }, [apiClient]);

    const createNewSession = useCallback(async (): Promise<ChatSession> => {
        const response = await apiClient.post('/api/v1/chat/session/new');
        return response.data;
    }, [apiClient]);

    const sendMessage = useCallback(async (
        sessionId: string,
        request: SendMessageRequest
    ): Promise<ChatMessage> => {
        const response = await apiClient.post(
            `/api/v1/chat/message?session_id=${sessionId}`,
            request
        );
        return response.data;
    }, [apiClient]);

    const getSessionMessages = useCallback(async (
        sessionId: string,
        limit: number = 50
    ): Promise<ChatMessage[]> => {
        const response = await apiClient.get(
            `/api/v1/chat/session/${sessionId}/messages`,
            { params: { limit } }
        );
        return response.data;
    }, [apiClient]);

    const getUserSessions = useCallback(async (
        includeArchived: boolean = false,
        limit: number = 50
    ): Promise<ChatSession[]> => {
        const response = await apiClient.get('/api/v1/chat/sessions', {
            params: { include_archived: includeArchived, limit }
        });
        return response.data;
    }, [apiClient]);

    const archiveSession = useCallback(async (sessionId: string): Promise<void> => {
        await apiClient.post(`/api/v1/chat/session/${sessionId}/archive`);
    }, [apiClient]);

    const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
        await apiClient.delete(`/api/v1/chat/session/${sessionId}`);
    }, [apiClient]);

    return useMemo(() => ({
        getActiveSession,
        createNewSession,
        sendMessage,
        getSessionMessages,
        getUserSessions,
        archiveSession,
        deleteSession
    }), [
        getActiveSession,
        createNewSession,
        sendMessage,
        getSessionMessages,
        getUserSessions,
        archiveSession,
        deleteSession
    ]);
};





