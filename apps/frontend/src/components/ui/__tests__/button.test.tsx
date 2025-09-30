import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../button";

describe("Button", () => {
    it("should render with default variant", () => {
        render(<Button>Click me</Button>);
        const button = screen.getByRole("button", { name: /click me/i });
        expect(button).toBeInTheDocument();
    });

    it("should render with different variants", () => {
        const { rerender } = render(<Button variant="destructive">Delete</Button>);
        expect(screen.getByRole("button")).toHaveClass("bg-destructive");

        rerender(<Button variant="outline">Outline</Button>);
        expect(screen.getByRole("button")).toHaveClass("border-input");

        rerender(<Button variant="secondary">Secondary</Button>);
        expect(screen.getByRole("button")).toHaveClass("bg-secondary");
    });

    it("should render with different sizes", () => {
        const { rerender } = render(<Button size="sm">Small</Button>);
        expect(screen.getByRole("button")).toHaveClass("h-9");

        rerender(<Button size="lg">Large</Button>);
        expect(screen.getByRole("button")).toHaveClass("h-11");

        rerender(<Button size="icon">Icon</Button>);
        expect(screen.getByRole("button")).toHaveClass("h-10 w-10");
    });

    it("should handle click events", () => {
        const handleClick = jest.fn();
        render(<Button onClick={handleClick}>Click me</Button>);

        fireEvent.click(screen.getByRole("button"));
        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it("should be disabled when disabled prop is true", () => {
        render(<Button disabled>Disabled</Button>);
        const button = screen.getByRole("button");
        expect(button).toBeDisabled();
    });

    it("should render as child when asChild is true", () => {
        render(
            <Button asChild>
                <a href="/test">Link Button</a>
            </Button>
        );
        const link = screen.getByRole("link");
        expect(link).toBeInTheDocument();
        expect(link).toHaveAttribute("href", "/test");
    });

    it("should apply custom className", () => {
        render(<Button className="custom-class">Custom</Button>);
        expect(screen.getByRole("button")).toHaveClass("custom-class");
    });
});
