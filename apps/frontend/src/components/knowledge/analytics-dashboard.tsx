"use client";

import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText, TrendingUp, BarChart3, PieChart, Calendar, AlertCircle } from "lucide-react";
import { useDocumentAnalytics, type DocumentAnalytics } from "@/hooks/use-ragie-queries";

interface AnalyticsDashboardProps {
    className?: string;
}

export function AnalyticsDashboard({ className }: AnalyticsDashboardProps) {
    const { data: analytics, isLoading, error } = useDocumentAnalytics();

    if (isLoading) {
        return <AnalyticsLoadingSkeleton className={className} />;
    }

    if (error) {
        return (
            <div className={`p-6 ${className}`}>
                <Card>
                    <CardContent className="flex items-center justify-center p-6">
                        <div className="text-center">
                            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                            <p className="text-sm text-muted-foreground">Failed to load analytics data</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (!analytics) {
        return null;
    }

    // Safely destructure with defaults
    const analyticsData = analytics as DocumentAnalytics;
    const total_documents = analyticsData.total_documents || 0;
    const by_file_type = analyticsData.by_file_type || {};
    const by_status = analyticsData.by_status || {};
    const upload_trends = analyticsData.upload_trends || {};

    // Calculate percentages for file types
    const fileTypeEntries = Object.entries(by_file_type).sort(([, a], [, b]) => (b as any).count - (a as any).count);

    // Calculate percentages for status
    const statusEntries = Object.entries(by_status).sort(([, a], [, b]) => (b as number) - (a as number));

    const getStatusColor = (status: string) => {
        switch (status) {
            case "ready":
                return "bg-green-500";
            case "processing":
                return "bg-blue-500";
            case "failed":
                return "bg-red-500";
            default:
                return "bg-gray-500";
        }
    };

    const getStatusVariant = (status: string) => {
        switch (status) {
            case "ready":
                return "default";
            case "processing":
                return "secondary";
            case "failed":
                return "destructive";
            default:
                return "outline";
        }
    };

    return (
        <div className={`space-y-6 ${className}`}>
            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
                        <FileText className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{total_documents}</div>
                        <p className="text-xs text-muted-foreground">Documents in your knowledge base</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">This Week</CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{upload_trends.last_7_days}</div>
                        <p className="text-xs text-muted-foreground">Documents uploaded</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">This Month</CardTitle>
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{upload_trends.last_30_days}</div>
                        <p className="text-xs text-muted-foreground">Documents uploaded</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Ready</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{by_status.ready || 0}</div>
                        <p className="text-xs text-muted-foreground">Documents ready for search</p>
                    </CardContent>
                </Card>
            </div>

            {/* File Types and Status */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* File Types */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PieChart className="h-5 w-5" />
                            File Types
                        </CardTitle>
                        <CardDescription>Distribution of document types</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {fileTypeEntries.length > 0 ? (
                            fileTypeEntries.map(([fileType, data]) => {
                                const count = (data as any).count;
                                const percentage = total_documents > 0 ? (count / total_documents) * 100 : 0;

                                return (
                                    <div key={fileType} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Badge variant="outline" className="text-xs">
                                                    {fileType.toUpperCase()}
                                                </Badge>
                                                <span className="text-sm font-medium">{count}</span>
                                            </div>
                                            <span className="text-xs text-muted-foreground">{percentage.toFixed(1)}%</span>
                                        </div>
                                        <Progress value={percentage} className="h-2" />
                                    </div>
                                );
                            })
                        ) : (
                            <p className="text-sm text-muted-foreground text-center py-4">No documents uploaded yet</p>
                        )}
                    </CardContent>
                </Card>

                {/* Processing Status */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <BarChart3 className="h-5 w-5" />
                            Processing Status
                        </CardTitle>
                        <CardDescription>Current status of all documents</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {statusEntries.length > 0 ? (
                            statusEntries.map(([status, count]) => {
                                const percentage = total_documents > 0 ? ((count as number) / total_documents) * 100 : 0;

                                return (
                                    <div key={status} className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <Badge variant={getStatusVariant(status) as any} className="text-xs">
                                                    {status.charAt(0).toUpperCase() + status.slice(1)}
                                                </Badge>
                                                <span className="text-sm font-medium">{count}</span>
                                            </div>
                                            <span className="text-xs text-muted-foreground">{percentage.toFixed(1)}%</span>
                                        </div>
                                        <Progress value={percentage} className="h-2" />
                                    </div>
                                );
                            })
                        ) : (
                            <p className="text-sm text-muted-foreground text-center py-4">No status data available</p>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

function AnalyticsLoadingSkeleton({ className }: { className?: string }) {
    return (
        <div className={`space-y-6 ${className}`}>
            {/* Overview Cards Skeleton */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <Card key={i}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-4 w-4" />
                        </CardHeader>
                        <CardContent>
                            <Skeleton className="h-8 w-16 mb-2" />
                            <Skeleton className="h-3 w-32" />
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Charts Skeleton */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {Array.from({ length: 2 }).map((_, i) => (
                    <Card key={i}>
                        <CardHeader>
                            <Skeleton className="h-6 w-32" />
                            <Skeleton className="h-4 w-48" />
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {Array.from({ length: 3 }).map((_, j) => (
                                <div key={j} className="space-y-2">
                                    <div className="flex items-center justify-between">
                                        <Skeleton className="h-4 w-20" />
                                        <Skeleton className="h-4 w-12" />
                                    </div>
                                    <Skeleton className="h-2 w-full" />
                                </div>
                            ))}
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    );
}
