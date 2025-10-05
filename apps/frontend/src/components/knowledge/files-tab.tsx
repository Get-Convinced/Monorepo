"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { StatusBadge } from "@/components/shared/status-badge";
import { StatusIcon } from "@/components/shared/status-icon";
import { FileUploadModal } from "./file-upload-modal";
import { Upload, FileText, Tag, Search, Download, Trash2, Filter, RefreshCw } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    useRagieDocuments,
    useDeleteDocument,
    useBulkDelete,
    useDownloadDocument,
    useUpdateMetadata,
    type RagieDocument,
} from "@/hooks/use-ragie-queries";
import { useAuth } from "@frontegg/nextjs";
import { formatDistanceToNow } from "date-fns";

export function FilesTab() {
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

    // Single source of truth - React Query only
    const { data: documentsData, isLoading, error, refetch } = useRagieDocuments();
    const deleteDocument = useDeleteDocument();
    const bulkDelete = useBulkDelete();
    const downloadDocument = useDownloadDocument();
    const updateMetadata = useUpdateMetadata();

    const documents = (documentsData as RagieDocument[]) || [];

    // Simple filtering - no complex useMemo
    const filteredDocuments = documents.filter((doc: RagieDocument) => {
        if (statusFilter !== "all" && doc.status !== statusFilter) return false;
        if (searchQuery) {
            const query = searchQuery.toLowerCase();
            return (
                doc.name.toLowerCase().includes(query) ||
                doc.metadata?.title?.toLowerCase().includes(query) ||
                doc.metadata?.tags?.some((tag) => tag.toLowerCase().includes(query))
            );
        }
        return true;
    });

    // Simplified handlers - no complex callbacks
    const handleSelectAll = (checked: boolean) => {
        setSelectedFiles(checked ? new Set(filteredDocuments.map((doc) => doc.id)) : new Set());
    };

    const handleSelectFile = (fileId: string, checked: boolean) => {
        const newSet = new Set(selectedFiles);
        checked ? newSet.add(fileId) : newSet.delete(fileId);
        setSelectedFiles(newSet);
    };

    const handleDelete = (documentId: string) => {
        if (confirm("Are you sure you want to delete this document?")) {
            deleteDocument.mutate(documentId);
            setSelectedFiles((prev) => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
            });
        }
    };

    const handleBulkDelete = () => {
        const selectedCount = selectedFiles.size;
        if (selectedCount === 0) return;

        if (confirm(`Delete ${selectedCount} selected documents?`)) {
            bulkDelete.mutate(Array.from(selectedFiles));
            setSelectedFiles(new Set());
        }
    };

    const handleDownload = (doc: RagieDocument) => {
        downloadDocument.mutate({ documentId: doc.id, filename: doc.name });
    };

    const handleUpdateTags = (documentId: string, newTags: string[]) => {
        updateMetadata.mutate({ documentId, metadata: { tags: newTags } });
    };

    const formatDate = (dateString: string): string => {
        try {
            return formatDistanceToNow(new Date(dateString), { addSuffix: true });
        } catch {
            return dateString;
        }
    };

    if (error) {
        return (
            <Card>
                <CardContent className="p-6 text-center">
                    <p className="mb-4 text-red-600">Failed to load documents</p>
                    <Button variant="outline" onClick={() => refetch()}>
                        <RefreshCw className="mr-2 w-4 h-4" />
                        Retry
                    </Button>
                </CardContent>
            </Card>
        );
    }

    return (
        <>
            <Card>
                <CardHeader>
                    <div className="flex justify-between items-center">
                        <div>
                            <CardTitle className="flex gap-2 items-center">
                                <FileText className="w-5 h-5" />
                                Files ({filteredDocuments.length})
                            </CardTitle>
                            <CardDescription>Upload and manage documents</CardDescription>
                        </div>
                        <div className="flex gap-2">
                            <Button onClick={() => setUploadModalOpen(true)}>
                                <Upload className="mr-2 w-4 h-4" />
                                Upload Files
                            </Button>
                        </div>
                    </div>
                </CardHeader>

                <CardContent className="space-y-4">
                    {/* Simple Controls */}
                    <div className="flex gap-4">
                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-1/2 w-4 h-4 transform -translate-y-1/2 text-muted-foreground" />
                            <Input
                                placeholder="Search files..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>

                        <Select value={statusFilter} onValueChange={(value: string) => setStatusFilter(value)}>
                            <SelectTrigger className="w-[180px]">
                                <Filter className="mr-2 w-4 h-4" />
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="ready">Ready</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                                <SelectItem value="partitioning">Partitioning</SelectItem>
                                <SelectItem value="partitioned">Partitioned</SelectItem>
                                <SelectItem value="refined">Refined</SelectItem>
                                <SelectItem value="chunked">Chunked</SelectItem>
                                <SelectItem value="indexed">Indexed</SelectItem>
                                <SelectItem value="summary_indexed">Summary Indexed</SelectItem>
                                <SelectItem value="keyword_indexed">Keyword Indexed</SelectItem>
                                <SelectItem value="failed">Failed</SelectItem>
                            </SelectContent>
                        </Select>

                        <Button variant="outline" onClick={() => refetch()} disabled={isLoading}>
                            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
                            Refresh
                        </Button>
                    </div>

                    {/* Bulk Actions */}
                    {selectedFiles.size > 0 && (
                        <div className="flex justify-between items-center p-3 rounded-lg bg-muted">
                            <span className="text-sm font-medium">{selectedFiles.size} selected</span>
                            <div className="flex gap-2">
                                <Button variant="destructive" size="sm" onClick={handleBulkDelete} disabled={bulkDelete.isPending}>
                                    <Trash2 className="mr-2 w-4 h-4" />
                                    Delete
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => setSelectedFiles(new Set())}>
                                    Clear
                                </Button>
                            </div>
                        </div>
                    )}

                    {/* Files List */}
                    {isLoading ? (
                        <div className="space-y-3">
                            {Array.from({ length: 3 }).map((_, i) => (
                                <div key={i} className="p-4 bg-gray-50 rounded-lg animate-pulse">
                                    <div className="mb-2 w-3/4 h-4 bg-gray-300 rounded"></div>
                                    <div className="w-1/2 h-3 bg-gray-300 rounded"></div>
                                </div>
                            ))}
                        </div>
                    ) : filteredDocuments.length === 0 ? (
                        <div className="py-8 text-center">
                            <FileText className="mx-auto mb-4 w-12 h-12 text-muted-foreground" />
                            <h3 className="mb-2 text-lg font-semibold">No files found</h3>
                            <p className="mb-4 text-muted-foreground">
                                {searchQuery || statusFilter !== "all"
                                    ? "Try adjusting your search or filter"
                                    : "Upload your first document to get started"}
                            </p>
                            {!searchQuery && statusFilter === "all" && (
                                <Button onClick={() => setUploadModalOpen(true)}>
                                    <Upload className="mr-2 w-4 h-4" />
                                    Upload Files
                                </Button>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {/* Select All */}
                            <div className="flex items-center pb-2 space-x-2 border-b">
                                <Checkbox checked={selectedFiles.size === filteredDocuments.length} onCheckedChange={handleSelectAll} />
                                <span className="text-sm text-muted-foreground">Select all ({filteredDocuments.length})</span>
                            </div>

                            {/* Document List */}
                            {filteredDocuments.map((doc: RagieDocument) => (
                                <div key={doc.id} className="flex items-center p-4 space-x-3 rounded-lg border">
                                    <Checkbox
                                        checked={selectedFiles.has(doc.id)}
                                        onCheckedChange={(checked) => handleSelectFile(doc.id, checked as boolean)}
                                    />

                                    <StatusIcon status={doc.status} />

                                    <div className="flex-1 min-w-0">
                                        <div className="flex justify-between items-center">
                                            <div className="flex-1 min-w-0">
                                                <p className="font-medium truncate">{doc.name}</p>
                                                <p className="text-sm text-muted-foreground">
                                                    {doc.metadata?.title && `${doc.metadata.title} • `}
                                                    Updated {formatDate(doc.updated_at)}
                                                </p>
                                                {doc.metadata?.tags && doc.metadata.tags.length > 0 && (
                                                    <div className="flex gap-1 items-center mt-1">
                                                        <Tag className="w-3 h-3 text-muted-foreground" />
                                                        <div className="flex flex-wrap gap-1">
                                                            {doc.metadata.tags.map((tag, index) => (
                                                                <Badge key={index} variant="outline" className="text-xs">
                                                                    {tag}
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex items-center ml-4">
                                                <StatusBadge status={doc.status} />
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDownload(doc)}
                                            disabled={downloadDocument.isPending}
                                        >
                                            <Download className="w-4 h-4" />
                                        </Button>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDelete(doc.id)}
                                            disabled={deleteDocument.isPending}
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            <FileUploadModal open={uploadModalOpen} onOpenChange={setUploadModalOpen} />
        </>
    );
}
