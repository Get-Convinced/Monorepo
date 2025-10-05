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
        <QueryClientProvider client={queryClient}>
            {children}
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

            const { result } = renderHook(() => useOrganizations(), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(result.current.data).toEqual(mockOrganizations);
        });

        it('should handle fetch error', async () => {
            const { result } = renderHook(() => useOrganizations(), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isError).toBe(true);
            });

            expect(result.current.error).toBeDefined();
        });
    });

    describe('useOrganization', () => {
        it('should fetch single organization successfully', async () => {
            const mockOrganization = { id: '1', name: 'Org 1', slug: 'org-1' };

            const { result } = renderHook(() => useOrganization('1'), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(result.current.data).toEqual(mockOrganization);
        });

        it('should handle organization not found', async () => {
            const { result } = renderHook(() => useOrganization('999'), {
                wrapper: createWrapper()
            });

            await waitFor(() => {
                expect(result.current.isError).toBe(true);
            });

            expect(result.current.error).toBeDefined();
        });
    });

    describe('useUpdateOrganization', () => {
        it('should update organization successfully', async () => {
            const updateData = { name: 'Updated Org Name' };
            const { result } = renderHook(() => useUpdateOrganization(), {
                wrapper: createWrapper()
            });

            result.current.mutate({ id: '1', ...updateData });

            await waitFor(() => {
                expect(result.current.isSuccess).toBe(true);
            });

            expect(result.current.data).toBeDefined();
        });

        it('should handle update error', async () => {
            const { result } = renderHook(() => useUpdateOrganization(), {
                wrapper: createWrapper()
            });

            result.current.mutate({ id: '999', name: 'Invalid' });

            await waitFor(() => {
                expect(result.current.isError).toBe(true);
            });

            expect(result.current.error).toBeDefined();
        });
    });
});
