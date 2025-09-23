"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { MarkdownRenderer } from "@/components/shared/markdown-renderer";
import { Bot, User } from "lucide-react";

export function MessageArea() {
    const messages = [
        {
            id: "1",
            type: "user" as const,
            content: "Can you help me analyze the uploaded document?",
            timestamp: "2:30 PM",
        },
        {
            id: "2",
            type: "ai" as const,
            content:
                "I'd be happy to help you analyze the document! I can see you've uploaded a PDF file. What specific aspects would you like me to focus on? I can help with summarization, key points extraction, or answer specific questions about the content.",
            timestamp: "2:31 PM",
        },
        {
            id: "3",
            type: "user" as const,
            content: "Please summarize the key findings and create a proposal outline.",
            timestamp: "2:32 PM",
        },
        {
            id: "4",
            type: "ai" as const,
            content:
                'Based on the document analysis, here are the key findings:\n\n## Key Findings\n- Market growth of **15%** year-over-year\n- Increased demand for AI-powered solutions\n- Competitive landscape shows 3 major players\n\n## Proposal Outline\n1. **Executive Summary**\n2. Market Analysis\n3. Solution Architecture\n4. Implementation Timeline\n5. Budget Requirements\n6. Risk Assessment\n\n> Would you like me to elaborate on any of these sections?\n\nHere\'s a code example for the implementation:\n\n```javascript\nconst proposal = {\n  title: "AI-Powered Solution",\n  timeline: "6 months",\n  budget: "$500K"\n};\n```',
            timestamp: "2:33 PM",
        },
        {
            id: "5",
            type: "user" as const,
            content: "Great! Can you also create a table comparing the different solutions?",
            timestamp: "2:34 PM",
        },
        {
            id: "6",
            type: "ai" as const,
            content:
                "Absolutely! Here's a comparison table:\n\n| Solution | Cost | Timeline | Risk Level |\n|----------|------|----------|------------|\n| Option A | $300K | 4 months | Low |\n| Option B | $500K | 6 months | Medium |\n| Option C | $800K | 8 months | High |\n\n**Recommendation:** I'd suggest Option B as it provides the best balance of cost, timeline, and risk.\n\n- ✅ **Pros:** Good ROI, manageable timeline\n- ⚠️ **Cons:** Medium risk level\n- 🎯 **Next Steps:** Schedule stakeholder review",
            timestamp: "2:35 PM",
        },
    ];

    return (
        <ScrollArea className="h-full">
            <div className="p-4 pb-4 mx-auto space-y-4 max-w-4xl">
                {messages.map((message) => (
                    <div key={message.id} className={`flex gap-3 ${message.type === "user" ? "justify-end" : "justify-start"}`}>
                        {message.type === "ai" && (
                            <Avatar className="mt-1 w-8 h-8">
                                <AvatarFallback className="bg-primary text-primary-foreground">
                                    <Bot className="w-4 h-4" />
                                </AvatarFallback>
                            </Avatar>
                        )}

                        <Card className={`max-w-[80%] ${message.type === "user" ? "bg-primary text-primary-foreground" : "bg-card"}`}>
                            <CardContent className="p-3">
                                <div className="text-sm">
                                    <MarkdownRenderer content={message.content} className={message.type === "user" ? "prose-invert" : ""} />
                                </div>
                                <p
                                    className={`text-xs mt-2 ${
                                        message.type === "user" ? "text-primary-foreground/70" : "text-muted-foreground"
                                    }`}
                                >
                                    {message.timestamp}
                                </p>
                            </CardContent>
                        </Card>

                        {message.type === "user" && (
                            <Avatar className="mt-1 w-8 h-8">
                                <AvatarFallback className="bg-secondary">
                                    <User className="w-4 h-4" />
                                </AvatarFallback>
                            </Avatar>
                        )}
                    </div>
                ))}
            </div>
        </ScrollArea>
    );
}
