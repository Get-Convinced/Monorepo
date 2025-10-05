"use client";

import { Badge } from "@/components/ui/badge";

type RagieStatus =
    | "pending"
    | "partitioning"
    | "partitioned"
    | "refined"
    | "chunked"
    | "indexed"
    | "summary_indexed"
    | "keyword_indexed"
    | "ready"
    | "failed";

interface StatusBadgeProps {
    status: RagieStatus | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
    switch (status) {
        case "ready":
            return (
                <Badge variant="default" className="text-green-800 bg-green-100">
                    Ready
                </Badge>
            );
        case "pending":
            return (
                <Badge variant="secondary" className="text-gray-800 bg-gray-100">
                    Pending
                </Badge>
            );
        case "partitioning":
            return (
                <Badge variant="secondary" className="text-blue-800 bg-blue-100">
                    Partitioning
                </Badge>
            );
        case "partitioned":
            return (
                <Badge variant="secondary" className="text-blue-800 bg-blue-100">
                    Partitioned
                </Badge>
            );
        case "refined":
            return (
                <Badge variant="secondary" className="text-purple-800 bg-purple-100">
                    Refined
                </Badge>
            );
        case "chunked":
            return (
                <Badge variant="secondary" className="text-indigo-800 bg-indigo-100">
                    Chunked
                </Badge>
            );
        case "indexed":
            return (
                <Badge variant="secondary" className="text-cyan-800 bg-cyan-100">
                    Indexed
                </Badge>
            );
        case "summary_indexed":
            return (
                <Badge variant="secondary" className="text-teal-800 bg-teal-100">
                    Summary Indexed
                </Badge>
            );
        case "keyword_indexed":
            return (
                <Badge variant="secondary" className="text-emerald-800 bg-emerald-100">
                    Keyword Indexed
                </Badge>
            );
        case "failed":
            return <Badge variant="destructive">Failed</Badge>;
        default:
            return <Badge variant="secondary">Unknown</Badge>;
    }
}
