import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { ChatInterface } from "@/components/chat/chat-interface";
import { getAppUserSession } from "@frontegg/nextjs/app";
import { redirect } from "next/navigation";

export default async function ChatPage() {
    const userSession = await getAppUserSession();

    if (!userSession) {
        redirect("/account/login");
    }

    return (
        <SidebarLayout>
            <ChatInterface />
        </SidebarLayout>
    );
}
