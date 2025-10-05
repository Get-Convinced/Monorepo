"use client";

import { AlertCircle, CheckCircle, Clock, FileText, Layers, Sparkles, Hash, FileSearch, Tag, Loader2 } from "lucide-react";

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

interface StatusIconProps {
    status: RagieStatus | string;
}

export function StatusIcon({ status }: StatusIconProps) {
    switch (status) {
        case "ready":
            return <CheckCircle className="w-4 h-4 text-green-500" />;
        case "pending":
            return <Clock className="w-4 h-4 text-gray-500" />;
        case "partitioning":
            return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
        case "partitioned":
            return <Layers className="w-4 h-4 text-blue-500" />;
        case "refined":
            return <Sparkles className="w-4 h-4 text-purple-500" />;
        case "chunked":
            return <FileText className="w-4 h-4 text-indigo-500" />;
        case "indexed":
            return <Hash className="w-4 h-4 text-cyan-500" />;
        case "summary_indexed":
            return <FileSearch className="w-4 h-4 text-teal-500" />;
        case "keyword_indexed":
            return <Tag className="w-4 h-4 text-emerald-500" />;
        case "failed":
            return <AlertCircle className="w-4 h-4 text-red-500" />;
        default:
            return <Clock className="w-4 h-4 text-gray-500" />;
    }
}
