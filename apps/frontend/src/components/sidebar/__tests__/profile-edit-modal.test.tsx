/**
 * Unit tests for ProfileEditModal component
 *
 * Tests the updated profile edit modal functionality including:
 * - Modal rendering and user data loading
 * - Form interactions and validation
 * - API integration for profile updates
 * - Loading states and error handling
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { ProfileEditModal } from "../profile-edit-modal";
import { useAuth } from "@frontegg/nextjs";
// FIXME: Update to use new hook-based API approach
// import { userApi } from "@/lib/api-client";

// Mock dependencies
jest.mock("@frontegg/nextjs");
jest.mock("@/lib/api-client");
jest.mock("sonner");

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockUserApi = userApi as jest.Mocked<typeof userApi>;
const mockToast = toast as jest.Mocked<typeof toast>;

describe("ProfileEditModal", () => {
    const mockUser = {
        id: "user-123",
        name: "John Doe",
        email: "john.doe@example.com",
        avatar_url: "https://example.com/avatar.jpg",
        profile_data: {
            phone: "+1234567890",
            description: "Software Engineer",
        },
        isAuthenticated: true,
    };

    const mockRefreshUser = jest.fn();
    const mockOnOpenChange = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();

        mockUseAuth.mockReturnValue({
            user: mockUser,
            refreshUser: mockRefreshUser,
            isAuthenticated: true,
            isLoading: false,
            error: null,
            login: jest.fn(),
            logout: jest.fn(),
            switchOrganization: jest.fn(),
        });
    });

    describe("Modal Rendering", () => {
        it("should not render when modal is closed", () => {
            render(<ProfileEditModal open={false} onOpenChange={mockOnOpenChange} />);

            expect(screen.queryByText("Edit Profile")).not.toBeInTheDocument();
        });

        it("should render modal when open is true", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByText("Edit Profile")).toBeInTheDocument();
            expect(screen.getByText("Save Changes")).toBeInTheDocument();
            expect(screen.getByText("Cancel")).toBeInTheDocument();
        });

        it("should load user data when modal opens", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByDisplayValue("John Doe")).toBeInTheDocument();
            expect(screen.getByDisplayValue("+1234567890")).toBeInTheDocument();
            expect(screen.getByDisplayValue("Software Engineer")).toBeInTheDocument();
        });

        it("should show user avatar with initials", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const avatar = screen.getByText("JD");
            expect(avatar).toBeInTheDocument();
        });

        it("should handle user without profile data", () => {
            const userWithoutProfile = {
                id: "user-456",
                name: "Jane Smith",
                email: "jane@example.com",
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

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByDisplayValue("Jane Smith")).toBeInTheDocument();
            // Phone and description should be empty
            expect(screen.getByPlaceholderText("Enter your phone number")).toHaveValue("");
            expect(screen.getByPlaceholderText("Tell us about yourself")).toHaveValue("");
        });
    });

    describe("Form Interactions", () => {
        it("should update name field when user types", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Updated Name" } });

            expect(screen.getByDisplayValue("Updated Name")).toBeInTheDocument();
        });

        it("should update phone field when user types", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const phoneInput = screen.getByDisplayValue("+1234567890");
            fireEvent.change(phoneInput, { target: { value: "+0987654321" } });

            expect(screen.getByDisplayValue("+0987654321")).toBeInTheDocument();
        });

        it("should update description field when user types", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const descriptionInput = screen.getByDisplayValue("Software Engineer");
            fireEvent.change(descriptionInput, { target: { value: "Senior Developer" } });

            expect(screen.getByDisplayValue("Senior Developer")).toBeInTheDocument();
        });

        it("should close modal when cancel button is clicked", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const cancelButton = screen.getByText("Cancel");
            fireEvent.click(cancelButton);

            expect(mockOnOpenChange).toHaveBeenCalledWith(false);
        });
    });

    describe("Form Submission", () => {
        it("should call userApi.updateUser with correct data on save", async () => {
            mockUserApi.updateUser.mockResolvedValue(mockUser);

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            // Update form fields
            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Updated Name" } });

            const phoneInput = screen.getByDisplayValue("+1234567890");
            fireEvent.change(phoneInput, { target: { value: "+0987654321" } });

            const descriptionInput = screen.getByDisplayValue("Software Engineer");
            fireEvent.change(descriptionInput, { target: { value: "Senior Developer" } });

            // Submit form
            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockUserApi.updateUser).toHaveBeenCalledWith("user-123", {
                    name: "Updated Name",
                    profile_data: {
                        phone: "+1234567890",
                        description: "Software Engineer",
                        phone: "+0987654321",
                        description: "Senior Developer",
                    },
                });
            });
        });

        it("should show success toast and close modal on successful save", async () => {
            mockUserApi.updateUser.mockResolvedValue(mockUser);

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockToast.success).toHaveBeenCalledWith("Profile updated successfully");
                expect(mockRefreshUser).toHaveBeenCalled();
                expect(mockOnOpenChange).toHaveBeenCalledWith(false);
            });
        });

        it("should show error toast on save failure", async () => {
            const error = new Error("Update failed");
            mockUserApi.updateUser.mockRejectedValue(error);

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("Failed to update profile. Please try again.");
                expect(mockOnOpenChange).not.toHaveBeenCalledWith(false); // Modal should stay open
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

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

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

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            // Check that fields are disabled during save
            const nameInput = screen.getByDisplayValue("John Doe");
            expect(nameInput).toBeDisabled();

            const phoneInput = screen.getByDisplayValue("+1234567890");
            expect(phoneInput).toBeDisabled();

            const descriptionInput = screen.getByDisplayValue("Software Engineer");
            expect(descriptionInput).toBeDisabled();

            const cancelButton = screen.getByText("Cancel");
            expect(cancelButton).toBeDisabled();
        });

        it("should show loading spinner in save button while saving", async () => {
            mockUserApi.updateUser.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            const saveButton = screen.getByText("Save Changes");
            fireEvent.click(saveButton);

            // Should show loading spinner
            expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
        });
    });

    describe("Data Loading on Modal Open", () => {
        it("should reload user data when modal reopens", () => {
            const { rerender } = render(<ProfileEditModal open={false} onOpenChange={mockOnOpenChange} />);

            // Update user data
            const updatedUser = {
                ...mockUser,
                name: "Updated User",
                profile_data: {
                    phone: "+9999999999",
                    description: "Updated description",
                },
                isAuthenticated: true,
            };

            mockUseAuth.mockReturnValue({
                user: updatedUser,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            // Reopen modal
            rerender(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByDisplayValue("Updated User")).toBeInTheDocument();
            expect(screen.getByDisplayValue("+9999999999")).toBeInTheDocument();
            expect(screen.getByDisplayValue("Updated description")).toBeInTheDocument();
        });

        it("should not reload data when modal stays open", () => {
            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            // Change form values
            const nameInput = screen.getByDisplayValue("John Doe");
            fireEvent.change(nameInput, { target: { value: "Changed Name" } });

            // User data changes but modal stays open - should not reload
            const updatedUser = { ...mockUser, name: "Different Name", isAuthenticated: true };
            mockUseAuth.mockReturnValue({
                user: updatedUser,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            // Form should still show user's changes, not the updated user data
            expect(screen.getByDisplayValue("Changed Name")).toBeInTheDocument();
        });
    });

    describe("Edge Cases", () => {
        it("should handle empty user data gracefully", () => {
            const emptyUser = {
                id: "user-empty",
                name: "",
                email: "empty@example.com",
                profile_data: {},
                isAuthenticated: true,
            };

            mockUseAuth.mockReturnValue({
                user: emptyUser,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByDisplayValue("")).toBeInTheDocument(); // Empty name
            expect(screen.getByPlaceholderText("Enter your phone number")).toHaveValue("");
            expect(screen.getByPlaceholderText("Tell us about yourself")).toHaveValue("");
        });

        it("should handle user with null profile_data", () => {
            const userWithNullProfile = {
                id: "user-null",
                name: "Null Profile User",
                email: "null@example.com",
                profile_data: null,
                isAuthenticated: true,
            };

            mockUseAuth.mockReturnValue({
                user: userWithNullProfile,
                refreshUser: mockRefreshUser,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<ProfileEditModal open={true} onOpenChange={mockOnOpenChange} />);

            expect(screen.getByDisplayValue("Null Profile User")).toBeInTheDocument();
            expect(screen.getByPlaceholderText("Enter your phone number")).toHaveValue("");
            expect(screen.getByPlaceholderText("Tell us about yourself")).toHaveValue("");
        });
    });
});
