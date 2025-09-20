"use client";

import {  useEffect, useState } from "react";
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
import { useAuth, useAuthActions } from "@frontegg/react";

export function UserProfile() {
    const router = useRouter();
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
     const { logout } = useAuthActions(); 

 const handleLogout = () => {
    logout(); 
    localStorage.removeItem('user'); 
    router.push('/login');
  };
    


    const defaultUser = {
        name: "John Doe",
        email: "john@example.com",
        role: "Product Manager",
        avatar: "/user-avatar.jpg",
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
                                <Avatar className="h-8 w-8 rounded-lg">
                                    <AvatarImage src={defaultUser.avatar} alt={defaultUser.name} />
                                    <AvatarFallback className="rounded-lg">
                                        {defaultUser.name
                                            .split(" ")
                                            .map((n) => n[0])
                                            .join("")}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-semibold">{defaultUser.name}</span>
                                    <span className="truncate text-xs">{defaultUser.role}</span>
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
                                <User className="h-4 w-4" />
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-semibold">{defaultUser.name}</span>
                                    <span className="truncate text-xs">{defaultUser.email}</span>
                                </div>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="gap-2 p-2" onClick={() => setIsEditModalOpen(true)}>
                                <User className="h-4 w-4" />
                                <span>Edit Profile</span>
                            </DropdownMenuItem>
                            <DropdownMenuItem className="gap-2 p-2">
                                <Settings className="h-4 w-4" />
                                <span>Account Settings</span>
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="gap-2 p-2 text-red-600" onClick={handleLogout}>
                                <LogOut className="h-4 w-4" />
                                <span >Sign out</span>
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </SidebarMenuItem>
            </SidebarMenu>

            <ProfileEditModal open={isEditModalOpen} onOpenChange={setIsEditModalOpen} />
        </>
    );
}
