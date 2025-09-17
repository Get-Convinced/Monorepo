"use client";
import { useEffect, useState } from "react";
import { Alert, Button, Card, Flex, Typography } from "antd";

export default function GetStartedPage() {
    const [status, setStatus] = useState<string>("checking...");
    const [error, setError] = useState<string | null>(null);

    async function checkBackend() {
        setError(null);
        setStatus("checking...");
        try {
            const res = await fetch(`/api/health`, { cache: "no-store" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            setStatus(`backend: ${data.status}`);
        } catch (e: any) {
            setError(e.message || "Request failed");
            setStatus("unavailable");
        }
    }

    useEffect(() => {
        checkBackend();
    }, []);

    return (
        <Flex vertical gap={16} align="center" style={{ padding: 24 }}>
            <Typography.Title level={2}>Get Started</Typography.Title>
            <Card style={{ maxWidth: 640, width: "100%" }}>
                <Typography.Paragraph>API Base: {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8082"}</Typography.Paragraph>
                {error ? <Alert type="error" message={error} /> : <Alert type="success" message={status} />}
                <Button onClick={checkBackend} style={{ marginTop: 12 }}>
                    Re-check
                </Button>
            </Card>
        </Flex>
    );
}
