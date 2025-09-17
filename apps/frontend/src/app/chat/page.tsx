"use client";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "../../components/DashboardLayout";
import { Card, Col, Row, Tabs, Typography, Input, Button, List, Collapse } from "antd";
import { FileTextOutlined, FileExcelOutlined, ArrowRightOutlined, DownOutlined } from "@ant-design/icons";

export default function ChatPage() {
    const router = useRouter();
    // For Phase 2, we'll use a placeholder name until auth is fully wired
    const displayName = "Arjun";
    const [activeMode, setActiveMode] = useState<string>("qa");
    const [prompt, setPrompt] = useState<string>("");
    const [activeSideTab, setActiveSideTab] = useState<string>("library");
    const [search, setSearch] = useState<string>("");
    const [libraryExpanded, setLibraryExpanded] = useState<boolean>(true);
    const [messages, setMessages] = useState<Array<{ id: string; text: string; sender: "user" | "assistant"; timestamp: number }>>([]);
    const [isLoading, setIsLoading] = useState<boolean>(false);

    type RecentItem = { key: string; label: string; href: string; updatedAt: number; type: string };
    const [recentItems, setRecentItems] = useState<RecentItem[]>([]);

    const suggestions: string[] = [
        "how does Docket take care of outdated data?",
        "What is Docket?",
        "Is Docket SOC compliant?",
        "why is sky blue?",
    ];

    // Mock recent chat conversations only
    const mockRecentItems: RecentItem[] = [
        {
            key: "1",
            label: "how Docket is different from the new Notion AI?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 30,
            type: "conversation",
        },
        {
            key: "2",
            label: "what are the top features of Docket?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 60,
            type: "conversation",
        },
        {
            key: "3",
            label: "What types of questions Docket can answer",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 90,
            type: "conversation",
        },
        {
            key: "4",
            label: "How is Docket different from Notion AI?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 240,
            type: "conversation",
        },
        {
            key: "5",
            label: "How does Docket take care of outdated data?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 300,
            type: "conversation",
        },
        {
            key: "6",
            label: "Is Docket SOC compliant?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 360,
            type: "conversation",
        },
        {
            key: "7",
            label: "What are the types of questions that Docket can answer?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 420,
            type: "conversation",
        },
        {
            key: "8",
            label: "How can Docket's AI Sales Engineer help with RFPs?",
            href: "/chat",
            updatedAt: Date.now() - 1000 * 60 * 480,
            type: "conversation",
        },
    ];

    useEffect(() => {
        setRecentItems(mockRecentItems);
    }, []);

    const last7Days = useMemo(() => {
        const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
        return recentItems.filter((i) => i.updatedAt >= weekAgo && (!search || i.label.toLowerCase().includes(search.toLowerCase())));
    }, [recentItems, search]);

    const handleSubmit = useCallback(async () => {
        if (!prompt.trim()) return;

        const userMessage = {
            id: Date.now().toString(),
            text: prompt,
            sender: "user" as const,
            timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setPrompt("");
        setIsLoading(true);

        // Mock API response with delay
        setTimeout(() => {
            const assistantMessage = {
                id: (Date.now() + 1).toString(),
                text: `Based on your question about "${prompt.slice(0, 50)}${
                    prompt.length > 50 ? "..." : ""
                }", here's what I can tell you:\n\nDocket is an AI-powered knowledge management platform that helps organizations manage and access their information more effectively. It uses advanced AI to understand context and provide accurate responses to user queries.\n\nWould you like me to elaborate on any specific aspect?`,
                sender: "assistant" as const,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
            setIsLoading(false);
        }, 1500);
    }, [activeMode, prompt]);

    const handleKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
            e.preventDefault();
            handleSubmit();
        }
    };

    const sidebarContent = (
        <>
            <Tabs
                activeKey={activeSideTab}
                onChange={setActiveSideTab}
                items={[
                    { key: "library", label: "Library" },
                    { key: "collections", label: "Collections" },
                ]}
                style={{ marginBottom: 16 }}
            />
            {activeSideTab === "library" && (
                <>
                    <Input.Search
                        placeholder="Search"
                        allowClear
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ marginBottom: 12 }}
                    />
                    <Typography.Text type="secondary" style={{ color: "rgba(255,255,255,0.65)", fontSize: 12, textTransform: "uppercase" }}>
                        LAST 7 DAYS
                    </Typography.Text>
                    <div style={{ marginTop: 12 }}>
                        {last7Days.map((item) => (
                            <div
                                key={item.key}
                                style={{
                                    padding: "12px 16px",
                                    marginBottom: 8,
                                    borderRadius: 8,
                                    background: "rgba(255,255,255,0.05)",
                                    cursor: "pointer",
                                    transition: "all 0.2s",
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.background = "rgba(255,255,255,0.1)";
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.background = "rgba(255,255,255,0.05)";
                                }}
                                onClick={() => router.push(item.href as any)}
                            >
                                <Typography.Text
                                    style={{
                                        color: "rgba(255,255,255,0.85)",
                                        fontSize: 14,
                                        lineHeight: "1.4",
                                        display: "block",
                                    }}
                                >
                                    {item.label}
                                </Typography.Text>
                                <Typography.Text
                                    style={{
                                        color: "rgba(255,255,255,0.45)",
                                        fontSize: 12,
                                        marginTop: 4,
                                        display: "block",
                                    }}
                                >
                                    {Math.floor((Date.now() - item.updatedAt) / (1000 * 60))} minutes ago
                                </Typography.Text>
                            </div>
                        ))}
                    </div>
                </>
            )}
            {activeSideTab === "collections" && (
                <Typography.Text type="secondary" style={{ color: "rgba(255,255,255,0.65)" }}>
                    Collections coming soon
                </Typography.Text>
            )}
        </>
    );

    return (
        <DashboardLayout sidebarContent={sidebarContent}>
            <div style={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column" }}>
                {/* Header with tabs */}
                <div style={{ padding: "16px 24px", borderBottom: "1px solid #f0f0f0", background: "#fff" }}>
                    <Tabs
                        activeKey={activeMode}
                        onChange={setActiveMode}
                        items={[
                            { key: "qa", label: "Q&A" },
                            { key: "docs", label: "Docs" },
                            { key: "rfp", label: "RFP" },
                        ]}
                    />
                </div>

                {/* Chat Area */}
                <div style={{ flex: 1, display: "flex", flexDirection: "column", background: "#fafafa" }}>
                    {messages.length === 0 ? (
                        /* Welcome State */
                        <div
                            style={{
                                flex: 1,
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                justifyContent: "center",
                                padding: "40px 20px",
                            }}
                        >
                            <Typography.Title
                                level={2}
                                style={{
                                    color: "#8c8c8c",
                                    fontWeight: 400,
                                    marginBottom: 40,
                                    fontSize: "28px",
                                    textAlign: "center",
                                }}
                            >
                                Hello {displayName}, what are you looking for?
                            </Typography.Title>

                            {/* Suggestion cards */}
                            <div style={{ width: "100%", maxWidth: 600, marginBottom: 40 }}>
                                <Row gutter={[16, 16]}>
                                    {suggestions.map((s, idx) => (
                                        <Col span={12} key={idx}>
                                            <Card
                                                hoverable
                                                onClick={() => setPrompt(s)}
                                                style={{
                                                    borderRadius: 8,
                                                    border: "1px solid #f0f0f0",
                                                    height: 80,
                                                }}
                                                bodyStyle={{
                                                    display: "flex",
                                                    justifyContent: "space-between",
                                                    alignItems: "center",
                                                    padding: "16px 20px",
                                                    height: "100%",
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        fontSize: 14,
                                                        color: "#595959",
                                                        lineHeight: "1.4",
                                                    }}
                                                >
                                                    {s}
                                                </span>
                                                <ArrowRightOutlined style={{ color: "#bfbfbf", fontSize: 12 }} />
                                            </Card>
                                        </Col>
                                    ))}
                                </Row>
                            </div>
                        </div>
                    ) : (
                        /* Conversation State */
                        <div style={{ flex: 1, overflow: "auto", padding: "24px" }}>
                            <div style={{ maxWidth: 800, margin: "0 auto" }}>
                                {messages.map((message) => (
                                    <div
                                        key={message.id}
                                        style={{
                                            display: "flex",
                                            justifyContent: message.sender === "user" ? "flex-end" : "flex-start",
                                            marginBottom: 16,
                                        }}
                                    >
                                        <div
                                            style={{
                                                maxWidth: "70%",
                                                padding: "12px 16px",
                                                borderRadius: 12,
                                                background: message.sender === "user" ? "#1677ff" : "#fff",
                                                color: message.sender === "user" ? "#fff" : "#333",
                                                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                                                whiteSpace: "pre-wrap",
                                                lineHeight: "1.5",
                                            }}
                                        >
                                            {message.text}
                                        </div>
                                    </div>
                                ))}
                                {isLoading && (
                                    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 16 }}>
                                        <div
                                            style={{
                                                padding: "12px 16px",
                                                borderRadius: 12,
                                                background: "#fff",
                                                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                                            }}
                                        >
                                            <Typography.Text type="secondary">Thinking...</Typography.Text>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Input Area */}
                    <div style={{ padding: "16px 24px", background: "#fff", borderTop: "1px solid #f0f0f0" }}>
                        <div style={{ maxWidth: 800, margin: "0 auto" }}>
                            <div style={{ position: "relative", marginBottom: 8 }}>
                                <Input
                                    size="large"
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Type your question here..."
                                    disabled={isLoading}
                                    style={{
                                        height: 56,
                                        fontSize: 16,
                                        borderRadius: 8,
                                        paddingRight: 100,
                                    }}
                                />
                                <Button
                                    type="primary"
                                    size="large"
                                    onClick={handleSubmit}
                                    loading={isLoading}
                                    disabled={!prompt.trim()}
                                    style={{
                                        position: "absolute",
                                        right: 8,
                                        top: 8,
                                        height: 40,
                                        borderRadius: 6,
                                    }}
                                >
                                    Ask
                                </Button>
                            </div>
                            <Typography.Text
                                type="secondary"
                                style={{
                                    fontSize: 12,
                                    letterSpacing: "0.5px",
                                    textTransform: "uppercase",
                                }}
                            >
                                SHORTCUT PRESS ⌘ TO ASK
                            </Typography.Text>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
