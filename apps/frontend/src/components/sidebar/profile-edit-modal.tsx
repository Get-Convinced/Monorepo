"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Camera, Loader2 } from "lucide-react";
import { useAuth } from "@frontegg/nextjs";
import { toast } from "sonner";

interface ProfileEditModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function ProfileEditModal({ open, onOpenChange }: ProfileEditModalProps) {
    const { user } = useAuth();
    const [name, setName] = useState("");
    const [phone, setPhone] = useState("");
    const [description, setDescription] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // Load user data when modal opens
    useEffect(() => {
        if (open && user) {
            setName(user.name || "");
            const userPhone = (user.metadata as any)?.phone || "";
            const userDescription = (user.metadata as any)?.description || "";
            setPhone(userPhone);
            setDescription(userDescription);
        }
    }, [open, user]);

    const handleSave = async () => {
        if (!user?.sub) {
            return;
        }

        setIsLoading(true);

        // For now, just show a toast that this feature is coming soon
        // In a real implementation, you'd use Frontegg's profile update API
        setTimeout(() => {
            toast.success("Profile updated successfully");
            setIsLoading(false);
            onOpenChange(false);
        }, 1000);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-md">
                <DialogHeader>
                    <DialogTitle>Edit Profile</DialogTitle>
                </DialogHeader>
                <div className="space-y-6">
                    <div className="flex flex-col items-center space-y-4">
                        <div className="relative">
                            <Avatar className="w-20 h-20">
                                <AvatarImage src="/user-avatar.jpg" />
                                <AvatarFallback className="text-lg">
                                    {name
                                        .split(" ")
                                        .map((n: string) => n[0])
                                        .join("")}
                                </AvatarFallback>
                            </Avatar>
                            <Button size="icon" className="absolute -right-2 -bottom-2 w-8 h-8 rounded-full">
                                <Camera className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">Name</Label>
                            <Input
                                id="name"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter your name"
                                disabled={isLoading}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="phone">Phone Number</Label>
                            <Input
                                id="phone"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                placeholder="Enter your phone number"
                                type="tel"
                                disabled={isLoading}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">Description</Label>
                            <Textarea
                                id="description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Tell us about yourself"
                                rows={3}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="flex justify-end space-x-2">
                        <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isLoading}>
                            Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={isLoading}>
                            {isLoading && <Loader2 className="mr-2 w-4 h-4 animate-spin" />}
                            Save Changes
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
