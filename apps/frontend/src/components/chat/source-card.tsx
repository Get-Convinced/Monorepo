"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, ExternalLink, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import { ChatSource } from "@/lib/api/chat";
import { cn } from "@/lib/utils";

interface SourceCardProps {
    source: ChatSource;
    index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const relevancePercentage = Math.round(source.relevance_score * 100);
    const sourceNumber = source.source_number ?? index + 1;
    
    return (
        <Card className={cn(
            "border-l-4 transition-all",
            source.is_used 
                ? "border-l-green-500 hover:border-l-green-600" 
                : "border-l-primary/50 hover:border-l-primary"
        )}>
            <CardContent className="p-3 space-y-2">
                {/* Header with badges */}
                <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                        <FileText className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                                <p className="text-sm font-medium truncate">
                                    {source.document_name}
                                </p>
                                {source.is_used && (
                                    <Badge 
                                        variant="default" 
                                        className="bg-green-500 hover:bg-green-600 text-white flex items-center gap-1 text-xs"
                                    >
                                        <CheckCircle2 className="w-3 h-3" />
                                        Used
                                    </Badge>
                                )}
                            </div>
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
                
                {/* Usage reason (if source was used) */}
                {source.is_used && source.usage_reason && (
                    <div className="pl-6 p-2 bg-green-50 dark:bg-green-950/20 rounded-md border border-green-200 dark:border-green-800">
                        <p className="text-xs font-medium text-green-800 dark:text-green-200 mb-1">
                            Why this source was used:
                        </p>
                        <p className="text-xs text-green-700 dark:text-green-300">
                            {source.usage_reason}
                        </p>
                    </div>
                )}
                
                {/* Preview text (collapsed by default) */}
                {source.chunk_text && (
                    <div className="pl-6">
                        <p className={cn(
                            "text-xs text-muted-foreground",
                            !isExpanded && "line-clamp-2"
                        )}>
                            {source.chunk_text}
                        </p>
                        {source.chunk_text.length > 200 && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2 text-xs mt-1"
                                onClick={() => setIsExpanded(!isExpanded)}
                            >
                                {isExpanded ? (
                                    <>
                                        <ChevronUp className="w-3 h-3 mr-1" />
                                        Show less
                                    </>
                                ) : (
                                    <>
                                        <ChevronDown className="w-3 h-3 mr-1" />
                                        Show more
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                )}
                
                {/* Footer */}
                <div className="flex items-center gap-1 text-xs text-muted-foreground pl-6">
                    <ExternalLink className="w-3 h-3" />
                    <span>Source {sourceNumber}</span>
                </div>
            </CardContent>
        </Card>
    );
}





