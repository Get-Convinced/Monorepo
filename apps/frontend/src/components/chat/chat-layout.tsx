"use client";

import { useState } from "react";
import { ChatInterface } from "./chat-interface";
import { SessionsSidebar } from "./sessions-sidebar";
import { useChat } from "@/hooks/useChat";
import { useChatSessions } from "@/hooks/useChatSessions";

export function ChatLayout() {
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    
    const {
        session,
        sessionLoading,
        messages,
        messagesLoading,
        isSending,
        error,
        sendMessage,
        createNewSession,
        switchToSession,
        retryLastMessage,
        scrollToBottom
    } = useChat();

    const {
        sessions,
        isLoading: sessionsLoading,
        archiveSession,
        deleteSession,
        refreshSessions
    } = useChatSessions();

    const handleSessionSelect = async (sessionId: string) => {
        if (session?.id === sessionId) return; // Already selected
        
        await switchToSession(sessionId);
        // Refresh sessions to update active status
        await refreshSessions();
    };

    const handleNewChat = async () => {
        await createNewSession();
        // Refresh sessions to show the new session
        await refreshSessions();
    };

    const handleArchiveSession = async (sessionId: string) => {
        await archiveSession(sessionId);
        // If we're archiving the current session, create a new one
        if (session?.id === sessionId) {
            await handleNewChat();
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        await deleteSession(sessionId);
        // If we're deleting the current session, create a new one
        if (session?.id === sessionId) {
            await handleNewChat();
        }
    };

    return (
        <div className="flex h-full">
            <SessionsSidebar
                sessions={sessions}
                currentSessionId={session?.id || null}
                isLoading={sessionsLoading}
                onSessionSelect={handleSessionSelect}
                onNewChat={handleNewChat}
                onArchiveSession={handleArchiveSession}
                onDeleteSession={handleDeleteSession}
                isCollapsed={sidebarCollapsed}
                onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
            />
            
            <div className="flex-1 flex flex-col min-w-0">
                <ChatInterface
                    session={session}
                    sessionLoading={sessionLoading}
                    messages={messages}
                    messagesLoading={messagesLoading}
                    isSending={isSending}
                    error={error}
                    sendMessage={sendMessage}
                    createNewSession={handleNewChat}
                    retryLastMessage={retryLastMessage}
                    scrollToBottom={scrollToBottom}
                />
            </div>
        </div>
    );
}

