"use client";

import { useState } from "react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Settings2, Zap, Scale, Sparkles } from "lucide-react";
import { ResponseMode } from "@/lib/api/chat";

interface SettingsDropdownProps {
    mode: ResponseMode;
    model: 'gpt-4o' | 'gpt-3.5-turbo';
    onModeChange: (mode: ResponseMode) => void;
    onModelChange: (model: 'gpt-4o' | 'gpt-3.5-turbo') => void;
}

const modeIcons = {
    [ResponseMode.STRICT]: Zap,
    [ResponseMode.BALANCED]: Scale,
    [ResponseMode.CREATIVE]: Sparkles,
};

const modeLabels = {
    [ResponseMode.STRICT]: 'Strict',
    [ResponseMode.BALANCED]: 'Balanced',
    [ResponseMode.CREATIVE]: 'Creative',
};

const modeDescriptions = {
    [ResponseMode.STRICT]: 'Factual only, no assumptions',
    [ResponseMode.BALANCED]: 'Balanced, reasonable inferences',
    [ResponseMode.CREATIVE]: 'Broader context, general knowledge',
};

export function SettingsDropdown({
    mode,
    model,
    onModeChange,
    onModelChange
}: SettingsDropdownProps) {
    const ModeIcon = modeIcons[mode];

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9">
                    <Settings2 className="h-4 w-4" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
                <DropdownMenuLabel className="flex items-center gap-2">
                    <Settings2 className="h-4 w-4" />
                    Chat Settings
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                    Response Mode
                </DropdownMenuLabel>
                <DropdownMenuRadioGroup value={mode} onValueChange={(value) => onModeChange(value as ResponseMode)}>
                    {Object.entries(ResponseMode).map(([key, value]) => {
                        const Icon = modeIcons[value];
                        return (
                            <DropdownMenuRadioItem key={value} value={value} className="flex flex-col items-start gap-1 py-3">
                                <div className="flex items-center gap-2">
                                    <Icon className="h-4 w-4" />
                                    <span className="font-medium">{modeLabels[value]}</span>
                                </div>
                                <span className="text-xs text-muted-foreground pl-6">
                                    {modeDescriptions[value]}
                                </span>
                            </DropdownMenuRadioItem>
                        );
                    })}
                </DropdownMenuRadioGroup>
                
                <DropdownMenuSeparator />
                
                <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">
                    Model
                </DropdownMenuLabel>
                <DropdownMenuRadioGroup value={model} onValueChange={(value) => onModelChange(value as 'gpt-4o' | 'gpt-3.5-turbo')}>
                    <DropdownMenuRadioItem value="gpt-4o" className="flex flex-col items-start gap-1 py-2">
                        <span className="font-medium">GPT-4o</span>
                        <span className="text-xs text-muted-foreground">
                            Most capable (Recommended)
                        </span>
                    </DropdownMenuRadioItem>
                    <DropdownMenuRadioItem value="gpt-3.5-turbo" className="flex flex-col items-start gap-1 py-2">
                        <span className="font-medium">GPT-3.5 Turbo</span>
                        <span className="text-xs text-muted-foreground">
                            Faster responses
                        </span>
                    </DropdownMenuRadioItem>
                </DropdownMenuRadioGroup>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}





