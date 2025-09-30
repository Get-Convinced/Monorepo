"use client";

import { useState, useEffect } from "react";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { ChevronDown, Building2, Settings } from "lucide-react";
import { useAuth } from "@frontegg/nextjs";
import { useOrganizations } from "@/hooks/use-organization-queries";
import { useRouter } from "next/navigation";

interface Organization {
    id: string;
    name: string;
    role?: string;
}

export function OrganizationSelector() {
    const { user } = useAuth();
    const router = useRouter();
    const { data: organizations = [], isLoading: loading } = useOrganizations();

    // Fallback to user's organizations from auth if API fails
    const fallbackOrganizations =
        user?.tenantIds?.map((orgId) => ({
            id: orgId,
            name: `Organization ${orgId.slice(-4)}`,
            role: "Member",
        })) || [];

    const displayOrganizations = organizations.length > 0 ? organizations : fallbackOrganizations;
    const currentOrg = displayOrganizations.find((org) => org.id === user?.tenantId) || displayOrganizations[0];

    // Show loading state or fallback if no organizations
    if (loading) {
        return (
            <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton size="lg" disabled>
                        <Building2 className="h-4 w-4" />
                        <div className="grid flex-1 text-left text-sm leading-tight">
                            <span className="truncate font-semibold">Loading...</span>
                            <span className="truncate text-xs">Please wait</span>
                        </div>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        );
    }

    if (!currentOrg) {
        return (
            <SidebarMenu>
                <SidebarMenuItem>
                    <SidebarMenuButton size="lg" disabled>
                        <Building2 className="h-4 w-4" />
                        <div className="grid flex-1 text-left text-sm leading-tight">
                            <span className="truncate font-semibold">No Organization</span>
                            <span className="truncate text-xs">Contact admin</span>
                        </div>
                    </SidebarMenuButton>
                </SidebarMenuItem>
            </SidebarMenu>
        );
    }

    return (
        <SidebarMenu>
            <SidebarMenuItem>
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <SidebarMenuButton
                            size="lg"
                            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                        >
                            <Building2 className="h-4 w-4" />
                            <div className="grid flex-1 text-left text-sm leading-tight">
                                <span className="truncate font-semibold">{currentOrg.name}</span>
                                <span className="truncate text-xs">{currentOrg.role || "Member"}</span>
                            </div>
                            <ChevronDown className="ml-auto" />
                        </SidebarMenuButton>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent
                        className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                        side="bottom"
                        align="start"
                        sideOffset={4}
                    >
                        {displayOrganizations.map((org) => (
                            <DropdownMenuItem
                                key={org.id}
                                className="gap-2 p-2"
                                onClick={() => {
                                    // For now, just show a message - Frontegg handles organization switching
                                    console.log("Organization switching not implemented yet");
                                }}
                            >
                                <Building2 className="h-4 w-4" />
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-semibold">{org.name}</span>
                                    <span className="truncate text-xs">{org.role || "Member"}</span>
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="gap-2 p-2" onClick={() => router.push("/settings?tab=organization")}>
                            <Settings className="h-4 w-4" />
                            <span>Organization Settings</span>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarMenuItem>
        </SidebarMenu>
    );
}
