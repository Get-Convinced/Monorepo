"use client";
import React, { useMemo, useState } from "react";
import { Layout, Typography } from "antd";
import { HomeOutlined, FolderOutlined, DatabaseOutlined, SettingOutlined, MenuUnfoldOutlined, MenuFoldOutlined } from "@ant-design/icons";
import { usePathname, useRouter } from "next/navigation";

const { Header, Sider, Content } = Layout;

interface DashboardLayoutProps {
    children: React.ReactNode;
    sidebarContent?: React.ReactNode;
}

export default function DashboardLayout({ children, sidebarContent }: DashboardLayoutProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [secondarySidebarCollapsed, setSecondarySidebarCollapsed] = useState<boolean>(false);

    const selectedKeys = useMemo<string[]>(() => {
        if (pathname?.startsWith("/knowledge")) return ["knowledge"];
        if (pathname?.startsWith("/chat")) return ["chat"];
        return [];
    }, [pathname]);

    const onMenuClick = (key: string) => {
        if (key === "chat") router.push("/chat");
        if (key === "knowledge") router.push("/knowledge");
    };

    return (
        <Layout style={{ minHeight: "100vh" }}>
            {/* Primary Sidebar - Icons only */}
            <Sider width={60} style={{ background: "#f5f5f5", borderRight: "1px solid #e8e8e8" }}>
                <div style={{ padding: "16px 0", display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
                    <div style={{ padding: "8px 12px", borderRadius: 8, background: "#1677ff" }}>
                        <HomeOutlined style={{ fontSize: 20, color: "#fff" }} />
                    </div>
                    <div
                        onClick={() => onMenuClick("chat")}
                        style={{
                            padding: "8px 12px",
                            borderRadius: 8,
                            cursor: "pointer",
                            background: selectedKeys.includes("chat") ? "#1677ff" : "transparent",
                            transition: "all 0.2s",
                        }}
                    >
                        <HomeOutlined style={{ fontSize: 20, color: selectedKeys.includes("chat") ? "#fff" : "#666" }} />
                    </div>
                    <div style={{ padding: "8px 12px", borderRadius: 8, cursor: "pointer" }}>
                        <FolderOutlined style={{ fontSize: 20, color: "#666" }} />
                    </div>
                    <div
                        onClick={() => onMenuClick("knowledge")}
                        style={{
                            padding: "8px 12px",
                            borderRadius: 8,
                            cursor: "pointer",
                            background: selectedKeys.includes("knowledge") ? "#1677ff" : "transparent",
                            transition: "all 0.2s",
                        }}
                    >
                        <DatabaseOutlined style={{ fontSize: 20, color: selectedKeys.includes("knowledge") ? "#fff" : "#666" }} />
                    </div>
                    <div style={{ padding: "8px 12px", borderRadius: 8, cursor: "pointer" }}>
                        <SettingOutlined style={{ fontSize: 20, color: "#666" }} />
                    </div>
                </div>
            </Sider>

            {/* Secondary Sidebar - Content */}
            {sidebarContent && (
                <Sider
                    width={300}
                    collapsible
                    collapsed={secondarySidebarCollapsed}
                    onCollapse={setSecondarySidebarCollapsed}
                    trigger={null}
                    style={{ background: "#001529" }}
                >
                    <div style={{ padding: 16 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                            <Typography.Title level={4} style={{ color: "#fff", margin: 0 }}>
                                Home
                            </Typography.Title>
                            <div
                                onClick={() => setSecondarySidebarCollapsed(!secondarySidebarCollapsed)}
                                style={{ cursor: "pointer", color: "rgba(255,255,255,0.65)" }}
                            >
                                {secondarySidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                            </div>
                        </div>
                        {!secondarySidebarCollapsed && sidebarContent}
                    </div>
                </Sider>
            )}

            <Layout>
                <Header style={{ background: "#fff", display: "flex", alignItems: "center", gap: 8, paddingLeft: 16 }}>
                    <Typography.Text>Internal Dashboard</Typography.Text>
                </Header>
                <Content style={{ padding: 16 }}>{children}</Content>
            </Layout>
        </Layout>
    );
}
