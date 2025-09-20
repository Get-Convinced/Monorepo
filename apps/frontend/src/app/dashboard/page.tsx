'use client';

import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { ChatInterface } from "@/components/chat/chat-interface";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [userData, setUserData] = useState<{ accessToken?: string; verified?: boolean } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem('user');
    if (stored) {
      setUserData(JSON.parse(stored));
    } else {
      setUserData(null);
    }
    setLoading(true); 
  }, []);

  useEffect(() => {
    if (loading) {
      if (!userData?.verified) {
        router.replace('/login');
      }
    }
  }, [userData, loading, router]);

  if (!userData?.verified) {
    return null;
  }

  return (
    <SidebarLayout>
      <ChatInterface />
    </SidebarLayout>
  );
}
