"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function ChatHeader() {
    return (
        <div className="flex justify-between items-center p-4 border-b flex-shrink-0">
            <Tabs defaultValue="qa" className="w-full">
                <TabsList>
                    <TabsTrigger value="qa">Q&A</TabsTrigger>
                    <TabsTrigger value="docs" disabled>
                        Docs
                    </TabsTrigger>
                    <TabsTrigger value="rfp" disabled>
                        RFP
                    </TabsTrigger>
                </TabsList>
            </Tabs>
            <div className="flex gap-2 items-center">
                <Button variant="outline" size="sm">
                    Upload Files
                </Button>
                <Avatar>
                    <AvatarImage src="/user-avatar.jpg" />
                    <AvatarFallback>U</AvatarFallback>
                </Avatar>
            </div>
        </div>
    );
}
