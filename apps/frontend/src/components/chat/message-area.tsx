"use client";

import { useEffect, useRef, useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { MarkdownRenderer } from "@/components/shared/markdown-renderer";
import { Bot, User, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { ChatMessage } from "@/lib/api/chat";
import { SourcesButton } from "./sources-button";
import { SourcesModal } from "./sources-modal";
import { format } from "date-fns";

interface MessageAreaProps {
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
    onRetry?: () => void;
}

export function MessageArea({ messages, loading, error, onRetry }: MessageAreaProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [sourcesModalOpen, setSourcesModalOpen] = useState(false);
    const [selectedMessageSources, setSelectedMessageSources] = useState<{
        sources: ChatMessage["sources"];
        content: string;
    } | null>(null);

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const formatTimestamp = (timestamp: string) => {
        try {
            return format(new Date(timestamp), "h:mm a");
        } catch {
            return "";
        }
    };

    const handleShowSources = (sources: ChatMessage["sources"], content: string) => {
        if (sources && sources.length > 0) {
            setSelectedMessageSources({ sources, content });
            setSourcesModalOpen(true);
        }
    };

    const handleCloseSourcesModal = () => {
        setSourcesModalOpen(false);
        setSelectedMessageSources(null);
    };

    return (
        <>
            <ScrollArea className="h-full">
                <div className="p-4 pb-4 mx-auto space-y-4 max-w-4xl">
                    {messages.length === 0 && !loading && (
                        <div className="flex items-center justify-center h-full min-h-[300px]">
                            <div className="text-center space-y-2">
                                <Bot className="w-12 h-12 mx-auto text-muted-foreground/50" />
                                <p className="text-sm text-muted-foreground">No messages yet. Start a conversation!</p>
                            </div>
                        </div>
                    )}

                    {messages.map((message) => (
                        <div key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                            {message.role === "assistant" && (
                                <Avatar className="mt-1 w-8 h-8 flex-shrink-0">
                                    <AvatarFallback className="bg-primary text-primary-foreground">
                                        <Bot className="w-4 h-4" />
                                    </AvatarFallback>
                                </Avatar>
                            )}

                            <div className={`flex flex-col gap-2 ${message.role === "user" ? "max-w-[80%]" : "max-w-[85%]"}`}>
                                <Card className={`${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-card"}`}>
                                    <CardContent className="p-3">
                                        <div className="text-sm">
                                            <MarkdownRenderer
                                                content={message.content}
                                                className={message.role === "user" ? "prose-invert" : ""}
                                            />
                                        </div>

                                        {message.status === "failed" && message.error_message && (
                                            <div className="mt-2 p-2 bg-destructive/10 rounded text-xs text-destructive">
                                                <AlertCircle className="w-3 h-3 inline mr-1" />
                                                {message.error_message}
                                            </div>
                                        )}

                                        <div className="flex items-center justify-between mt-2">
                                            <div className="flex items-center gap-2">
                                                <p
                                                    className={`text-xs ${
                                                        message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                                                    }`}
                                                >
                                                    {formatTimestamp(message.created_at)}
                                                </p>
                                                {message.role === "assistant" && message.sources && message.sources.length > 0 && (
                                                    <SourcesButton
                                                        sources={message.sources}
                                                        onClick={() => handleShowSources(message.sources, message.content)}
                                                    />
                                                )}
                                            </div>
                                            {message.tokens_total && (
                                                <p className="text-xs text-muted-foreground">{message.tokens_total} tokens</p>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            </div>

                            {message.role === "user" && (
                                <Avatar className="mt-1 w-8 h-8 flex-shrink-0">
                                    <AvatarFallback className="bg-secondary">
                                        <User className="w-4 h-4" />
                                    </AvatarFallback>
                                </Avatar>
                            )}
                        </div>
                    ))}

                    {/* Loading indicator */}
                    {loading && (
                        <div className="flex gap-3 justify-start">
                            <Avatar className="mt-1 w-8 h-8 flex-shrink-0">
                                <AvatarFallback className="bg-primary text-primary-foreground">
                                    <Bot className="w-4 h-4" />
                                </AvatarFallback>
                            </Avatar>
                            <Card className="bg-card">
                                <CardContent className="p-3">
                                    <div className="flex items-center gap-2">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span className="text-sm text-muted-foreground">Thinking...</span>
                                    </div>
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    {/* Error state */}
                    {error && (
                        <div className="flex gap-3 justify-center">
                            <Card className="bg-destructive/10 border-destructive/20">
                                <CardContent className="p-3 flex items-center justify-between gap-4">
                                    <div className="flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4 text-destructive" />
                                        <span className="text-sm text-destructive">{error}</span>
                                    </div>
                                    {onRetry && (
                                        <Button size="sm" variant="ghost" onClick={onRetry} className="h-7">
                                            <RefreshCw className="w-3 h-3 mr-1" />
                                            Retry
                                        </Button>
                                    )}
                                </CardContent>
                            </Card>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </ScrollArea>

            {/* Sources Modal */}
            {selectedMessageSources && (
                <SourcesModal
                    isOpen={sourcesModalOpen}
                    onClose={handleCloseSourcesModal}
                    sources={selectedMessageSources.sources || []}
                    messageContent={selectedMessageSources.content}
                />
            )}
        </>
    );
}
