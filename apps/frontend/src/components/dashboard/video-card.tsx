"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Play, Globe, FileText, FileSpreadsheet } from "lucide-react";

interface VideoCardProps {
    title: string;
    videoUrl?: string;
    sources?: {
        urls: number;
        battleCards: number;
        salesAssets: number;
    };
}

export const VideoCard: React.FC<VideoCardProps> = ({ title, videoUrl, sources = { urls: 4215, battleCards: 3, salesAssets: 5 } }) => {
    return (
        <Card className="overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-br from-yellow-400/20 via-pink-500/20 to-purple-600/20" />
            <CardContent className="relative p-8">
                <div className="flex justify-between items-start">
                    <div className="flex-1">
                        <h2 className="mb-6 text-3xl font-bold text-foreground">{title}</h2>

                        {/* Video Player Placeholder */}
                        <div className="relative mx-auto mb-6 w-full max-w-md">
                            <div className="flex justify-center items-center bg-gradient-to-br from-pink-500 to-purple-600 rounded-2xl shadow-lg aspect-video">
                                <Button
                                    size="lg"
                                    className="p-0 w-16 h-16 rounded-full border-0 bg-white/20 hover:bg-white/30"
                                    onClick={() => {
                                        // Handle video play
                                        console.log("Play video");
                                    }}
                                >
                                    <Play className="ml-1 w-8 h-8 text-white" fill="currentColor" />
                                </Button>
                            </div>
                        </div>
                    </div>

                    {/* Sources Overlay */}
                    <div className="p-4 max-w-xs rounded-xl shadow-lg backdrop-blur-sm bg-white/90 dark:bg-gray-800/90">
                        <h3 className="mb-3 text-sm font-semibold text-foreground">Answered using these sources:</h3>
                        <div className="space-y-2">
                            <div className="flex gap-2 items-center text-sm">
                                <Globe className="w-4 h-4 text-blue-600" />
                                <span className="text-foreground">Convinced has analyzed {sources.urls.toLocaleString()} URLs</span>
                            </div>
                            <div className="flex gap-2 items-center text-sm">
                                <FileSpreadsheet className="w-4 h-4 text-green-600" />
                                <span className="text-foreground">User uploaded {sources.battleCards} battle cards</span>
                            </div>
                            <div className="flex gap-2 items-center text-sm">
                                <FileText className="w-4 h-4 text-blue-600" />
                                <span className="text-foreground">User uploaded {sources.salesAssets} sales assets</span>
                            </div>
                        </div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};
