"use client";

import { Badge } from "@/components/ui/badge";

interface StatusBadgeProps {
    status: "ready" | "processing" | "failed";
}

export function StatusBadge({ status }: StatusBadgeProps) {
    switch (status) {
        case "ready":
            return (
                <Badge variant="default" className="text-green-800 bg-green-100">
                    Ready
                </Badge>
            );
        case "processing":
            return (
                <Badge variant="secondary" className="text-yellow-800 bg-yellow-100">
                    Processing
                </Badge>
            );
        case "failed":
            return <Badge variant="destructive">Failed</Badge>;
        default:
            return <Badge variant="secondary">Unknown</Badge>;
    }
}
