// app/page.tsx
'use client';

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.push("/login"); 
    }, 1000);
    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh",
      gap: "20px",
    }}>
      <h1>Welcome to My App</h1>
      <p>Redirecting to login...</p>
      <div className="loader" />
    </div>
  );
}
