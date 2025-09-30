import { render, screen, fireEvent } from "@testing-library/react";
import { Input } from "../input";

describe("Input", () => {
    it("should render with default props", () => {
        render(<Input />);
        const input = screen.getByRole("textbox");
        expect(input).toBeInTheDocument();
        expect(input).toHaveClass("flex h-10 w-full rounded-md border border-input bg-background px-3 py-2");
    });

    it("should render with custom placeholder", () => {
        render(<Input placeholder="Enter your name" />);
        expect(screen.getByPlaceholderText("Enter your name")).toBeInTheDocument();
    });

    it("should handle value changes", () => {
        const handleChange = jest.fn();
        render(<Input onChange={handleChange} />);

        const input = screen.getByRole("textbox");
        fireEvent.change(input, { target: { value: "test value" } });

        expect(handleChange).toHaveBeenCalledTimes(1);
        expect(input).toHaveValue("test value");
    });

    it("should be disabled when disabled prop is true", () => {
        render(<Input disabled />);
        const input = screen.getByRole("textbox");
        expect(input).toBeDisabled();
    });

    it("should render with different types", () => {
        const { rerender } = render(<Input type="email" />);
        expect(screen.getByRole("textbox")).toHaveAttribute("type", "email");

        rerender(<Input type="password" />);
        expect(screen.getByDisplayValue("")).toHaveAttribute("type", "password");
    });

    it("should apply custom className", () => {
        render(<Input className="custom-class" />);
        expect(screen.getByRole("textbox")).toHaveClass("custom-class");
    });

    it("should forward ref correctly", () => {
        const ref = { current: null };
        render(<Input ref={ref} />);
        expect(ref.current).toBeInstanceOf(HTMLInputElement);
    });
});
