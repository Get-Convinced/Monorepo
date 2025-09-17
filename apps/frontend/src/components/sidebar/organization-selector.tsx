"use client";

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { ChevronDown, Building2 } from "lucide-react";

export function OrganizationSelector() {
    const organizations = [
        { id: "1", name: "Acme Inc", role: "Owner" },
        { id: "2", name: "Acme Corp", role: "Admin" },
        { id: "3", name: "Startup Co", role: "Member" },
    ];

    const currentOrg = organizations[0];

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
                                <span className="truncate text-xs">{currentOrg.role}</span>
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
                        {organizations.map((org) => (
                            <DropdownMenuItem key={org.id} className="gap-2 p-2">
                                <Building2 className="h-4 w-4" />
                                <div className="grid flex-1 text-left text-sm leading-tight">
                                    <span className="truncate font-semibold">{org.name}</span>
                                    <span className="truncate text-xs">{org.role}</span>
                                </div>
                            </DropdownMenuItem>
                        ))}
                        <DropdownMenuItem className="gap-2 p-2">
                            <Building2 className="h-4 w-4" />
                            <span>Create organization</span>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </SidebarMenuItem>
        </SidebarMenu>
    );
}
