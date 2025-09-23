"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PieChart, MessageCircle, FileText, Clock, RefreshCw } from "lucide-react";

interface UsageMetric {
    id: string;
    label: string;
    value: number;
    unit?: string;
    icon: React.ReactNode;
    color?: string;
}

interface UsageCardProps {
    title?: string;
    metrics: UsageMetric[];
    lastRefreshed?: string;
}

export const UsageCard: React.FC<UsageCardProps> = ({ title = "Usage", metrics, lastRefreshed = "4 days ago" }) => {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div className="flex items-center gap-2">
                    <PieChart className="w-5 h-5 text-blue-600" />
                    <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                </div>
                <Badge variant="outline" className="text-blue-600 border-blue-200 dark:border-blue-800">
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Refreshed {lastRefreshed}
                </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
                {metrics.map((metric) => (
                    <div key={metric.id} className="flex items-center gap-3">
                        <div className={`flex-shrink-0 p-2 rounded-lg ${metric.color || "bg-blue-100 dark:bg-blue-900/20"}`}>
                            {metric.icon}
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-foreground">
                                {metric.value.toLocaleString()} {metric.unit || ""} {metric.label}
                            </p>
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
};
