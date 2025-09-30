/**
 * FIXME: These tests need to be updated for the new hook-based API approach
 * 
 * The organizationApi object has been replaced with useOrganizationApi hook.
 * These tests currently won't work and need to be refactored to properly
 * mock the hook-based approach.
 */

import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOrganizations, useOrganization, useUpdateOrganization } from '../use-organization-queries';

// Mock the organization API hook
jest.mock('../use-organization-api', () => ({
    useOrganizationApi: () => ({
        getOrganizations: jest.fn(),
        getOrganizationById: jest.fn(),
        updateOrganization: jest.fn(),
    })
}));

// Mock sonner toast
jest.mock('sonner', () => ({
    toast: {
        success: jest.fn(),
        error: jest.fn(),
    }
}));

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
    });

    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client= { queryClient } >
        { children }
        </QueryClientProvider>
    );
};

describe('useOrganizationQueries', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('useOrganizations', () => {
        it('should fetch organizations successfully', async () => {
            const mockOrganizations = [
                { id: '1', name: 'Org 1', slug: 'org-1' },
                { id: '2', name: 'Org 2', slug: 'org-2' }
            ];
            // TODO: Fix this mock to work with the new hook-based approach
            // (organizationApi.getOrganizations as jest.Mock).mockResolvedValue(mockOrganizations);

            const { result } = renderHook(() => useOrganizations(), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(result.current.data).toEqual(mockOrganizations);
            expect(organizationApi.getOrganizations).toHaveBeenCalledTimes(1);
        });

        it('should handle fetch error', async () => {
            const error = new Error('Failed to fetch organizations');
            (organizationApi.getOrganizations as jest.Mock).mockRejectedValue(error);

            const { result } = renderHook(() => useOrganizations(), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isError).toBe(true);
            });

            expect(result.current.error).toBe(error);
        });
    });

    describe('useOrganization', () => {
        it('should fetch single organization successfully', async () => {
            const mockOrganization = { id: '1', name: 'Test Org', slug: 'test-org' };
            (organizationApi.getOrganizationById as jest.Mock).mockResolvedValue(mockOrganization);

            const { result } = renderHook(() => useOrganization('1'), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(result.current.data).toEqual(mockOrganization);
            expect(organizationApi.getOrganizationById).toHaveBeenCalledWith('1');
        });

        it('should not fetch when orgId is empty', () => {
            const { result } = renderHook(() => useOrganization(''), {
                wrapper: createWrapper()
            });

            expect(result.current.isLoading).toBe(false);
            expect(organizationApi.getOrganizationById).not.toHaveBeenCalled();
        });
    });

    describe('useUpdateOrganization', () => {
        it('should update organization successfully', async () => {
            const mockUpdatedOrg = { id: '1', name: 'Updated Org', slug: 'updated-org' };
            (organizationApi.updateOrganization as jest.Mock).mockResolvedValue(mockUpdatedOrg);

            const { result } = renderHook(() => useUpdateOrganization(), {
                wrapper: createWrapper()
            });

            const updateData = { name: 'Updated Org' };
            result.current.mutate({ orgId: '1', data: updateData });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(organizationApi.updateOrganization).toHaveBeenCalledWith('1', updateData);
        });

        it('should handle update error', async () => {
            const error = new Error('Failed to update organization');
            (organizationApi.updateOrganization as jest.Mock).mockRejectedValue(error);

            const { result } = renderHook(() => useUpdateOrganization(), {
                wrapper: createWrapper()
            });

            const updateData = { name: 'Updated Org' };
            result.current.mutate({ orgId: '1', data: updateData });

            await waitFor(() => {
                expect(result.current.isError).toBe(true);
            });

            expect(result.current.error).toBe(error);
        });
    });
});
