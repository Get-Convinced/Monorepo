"use client";

import { useState, useEffect, useCallback, useRef } from 'react';
import { useChatApi, ChatSession } from '@/lib/api/chat';
import { toast } from 'sonner';

interface UseChatSessionsReturn {
    sessions: ChatSession[];
    isLoading: boolean;
    error: string | null;
    loadSessions: () => Promise<void>;
    archiveSession: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
    refreshSessions: () => Promise<void>;
}

export const useChatSessions = (): UseChatSessionsReturn => {
    const chatApi = useChatApi();
    const chatApiRef = useRef(chatApi);

    // Keep ref updated
    chatApiRef.current = chatApi;

    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadSessions = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            const userSessions = await chatApiRef.current.getUserSessions(false, 50); // Exclude archived, limit 50
            setSessions(userSessions);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to load chat sessions';
            setError(errorMessage);
            toast.error(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, []); // No dependencies - use ref instead

    const archiveSession = useCallback(async (sessionId: string) => {
        try {
            await chatApiRef.current.archiveSession(sessionId);

            // Update local state
            setSessions(prev => prev.filter(session => session.id !== sessionId));

            toast.success("Session archived successfully");
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to archive session';
            toast.error(errorMessage);
        }
    }, []);

    const deleteSession = useCallback(async (sessionId: string) => {
        try {
            await chatApiRef.current.deleteSession(sessionId);

            // Update local state
            setSessions(prev => prev.filter(session => session.id !== sessionId));

            toast.success("Session deleted successfully");
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to delete session';
            toast.error(errorMessage);
        }
    }, []);

    const refreshSessions = useCallback(async () => {
        await loadSessions();
    }, [loadSessions]);

    // Load sessions on mount
    useEffect(() => {
        loadSessions();
    }, []); // Empty dependency array - only run once on mount

    return {
        sessions,
        isLoading,
        error,
        loadSessions,
        archiveSession,
        deleteSession,
        refreshSessions,
    };
};
