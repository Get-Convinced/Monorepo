'use client';

import dynamic from 'next/dynamic';
import { ReactNode } from 'react';

const FronteggProvider = dynamic(
  () => import('@frontegg/react').then((mod) => mod.FronteggProvider),
  { ssr: false }
);

export function Providers({ children }: { children: ReactNode }) {
  return (
    <FronteggProvider
      contextOptions={{
        baseUrl: process.env.NEXT_PUBLIC_FRONTEGG_BASE_URL!,
        clientId: process.env.NEXT_PUBLIC_FRONTEGG_CLIENT_ID!,
        
      }}
      hostedLoginBox={true}
    >
      {children}
    </FronteggProvider>
  );
}