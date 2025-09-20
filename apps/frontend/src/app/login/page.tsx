"use client";

import { useLoginWithRedirect } from "@frontegg/react";
import { useSimpleAuth } from "@/hooks/use-simple-auth";
import { useEffect } from "react";

export default function Login() {
  const {
    isAuthenticated,
    isLoading,
    user,
    isRedirecting,
    shouldRedirect,
    redirectToDashboard,
  } = useSimpleAuth();
  const loginWithRedirect = useLoginWithRedirect();

  useEffect(() => {
    if (shouldRedirect && isAuthenticated && user) {
      console.log("User is authenticated, redirecting to dashboard");
      redirectToDashboard();
    }
  }, [isAuthenticated, user, shouldRedirect, redirectToDashboard]);

  // Show loading state
  if (isLoading || isRedirecting) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
        <p className="mb-4 text-lg">
          {isRedirecting ? "Redirecting..." : "Loading..."}
        </p>
      </div>
    );
  }

  // Show message for authenticated users (middleware should redirect, but just in case)
  if (isAuthenticated && user) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="text-green-600 text-6xl mb-4">✓</div>
          <p className="mb-4 text-lg font-semibold">
            You are already logged in!
          </p>
          <p className="mb-4 text-sm text-gray-600">
            Welcome back, {user.email}
          </p>
          <p className="mb-4 text-sm text-gray-500">
            Redirecting to dashboard...
          </p>
        </div>
      </div>
    );
  }

  // Show login form for unauthenticated users
  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <h1 className="mb-6 text-2xl font-bold">Welcome Back</h1>
      <p className="mb-4 text-lg">Please log in to continue</p>
      <button
        onClick={() => loginWithRedirect()}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
        Login with Frontegg
      </button>
    </div>
  );
}
