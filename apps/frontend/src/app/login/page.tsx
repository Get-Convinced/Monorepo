"use client";
import { useLoginWithRedirect } from "@frontegg/nextjs";
import Image from "next/image";
import { useRouter } from "next/navigation";

interface LoginProps {
    isHosted: boolean;
}
const Login = (props: LoginProps) => {
    const loginWithRedirect = useLoginWithRedirect();
    const router = useRouter();

    const login = () => {
        console.log("🔐 Login button clicked, isHosted:", props.isHosted);
        if (props.isHosted) {
            console.log("🔐 Using hosted login");
            loginWithRedirect();
        } else {
            console.log("🔐 Redirecting to account login");
            router.push("/account/login");
        }
    };
    return (
        <section className="flex justify-center items-center p-4 min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
            <div className="flex flex-col items-center p-8 w-full max-w-md bg-white rounded-2xl shadow-lg md:p-12">
                {/* Dummy image */}
                <Image src="https://via.placeholder.com/64" alt="login" width={64} height={64} className="mb-6 rounded-full" />

                <h1 className="mb-2 text-3xl font-semibold text-gray-800">Welcome Back!</h1>
                <p className="mb-8 text-center text-gray-500">
                    This is Frontegg&apos;s sample app that lets you experiment with authentication flows.
                </p>

                <button
                    className="py-3 w-full font-medium text-white bg-indigo-600 rounded-lg shadow-md transition duration-200 hover:bg-indigo-700"
                    onClick={login}
                >
                    Sign in
                </button>

                <p className="mt-6 text-sm text-center text-gray-400">&copy; 2025 Frontegg. All rights reserved.</p>
            </div>
        </section>
    );
};

export default Login;
