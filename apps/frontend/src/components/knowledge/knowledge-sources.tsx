"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { WebsitesTab } from "./websites-tab";
import { FilesTab } from "./files-tab";
import { IntegrationsTab } from "./integrations-tab";
import { Globe, FileText, Database } from "lucide-react";

interface Website {
    id: number;
    url: string;
    title: string;
    status: "ready" | "processing" | "failed";
    addedAt: string;
}

interface File {
    id: number;
    name: string;
    type: string;
    size: string;
    status: "ready" | "processing" | "failed";
    tags: string[];
    uploadedAt: string;
}

interface Integration {
    name: string;
    description: string;
    status: "connected" | "available";
    files: number;
    icon: string;
}

interface KnowledgeSourcesProps {
    websites: Website[];
    files: File[];
    integrations: Integration[];
    onUpdateFileTags: (fileId: number, newTags: string[]) => void;
}

export function KnowledgeSources({ websites, files, integrations, onUpdateFileTags }: KnowledgeSourcesProps) {
    return (
        <Tabs defaultValue="websites" className="w-full">
            <TabsList className="grid grid-cols-3 w-full">
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
            </TabsList>

            <TabsContent value="websites" className="space-y-4">
                <WebsitesTab websites={websites} />
            </TabsContent>

            <TabsContent value="files" className="space-y-4">
                <FilesTab files={files} onUpdateFileTags={onUpdateFileTags} />
            </TabsContent>

            <TabsContent value="integrations" className="space-y-4">
                <IntegrationsTab integrations={integrations} />
            </TabsContent>
        </Tabs>
    );
}
