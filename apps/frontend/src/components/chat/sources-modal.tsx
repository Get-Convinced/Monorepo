"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, ExternalLink, X } from "lucide-react";
import { ChatSource } from "@/lib/api/chat";

interface SourcesModalProps {
    isOpen: boolean;
    onClose: () => void;
    sources: ChatSource[];
    messageContent: string;
}

export function SourcesModal({ isOpen, onClose, sources, messageContent }: SourcesModalProps) {
    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0">
                <DialogHeader className="flex-shrink-0 p-6 pb-4">
                    <DialogTitle className="flex items-center justify-between">
                        <span>Sources & Citations</span>
                        <button onClick={onClose} className="p-1 hover:bg-muted rounded-sm transition-colors">
                            <X className="w-4 h-4" />
                        </button>
                    </DialogTitle>
                </DialogHeader>

                <div className="flex-1 min-h-0 flex flex-col gap-4 px-6 pb-6">
                    {/* Message content preview */}
                    <div className="flex-shrink-0 p-3 bg-muted/50 rounded-lg">
                        <p className="text-sm text-muted-foreground mb-1">Response:</p>
                        <p className="text-sm line-clamp-3">{messageContent}</p>
                    </div>

                    {/* Sources list */}
                    <div className="flex-1 min-h-0 flex flex-col">
                        <p className="text-sm font-medium text-muted-foreground mb-3 flex-shrink-0">
                            {sources.length} source{sources.length !== 1 ? "s" : ""} found:
                        </p>

                        <ScrollArea className="flex-1">
                            <div className="space-y-3 pr-4">
                                {sources.map((source, index) => (
                                    <SourceCard key={source.id} source={source} index={index} />
                                ))}
                            </div>
                        </ScrollArea>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

function SourceCard({ source, index }: { source: ChatSource; index: number }) {
    const relevancePercentage = Math.round(source.relevance_score * 100);

    return (
        <Card className="border-l-4 border-l-primary/50 hover:border-l-primary transition-colors">
            <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                        <FileText className="w-5 h-5 mt-0.5 text-primary flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{source.document_name}</p>
                            {source.page_number && <p className="text-xs text-muted-foreground mt-1">Page {source.page_number}</p>}
                        </div>
                    </div>
                    <Badge variant={relevancePercentage >= 80 ? "default" : "secondary"} className="flex-shrink-0 text-xs">
                        {relevancePercentage}%
                    </Badge>
                </div>

                {source.chunk_text && (
                    <div className="pl-8">
                        <p className="text-sm text-muted-foreground leading-relaxed">{source.chunk_text}</p>
                    </div>
                )}

                <div className="flex items-center gap-2 text-xs text-muted-foreground pl-8">
                    <ExternalLink className="w-3 h-3" />
                    <span>Source {index + 1}</span>
                </div>
            </CardContent>
        </Card>
    );
}
