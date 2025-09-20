'use client';

import { useAuth } from '@frontegg/react';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export function useAuthSession() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [hasCheckedStorage, setHasCheckedStorage] = useState(false);

  // Check sessionStorage on mount for faster initial load
  const [initialAuthState, setInitialAuthState] = useState<{
    isAuthenticated: boolean;
    user: any;
  } | null>(null);

  useEffect(() => {
    const storedAuth = sessionStorage.getItem('frontegg_auth');
    console.log('Checking stored auth:', storedAuth);
    if (storedAuth) {
      try {
        const parsed = JSON.parse(storedAuth);
        // Check if session is not too old (24 hours)
        const isRecent = Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000;
        if (isRecent) {
          console.log('Using stored auth state:', parsed);
          setInitialAuthState({
            isAuthenticated: parsed.isAuthenticated,
            user: parsed.user
          });
        } else {
          console.log('Stored auth expired, removing');
          sessionStorage.removeItem('frontegg_auth');
        }
      } catch (error) {
        console.log('Error parsing stored auth:', error);
        sessionStorage.removeItem('frontegg_auth');
      }
    }
    setHasCheckedStorage(true);
  }, []);

  // Store authentication state in sessionStorage for persistence
  useEffect(() => {
    if (!isLoading && hasCheckedStorage) {
      if (isAuthenticated && user) {
        console.log('Storing auth state in sessionStorage');
        // Store auth state in sessionStorage
        sessionStorage.setItem('frontegg_auth', JSON.stringify({
          isAuthenticated: true,
          user: {
            email: user.email,
            name: user.name,
            id: user.id
          },
          timestamp: Date.now()
        }));
      } else if (isAuthenticated === false) {
        console.log('Clearing auth state from sessionStorage');
        // Only clear if we're sure user is not authenticated
        sessionStorage.removeItem('frontegg_auth');
      }
    }
  }, [isAuthenticated, isLoading, user, hasCheckedStorage]);

  console.log('useAuthSession state:', {
    isAuthenticated,
    isLoading,
    user: user?.email,
    hasCheckedStorage,
    initialAuthState: initialAuthState?.isAuthenticated,
    initialUser: initialAuthState?.user?.email
  });

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

  // Determine the effective authentication state
  const effectiveIsAuthenticated = hasCheckedStorage 
    ? (isAuthenticated || initialAuthState?.isAuthenticated)
    : initialAuthState?.isAuthenticated;
  
  const effectiveUser = hasCheckedStorage 
    ? (user || initialAuthState?.user)
    : initialAuthState?.user;

  // Show loading only if Frontegg is still loading AND we don't have stored auth
  const effectiveIsLoading = isLoading && !initialAuthState?.isAuthenticated;

  return {
    isAuthenticated: effectiveIsAuthenticated,
    isLoading: effectiveIsLoading,
    user: effectiveUser,
    isRedirecting,
    redirectToDashboard,
    redirectToLogin
  };
}
