"use client";

import { useState } from "react";
import { ChatHeader } from "./chat-header";
import { MessageArea } from "./message-area";
import { InputArea } from "./input-area";
import { SuggestedPrompts } from "./suggested-prompts";

export function ChatInterface() {
    const [suggestedPromptsVisible, setSuggestedPromptsVisible] = useState(true);

    const handleCloseSuggestedPrompts = () => {
        setSuggestedPromptsVisible(false);
    };

    const handlePromptClick = (prompt: string) => {
        // TODO: Implement prompt selection logic
        console.log("Selected prompt:", prompt);
        // Close the suggested prompts after selection for better UX
        setSuggestedPromptsVisible(false);
    };

    const handleToggleSuggestedPrompts = () => {
        setSuggestedPromptsVisible(!suggestedPromptsVisible);
    };

    return (
        <div className="flex flex-col h-full max-h-full overflow-hidden">
            <ChatHeader />
            <div className="flex-1 min-h-0 overflow-hidden">
                <MessageArea />
            </div>
            <div className="flex-shrink-0">
                <SuggestedPrompts
                    isVisible={suggestedPromptsVisible}
                    onClose={handleCloseSuggestedPrompts}
                    onPromptClick={handlePromptClick}
                />
                <InputArea
                    showSuggestedPrompts={suggestedPromptsVisible}
                    onToggleSuggestedPrompts={handleToggleSuggestedPrompts}
                    onStartTyping={handleCloseSuggestedPrompts}
                />
            </div>
        </div>
    );
}
