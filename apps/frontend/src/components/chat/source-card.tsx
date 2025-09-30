"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, ExternalLink } from "lucide-react";
import { ChatSource } from "@/lib/api/chat";

interface SourceCardProps {
    source: ChatSource;
    index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
    const relevancePercentage = Math.round(source.relevance_score * 100);
    
    return (
        <Card className="border-l-4 border-l-primary/50 hover:border-l-primary transition-colors">
            <CardContent className="p-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                        <FileText className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                                {source.document_name}
                            </p>
                            {source.page_number && (
                                <p className="text-xs text-muted-foreground">
                                    Page {source.page_number}
                                </p>
                            )}
                        </div>
                    </div>
                    <Badge 
                        variant={relevancePercentage >= 80 ? "default" : "secondary"}
                        className="flex-shrink-0 text-xs"
                    >
                        {relevancePercentage}%
                    </Badge>
                </div>
                
                {source.chunk_text && (
                    <p className="text-xs text-muted-foreground line-clamp-2 pl-6">
                        {source.chunk_text}
                    </p>
                )}
                
                <div className="flex items-center gap-1 text-xs text-muted-foreground pl-6">
                    <ExternalLink className="w-3 h-3" />
                    <span>Source {index + 1}</span>
                </div>
            </CardContent>
        </Card>
    );
}

