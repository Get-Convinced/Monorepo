"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MarkdownInput } from "@/components/shared/markdown-input";
import { Send, Lightbulb, Loader2 } from "lucide-react";
import { ResponseMode } from "@/lib/api/chat";
import { Badge } from "@/components/ui/badge";

interface InputAreaProps {
    showSuggestedPrompts?: boolean;
    onToggleSuggestedPrompts?: () => void;
    onStartTyping?: () => void;
    onSendMessage: (message: string) => Promise<void>;
    disabled?: boolean;
    currentMode: ResponseMode;
}

const modeBadgeColors = {
    [ResponseMode.STRICT]: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
    [ResponseMode.BALANCED]: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200",
    [ResponseMode.CREATIVE]: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200",
};

const modeLabels = {
    [ResponseMode.STRICT]: "Strict",
    [ResponseMode.BALANCED]: "Balanced",
    [ResponseMode.CREATIVE]: "Creative",
};

export function InputArea({
    showSuggestedPrompts = false,
    onToggleSuggestedPrompts,
    onStartTyping,
    onSendMessage,
    disabled = false,
    currentMode,
}: InputAreaProps) {
    const [message, setMessage] = useState("");
    const [isSending, setIsSending] = useState(false);

    const handleMessageChange = (newMessage: string) => {
        setMessage(newMessage);
        // Close suggested prompts when user starts typing
        if (newMessage.trim() && showSuggestedPrompts && onStartTyping) {
            onStartTyping();
        }
    };

    const handleSend = async () => {
        if (message.trim() && !isSending && !disabled) {
            setIsSending(true);
            try {
                await onSendMessage(message.trim());
                setMessage("");
            } catch (error) {
                console.error("Failed to send message:", error);
            } finally {
                setIsSending(false);
            }
        }
    };

    const isDisabled = disabled || isSending || !message.trim();

    return (
        <div className="p-4 border-t bg-card shadow-sm">
            <div className="flex flex-col gap-2 max-w-4xl mx-auto">
                <div className="flex items-center justify-between px-1">
                    <Badge variant="secondary" className={`text-xs ${modeBadgeColors[currentMode]}`}>
                        Mode: {modeLabels[currentMode]}
                    </Badge>
                    <p className="text-xs text-muted-foreground">Enter to send • Shift+Enter for new line</p>
                </div>
                <div className="flex gap-2">
                    <MarkdownInput
                        value={message}
                        onChange={handleMessageChange}
                        placeholder="Ask a question about your documents..."
                        onSend={handleSend}
                        className="flex-1"
                        disabled={disabled || isSending}
                    />
                    {!showSuggestedPrompts && onToggleSuggestedPrompts && (
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={onToggleSuggestedPrompts}
                            title="Show suggested prompts"
                            disabled={disabled || isSending}
                        >
                            <Lightbulb className="h-4 w-4" />
                        </Button>
                    )}
                    <Button size="icon" onClick={handleSend} disabled={isDisabled}>
                        {isSending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                    </Button>
                </div>
            </div>
        </div>
    );
}
