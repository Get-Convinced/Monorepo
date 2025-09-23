"use client";

import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { ThemeToggle } from "@/components/theme-toggle";

export function SidebarLayout({ children }: { children: React.ReactNode }) {
    return (
        <SidebarProvider className="h-full">
            <AppSidebar />
            <main className="flex-1 flex flex-col h-full">
                <header className="flex h-16 items-center gap-2 border-b px-4 flex-shrink-0">
                    <SidebarTrigger className="-ml-1" />
                    <div className="flex-1" />
                    <ThemeToggle />
                </header>
                <div className="flex-1 overflow-hidden min-h-0">{children}</div>
            </main>
        </SidebarProvider>
    );
}
