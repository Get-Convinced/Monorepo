"use client";
import { useLoginWithRedirect } from "@frontegg/nextjs";
import { getAppUserSession } from "@frontegg/nextjs/app";
import Image from "next/image";
import { redirect, useRouter } from "next/navigation";

interface LoginProps {
  isHosted: boolean;
}
const Login = async(props: LoginProps) => {
  // const loginWithRedirect = useLoginWithRedirect();

  const userSession = await getAppUserSession();
  if (!userSession) {
    redirect("/account/login");
  }
  const router = useRouter();
  // const login = () => {
  //   if (props.isHosted) {
  //     loginWithRedirect();
  //   } else {
  //     router.push("/account/login");
  //   }
  // };
  return (
    <section className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 p-4">
      <div className="bg-white shadow-lg rounded-2xl p-8 md:p-12 max-w-md w-full flex flex-col items-center">
        {/* Dummy image */}
        <Image
          src="https://via.placeholder.com/64"
          alt="login"
          width={64}
          height={64}
          className="mb-6 rounded-full"
        />

        <h1 className="text-3xl font-semibold text-gray-800 mb-2">
          Welcome Back!
        </h1>
        <p className="text-gray-500 text-center mb-8">
          This is Frontegg&apos;s sample app that lets you experiment with
          authentication flows.
        </p>

        <button
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-3 rounded-lg shadow-md transition duration-200"
          // onClick={login}
        >
          Sign in
        </button>

        <p className="text-gray-400 text-sm mt-6 text-center">
          &copy; 2025 Frontegg. All rights reserved.
        </p>
      </div>
    </section>
  );
};

export default Login;
