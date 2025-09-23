"use client";

import { VideoCard } from "./video-card";
import { SetupProgressCard } from "./setup-progress-card";
import { UsageCard } from "./usage-card";
import { HelpCard } from "./help-card";
import { MessageCircle, FileText, Clock } from "lucide-react";

export const IntroDashboard: React.FC = () => {
    // Setup progress data
    const setupTasks = [
        {
            id: "add-documents",
            title: "Add 10 documents to your Knowledge Base",
            completed: true,
            description: "Upload PDFs, Word docs, or other files",
        },
        {
            id: "ask-question",
            title: "Ask Convinced a Question",
            completed: true,
            description: "Test the AI with your first query",
        },
        {
            id: "automate-questionnaire",
            title: "Automate a Questionnaire",
            completed: false,
            description: "Set up automated Q&A workflows",
        },
        {
            id: "connect-integrations",
            title: "Connect Convinced to Slack, Teams, or Google Chat",
            completed: false,
            description: "Integrate with your team's communication tools",
        },
    ];

    // Usage metrics data
    const usageMetrics = [
        {
            id: "answers-generated",
            label: "Answers Generated",
            value: 4,
            icon: <MessageCircle className="w-4 h-4 text-blue-600" />,
            color: "bg-blue-100 dark:bg-blue-900/20",
        },
        {
            id: "words-generated",
            label: "Words Generated",
            value: 397,
            icon: <FileText className="w-4 h-4 text-blue-600" />,
            color: "bg-blue-100 dark:bg-blue-900/20",
        },
        {
            id: "time-saved",
            label: "Hours Saved Typing Answers",
            value: 0.2,
            unit: "",
            icon: <Clock className="w-4 h-4 text-blue-600" />,
            color: "bg-blue-100 dark:bg-blue-900/20",
        },
    ];

    const handleScheduleWalkthrough = () => {
        // Handle scheduling walkthrough
        console.log("Schedule walkthrough clicked");
    };

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold">Welcome to Convinced</h1>
                    <p className="text-muted-foreground">Your AI-powered knowledge assistant is ready to help</p>
                </div>
            </div>

            {/* Video Card */}
            <VideoCard
                title="Get Started with Convinced"
                sources={{
                    urls: 4215,
                    battleCards: 3,
                    salesAssets: 5,
                }}
            />

            {/* Progress and Usage Cards */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <SetupProgressCard tasks={setupTasks} completionPercentage={50} />
                <UsageCard metrics={usageMetrics} lastRefreshed="4 days ago" />
            </div>

            {/* Help Card */}
            <HelpCard onButtonClick={handleScheduleWalkthrough} />
        </div>
    );
};
