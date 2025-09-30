import { renderHook } from "@testing-library/react";
import { useMobile } from "../use-mobile";

// Mock window.matchMedia
const mockMatchMedia = jest.fn();
Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: mockMatchMedia,
});

describe("useMobile", () => {
    beforeEach(() => {
        mockMatchMedia.mockClear();
    });

    it("should return true for mobile screen size", () => {
        mockMatchMedia.mockReturnValue({
            matches: true,
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
        });

        const { result } = renderHook(() => useMobile());
        expect(result.current).toBe(true);
    });

    it("should return false for desktop screen size", () => {
        mockMatchMedia.mockReturnValue({
            matches: false,
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
        });

        const { result } = renderHook(() => useMobile());
        expect(result.current).toBe(false);
    });

    it("should call matchMedia with correct query", () => {
        mockMatchMedia.mockReturnValue({
            matches: false,
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
        });

        renderHook(() => useMobile());

        expect(mockMatchMedia).toHaveBeenCalledWith("(max-width: 768px)");
    });

    it("should handle SSR by returning false initially", () => {
        // Mock SSR environment
        const originalMatchMedia = window.matchMedia;
        delete (window as any).matchMedia;

        const { result } = renderHook(() => useMobile());
        expect(result.current).toBe(false);

        // Restore matchMedia
        window.matchMedia = originalMatchMedia;
    });
});
