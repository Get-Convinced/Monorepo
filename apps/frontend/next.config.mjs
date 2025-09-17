/** @type {import('next').NextConfig} */
const backendBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8082";

const nextConfig = {
    experimental: {
        typedRoutes: true,
        externalDir: true,
    },
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: `${backendBase}/:path*`,
            },
        ];
    },
};

export default nextConfig;
