"use client";

import { useState, useMemo } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { X, Info } from "lucide-react";
import { ChatSource } from "@/lib/api/chat";
import { SourceCard } from "./source-card";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface SourcesModalProps {
    isOpen: boolean;
    onClose: () => void;
    sources: ChatSource[];
    messageContent: string;
}

export function SourcesModal({ isOpen, onClose, sources, messageContent }: SourcesModalProps) {
    const [showAllSources, setShowAllSources] = useState(false);
    
    // Detect if this is a legacy message (no source usage tracking)
    const isLegacyMessage = sources.length > 0 && sources.every(s => !s.source_number);
    
    // Filter sources based on toggle
    const filteredSources = useMemo(() => {
        if (showAllSources || isLegacyMessage) {
            return sources;
        }
        return sources.filter(s => s.is_used);
    }, [sources, showAllSources, isLegacyMessage]);
    
    const usedSourcesCount = sources.filter(s => s.is_used).length;
    const totalSourcesCount = sources.length;
    
    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-4xl h-[85vh] flex flex-col p-0">
                <DialogHeader className="flex-shrink-0 p-6 pb-4">
                    <DialogTitle className="flex items-center justify-between">
                        <span>Sources & Citations</span>
                        <button 
                            onClick={onClose} 
                            className="p-1 hover:bg-muted rounded-sm transition-colors"
                            aria-label="Close"
                        >
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
                    
                    {/* Legacy message notice */}
                    {isLegacyMessage && (
                        <Alert className="flex-shrink-0">
                            <Info className="h-4 w-4" />
                            <AlertDescription className="text-xs">
                                Legacy message: All sources shown. Source usage tracking was not available when this message was generated.
                            </AlertDescription>
                        </Alert>
                    )}

                    {/* Controls */}
                    {!isLegacyMessage && (
                        <div className="flex-shrink-0 flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                            <div className="flex items-center gap-2">
                                <Badge variant="default" className="bg-green-500">
                                    {usedSourcesCount} Used
                                </Badge>
                                <span className="text-sm text-muted-foreground">
                                    / {totalSourcesCount} Total
                                </span>
                            </div>
                            
                            <div className="flex items-center space-x-2">
                                <Switch 
                                    id="show-all" 
                                    checked={showAllSources}
                                    onCheckedChange={setShowAllSources}
                                />
                                <Label 
                                    htmlFor="show-all" 
                                    className="text-sm font-medium cursor-pointer"
                                >
                                    Show all sources
                                </Label>
                            </div>
                        </div>
                    )}

                    {/* Sources list */}
                    <div className="flex-1 min-h-0 flex flex-col">
                        <p className="text-sm font-medium text-muted-foreground mb-3 flex-shrink-0">
                            {filteredSources.length} source{filteredSources.length !== 1 ? "s" : ""} displayed:
                        </p>

                        <ScrollArea className="flex-1">
                            <div className="space-y-3 pr-4">
                                {filteredSources.length > 0 ? (
                                    filteredSources.map((source, index) => (
                                        <SourceCard key={source.id} source={source} index={index} />
                                    ))
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <p className="text-sm">No sources were directly used in this response.</p>
                                        <p className="text-xs mt-2">Toggle &quot;Show all sources&quot; to see all retrieved sources.</p>
                                    </div>
                                )}
                            </div>
                        </ScrollArea>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
