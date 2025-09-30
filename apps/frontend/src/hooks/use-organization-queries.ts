import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useMemo } from 'react';
import { useApiClient, ApiResponse } from '@/lib/api-client';

// Internal API hook for Organization operations
const useOrganizationApi = () => {
    const apiClient = useApiClient();

    return useMemo(() => ({
        async getOrganizations(limit: number = 100, offset: number = 0): Promise<any[]> {
            const response = await apiClient.get('/organizations/', {
                params: { limit, offset }
            });
            // Backend returns {organizations: [], total: 0, limit: 100, offset: 0}
            return response.data.organizations || [];
        },

        async getOrganizationById(orgId: string): Promise<any> {
            const response = await apiClient.get<ApiResponse<any>>(`/organizations/${orgId}`);
            return response.data.data;
        },

        async updateOrganization(orgId: string, orgData: {
            name?: string;
            slug?: string;
            description?: string;
            settings?: any;
        }): Promise<any> {
            const response = await apiClient.put<ApiResponse<any>>(`/organizations/${orgId}`, orgData);
            return response.data.data;
        },

        async createOrganization(orgData: {
            name: string;
            slug: string;
            description?: string;
            settings?: any;
        }): Promise<any> {
            const response = await apiClient.post<ApiResponse<any>>('/organizations/', orgData);
            return response.data.data;
        }
    }), [apiClient]);
};

// Query keys
export const organizationKeys = {
    all: ["organizations"] as const,
    lists: () => [...organizationKeys.all, "list"] as const,
    list: (filters: Record<string, any>) => [...organizationKeys.lists(), filters] as const,
    details: () => [...organizationKeys.all, "detail"] as const,
    detail: (id: string) => [...organizationKeys.details(), id] as const,
};

// Get all organizations
export function useOrganizations(limit: number = 100, offset: number = 0) {
    const organizationApi = useOrganizationApi();

    return useQuery({
        queryKey: organizationKeys.list({ limit, offset }),
        queryFn: async () => {
            try {
                const result = await organizationApi.getOrganizations(limit, offset);
                // Ensure we always return an array, never undefined
                return Array.isArray(result) ? result : [];
            } catch (error) {
                console.error("Failed to fetch organizations:", error);
                // Return empty array on error to prevent undefined
                return [];
            }
        },
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

// Get organization by ID
export function useOrganization(orgId: string) {
    const organizationApi = useOrganizationApi();

    return useQuery({
        queryKey: organizationKeys.detail(orgId),
        queryFn: async () => {
            try {
                const result = await organizationApi.getOrganizationById(orgId);
                // Return the result or null if not found
                return result || null;
            } catch (error) {
                console.error("Failed to fetch organization:", error);
                // Return null on error to prevent undefined
                return null;
            }
        },
        enabled: !!orgId, // Only run query if orgId exists
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}

// Update organization mutation
export function useUpdateOrganization() {
    const queryClient = useQueryClient();
    const organizationApi = useOrganizationApi();

    return useMutation({
        mutationFn: ({ orgId, data }: { orgId: string; data: any }) =>
            organizationApi.updateOrganization(orgId, data),
        onSuccess: (updatedOrg, { orgId }) => {
            // Update the specific organization cache
            queryClient.setQueryData(organizationKeys.detail(orgId), updatedOrg);

            // Invalidate organization lists to refetch
            queryClient.invalidateQueries({ queryKey: organizationKeys.lists() });

            toast.success("Organization updated successfully");
        },
        onError: (error: any) => {
            console.error("Failed to update organization:", error);
            toast.error("Failed to update organization. Please try again.");
        },
    });
}

// Create organization mutation
export function useCreateOrganization() {
    const queryClient = useQueryClient();
    const organizationApi = useOrganizationApi();

    return useMutation({
        mutationFn: (data: any) => organizationApi.createOrganization(data),
        onSuccess: (newOrg) => {
            // Invalidate organization lists to refetch
            queryClient.invalidateQueries({ queryKey: organizationKeys.lists() });

            toast.success("Organization created successfully");
        },
        onError: (error: any) => {
            console.error("Failed to create organization:", error);
            toast.error("Failed to create organization. Please try again.");
        },
    });
}
