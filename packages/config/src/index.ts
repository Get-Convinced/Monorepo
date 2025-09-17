export type AppEnv = "local" | "dev" | "prod";

export function getEnv(): AppEnv {
    const value = process.env.APP_ENV || "local";
    if (value === "dev" || value === "prod") return value;
    return "local";
}

export const config = {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
};
