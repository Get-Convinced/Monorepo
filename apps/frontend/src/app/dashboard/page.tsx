import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { ChatInterface } from "@/components/chat/chat-interface";

export default function DashboardPage() {
    return (
        <SidebarLayout>
            <ChatInterface />
        </SidebarLayout>
    );
}
