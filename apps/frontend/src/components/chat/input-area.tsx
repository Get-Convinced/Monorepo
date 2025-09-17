"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MarkdownInput } from "@/components/shared/markdown-input";
import { Paperclip, Send } from "lucide-react";

export function InputArea() {
    const [message, setMessage] = useState("");

    const handleSend = () => {
        if (message.trim()) {
            // TODO: Implement actual message sending
            console.log("Sending message:", message);
            setMessage("");
        }
    };

    return (
        <div className="p-4 border-t">
            <div className="flex gap-2 max-w-4xl mx-auto">
                <Button variant="outline" size="icon">
                    <Paperclip className="h-4 w-4" />
                </Button>
                <MarkdownInput
                    value={message}
                    onChange={setMessage}
                    placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
                    onSend={handleSend}
                    className="flex-1"
                />
                <Button size="icon" onClick={handleSend} disabled={!message.trim()}>
                    <Send className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}
