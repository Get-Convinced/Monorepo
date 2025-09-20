"use client";

import { SidebarLayout } from "@/components/dashboard/sidebar-layout";
import { ChatInterface } from "@/components/chat/chat-interface";
import { useSimpleAuth } from "@/hooks/use-simple-auth";
import { useEffect } from "react";

export default function DashboardPage() {
  const {
    isAuthenticated,
    isLoading,
    user,
    isRedirecting,
    shouldRedirect,
    redirectToLogin,
    originalIsAuthenticated,
    originalUser,
    hasStoredAuth,
  } = useSimpleAuth();


  useEffect(() => {
    if (shouldRedirect && isAuthenticated === false && !user) {
      redirectToLogin();
    }
  }, [user, isAuthenticated, shouldRedirect, redirectToLogin]);

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg">Loading...</p>
        </div>
      </div>
    );
  }

  // Show loading if not authenticated (redirect will happen)
  // Use the effective values from the hook
  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg">Redirecting...</p>
        </div>
      </div>
    );
  }

  return (
    <SidebarLayout>
      <ChatInterface />
    </SidebarLayout>
  );
}
