"use client";

import { useEffect, useRef } from "react";
import { Textarea } from "@/components/ui/textarea";

interface MarkdownInputProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    onSend?: () => void;
    disabled?: boolean;
    minHeight?: number; // in pixels
    maxHeight?: number; // in pixels
}

export function MarkdownInput({
    value,
    onChange,
    placeholder = "Type your message... (Enter to send, Shift+Enter for new line)",
    className = "",
    onSend,
    disabled = false,
    minHeight = 60,
    maxHeight = 300,
}: MarkdownInputProps) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea based on content
    useEffect(() => {
        const textarea = textareaRef.current;
        if (!textarea) return;

        // Reset height to measure scrollHeight accurately
        textarea.style.height = `${minHeight}px`;

        // Calculate new height
        const scrollHeight = textarea.scrollHeight;
        const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);

        // Set new height
        textarea.style.height = `${newHeight}px`;
    }, [value, minHeight, maxHeight]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSend?.();
        }
        // Shift+Enter allows new lines (default textarea behavior)
    };

    return (
        <div className={className}>
            <Textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="resize-none text-sm transition-[height] duration-75 overflow-y-auto"
                style={{
                    minHeight: `${minHeight}px`,
                    maxHeight: `${maxHeight}px`,
                }}
                onKeyDown={handleKeyDown}
                disabled={disabled}
            />
        </div>
    );
}
