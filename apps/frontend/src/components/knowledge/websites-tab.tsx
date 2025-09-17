"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StatusBadge } from "@/components/shared/status-badge";
import { StatusIcon } from "@/components/shared/status-icon";
import { Globe, Plus, ExternalLink } from "lucide-react";

interface Website {
    id: number;
    url: string;
    title: string;
    status: "ready" | "processing" | "failed";
    addedAt: string;
}

interface WebsitesTabProps {
    websites: Website[];
}

export function WebsitesTab({ websites }: WebsitesTabProps) {
    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="flex gap-2 items-center">
                            <Globe className="w-5 h-5" />
                            Websites
                        </CardTitle>
                        <CardDescription>Add and manage web URLs for processing</CardDescription>
                    </div>
                    <Button>
                        <Plus className="mr-2 w-4 h-4" />
                        Add URL
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Add URL Form */}
                <div className="p-4 rounded-lg border-2 border-dashed border-muted-foreground/25">
                    <div className="space-y-3">
                        <Label htmlFor="url">Website URL</Label>
                        <div className="flex gap-2">
                            <Input id="url" placeholder="https://example.com/documentation" className="flex-1" />
                            <Button>Add</Button>
                        </div>
                    </div>
                </div>

                {/* Websites List */}
                <div className="space-y-3">
                    {websites.map((website) => (
                        <div key={website.id} className="flex justify-between items-center p-4 rounded-lg border">
                            <div className="flex gap-3 items-center">
                                <StatusIcon status={website.status} />
                                <div>
                                    <p className="font-medium">{website.title}</p>
                                    <div className="flex gap-2 items-center">
                                        <p className="text-sm text-muted-foreground">{website.url}</p>
                                        <ExternalLink className="w-3 h-3 text-muted-foreground" />
                                    </div>
                                    <p className="text-xs text-muted-foreground">Added {website.addedAt}</p>
                                </div>
                            </div>
                            <div className="flex gap-2 items-center">
                                <StatusBadge status={website.status} />
                                <Button variant="outline" size="sm">
                                    Remove
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
