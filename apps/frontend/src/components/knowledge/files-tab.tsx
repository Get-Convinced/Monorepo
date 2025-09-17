"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/shared/status-badge";
import { StatusIcon } from "@/components/shared/status-icon";
import { TagManager } from "./tag-manager";
import { Upload, FileText, Tag } from "lucide-react";

interface File {
    id: number;
    name: string;
    type: string;
    size: string;
    status: "ready" | "processing" | "failed";
    tags: string[];
    uploadedAt: string;
}

interface FilesTabProps {
    files: File[];
    onUpdateFileTags: (fileId: number, newTags: string[]) => void;
}

export function FilesTab({ files, onUpdateFileTags }: FilesTabProps) {
    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle className="flex gap-2 items-center">
                            <FileText className="w-5 h-5" />
                            Files
                        </CardTitle>
                        <CardDescription>Upload and manage documents with tags</CardDescription>
                    </div>
                    <Button>
                        <Upload className="mr-2 w-4 h-4" />
                        Upload Files
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                {/* Upload Area */}
                <div className="p-8 text-center rounded-lg border-2 border-dashed border-muted-foreground/25">
                    <Upload className="mx-auto mb-4 w-12 h-12 text-muted-foreground" />
                    <h3 className="mb-2 text-lg font-semibold">Drag files here to upload</h3>
                    <p className="mb-4 text-sm text-muted-foreground">Supports: PDF, DOC, DOCX, TXT, XLS, PPT, Images</p>
                    <Button>
                        <Upload className="mr-2 w-4 h-4" />
                        Choose Files
                    </Button>
                </div>

                {/* Files List */}
                <div className="space-y-3">
                    {files.map((file) => (
                        <div key={file.id} className="flex justify-between items-center p-4 rounded-lg border">
                            <div className="flex gap-3 items-center">
                                <StatusIcon status={file.status} />
                                <div>
                                    <p className="font-medium">{file.name}</p>
                                    <p className="text-sm text-muted-foreground">
                                        {file.type} • {file.size} • Uploaded {file.uploadedAt}
                                    </p>
                                    <div className="flex gap-1 items-center mt-1">
                                        <Tag className="w-3 h-3 text-muted-foreground" />
                                        <div className="flex flex-wrap gap-1">
                                            {file.tags.map((tag, index) => (
                                                <Badge key={index} variant="outline" className="text-xs">
                                                    {tag}
                                                </Badge>
                                            ))}
                                            <TagManager
                                                fileId={file.id}
                                                currentTags={file.tags}
                                                onTagsUpdate={(newTags) => onUpdateFileTags(file.id, newTags)}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="flex gap-2 items-center">
                                <StatusBadge status={file.status} />
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
