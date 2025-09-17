"use client";

import { AlertCircle, CheckCircle, Clock } from "lucide-react";

interface StatusIconProps {
    status: "ready" | "processing" | "failed";
}

export function StatusIcon({ status }: StatusIconProps) {
    switch (status) {
        case "ready":
            return <CheckCircle className="w-4 h-4 text-green-500" />;
        case "processing":
            return <Clock className="w-4 h-4 text-yellow-500" />;
        case "failed":
            return <AlertCircle className="w-4 h-4 text-red-500" />;
        default:
            return <Clock className="w-4 h-4 text-gray-500" />;
    }
}
