"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { HelpCircle, Calendar } from "lucide-react";

interface HelpCardProps {
    title?: string;
    description?: string;
    buttonText?: string;
    onButtonClick?: () => void;
}

export const HelpCard: React.FC<HelpCardProps> = ({
    title = "Need Help?",
    description = "Get personalized assistance with your setup",
    buttonText = "Schedule Walkthrough",
    onButtonClick,
}) => {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div className="flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-purple-600" />
                    <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    className="text-purple-600 border-purple-200 hover:bg-purple-50 dark:border-purple-800 dark:hover:bg-purple-900/20"
                    onClick={onButtonClick}
                >
                    <Calendar className="w-4 h-4 mr-2" />
                    {buttonText}
                </Button>
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">{description}</p>
            </CardContent>
        </Card>
    );
};
