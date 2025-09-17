"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Sun, Moon, Monitor } from "lucide-react";

type Theme = "light" | "dark" | "system";

export function ThemeToggle() {
    const [theme, setTheme] = useState<Theme>("system");
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        // Check for saved theme preference or default to system
        const savedTheme = localStorage.getItem("theme") as Theme | null;
        const initialTheme = savedTheme || "system";
        setTheme(initialTheme);
        applyTheme(initialTheme);
    }, []);

    const applyTheme = (newTheme: Theme) => {
        const root = document.documentElement;
        const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

        // Remove existing theme classes
        root.classList.remove("light", "dark");

        if (newTheme === "system") {
            // Use system preference
            if (prefersDark) {
                root.classList.add("dark");
            } else {
                root.classList.add("light");
            }
        } else {
            // Use explicit theme
            root.classList.add(newTheme);
        }

        localStorage.setItem("theme", newTheme);
    };

    const toggleTheme = () => {
        const themes: Theme[] = ["light", "dark", "system"];
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        const newTheme = themes[nextIndex];

        setTheme(newTheme);
        applyTheme(newTheme);
    };

    const getIcon = () => {
        switch (theme) {
            case "light":
                return <Sun className="h-[1.2rem] w-[1.2rem]" />;
            case "dark":
                return <Moon className="h-[1.2rem] w-[1.2rem]" />;
            case "system":
                return <Monitor className="h-[1.2rem] w-[1.2rem]" />;
        }
    };

    const getLabel = () => {
        switch (theme) {
            case "light":
                return "Light theme";
            case "dark":
                return "Dark theme";
            case "system":
                return "System theme";
        }
    };

    // Prevent hydration mismatch by not rendering until mounted
    if (!mounted) {
        return (
            <Button variant="outline" size="icon" className="relative">
                <Monitor className="h-[1.2rem] w-[1.2rem]" />
                <span className="sr-only">Toggle theme</span>
            </Button>
        );
    }

    return (
        <Button variant="outline" size="icon" onClick={toggleTheme} className="relative" title={getLabel()}>
            {getIcon()}
            <span className="sr-only">Toggle theme</span>
        </Button>
    );
}
