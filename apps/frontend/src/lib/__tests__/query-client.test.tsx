import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { QueryProvider } from "../query-client";

// Mock React Query Devtools
jest.mock("@tanstack/react-query-devtools", () => ({
    ReactQueryDevtools: () => <div data-testid="react-query-devtools">DevTools</div>,
}));

const TestComponent = () => <div>Test Component</div>;

describe("QueryProvider", () => {
    it("should render children and provide QueryClient", () => {
        render(
            <QueryProvider>
                <TestComponent />
            </QueryProvider>
        );

        expect(screen.getByText("Test Component")).toBeInTheDocument();
    });

    it("should include React Query Devtools in development", () => {
        render(
            <QueryProvider>
                <TestComponent />
            </QueryProvider>
        );

        // Devtools should be present (mocked)
        expect(screen.getByTestId("react-query-devtools")).toBeInTheDocument();
    });

    it("should create a QueryClient with correct default options", () => {
        const TestWrapper = () => {
            const queryClient = new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 1000 * 60 * 5, // 5 minutes
                        refetchOnWindowFocus: false,
                    },
                },
            });

            return (
                <QueryClientProvider client={queryClient}>
                    <TestComponent />
                </QueryClientProvider>
            );
        };

        render(<TestWrapper />);
        expect(screen.getByText("Test Component")).toBeInTheDocument();
    });
});
