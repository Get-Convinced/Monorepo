import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { KnowledgeSources } from "@/components/knowledge/knowledge-sources";
import { getAppUserSession } from "@frontegg/nextjs/app";
import { redirect } from "next/navigation";

export default async function KnowledgePage() {
    const userSession = await getAppUserSession();

    if (!userSession) {
        redirect("/account/login");
    }

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
                        <p className="text-muted-foreground">Manage your files, websites, and integrations</p>
                    </div>
                </div>

                <KnowledgeSources integrations={integrations} />
            </div>
        </SidebarLayout>
    );
}
