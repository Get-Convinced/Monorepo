import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { KnowledgeSourcesClient } from "@/components/knowledge/knowledge-sources-client";
import { getAppUserSession } from "@frontegg/nextjs/app";
import { redirect } from "next/navigation";

export default async function KnowledgePage() {
  const userSession = await getAppUserSession();

  if (!userSession) {
    redirect("/account/login");
  }

  const websites = [
    {
      id: 1,
      url: "https://docs.example.com/api",
      title: "API Documentation",
      status: "ready" as const,
      addedAt: "2024-01-15",
    },
    {
      id: 2,
      url: "https://blog.example.com/updates",
      title: "Product Updates",
      status: "processing" as const,
      addedAt: "2024-01-16",
    },
    {
      id: 3,
      url: "https://github.com/company/repo",
      title: "GitHub Repository",
      status: "failed" as const,
      addedAt: "2024-01-17",
    },
  ];

  const files = [
    {
      id: 1,
      name: "Q4_Report.pdf",
      type: "PDF",
      size: "2.4 MB",
      status: "ready" as const,
      tags: ["financial", "quarterly", "reports"],
      uploadedAt: "2024-01-15",
    },
    {
      id: 2,
      name: "Product_Specs.docx",
      type: "DOCX",
      size: "1.8 MB",
      status: "processing" as const,
      tags: ["product", "specifications"],
      uploadedAt: "2024-01-16",
    },
    {
      id: 3,
      name: "Market_Analysis.xlsx",
      type: "XLSX",
      size: "3.2 MB",
      status: "failed" as const,
      tags: ["market", "analysis"],
      uploadedAt: "2024-01-17",
    },
  ];

  const integrations = [
    {
      name: "Google Drive",
      description: "Access and sync files from your Google Drive",
      status: "connected" as const,
      files: 24,
      icon: "📁",
    },
    {
      name: "Slack",
      description: "Import messages and files from Slack channels",
      status: "available" as const,
      files: 0,
      icon: "💬",
    },
    {
      name: "Notion",
      description: "Sync pages and databases from Notion workspace",
      status: "connected" as const,
      files: 12,
      icon: "📝",
    },
    {
      name: "Confluence",
      description: "Import documentation from Confluence spaces",
      status: "available" as const,
      files: 0,
      icon: "🏢",
    },
  ];

  return (
    <SidebarLayout>
      <div className="p-6 space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Knowledge Sources</h1>
            <p className="text-muted-foreground">
              Manage your files, websites, and integrations
            </p>
          </div>
        </div>

        <KnowledgeSourcesClient
          websites={websites}
          files={files}
          integrations={integrations}
        />
      </div>
    </SidebarLayout>
  );
}
