"use client";

import { Textarea } from "@/components/ui/textarea";

interface MarkdownInputProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    onSend?: () => void;
    disabled?: boolean;
}

export function MarkdownInput({
    value,
    onChange,
    placeholder = "Type your message... (Enter to send, Shift+Enter for new line)",
    className = "",
    onSend,
    disabled = false,
}: MarkdownInputProps) {
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
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                className="min-h-[60px] resize-none text-sm"
                onKeyDown={handleKeyDown}
                disabled={disabled}
            />
        </div>
    );
}
