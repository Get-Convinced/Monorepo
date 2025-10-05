"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
    MessageSquare, 
    Plus, 
    Archive, 
    Trash2, 
    ChevronLeft, 
    ChevronRight,
    MoreVertical,
    Clock
} from "lucide-react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChatSession } from "@/lib/api/chat";
import { formatDistanceToNow } from "date-fns";

interface SessionsSidebarProps {
    sessions: ChatSession[];
    currentSessionId: string | null;
    isLoading: boolean;
    onSessionSelect: (sessionId: string) => void;
    onNewChat: () => void;
    onArchiveSession: (sessionId: string) => void;
    onDeleteSession: (sessionId: string) => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

export function SessionsSidebar({
    sessions,
    currentSessionId,
    isLoading,
    onSessionSelect,
    onNewChat,
    onArchiveSession,
    onDeleteSession,
    isCollapsed,
    onToggleCollapse
}: SessionsSidebarProps) {
    const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);

    const handleSessionAction = (action: 'archive' | 'delete', sessionId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (action === 'archive') {
            onArchiveSession(sessionId);
        } else if (action === 'delete') {
            onDeleteSession(sessionId);
        }
    };

    if (isCollapsed) {
        return (
            <div className="w-12 border-r bg-card flex flex-col items-center py-4 gap-2">
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onToggleCollapse}
                    className="h-8 w-8"
                >
                    <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onNewChat}
                    className="h-8 w-8"
                    title="New Chat"
                >
                    <Plus className="h-4 w-4" />
                </Button>
                <div className="w-6 h-px bg-border" />
                <div className="flex flex-col gap-1">
                    {sessions.slice(0, 5).map((session) => (
                        <Button
                            key={session.id}
                            variant={currentSessionId === session.id ? "default" : "ghost"}
                            size="icon"
                            className="h-8 w-8"
                            onClick={() => onSessionSelect(session.id)}
                            title={session.title}
                        >
                            <MessageSquare className="h-4 w-4" />
                        </Button>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="w-80 border-r bg-card flex flex-col">
            {/* Header */}
            <div className="p-4 border-b">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="font-semibold text-lg">Chat History</h2>
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onToggleCollapse}
                        className="h-8 w-8"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </Button>
                </div>
                <Button onClick={onNewChat} className="w-full" size="sm">
                    <Plus className="h-4 w-4 mr-2" />
                    New Chat
                </Button>
            </div>

            {/* Sessions List */}
            <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="text-sm text-muted-foreground">Loading sessions...</div>
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                            <MessageSquare className="h-8 w-8 text-muted-foreground mb-2" />
                            <p className="text-sm text-muted-foreground">No chat history yet</p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Start a conversation to see it here
                            </p>
                        </div>
                    ) : (
                        sessions.map((session) => (
                            <Card
                                key={session.id}
                                className={`cursor-pointer transition-all hover:shadow-sm ${
                                    currentSessionId === session.id
                                        ? 'ring-2 ring-primary bg-primary/5'
                                        : 'hover:bg-muted/50'
                                }`}
                                onMouseEnter={() => setHoveredSessionId(session.id)}
                                onMouseLeave={() => setHoveredSessionId(null)}
                                onClick={() => onSessionSelect(session.id)}
                            >
                                <CardContent className="p-3">
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <h3 className="font-medium text-sm truncate">
                                                    {session.title}
                                                </h3>
                                                {session.is_active && (
                                                    <Badge variant="secondary" className="text-xs">
                                                        Active
                                                    </Badge>
                                                )}
                                            </div>
                                            
                                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                <Clock className="h-3 w-3" />
                                                <span>
                                                    {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true })}
                                                </span>
                                                {session.message_count && session.message_count > 0 && (
                                                    <>
                                                        <span>•</span>
                                                        <span>{session.message_count} messages</span>
                                                    </>
                                                )}
                                            </div>
                                        </div>

                                        {/* Actions Menu */}
                                        <DropdownMenu>
                                            <DropdownMenuTrigger asChild>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <MoreVertical className="h-3 w-3" />
                                                </Button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end">
                                                <DropdownMenuItem
                                                    onClick={(e) => handleSessionAction('archive', session.id, e)}
                                                    className="text-orange-600"
                                                >
                                                    <Archive className="h-4 w-4 mr-2" />
                                                    Archive
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={(e) => handleSessionAction('delete', session.id, e)}
                                                    className="text-red-600"
                                                >
                                                    <Trash2 className="h-4 w-4 mr-2" />
                                                    Delete
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                </CardContent>
                            </Card>
                        ))
                    )}
                </div>
            </ScrollArea>
        </div>
    );
}
