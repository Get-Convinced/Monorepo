"use client";

import { useAuth, useLoginWithRedirect } from "@frontegg/nextjs";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function LoginClient() {
    const { isAuthenticated, isLoading } = useAuth();
    const loginWithRedirect = useLoginWithRedirect();
    const router = useRouter();
    const searchParams = useSearchParams();

    useEffect(() => {
        // If already authenticated, redirect to the intended page or dashboard
        if (isAuthenticated) {
            const redirectTo = searchParams.get("redirectTo") || "/dashboard";
            router.push(redirectTo);
        }
    }, [isAuthenticated, router, searchParams]);

    const handleLogin = () => {
        loginWithRedirect();
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center min-h-screen bg-gray-50">
                <div className="w-32 h-32 rounded-full border-b-2 border-blue-600 animate-spin"></div>
            </div>
        );
    }

    if (isAuthenticated) {
        return (
            <div className="flex justify-center items-center min-h-screen bg-gray-50">
                <div className="text-center">
                    <p className="mb-4 text-gray-600">Redirecting to dashboard...</p>
                    <div className="mx-auto w-8 h-8 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex justify-center items-center min-h-screen bg-gray-50">
            <div className="space-y-8 w-full max-w-md">
                <div>
                    <h2 className="mt-6 text-3xl font-extrabold text-center text-gray-900">Sign in to your account</h2>
                    <p className="mt-2 text-sm text-center text-gray-600">Welcome to the AI Knowledge Agent</p>
                </div>
                <div className="mt-8 space-y-6">
                    <div>
                        <button
                            onClick={handleLogin}
                            className="flex relative justify-center px-4 py-3 w-full text-sm font-medium text-white bg-blue-600 rounded-md border border-transparent transition-colors group hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                        >
                            Sign in with Frontegg
                        </button>
                    </div>
                    <div className="text-center">
                        <p className="text-xs text-gray-500">Secure authentication powered by Frontegg</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
