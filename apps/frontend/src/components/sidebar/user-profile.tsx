"use client";

import { useState } from "react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChevronUp, User, Settings, LogOut } from "lucide-react";
import { ProfileEditModal } from "./profile-edit-modal";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { useAuth } from "@frontegg/nextjs";

export function UserProfile() {
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const router = useRouter();
    const { user: fronteggUser } = useAuth();

    const logout = useCallback(() => {
        router.replace("/account/logout");
    }, [router]);

    const user = {
        name: fronteggUser?.name || "John Doe",
        email: fronteggUser?.email || "john@example.com",
        role: "Admin",
        avatar: fronteggUser?.profilePictureUrl || "/user-avatar.jpg",
    };

    return (
        <>
            <SidebarMenu>
                <SidebarMenuItem>
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <SidebarMenuButton
                                size="lg"
                                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                            >
                                <Avatar className="w-8 h-8 rounded-lg">
                                    <AvatarImage src={user.avatar} alt={user.name} />
                                    <AvatarFallback className="rounded-lg">
                                        {user.name
                                            .split(" ")
                                            .map((n: string) => n[0])
                                            .join("")}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="grid flex-1 text-sm leading-tight text-left">
                                    <span className="font-semibold truncate">{user.name}</span>
                                    <span className="text-xs truncate">{user.role}</span>
                                </div>
                                <ChevronUp className="ml-auto" />
                            </SidebarMenuButton>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent
                            className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                            side="top"
                            align="end"
                            sideOffset={4}
                        >
                            <DropdownMenuItem className="gap-2 p-2">
                                <User className="w-4 h-4" />
                                <div className="grid flex-1 text-sm leading-tight text-left">
                                    <span className="font-semibold truncate">{user.name}</span>
                                    <span className="text-xs truncate">{user.email}</span>
                                </div>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="gap-2 p-2" onClick={() => setIsEditModalOpen(true)}>
                                <User className="w-4 h-4" />
                                <span>Edit Profile</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem className="gap-2 p-2">
                                <Settings className="w-4 h-4" />
                                <span>Account Settings</span>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="gap-2 p-2 text-red-600" onClick={logout}>
                                <LogOut className="w-4 h-4" />
                                <span>Sign out</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </SidebarMenuItem>
            </SidebarMenu>

            <ProfileEditModal open={isEditModalOpen} onOpenChange={setIsEditModalOpen} />
        </>
    );
}
