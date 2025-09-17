"use client";

import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader } from "@/components/ui/sidebar";
import { OrganizationSelector } from "@/components/sidebar/organization-selector";
import { NavigationMenu } from "@/components/sidebar/navigation-menu";
import { UserProfile } from "@/components/sidebar/user-profile";

export function AppSidebar() {
    return (
        <Sidebar collapsible="icon" className="border-r">
            <SidebarHeader>
                <OrganizationSelector />
            </SidebarHeader>
            <SidebarContent>
                <NavigationMenu />
            </SidebarContent>
            <SidebarFooter>
                <UserProfile />
            </SidebarFooter>
        </Sidebar>
    );
}
