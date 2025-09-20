"use client";

import dynamic from "next/dynamic";
import { ReactNode } from "react";

const FronteggProvider = dynamic(
  () => import("@frontegg/react").then((mod) => mod.FronteggProvider),
  { ssr: false }
);

export function Providers({ children }: { children: ReactNode }) {
  const baseUrl = process.env.NEXT_PUBLIC_FRONTEGG_BASE_URL;
  const clientId = process.env.NEXT_PUBLIC_FRONTEGG_CLIENT_ID;

  // Check if required environment variables are missing
  if (!baseUrl || !clientId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md mx-auto text-center p-6 bg-white rounded-lg shadow-lg">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Configuration Required
          </h1>
          <p className="text-gray-600 mb-4">
            Please configure your Frontegg credentials to continue.
          </p>
          <div className="text-left bg-yellow-50 p-4 rounded-md mb-4">
            <p className="text-sm text-gray-700 mb-2">
              <strong>Missing environment variables:</strong>
            </p>
            <ul className="text-sm text-gray-600 space-y-1">
              {!baseUrl && <li>• NEXT_PUBLIC_FRONTEGG_BASE_URL</li>}
              {!clientId && <li>• NEXT_PUBLIC_FRONTEGG_CLIENT_ID</li>}
            </ul>
          </div>
          <div className="text-left bg-blue-50 p-4 rounded-md">
            <p className="text-sm text-gray-700 mb-2">
              <strong>To fix this:</strong>
            </p>
            <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
              <li>
                Create a{" "}
                <code className="bg-gray-200 px-1 rounded">.env.local</code>{" "}
                file in your project root
              </li>
              <li>Add your Frontegg credentials from your dashboard</li>
              <li>Restart the development server</li>
            </ol>
          </div>
        </div>
      </div>
    );
  }

  return (
    <FronteggProvider
      contextOptions={{
        baseUrl,
        clientId,
        redirectUrl: `${
          process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"
        }/api/auth/[...frontegg]`,
      }}
      keepSessionAlive={true}
      hostedLoginBox={true}>
      {children}
    </FronteggProvider>
  );
}
