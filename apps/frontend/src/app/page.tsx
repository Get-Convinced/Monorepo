"use client";

import { useSimpleAuth } from "@/hooks/use-simple-auth";
import { useEffect } from "react";

export default function Home() {
  const {
    isAuthenticated,
    isLoading,
    user,
    isRedirecting,
    shouldRedirect,
    redirectToDashboard,
    redirectToLogin,
  } = useSimpleAuth();

  useEffect(() => {
    if (shouldRedirect) {
      if (isAuthenticated && user) {
        // User is authenticated, redirect to dashboard
        redirectToDashboard();
      } else if (isAuthenticated === false) {
        // User is definitely not authenticated, redirect to login
        redirectToLogin();
      }
    }
  }, [
    isAuthenticated,
    user,
    shouldRedirect,
    redirectToDashboard,
    redirectToLogin,
  ]);

  // Show loading state while checking authentication
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-lg">
          {isRedirecting ? "Redirecting..." : "Loading..."}
        </p>
      </div>
    </div>
  );
}
