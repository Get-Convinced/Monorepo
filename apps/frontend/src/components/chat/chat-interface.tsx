"use client";

import { useState } from "react";
import { ChatHeader } from "./chat-header";
import { MessageArea } from "./message-area";
import { InputArea } from "./input-area";
import { SuggestedPrompts } from "./suggested-prompts";
import { useChat } from "@/hooks/useChat";
import { ResponseMode } from "@/lib/api/chat";
import { Loader2 } from "lucide-react";

export function ChatInterface() {
    const [suggestedPromptsVisible, setSuggestedPromptsVisible] = useState(true);
    const [mode, setMode] = useState<ResponseMode>(ResponseMode.STRICT);
    const [model, setModel] = useState<'gpt-4o' | 'gpt-3.5-turbo'>('gpt-4o');
    
    const {
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
    } = useChat();

    const handleCloseSuggestedPrompts = () => {
        setSuggestedPromptsVisible(false);
    };

    const handlePromptClick = async (prompt: string) => {
        setSuggestedPromptsVisible(false);
        await sendMessage(prompt, mode, model);
    };

    const handleToggleSuggestedPrompts = () => {
        setSuggestedPromptsVisible(!suggestedPromptsVisible);
    };

    const handleSendMessage = async (message: string) => {
        await sendMessage(message, mode, model);
    };

    // Show loading state while session loads
    if (sessionLoading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-2">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Loading chat...</p>
                </div>
            </div>
        );
    }

    // Show empty messages when no session
    const showSuggestedPrompts = suggestedPromptsVisible && messages.length === 0;

    return (
        <div className="flex flex-col h-full max-h-full overflow-hidden">
            <ChatHeader 
                mode={mode}
                model={model}
                onModeChange={setMode}
                onModelChange={setModel}
                onNewChat={createNewSession}
            />
            <div className="flex-1 min-h-0 overflow-hidden">
                <MessageArea 
                    messages={messages}
                    loading={messagesLoading || isSending}
                    error={error}
                    onRetry={retryLastMessage}
                />
            </div>
            <div className="flex-shrink-0">
                {showSuggestedPrompts && (
                    <SuggestedPrompts
                        isVisible={showSuggestedPrompts}
                        onClose={handleCloseSuggestedPrompts}
                        onPromptClick={handlePromptClick}
                    />
                )}
                <InputArea
                    showSuggestedPrompts={showSuggestedPrompts}
                    onToggleSuggestedPrompts={handleToggleSuggestedPrompts}
                    onStartTyping={handleCloseSuggestedPrompts}
                    onSendMessage={handleSendMessage}
                    disabled={isSending}
                    currentMode={mode}
                />
            </div>
        </div>
    );
}
