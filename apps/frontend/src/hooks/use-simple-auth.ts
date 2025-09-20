'use client';

import { useAuth } from '@frontegg/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export function useSimpleAuth() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [hasStoredAuth, setHasStoredAuth] = useState(false);
  const [sessionRestoreTimeout, setSessionRestoreTimeout] = useState<NodeJS.Timeout | null>(null);

  // Store auth state in sessionStorage when authenticated
  useEffect(() => {
    if (!isLoading && hasInitialized) {
      if (isAuthenticated && user) {
        sessionStorage.setItem('frontegg_auth', JSON.stringify({
          isAuthenticated: true,
          user: {
            email: user.email,
            name: user.name,
            id: user.id
          },
          timestamp: Date.now()
        }));
        // Clear any pending timeout since we're authenticated
        if (sessionRestoreTimeout) {
          clearTimeout(sessionRestoreTimeout);
          setSessionRestoreTimeout(null);
        }
      } else if (isAuthenticated === false && !hasStoredAuth) {
        // Only clear if we're sure user is not authenticated AND we don't have stored auth
        sessionStorage.removeItem('frontegg_auth');
      }
    }
  }, [isAuthenticated, isLoading, user, hasInitialized, hasStoredAuth, sessionRestoreTimeout]);

  // Check for stored auth on mount
  useEffect(() => {
    const storedAuth = sessionStorage.getItem('frontegg_auth');
    if (storedAuth) {
      try {
        const parsed = JSON.parse(storedAuth);
        const isRecent = Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000; // 24 hours
        if (isRecent) {
          setHasStoredAuth(true);
          
          // Set a longer timeout to give Frontegg more time to restore the session
          const timeout = setTimeout(() => {
            console.log('Session restore timeout reached, but keeping stored auth for now');
          }, 10000); // 10 seconds timeout
          
          setSessionRestoreTimeout(timeout);
        } else {
          sessionStorage.removeItem('frontegg_auth');
        }
      } catch (error) {
        sessionStorage.removeItem('frontegg_auth');
      }
    }
    setHasInitialized(true);
  }, []);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (sessionRestoreTimeout) {
        clearTimeout(sessionRestoreTimeout);
      }
    };
  }, [sessionRestoreTimeout]);


  const redirectToDashboard = () => {
    if (!isRedirecting) {
      setIsRedirecting(true);
      router.push('/dashboard');
    }
  };

  const redirectToLogin = () => {
    if (!isRedirecting) {
      setIsRedirecting(true);
      router.push('/login');
    }
  };

  // Use stored auth data if Frontegg hasn't restored yet
  const effectiveIsAuthenticated = isAuthenticated || hasStoredAuth;
  const effectiveUser = user || (hasStoredAuth ? { email: 'Loading...' } : user);

  // Don't redirect until we've initialized and Frontegg has loaded
  // If we have stored auth, give Frontegg more time to restore the session
  const shouldRedirect = hasInitialized && !isLoading && (!hasStoredAuth || isAuthenticated !== undefined);

  // If we have stored auth but Frontegg hasn't restored yet, show loading
  const effectiveIsLoading = !hasInitialized || (isLoading && !hasStoredAuth) || (hasStoredAuth && isAuthenticated === undefined && !user);

  return {
    isAuthenticated: effectiveIsAuthenticated,
    isLoading: effectiveIsLoading,
    user: effectiveUser,
    isRedirecting,
    shouldRedirect,
    redirectToDashboard,
    redirectToLogin,
    // Also return the original values for debugging
    originalIsAuthenticated: isAuthenticated,
    originalUser: user,
    hasStoredAuth
  };
}
