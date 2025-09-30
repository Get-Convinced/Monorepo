"use client";

import React, { useState, useRef, useCallback } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Textarea } from "@/components/ui/textarea";
import { X, Upload, FileText, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { useUploadDocument, useUploadProgress } from "@/hooks/use-ragie-queries";
import { toast } from "sonner";

interface FileUploadModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

interface FileWithMetadata {
    file: File;
    id: string;
    title: string;
    description: string;
    tags: string[];
    status: "pending" | "uploading" | "processing" | "completed" | "failed";
    upload_id?: string;
    progress: number;
    error?: string;
}

const SUGGESTED_TAGS = [
    "financial",
    "quarterly",
    "reports",
    "product",
    "specifications",
    "market",
    "analysis",
    "contracts",
    "legal",
    "compliance",
    "onboarding",
    "training",
    "documentation",
    "policies",
    "procedures",
    "sales",
    "marketing",
    "customer",
    "support",
    "technical",
];

const SUPPORTED_FILE_TYPES = [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".jpg", ".jpeg", ".png", ".gif"];
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

// Simplified progress tracker - no custom events
function SimpleProgressTracker({
    fileData,
    onUpdate,
}: {
    fileData: FileWithMetadata;
    onUpdate: (id: string, updates: Partial<FileWithMetadata>) => void;
}) {
    const { data: progress } = useUploadProgress(
        fileData.upload_id || "",
        !!(fileData.upload_id && (fileData.status === "uploading" || fileData.status === "processing"))
    );

    React.useEffect(() => {
        if (progress && typeof progress === "object") {
            const progressData = progress as any;
            onUpdate(fileData.id, {
                status: progressData.status,
                progress: Math.max(progressData.upload_progress || 0, progressData.processing_progress || 0),
                error: progressData.error_message,
            });
        }
    }, [progress, fileData.id, onUpdate]);

    return null;
}

export function FileUploadModal({ open, onOpenChange }: FileUploadModalProps) {
    const [files, setFiles] = useState<FileWithMetadata[]>([]);
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const uploadMutation = useUploadDocument();

    const validateFile = (file: File): string | null => {
        if (file.size > MAX_FILE_SIZE) return "File too large (max 50MB)";
        const extension = "." + file.name.split(".").pop()?.toLowerCase();
        if (!SUPPORTED_FILE_TYPES.includes(extension)) return "File type not supported";
        return null;
    };

    const addFiles = (newFiles: File[]) => {
        const validFiles: FileWithMetadata[] = [];

        newFiles.forEach((file) => {
            const error = validateFile(file);
            if (error) {
                toast.error(`${file.name}: ${error}`);
                return;
            }

            // Check duplicates
            if (files.some((f) => f.file.name === file.name && f.file.size === file.size)) {
                toast.error(`${file.name} already selected`);
                return;
            }

            validFiles.push({
                file,
                id: Math.random().toString(36).substr(2, 9),
                title: file.name.replace(/\.[^/.]+$/, ""),
                description: "",
                tags: [],
                status: "pending",
                progress: 0,
            });
        });

        setFiles((prev) => [...prev, ...validFiles]);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragOver(false);
        addFiles(Array.from(e.dataTransfer.files));
    };

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        addFiles(Array.from(e.target.files || []));
        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const removeFile = useCallback((fileId: string) => {
        setFiles((prev) => prev.filter((f) => f.id !== fileId));
    }, []);

    const updateFile = useCallback((fileId: string, updates: Partial<FileWithMetadata>) => {
        setFiles((prev) => prev.map((f) => (f.id === fileId ? { ...f, ...updates } : f)));
    }, []);

    const addTag = useCallback((fileId: string, tag: string) => {
        if (!tag.trim()) return;
        setFiles((prev) =>
            prev.map((f) => {
                if (f.id === fileId && !f.tags.includes(tag.trim())) {
                    return { ...f, tags: [...f.tags, tag.trim()] };
                }
                return f;
            })
        );
    }, []);

    const removeTag = useCallback((fileId: string, tagToRemove: string) => {
        setFiles((prev) =>
            prev.map((f) => {
                if (f.id === fileId) {
                    return { ...f, tags: f.tags.filter((tag) => tag !== tagToRemove) };
                }
                return f;
            })
        );
    }, []);

    // Simplified upload - no complex background tracking
    const uploadFiles = async () => {
        const pendingFiles = files.filter((f) => f.status === "pending");
        if (pendingFiles.length === 0) {
            toast.error("No files to upload");
            return;
        }

        for (const fileData of pendingFiles) {
            try {
                updateFile(fileData.id, { status: "uploading", progress: 0 });

                const uploadResponse = await uploadMutation.mutateAsync({
                    file: fileData.file,
                    metadata: {
                        title: fileData.title || undefined,
                        description: fileData.description || undefined,
                        tags: fileData.tags.length > 0 ? fileData.tags : undefined,
                    },
                });

                updateFile(fileData.id, {
                    status: "uploading",
                    upload_id: uploadResponse.upload_id,
                    progress: 25,
                });
            } catch (error: any) {
                const errorMessage = error.response?.data?.error?.message || "Upload failed";
                updateFile(fileData.id, {
                    status: "failed",
                    progress: 0,
                    error: errorMessage,
                });
            }
        }
    };

    const handleClose = () => {
        const hasUploading = files.some((f) => f.status === "uploading" || f.status === "processing");
        if (hasUploading) {
            toast.error("Please wait for uploads to complete");
            return;
        }
        onOpenChange(false);
        setFiles([]);
    };

    return (
        <Dialog open={open} onOpenChange={handleClose}>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Upload Files</DialogTitle>
                </DialogHeader>

                <div className="space-y-6">
                    {/* Drop Zone */}
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                            isDragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25"
                        }`}
                        onDrop={handleDrop}
                        onDragOver={(e) => {
                            e.preventDefault();
                            setIsDragOver(true);
                        }}
                        onDragLeave={(e) => {
                            e.preventDefault();
                            setIsDragOver(false);
                        }}
                    >
                        <Upload className="mx-auto mb-4 w-12 h-12 text-muted-foreground" />
                        <h3 className="mb-2 text-lg font-semibold">{isDragOver ? "Drop files here" : "Drag files here"}</h3>
                        <p className="mb-4 text-sm text-muted-foreground">PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, Images (Max 50MB each)</p>
                        <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
                            <Upload className="mr-2 w-4 h-4" />
                            Choose Files
                        </Button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            accept={SUPPORTED_FILE_TYPES.join(",")}
                            onChange={handleFileSelect}
                            className="hidden"
                        />
                    </div>

                    {/* Files List */}
                    {files.length > 0 && (
                        <div className="space-y-4">
                            <h4 className="font-semibold">Selected Files ({files.length})</h4>

                            {files.map((fileData) => (
                                <div key={fileData.id} className="border rounded-lg p-4 space-y-4">
                                    {/* Progress Tracker */}
                                    {fileData.upload_id && <SimpleProgressTracker fileData={fileData} onUpdate={updateFile} />}

                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center space-x-3">
                                            <FileText className="w-8 h-8 text-primary" />
                                            <div>
                                                <div className="flex items-center space-x-2">
                                                    <p className="font-medium">{fileData.file.name}</p>
                                                    {fileData.status === "completed" && <CheckCircle className="w-5 h-5 text-green-500" />}
                                                    {fileData.status === "failed" && <AlertCircle className="w-5 h-5 text-red-500" />}
                                                    {(fileData.status === "uploading" || fileData.status === "processing") && (
                                                        <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
                                                    )}
                                                </div>
                                                <p className="text-sm text-muted-foreground">
                                                    {(fileData.file.size / 1024 / 1024).toFixed(2)} MB
                                                </p>
                                            </div>
                                        </div>

                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => removeFile(fileData.id)}
                                            disabled={fileData.status === "uploading" || fileData.status === "processing"}
                                        >
                                            <X className="w-4 h-4" />
                                        </Button>
                                    </div>

                                    {/* Progress Bar */}
                                    {(fileData.status === "uploading" || fileData.status === "processing") && (
                                        <Progress value={fileData.progress} className="w-full" />
                                    )}

                                    {/* Error Message */}
                                    {fileData.status === "failed" && fileData.error && (
                                        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{fileData.error}</div>
                                    )}

                                    {/* Metadata Fields - Only for pending files */}
                                    {fileData.status === "pending" && (
                                        <>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div>
                                                    <Label>Title (Optional)</Label>
                                                    <Input
                                                        value={fileData.title}
                                                        onChange={(e) => updateFile(fileData.id, { title: e.target.value })}
                                                        placeholder="Document title"
                                                    />
                                                </div>

                                                <div>
                                                    <Label>Description (Optional)</Label>
                                                    <Textarea
                                                        value={fileData.description}
                                                        onChange={(e) => updateFile(fileData.id, { description: e.target.value })}
                                                        placeholder="Brief description"
                                                        rows={2}
                                                    />
                                                </div>
                                            </div>

                                            {/* Tags */}
                                            <div>
                                                <Label>Tags (Optional)</Label>
                                                <div className="flex flex-wrap gap-1 mb-2">
                                                    {fileData.tags.map((tag) => (
                                                        <Badge key={tag} variant="secondary" className="text-xs">
                                                            {tag}
                                                            <button
                                                                onClick={() => removeTag(fileData.id, tag)}
                                                                className="ml-1 hover:text-red-500"
                                                            >
                                                                <X className="w-3 h-3" />
                                                            </button>
                                                        </Badge>
                                                    ))}
                                                </div>

                                                <div className="flex flex-wrap gap-1">
                                                    {SUGGESTED_TAGS.slice(0, 10).map((tag) => (
                                                        <Button
                                                            key={tag}
                                                            variant="outline"
                                                            size="sm"
                                                            className="text-xs h-6"
                                                            onClick={() => addTag(fileData.id, tag)}
                                                            disabled={fileData.tags.includes(tag)}
                                                        >
                                                            {tag}
                                                        </Button>
                                                    ))}
                                                </div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={handleClose}>
                            Cancel
                        </Button>
                        <Button onClick={uploadFiles} disabled={files.length === 0 || files.every((f) => f.status !== "pending")}>
                            Upload {files.filter((f) => f.status === "pending").length} Files
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
