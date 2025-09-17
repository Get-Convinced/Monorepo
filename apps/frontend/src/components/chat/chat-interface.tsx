"use client";

import { ChatHeader } from "./chat-header";
import { MessageArea } from "./message-area";
import { InputArea } from "./input-area";
import { SuggestedPrompts } from "./suggested-prompts";

export function ChatInterface() {
    return (
        <div className="flex flex-col h-full">
            <ChatHeader />
            <MessageArea />
            <SuggestedPrompts />
            <InputArea />
        </div>
    );
}
