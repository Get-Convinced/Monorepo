import "./globals.css";
import { FronteggAppProvider } from "@frontegg/nextjs/app";

export const metadata = { title: "AI Knowledge Agent", description: "MVP" };

export default async function RootLayout({ children }: { children: React.ReactNode }) {
    const app = await FronteggAppProvider({ children });
    return (
        <html lang="en">
            <body>{app}</body>
        </html>
    );
}
