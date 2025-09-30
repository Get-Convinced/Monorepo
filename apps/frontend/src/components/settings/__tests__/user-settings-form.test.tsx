/**
 * Unit tests for UserSettingsForm component
 *
 * FIXME: These tests need to be updated for the new hook-based API approach
 * The userApi object has been replaced with useUserApi hook.
 *
 * Tests user profile editing functionality including:
 * - Form rendering and initial state
 * - User input handling
 * - API integration and error handling
 * - Loading states and form validation
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { UserSettingsForm } from "../user-settings-form";
import { useAuth } from "@frontegg/nextjs";
// FIXME: Update to use new hook-based API approach
// import { userApi } from "@/lib/api-client";

// Mock dependencies
jest.mock("@frontegg/nextjs");
// jest.mock("@/lib/api-client"); // TODO: Update to mock useUserApi hook
jest.mock("@/hooks/use-user-api");
jest.mock("sonner");

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
// TODO: Fix this mock for the new hook-based approach
// const mockUserApi = userApi as jest.Mocked<typeof userApi>;
const mockToast = toast as jest.Mocked<typeof toast>;

describe("UserSettingsForm", () => {
    const mockUser = {
        sub: "user-123",
        name: "John Doe",
        email: "john.doe@example.com",
        profilePictureUrl: "https://example.com/avatar.jpg",
        metadata: {
            phone: "+1234567890",
            description: "Test user description",
        },
    };

    const mockRefreshUser = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();

        mockUseAuth.mockReturnValue({
            user: mockUser,
            isAuthenticated: true,
            isLoading: false,
            error: null,
        });
    });

    describe("Component Rendering", () => {
        it("should render user settings form with user data", () => {
            render(<UserSettingsForm />);

            expect(screen.getByDisplayValue("John Doe")).toBeInTheDocument();
            expect(screen.getByDisplayValue("john.doe@example.com")).toBeInTheDocument();
            expect(screen.getByDisplayValue("+1234567890")).toBeInTheDocument();
            expect(screen.getByText("Save Changes")).toBeInTheDocument();
        });

        it("should show avatar with user initials", () => {
            render(<UserSettingsForm />);

            const avatar = screen.getByText("JD");
            expect(avatar).toBeInTheDocument();
        });

        it("should disable email field", () => {
            render(<UserSettingsForm />);

            const emailInput = screen.getByDisplayValue("john.doe@example.com");
            expect(emailInput).toBeDisabled();
        });

        it("should show email disclaimer text", () => {
            render(<UserSettingsForm />);

            expect(screen.getByText(/Email address is managed by your authentication provider/)).toBeInTheDocument();
        });
    });

    describe("Form Interactions", () => {
        it("should update name field when user types", () => {
            render(<UserSettingsForm />);

            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Jane Doe" } });

            expect(screen.getByDisplayValue("Jane Doe")).toBeInTheDocument();
        });

        it("should update phone field when user types", () => {
            render(<UserSettingsForm />);

            const phoneInput = screen.getByDisplayValue("+1234567890");
            fireEvent.change(phoneInput, { target: { value: "+0987654321" } });

            expect(screen.getByDisplayValue("+0987654321")).toBeInTheDocument();
        });

        it("should reset form when reset button is clicked", () => {
            render(<UserSettingsForm />);

            // Change form values
            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Changed Name" } });

            // Click reset
            const resetButton = screen.getByText("Reset");
            fireEvent.click(resetButton);

            // Should revert to original values
            expect(screen.getByDisplayValue("John Doe")).toBeInTheDocument();
        });
    });

    describe("Form Submission", () => {
        it("should call userApi.updateUser with correct data on save", async () => {
            mockUserApi.updateUser.mockResolvedValue(mockUser);

            render(<UserSettingsForm />);

            // Change form values
            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Updated Name" } });

            const phoneInput = screen.getByDisplayValue("+1234567890");
            fireEvent.change(phoneInput, { target: { value: "+0987654321" } });

            // Submit form
            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockUserApi.updateUser).toHaveBeenCalledWith("user-123", {
                    name: "Updated Name",
                    profile_data: {
                        phone: "+1234567890",
                        description: "Test user description",
                        phone: "+0987654321",
                    },
                    avatar_url: "https://example.com/avatar.jpg",
                });
            });
        });

        it("should show success toast on successful save", async () => {
            mockUserApi.updateUser.mockResolvedValue(mockUser);

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockToast.success).toHaveBeenCalledWith("Profile updated successfully");
            });
        });

        it("should refresh user data after successful save", async () => {
            mockUserApi.updateUser.mockResolvedValue(mockUser);

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockRefreshUser).toHaveBeenCalled();
            });
        });

        it("should show error toast on save failure", async () => {
            const error = new Error("Update failed");
            mockUserApi.updateUser.mockRejectedValue(error);

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("Failed to update profile. Please try again.");
            });
        });

        it("should show error toast when user is not found", async () => {
            mockUseAuth.mockReturnValue({
                user: null,
                refreshUser: mockRefreshUser,
                isAuthenticated: false,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("User not found");
            });
        });
    });

    describe("Loading States", () => {
        it("should disable form fields while saving", async () => {
            mockUserApi.updateUser.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            // Check that fields are disabled during save
            const nameInput = screen.getByDisplayValue("John Doe");
            expect(nameInput).toBeDisabled();

            const resetButton = screen.getByText("Reset");
            expect(resetButton).toBeDisabled();
        });

        it("should show loading spinner in save button while saving", async () => {
            mockUserApi.updateUser.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<UserSettingsForm />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            // Should show loading spinner
            expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
        });
    });

    describe("Avatar Upload", () => {
        it("should show avatar upload placeholder message", () => {
            render(<UserSettingsForm />);

            const fileInput = screen.getByLabelText(/avatar-upload/i);
            const file = new File(["avatar"], "avatar.png", { type: "image/png" });

            fireEvent.change(fileInput, { target: { files: [file] } });

            expect(mockToast.info).toHaveBeenCalledWith("Avatar upload functionality coming soon");
        });
    });

    describe("Edge Cases", () => {
        it("should handle user with minimal data", () => {
            const minimalUser = {
                id: "user-456",
                name: "",
                email: "minimal@example.com",
                profile_data: {},
                isAuthenticated: true,
            };

            mockUseAuth.mockReturnValue({
                user: minimalUser,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<UserSettingsForm />);

            expect(screen.getByDisplayValue("")).toBeInTheDocument(); // Empty name
            expect(screen.getByDisplayValue("minimal@example.com")).toBeInTheDocument();
        });

        it("should handle user without profile_data", () => {
            const userWithoutProfile = {
                id: "user-789",
                name: "No Profile User",
                email: "noprofile@example.com",
                isAuthenticated: true,
            };

            mockUseAuth.mockReturnValue({
                user: userWithoutProfile,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<UserSettingsForm />);

            expect(screen.getByDisplayValue("No Profile User")).toBeInTheDocument();
            expect(screen.getByDisplayValue("noprofile@example.com")).toBeInTheDocument();
        });
    });
});
