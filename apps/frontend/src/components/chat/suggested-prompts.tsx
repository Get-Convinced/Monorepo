"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function SuggestedPrompts() {
    const prompts = [
        "Analyze the uploaded document",
        "Summarize key findings",
        "Create a proposal outline",
        "Generate questions for review",
    ];

    return (
        <div className="p-4 border-t">
            <div className="max-w-4xl mx-auto">
                <h3 className="text-sm font-medium text-muted-foreground mb-3">Suggested prompts</h3>
                <div className="grid grid-cols-2 gap-3">
                    {prompts.map((prompt, index) => (
                        <Button key={index} variant="outline" className="h-auto p-3 text-left justify-start">
                            <span className="text-sm">{prompt}</span>
                        </Button>
                    ))}
                </div>
            </div>
        </div>
    );
}
