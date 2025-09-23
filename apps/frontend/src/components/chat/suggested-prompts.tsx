"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface SuggestedPromptsProps {
    isVisible: boolean;
    onClose: () => void;
    onPromptClick?: (prompt: string) => void;
}

export function SuggestedPrompts({ isVisible, onClose, onPromptClick }: SuggestedPromptsProps) {
    const prompts = [
        "Analyze the uploaded document",
        "Summarize key findings",
        "Create a proposal outline",
        "Generate questions for review",
    ];

    if (!isVisible) {
        return null;
    }

    const handlePromptClick = (prompt: string) => {
        if (onPromptClick) {
            onPromptClick(prompt);
        }
    };

    return (
        <div className="p-4 border-t bg-background/95 backdrop-blur-sm shadow-sm">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-medium text-muted-foreground">Suggested prompts</h3>
                    <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0 hover:bg-muted">
                        <X className="h-4 w-4" />
                    </Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                    {prompts.map((prompt, index) => (
                        <Button
                            key={index}
                            variant="outline"
                            className="h-auto p-3 text-left justify-start hover:bg-accent"
                            onClick={() => handlePromptClick(prompt)}
                        >
                            <span className="text-sm">{prompt}</span>
                        </Button>
                    ))}
                </div>
            </div>
        </div>
    );
}
