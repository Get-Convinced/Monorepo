"use client";

import { Button } from "@/components/ui/button";
import { FileText } from "lucide-react";
import { ChatSource } from "@/lib/api/chat";

interface SourcesButtonProps {
    sources: ChatSource[];
    onClick: () => void;
}

export function SourcesButton({ sources, onClick }: SourcesButtonProps) {
    if (!sources || sources.length === 0) {
        return null;
    }

    return (
        <Button variant="ghost" size="sm" onClick={onClick} className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground">
            <FileText className="w-3 h-3 mr-1" />
            {sources.length} source{sources.length !== 1 ? "s" : ""}
        </Button>
    );
}

