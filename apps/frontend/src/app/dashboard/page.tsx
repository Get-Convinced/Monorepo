import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { ChatInterface } from "@/components/chat/chat-interface";

import { getAppUserSession } from "@frontegg/nextjs/app";
import { redirect } from "next/navigation";

export default async function DashboardPage() {
  const userSession = await getAppUserSession();
  console.log(userSession);
  if (!userSession) {
    redirect("/");
  }
  return (
    <SidebarLayout>
      <ChatInterface />
    </SidebarLayout>
  );
}
