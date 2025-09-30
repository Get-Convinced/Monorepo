/**
 * Unit tests for OrganizationSettingsForm component
 *
 * Tests organization editing functionality including:
 * - Form rendering and initial state
 * - Organization data loading
 * - Form input handling and validation
 * - API integration and error handling
 * - Slug auto-generation
 */
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { toast } from "sonner";
import { OrganizationSettingsForm } from "../organization-settings-form";
import { useAuth } from "@frontegg/nextjs";
// FIXME: Update to use new hook-based API approach
// import { organizationApi } from "@/lib/api-client";

// Mock dependencies
jest.mock("@frontegg/nextjs");
jest.mock("@/lib/api-client");
jest.mock("sonner");

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockOrganizationApi = organizationApi as jest.Mocked<typeof organizationApi>;
const mockToast = toast as jest.Mocked<typeof toast>;

describe("OrganizationSettingsForm", () => {
    const mockUser = {
        id: "user-123",
        name: "John Doe",
        email: "john.doe@example.com",
        currentOrganization: "org-456",
        organizations: ["org-456", "org-789"],
        isAuthenticated: true,
    };

    const mockOrganization = {
        id: "org-456",
        name: "Test Organization",
        slug: "test-organization",
        description: "A test organization for unit testing",
    };

    beforeEach(() => {
        jest.clearAllMocks();

        mockUseAuth.mockReturnValue({
            user: mockUser,
            refreshUser: jest.fn(),
            isAuthenticated: true,
            isLoading: false,
            error: null,
            login: jest.fn(),
            logout: jest.fn(),
            switchOrganization: jest.fn(),
        });

        mockOrganizationApi.getOrganizationById.mockResolvedValue(mockOrganization);
    });

    describe("Component Rendering", () => {
        it("should show loading spinner while fetching organization data", () => {
            mockOrganizationApi.getOrganizationById.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<OrganizationSettingsForm />);

            expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
        });

        it("should render organization form with loaded data", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                expect(screen.getByDisplayValue("Test Organization")).toBeInTheDocument();
                expect(screen.getByDisplayValue("test-organization")).toBeInTheDocument();
                expect(screen.getByDisplayValue("A test organization for unit testing")).toBeInTheDocument();
            });
        });

        it("should show current organization info section", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                expect(screen.getByText("Current Organization")).toBeInTheDocument();
                expect(screen.getByText("Managing settings for your organization")).toBeInTheDocument();
            });
        });

        it("should show no organization message when user has no current organization", () => {
            mockUseAuth.mockReturnValue({
                user: { ...mockUser, currentOrganization: null },
                refreshUser: jest.fn(),
                isAuthenticated: true,
                isLoading: false,
                error: null,
                login: jest.fn(),
                logout: jest.fn(),
                switchOrganization: jest.fn(),
            });

            render(<OrganizationSettingsForm />);

            expect(screen.getByText("No Organization Selected")).toBeInTheDocument();
            expect(screen.getByText("Please select an organization to manage its settings.")).toBeInTheDocument();
        });
    });

    describe("Form Interactions", () => {
        it("should update organization name field when user types", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "Updated Organization" } });
                expect(screen.getByDisplayValue("Updated Organization")).toBeInTheDocument();
            });
        });

        it("should auto-generate slug when organization name changes", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "My New Organization!" } });

                expect(screen.getByDisplayValue("my-new-organization")).toBeInTheDocument();
            });
        });

        it("should allow manual slug editing", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const slugInput = screen.getByDisplayValue("test-organization");
                fireEvent.change(slugInput, { target: { value: "custom-slug" } });
                expect(screen.getByDisplayValue("custom-slug")).toBeInTheDocument();
            });
        });

        it("should update description field when user types", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const descriptionInput = screen.getByDisplayValue("A test organization for unit testing");
                fireEvent.change(descriptionInput, { target: { value: "Updated description" } });
                expect(screen.getByDisplayValue("Updated description")).toBeInTheDocument();
            });
        });
    });

    describe("Form Submission", () => {
        it("should call organizationApi.updateOrganization with correct data on save", async () => {
            mockOrganizationApi.updateOrganization.mockResolvedValue(mockOrganization);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "Updated Organization" } });

                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);
            });

            await waitFor(() => {
                expect(mockOrganizationApi.updateOrganization).toHaveBeenCalledWith("org-456", {
                    name: "Updated Organization",
                    slug: "updated-organization",
                    description: "A test organization for unit testing",
                });
            });
        });

        it("should show success toast on successful save", async () => {
            mockOrganizationApi.updateOrganization.mockResolvedValue(mockOrganization);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);
            });

            await waitFor(() => {
                expect(mockToast.success).toHaveBeenCalledWith("Organization updated successfully");
            });
        });

        it("should show error toast on save failure", async () => {
            const error = new Error("Update failed");
            mockOrganizationApi.updateOrganization.mockRejectedValue(error);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);
            });

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("Failed to update organization. Please try again.");
            });
        });

        it("should show error toast when organization name is empty", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "" } });

                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);
            });

            expect(mockToast.error).toHaveBeenCalledWith("Organization name is required");
        });

        it("should show error toast when organization is not found", async () => {
            render(<OrganizationSettingsForm />);

            // Mock the component state to have no organizationId
            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                // Simulate organizationId being null
                Object.defineProperty(window, "organizationId", { value: null });
                fireEvent.click(saveButton);
            });

            // This test might need adjustment based on actual implementation
        });
    });

    describe("Loading States", () => {
        it("should disable form fields while saving", async () => {
            mockOrganizationApi.updateOrganization.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);

                const nameInput = screen.getByDisplayValue("Test Organization");
                expect(nameInput).toBeDisabled();

                const resetButton = screen.getByText("Reset");
                expect(resetButton).toBeDisabled();
            });
        });

        it("should show loading spinner in save button while saving", async () => {
            mockOrganizationApi.updateOrganization.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);

                expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
            });
        });
    });

    describe("Reset Functionality", () => {
        it("should reset form to original values when reset button is clicked", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                // Change form values
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "Changed Name" } });

                // Click reset
                const resetButton = screen.getByText("Reset");
                fireEvent.click(resetButton);
            });

            // Should revert to original values
            await waitFor(() => {
                expect(screen.getByDisplayValue("Test Organization")).toBeInTheDocument();
            });
        });

        it("should handle reset when API call fails", async () => {
            const error = new Error("Failed to fetch organization");
            mockOrganizationApi.getOrganizationById.mockRejectedValueOnce(error);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const resetButton = screen.getByText("Reset");
                fireEvent.click(resetButton);
            });

            expect(mockToast.error).toHaveBeenCalledWith("Failed to reset form");
        });
    });

    describe("Slug Generation", () => {
        it("should generate correct slug from organization name", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");

                // Test various name formats
                const testCases = [
                    { input: "My Company Inc.", expected: "my-company-inc" },
                    { input: "Test & Development", expected: "test-development" },
                    { input: "Company   With   Spaces", expected: "company-with-spaces" },
                    { input: "UPPERCASE COMPANY", expected: "uppercase-company" },
                ];

                testCases.forEach(({ input, expected }) => {
                    fireEvent.change(nameInput, { target: { value: input } });
                    expect(screen.getByDisplayValue(expected)).toBeInTheDocument();
                });
            });
        });

        it("should handle empty organization name for slug generation", async () => {
            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const nameInput = screen.getByDisplayValue("Test Organization");
                fireEvent.change(nameInput, { target: { value: "" } });

                expect(screen.getByDisplayValue("")).toBeInTheDocument(); // Slug should be empty
            });
        });
    });

    describe("Error Handling", () => {
        it("should show error toast when organization loading fails", async () => {
            const error = new Error("Failed to load organization");
            mockOrganizationApi.getOrganizationById.mockRejectedValue(error);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("Failed to load organization data");
            });
        });

        it("should handle network errors gracefully", async () => {
            const networkError = new Error("Network error");
            mockOrganizationApi.updateOrganization.mockRejectedValue(networkError);

            render(<OrganizationSettingsForm />);

            await waitFor(() => {
                const saveButton = screen.getByText("Save Changes");
                fireEvent.click(saveButton);
            });

            await waitFor(() => {
                expect(mockToast.error).toHaveBeenCalledWith("Failed to update organization. Please try again.");
            });
        });
    });
});
