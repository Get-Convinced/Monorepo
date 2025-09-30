"use client";

import { Button } from "@/components/ui/button";
import { MessageSquarePlus } from "lucide-react";
import { SettingsDropdown } from "./settings-dropdown";
import { ResponseMode } from "@/lib/api/chat";

interface ChatHeaderProps {
    mode: ResponseMode;
    model: "gpt-4o" | "gpt-3.5-turbo";
    onModeChange: (mode: ResponseMode) => void;
    onModelChange: (model: "gpt-4o" | "gpt-3.5-turbo") => void;
    onNewChat: () => void;
}

export function ChatHeader({ mode, model, onModeChange, onModelChange, onNewChat }: ChatHeaderProps) {
    return (
        <div className="flex justify-between items-center p-4 border-b flex-shrink-0 bg-card">
            <div className="flex items-center gap-3">
                <h1 className="text-lg font-semibold text-foreground">Chat</h1>
            </div>
            <div className="flex gap-2 items-center">
                <Button variant="outline" size="sm" onClick={onNewChat} className="gap-2">
                    <MessageSquarePlus className="h-4 w-4" />
                    New Chat
                </Button>
                <SettingsDropdown mode={mode} model={model} onModeChange={onModeChange} onModelChange={onModelChange} />
            </div>
        </div>
    );
}
