"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MarkdownInput } from "@/components/shared/markdown-input";
import { Paperclip, Send, Lightbulb } from "lucide-react";

interface InputAreaProps {
    showSuggestedPrompts?: boolean;
    onToggleSuggestedPrompts?: () => void;
    onStartTyping?: () => void;
}

export function InputArea({ showSuggestedPrompts = false, onToggleSuggestedPrompts, onStartTyping }: InputAreaProps) {
    const [message, setMessage] = useState("");

    const handleMessageChange = (newMessage: string) => {
        setMessage(newMessage);
        // Close suggested prompts when user starts typing
        if (newMessage.trim() && showSuggestedPrompts && onStartTyping) {
            onStartTyping();
        }
    };

    const handleSend = () => {
        if (message.trim()) {
            // TODO: Implement actual message sending
            console.log("Sending message:", message);
            setMessage("");
        }
    };

    return (
        <div className="p-4 border-t bg-background/95 backdrop-blur-sm shadow-sm">
            <div className="flex gap-2 max-w-4xl mx-auto">
                <Button variant="outline" size="icon">
                    <Paperclip className="h-4 w-4" />
                </Button>
                <MarkdownInput
                    value={message}
                    onChange={handleMessageChange}
                    placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                    onSend={handleSend}
                    className="flex-1"
                />
                {!showSuggestedPrompts && onToggleSuggestedPrompts && (
                    <Button variant="outline" size="icon" onClick={onToggleSuggestedPrompts} title="Show suggested prompts">
                        <Lightbulb className="h-4 w-4" />
                    </Button>
                )}
                <Button size="icon" onClick={handleSend} disabled={!message.trim()}>
                    <Send className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
