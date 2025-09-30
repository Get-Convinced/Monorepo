import "@testing-library/jest-dom";

// Mock Next.js router
jest.mock("next/navigation", () => ({
    useRouter: () => ({
        push: jest.fn(),
        replace: jest.fn(),
        prefetch: jest.fn(),
        back: jest.fn(),
        forward: jest.fn(),
        refresh: jest.fn(),
    }),
    useSearchParams: () => ({
        get: jest.fn(),
    }),
    usePathname: () => "/test-path",
}));

// Mock Frontegg hooks
jest.mock("@frontegg/nextjs", () => ({
    useAuthUser: jest.fn(() => ({
        id: "test-user",
        name: "Test User",
        email: "test@example.com",
        accessToken: "test-token",
        tenantId: "test-tenant",
    })),
    useLoginWithRedirect: jest.fn(() => jest.fn()),
    useAuth: jest.fn(() => ({
        logout: jest.fn(),
    })),
    FronteggProvider: ({ children }) => children,
}));

// Mock sonner toast
jest.mock("sonner", () => ({
    toast: {
        success: jest.fn(),
        error: jest.fn(),
        info: jest.fn(),
        warning: jest.fn(),
    },
}));

// Global test utilities
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}));

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(), // deprecated
        removeListener: jest.fn(), // deprecated
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    removeItem: jest.fn(),
    clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;
