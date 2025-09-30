"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { WebsitesTab } from "./websites-tab";
import { FilesTab } from "./files-tab";
import { IntegrationsTab } from "./integrations-tab";
import { AnalyticsDashboard } from "./analytics-dashboard";
import { Globe, FileText, Database, BarChart3 } from "lucide-react";

// Simplified - no complex props or legacy compatibility
interface KnowledgeSourcesProps {
    integrations?: any[]; // Keep minimal for integrations tab
}

export function KnowledgeSources({ integrations = [] }: KnowledgeSourcesProps) {
    return (
        <Tabs defaultValue="files" className="w-full">
            <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="websites" className="flex gap-2 items-center">
                    <Globe className="w-4 h-4" />
                    Websites
                </TabsTrigger>
                <TabsTrigger value="files" className="flex gap-2 items-center">
                    <FileText className="w-4 h-4" />
                    Files
                </TabsTrigger>
                <TabsTrigger value="integrations" className="flex gap-2 items-center">
                    <Database className="w-4 h-4" />
                    Integrations
                </TabsTrigger>
                <TabsTrigger value="analytics" className="flex gap-2 items-center">
                    <BarChart3 className="w-4 h-4" />
                    Analytics
                </TabsTrigger>
            </TabsList>

            <TabsContent value="websites" className="space-y-4">
                <WebsitesTab />
            </TabsContent>

            <TabsContent value="files" className="space-y-4">
                <FilesTab />
            </TabsContent>

            <TabsContent value="integrations" className="space-y-4">
                <IntegrationsTab integrations={integrations} />
            </TabsContent>

            <TabsContent value="analytics" className="space-y-4">
                <AnalyticsDashboard />
            </TabsContent>
        </Tabs>
    );
}
