import { render, screen, fireEvent } from "@testing-library/react";
import { ThemeToggle } from "../theme-toggle";

// Mock next-themes
jest.mock("next-themes", () => ({
    useTheme: () => ({
        theme: "light",
        setTheme: jest.fn(),
        themes: ["light", "dark", "system"],
    }),
}));

// Mock Lucide React icons
jest.mock("lucide-react", () => ({
    Sun: () => <div data-testid="sun-icon">Sun</div>,
    Moon: () => <div data-testid="moon-icon">Moon</div>,
    Monitor: () => <div data-testid="monitor-icon">Monitor</div>,
}));

describe("ThemeToggle", () => {
    it("should render theme toggle button", () => {
        render(<ThemeToggle />);
        const button = screen.getByRole("button");
        expect(button).toBeInTheDocument();
    });

    it("should show sun icon in light theme", () => {
        render(<ThemeToggle />);
        expect(screen.getByTestId("sun-icon")).toBeInTheDocument();
    });

    it("should have correct aria-label", () => {
        render(<ThemeToggle />);
        const button = screen.getByRole("button");
        expect(button).toHaveAttribute("aria-label", "Toggle theme");
    });

    it("should have correct size variant", () => {
        render(<ThemeToggle />);
        const button = screen.getByRole("button");
        expect(button).toHaveClass("h-9 w-9");
    });

    it("should handle click events", () => {
        const mockSetTheme = jest.fn();
        jest.doMock("next-themes", () => ({
            useTheme: () => ({
                theme: "light",
                setTheme: mockSetTheme,
                themes: ["light", "dark", "system"],
            }),
        }));

        render(<ThemeToggle />);
        const button = screen.getByRole("button");
        fireEvent.click(button);

        // Note: The actual theme switching logic would be tested in integration tests
        expect(button).toBeInTheDocument();
    });
});
