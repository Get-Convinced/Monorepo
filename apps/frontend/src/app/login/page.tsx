'use client';

import { useAuth, useLoginWithRedirect } from '@frontegg/react';
import { useRouter } from 'next/navigation';
import { getSession } from "@frontegg/nextjs/pages";
import { useEffect } from 'react';

export default function Login() {
  const { isAuthenticated, isLoading, user } = useAuth(); 
  const router = useRouter();
  const loginWithRedirect = useLoginWithRedirect();
  useEffect(() => {
    if (isAuthenticated && !isLoading && user) {
      localStorage.setItem('user', JSON.stringify(user));
      router.push('/dashboard'); 
    }
  }, [isAuthenticated, isLoading, user, router]);



  if (isAuthenticated && user) {
    return (
      <div className='flex flex-col items-center justify-center min-h-screen'>
        <p className='mb-4 text-lg'>You are already logged in as {user.email}</p>
        <p className='mb-4 text-sm text-gray-600'>Redirecting to dashboard...</p>
      </div>
    );
  }


 
  

  // Show login form for unauthenticated users
  return (
    <div className='flex flex-col items-center justify-center min-h-screen'>
      <h1 className='mb-6 text-2xl font-bold'>Welcome Back</h1>
      <p className='mb-4 text-lg'>Please log in to continue</p>
      <button
        onClick={() => loginWithRedirect({})}
        className='px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors'
      >
        Login with Frontegg
      </button>
    </div>
  );
}
