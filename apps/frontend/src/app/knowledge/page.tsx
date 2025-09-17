"use client";
import React from "react";
import DashboardLayout from "../../components/DashboardLayout";
import { Button, Card, Input, Segmented, Space, Table, Tag } from "antd";

interface FileRow {
    key: string;
    name: string;
    source: string;
    status: "processing" | "ready" | "failed";
    updatedAt: string;
}

const data: FileRow[] = [{ key: "1", name: "Product Doc.pdf", source: "Upload", status: "ready", updatedAt: "2025-09-13" }];

export default function KnowledgePage() {
    return (
        <DashboardLayout sidebarContent={null}>
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
                <Card>
                    <Space wrap>
                        <Input.Search placeholder="Search files" style={{ width: 260 }} />
                        <Segmented options={["All", "Upload", "URL", "Integration"]} />
                        <Segmented options={["Any", "ready", "processing", "failed"]} />
                        <Button type="primary">Upload</Button>
                    </Space>
                </Card>
                <Table
                    dataSource={data}
                    columns={[
                        { title: "Name", dataIndex: "name" },
                        { title: "Source", dataIndex: "source" },
                        {
                            title: "Status",
                            dataIndex: "status",
                            render: (s: FileRow["status"]) => (
                                <Tag color={s === "ready" ? "green" : s === "processing" ? "gold" : "red"}>{s}</Tag>
                            ),
                        },
                        { title: "Updated", dataIndex: "updatedAt", sorter: true },
                    ]}
                />
            </Space>
        </DashboardLayout>
    );
}
