"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, ArrowRight, Settings } from "lucide-react";

interface SetupTask {
    id: string;
    title: string;
    completed: boolean;
    description?: string;
}

interface SetupProgressCardProps {
    title?: string;
    tasks: SetupTask[];
    completionPercentage: number;
}

export const SetupProgressCard: React.FC<SetupProgressCardProps> = ({ title = "Setup Progress", tasks, completionPercentage }) => {
    const completedTasks = tasks.filter((task) => task.completed).length;
    const totalTasks = tasks.length;

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div className="flex items-center gap-2">
                    <Settings className="w-5 h-5 text-green-600" />
                    <CardTitle className="text-lg font-semibold">{title}</CardTitle>
                </div>
                <Badge variant="secondary" className="text-green-600 bg-green-50 dark:bg-green-900/20">
                    {completionPercentage}% Completed
                </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
                {tasks.map((task) => (
                    <div key={task.id} className="flex items-center gap-3">
                        <div className="flex-shrink-0">
                            {task.completed ? (
                                <CheckCircle className="w-5 h-5 text-green-600" />
                            ) : (
                                <div className="w-5 h-5 rounded-full border-2 border-gray-300 dark:border-gray-600 flex items-center justify-center">
                                    <ArrowRight className="w-3 h-3 text-gray-400" />
                                </div>
                            )}
                        </div>
                        <div className="flex-1">
                            <p className={`text-sm font-medium ${task.completed ? "text-foreground" : "text-muted-foreground"}`}>
                                {task.title}
                            </p>
                            {task.description && <p className="text-xs text-muted-foreground mt-1">{task.description}</p>}
                        </div>
                    </div>
                ))}

                <div className="pt-2 border-t">
                    <div className="flex justify-between text-xs text-muted-foreground">
                        <span>
                            {completedTasks} of {totalTasks} completed
                        </span>
                        <span>{completionPercentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
                        <div
                            className="bg-green-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${completionPercentage}%` }}
                        />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
