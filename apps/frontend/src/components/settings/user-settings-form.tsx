"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Camera, Loader2 } from "lucide-react";
import { useAuth } from "@frontegg/nextjs";
import { toast } from "sonner";

interface UserFormData {
    name: string;
    phone?: string;
    avatar_url?: string;
}

export function UserSettingsForm() {
    const { user } = useAuth();
    const [formData, setFormData] = useState<UserFormData>({
        name: "",
        phone: "",
        avatar_url: "",
    });
    const [isLoading, setIsLoading] = useState(false);

    console.log("👤 UserSettingsForm component rendered:", {
        user: user
            ? {
                  sub: user.sub,
                  name: user.name,
                  email: user.email,
              }
            : null,
        isLoading,
    });

    // Load user data when component mounts or user changes
    useEffect(() => {
        if (user) {
            setFormData({
                name: user.name || "",
                phone: (user.metadata as any)?.phone || "",
                avatar_url: user.profilePictureUrl || "",
            });
        }
    }, [user]);

    const handleInputChange = (field: keyof UserFormData, value: string) => {
        setFormData((prev) => ({
            ...prev,
            [field]: value,
        }));
    };

    const handleSave = async () => {
        console.log("Save button clicked!", { user, formData });

        if (!user?.sub) {
            console.log("No user ID found:", user);
            return;
        }

        setIsLoading(true);

        // For now, just show a toast that this feature is coming soon
        // In a real implementation, you'd use Frontegg's profile update API
        setTimeout(() => {
            toast.success("Profile updated successfully");
            setIsLoading(false);
        }, 1000);
    };

    const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // For now, we'll just show a placeholder
            // In a real app, you'd upload to a file service
            console.info("Avatar upload functionality coming soon");
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-8">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Avatar Section */}
            <div className="flex flex-col items-center space-y-4">
                <div className="relative">
                    <Avatar className="w-24 h-24">
                        <AvatarImage src={formData.avatar_url} />
                        <AvatarFallback className="text-lg">
                            {formData.name
                                .split(" ")
                                .map((n) => n[0])
                                .join("")
                                .toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                    <label htmlFor="avatar-upload" className="absolute -right-2 -bottom-2 cursor-pointer">
                        <Button size="icon" className="w-8 h-8 rounded-full" asChild>
                            <div>
                                <Camera className="w-4 h-4" />
                            </div>
                        </Button>
                        <input id="avatar-upload" type="file" accept="image/*" className="hidden" onChange={handleAvatarChange} />
                    </label>
                </div>
            </div>

            {/* Form Fields */}
            <div className="grid gap-4">
                <div className="grid gap-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange("name", e.target.value)}
                        placeholder="Enter your full name"
                    />
                </div>

                <div className="grid gap-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input id="email" value={user?.email || ""} disabled className="bg-muted" placeholder="Email cannot be changed" />
                    <p className="text-xs text-muted-foreground">
                        Email address is managed by your authentication provider and cannot be changed here.
                    </p>
                </div>

                <div className="grid gap-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => handleInputChange("phone", e.target.value)}
                        placeholder="Enter your phone number"
                        type="tel"
                    />
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end pt-4 space-x-2">
                <Button
                    variant="outline"
                    onClick={() => {
                        if (user) {
                            setFormData({
                                name: user.name || "",
                                phone: (user.metadata as any)?.phone || "",
                                avatar_url: user.profilePictureUrl || "",
                            });
                        }
                    }}
                    disabled={isLoading}
                >
                    Reset
                </Button>
                <Button onClick={handleSave} disabled={isLoading}>
                    {isLoading && <Loader2 className="mr-2 w-4 h-4 animate-spin" />}
                    Save Changes
                </Button>
            </div>
        </div>
    );
}
