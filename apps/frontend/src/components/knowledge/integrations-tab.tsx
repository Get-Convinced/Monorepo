"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Database } from "lucide-react";

interface Integration {
    name: string;
    description: string;
    status: "connected" | "available";
    files: number;
    icon: string;
}

interface IntegrationsTabProps {
    integrations: Integration[];
}

export function IntegrationsTab({ integrations }: IntegrationsTabProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex gap-2 items-center">
                    <Database className="w-5 h-5" />
                    Integrations
                </CardTitle>
                <CardDescription>Connect external services to sync data</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    {integrations.map((integration, index) => (
                        <div key={index} className="p-4 rounded-lg border transition-shadow hover:shadow-md">
                            <div className="flex justify-between items-center mb-3">
                                <div className="flex gap-3 items-center">
                                    <span className="text-2xl">{integration.icon}</span>
                                    <div>
                                        <h3 className="font-semibold">{integration.name}</h3>
                                        <p className="text-sm text-muted-foreground">{integration.files} files synced</p>
                                    </div>
                                </div>
                                <Badge variant={integration.status === "connected" ? "default" : "secondary"}>{integration.status}</Badge>
                            </div>
                            <p className="mb-3 text-sm text-muted-foreground">{integration.description}</p>
                            <Button variant={integration.status === "connected" ? "outline" : "default"} className="w-full">
                                {integration.status === "connected" ? "Manage" : "Connect"}
                            </Button>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
