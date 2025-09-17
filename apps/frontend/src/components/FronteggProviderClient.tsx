"use client";

import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import { FronteggProvider } from "@frontegg/react";

type FronteggProviderClientProps = PropsWithChildren<{
    baseUrl: string;
    clientId: string;
    hostedLoginBox?: boolean;
}>;

export default function FronteggProviderClient({ baseUrl, clientId, hostedLoginBox = true, children }: FronteggProviderClientProps) {
    const [isMounted, setIsMounted] = useState(false);
    useEffect(() => {
        setIsMounted(true);
    }, []);

    const contextOptions = useMemo(
        () => ({
            baseUrl,
            clientId,
        }),
        [baseUrl, clientId]
    );

    if (!isMounted || !baseUrl || !clientId) {
        // Avoid rendering children that might use useAuth before provider is ready
        return null;
    }

    return (
        <FronteggProvider contextOptions={contextOptions} hostedLoginBox={hostedLoginBox}>
            {children}
        </FronteggProvider>
    );
}
