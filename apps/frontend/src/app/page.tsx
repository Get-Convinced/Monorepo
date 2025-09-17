"use client";
import { Button, Flex, Space, Typography } from "antd";
import { useRouter } from "next/navigation";
import { useAuth, useLoginWithRedirect, useLoginActions } from "@frontegg/react-hooks";

export default function Page() {
    const router = useRouter();
    const { user, isAuthenticated, isLoading } = useAuth();
    const loginWithRedirect = useLoginWithRedirect();
    const { logout } = useLoginActions();
    return (
        <Flex vertical align="center" justify="center" style={{ minHeight: "100vh" }}>
            <Typography.Title>AI Knowledge Agent</Typography.Title>
            <Typography.Paragraph>Frontend is up. Backend and DP services coming next.</Typography.Paragraph>
            <Space>
                <Button type="primary" onClick={() => router.push("/get-started")}>
                    Get Started
                </Button>
                {isLoading ? null : isAuthenticated ? (
                    <>
                        <Typography.Text>Signed in as {user?.email}</Typography.Text>
                        <Button onClick={() => logout()}>Logout</Button>
                    </>
                ) : (
                    <Button onClick={() => loginWithRedirect()}>Login</Button>
                )}
            </Space>
        </Flex>
    );
}
