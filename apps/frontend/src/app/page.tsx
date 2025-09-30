import { getAppUserSession } from "@frontegg/nextjs/app";
import { redirect } from "next/navigation";
import Login from "./login/page";

export default async function Home() {
    const userSession = await getAppUserSession();
    if (userSession) {
        redirect("/dashboard");
    }

    const isHosted = process.env.FRONTEGG_HOSTED_LOGIN === "true";

    return (
        <main>
            <Login isHosted={isHosted} />
        </main>
    );
}
