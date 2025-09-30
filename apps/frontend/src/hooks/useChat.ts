/**
 * Custom hook for managing chat state and operations
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { useChatApi, ChatSession, ChatMessage, ResponseMode, SendMessageRequest } from '@/lib/api/chat';

interface UseChatReturn {
    // Session state
    session: ChatSession | null;
    sessionLoading: boolean;

    // Messages state
    messages: ChatMessage[];
    messagesLoading: boolean;

    // Sending state
    isSending: boolean;

    // Error state
    error: string | null;

    // Actions
    sendMessage: (question: string, mode?: ResponseMode, model?: 'gpt-4o' | 'gpt-3.5-turbo') => Promise<void>;
    createNewSession: () => Promise<void>;
    retryLastMessage: () => Promise<void>;

    // Utilities
    scrollToBottom: () => void;
}

export const useChat = (): UseChatReturn => {
    const chatApi = useChatApi();

    const [session, setSession] = useState<ChatSession | null>(null);
    const [sessionLoading, setSessionLoading] = useState(true);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [messagesLoading, setMessagesLoading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const lastQuestionRef = useRef<SendMessageRequest | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Scroll to bottom helper
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    // Load active session on mount
    useEffect(() => {
        const loadSession = async () => {
            try {
                setSessionLoading(true);
                setError(null);

                const activeSession = await chatApi.getActiveSession();
                setSession(activeSession);

                // Load messages for this session
                if (activeSession.id) {
                    setMessagesLoading(true);
                    const sessionMessages = await chatApi.getSessionMessages(activeSession.id);
                    setMessages(sessionMessages);
                }
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : 'Failed to load chat session';
                setError(errorMessage);
            } finally {
                setSessionLoading(false);
                setMessagesLoading(false);
            }
        };

        loadSession();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Only run once on mount

    // Scroll to bottom when messages change
    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);

    // Send message
    const sendMessage = useCallback(async (
        question: string,
        mode: ResponseMode = ResponseMode.STRICT,
        model: 'gpt-4o' | 'gpt-3.5-turbo' = 'gpt-4o'
    ) => {
        if (!session) {
            setError("No active session");
            return;
        }

        if (!question.trim()) {
            return;
        }

        setIsSending(true);
        setError(null);

        // Store request for retry
        lastQuestionRef.current = { question, mode, model };

        // Optimistically add user message
        const tempUserMessage: ChatMessage = {
            id: `temp-${Date.now()}`,
            session_id: session.id,
            role: 'user',
            content: question,
            status: 'completed',
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, tempUserMessage]);

        try {
            // Send to backend
            const response = await chatApi.sendMessage(session.id, {
                question,
                mode,
                model
            });

            // Replace temp message with real response
            setMessages(prev => [
                ...prev.filter(m => m.id !== tempUserMessage.id),
                tempUserMessage,
                response
            ]);

            // Update session title if it was "New Chat"
            if (session.title === 'New Chat') {
                setSession(prev => prev ? { ...prev, title: question.slice(0, 50) } : null);
            }

        } catch (err: any) {
            // Remove optimistic user message on error
            setMessages(prev => prev.filter(m => m.id !== tempUserMessage.id));

            let errorMessage = 'Failed to send message';

            if (err.response?.status === 429) {
                errorMessage = err.response.data.detail || 'Rate limit exceeded. Please try again later.';
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            }

            setError(errorMessage);
        } finally {
            setIsSending(false);
        }
    }, [session, chatApi]);

    // Create new session
    const createNewSession = useCallback(async () => {
        try {
            setSessionLoading(true);
            const newSession = await chatApi.createNewSession();
            setSession(newSession);
            setMessages([]);
            setError(null);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to create new session';
            setError(errorMessage);
        } finally {
            setSessionLoading(false);
        }
    }, [chatApi]);

    // Retry last message
    const retryLastMessage = useCallback(async () => {
        if (!lastQuestionRef.current) return;

        const { question, mode, model } = lastQuestionRef.current;
        await sendMessage(question, mode, model);
    }, [sendMessage]);

    return {
        session,
        sessionLoading,
        messages,
        messagesLoading,
        isSending,
        error,
        sendMessage,
        createNewSession,
        retryLastMessage,
        scrollToBottom
    };
};
