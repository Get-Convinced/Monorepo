"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Plus, X } from "lucide-react";

interface TagManagerProps {
    fileId: number;
    currentTags: string[];
    onTagsUpdate: (tags: string[]) => void;
}

const AVAILABLE_TAGS = [
    "financial",
    "quarterly",
    "reports",
    "product",
    "specifications",
    "market",
    "analysis",
    "technical",
    "documentation",
    "research",
    "presentation",
    "data",
    "strategy",
    "planning",
    "review",
];

export function TagManager({ fileId, currentTags, onTagsUpdate }: TagManagerProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [newTag, setNewTag] = useState("");

    const handleAddTag = (tag: string) => {
        if (tag && !currentTags.includes(tag)) {
            onTagsUpdate([...currentTags, tag]);
        }
        setNewTag("");
    };

    const handleRemoveTag = (tagToRemove: string) => {
        onTagsUpdate(currentTags.filter((tag) => tag !== tagToRemove));
    };

    const handleCreateNewTag = () => {
        if (newTag.trim() && !currentTags.includes(newTag.trim())) {
            onTagsUpdate([...currentTags, newTag.trim()]);
            setNewTag("");
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="px-2 h-6 text-xs">
                    <Plus className="mr-1 w-3 h-3" />
                    Add Tag
                </Button>
            </DialogTrigger>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>Manage Tags</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                    {/* Current Tags */}
                    <div>
                        <Label className="text-sm font-medium">Current Tags</Label>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {currentTags.map((tag) => (
                                <Badge key={tag} variant="outline" className="flex gap-1 items-center">
                                    {tag}
                                    <X className="w-3 h-3 cursor-pointer hover:text-red-500" onClick={() => handleRemoveTag(tag)} />
                                </Badge>
                            ))}
                        </div>
                    </div>

                    {/* Available Tags */}
                    <div>
                        <Label className="text-sm font-medium">Available Tags</Label>
                        <div className="flex overflow-y-auto flex-wrap gap-2 mt-2 max-h-32">
                            {AVAILABLE_TAGS.filter((tag) => !currentTags.includes(tag)).map((tag) => (
                                <Badge
                                    key={tag}
                                    variant="secondary"
                                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                                    onClick={() => handleAddTag(tag)}
                                >
                                    {tag}
                                </Badge>
                            ))}
                        </div>
                    </div>

                    {/* Create New Tag */}
                    <div>
                        <Label htmlFor="newTag" className="text-sm font-medium">
                            Create New Tag
                        </Label>
                        <div className="flex gap-2 mt-2">
                            <Input
                                id="newTag"
                                value={newTag}
                                onChange={(e) => setNewTag(e.target.value)}
                                placeholder="Enter new tag name"
                                onKeyDown={(e) => e.key === "Enter" && handleCreateNewTag()}
                            />
                            <Button onClick={handleCreateNewTag} disabled={!newTag.trim()}>
                                Add
                            </Button>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
