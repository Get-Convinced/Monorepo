/**
 * Integration tests for Settings API client functions
 * 
 * Tests the API client integration for settings-related functionality:
 * - User profile update API calls
 * - Organization update API calls
 * - Error handling and response parsing
 * - Authentication header injection
 */
import axios from 'axios';
import { userApi, organizationApi } from '../api-client';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('Settings API Integration', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    describe('User API', () => {
        describe('updateUser', () => {
            const userId = 'user-123';
            const updateData = {
                name: 'Updated Name',
                profile_data: {
                    phone: '+1234567890',
                    description: 'Updated description'
                },
                avatar_url: 'https://example.com/new-avatar.jpg'
            };

            const mockResponse = {
                data: {
                    success: true,
                    data: {
                        id: userId,
                        name: 'Updated Name',
                        email: 'user@example.com',
                        profile_data: {
                            phone: '+1234567890',
                            description: 'Updated description'
                        },
                        avatar_url: 'https://example.com/new-avatar.jpg',
                        updated_at: '2024-01-15T12:00:00Z'
                    },
                    meta: {
                        timestamp: '2024-01-15T12:00:00Z',
                        requestId: 'req-456'
                    }
                }
            };

            it('should make PUT request to correct endpoint with user data', async () => {
                mockedAxios.put.mockResolvedValue(mockResponse);

                const result = await userApi.updateUser(userId, updateData);

                expect(mockedAxios.put).toHaveBeenCalledWith(
                    `/users/${userId}`,
                    updateData
                );
                expect(result).toEqual(mockResponse.data.data);
            });

            it('should handle successful user update response', async () => {
                mockedAxios.put.mockResolvedValue(mockResponse);

                const result = await userApi.updateUser(userId, updateData);

                expect(result.id).toBe(userId);
                expect(result.name).toBe('Updated Name');
                expect(result.profile_data.phone).toBe('+1234567890');
            });

            it('should handle API error responses', async () => {
                const errorResponse = {
                    response: {
                        status: 400,
                        data: {
                            success: false,
                            error: {
                                code: 'VALIDATION_ERROR',
                                message: 'Invalid user data',
                                details: {
                                    name: ['Name is required']
                                }
                            }
                        }
                    }
                };

                mockedAxios.put.mockRejectedValue(errorResponse);

                await expect(userApi.updateUser(userId, updateData)).rejects.toEqual(errorResponse);
            });

            it('should handle network errors', async () => {
                const networkError = new Error('Network Error');
                mockedAxios.put.mockRejectedValue(networkError);

                await expect(userApi.updateUser(userId, updateData)).rejects.toThrow('Network Error');
            });

            it('should handle partial update data', async () => {
                const partialUpdate = { name: 'Only Name Update' };
                mockedAxios.put.mockResolvedValue(mockResponse);

                await userApi.updateUser(userId, partialUpdate);

                expect(mockedAxios.put).toHaveBeenCalledWith(
                    `/users/${userId}`,
                    partialUpdate
                );
            });
        });

        describe('getCurrentUser', () => {
            it('should make GET request to /users/me endpoint', async () => {
                const mockResponse = {
                    data: {
                        success: true,
                        data: {
                            id: 'user-123',
                            name: 'Current User',
                            email: 'current@example.com'
                        }
                    }
                };

                mockedAxios.get.mockResolvedValue(mockResponse);

                const result = await userApi.getCurrentUser();

                expect(mockedAxios.get).toHaveBeenCalledWith('/users/me');
                expect(result).toEqual(mockResponse.data.data);
            });
        });
    });

    describe('Organization API', () => {
        describe('updateOrganization', () => {
            const orgId = 'org-456';
            const updateData = {
                name: 'Updated Organization',
                slug: 'updated-organization',
                description: 'Updated organization description'
            };

            const mockResponse = {
                data: {
                    success: true,
                    data: {
                        id: orgId,
                        name: 'Updated Organization',
                        slug: 'updated-organization',
                        description: 'Updated organization description',
                        updated_at: '2024-01-15T12:00:00Z'
                    },
                    meta: {
                        timestamp: '2024-01-15T12:00:00Z',
                        requestId: 'req-789'
                    }
                }
            };

            it('should make PUT request to correct endpoint with organization data', async () => {
                mockedAxios.put.mockResolvedValue(mockResponse);

                const result = await organizationApi.updateOrganization(orgId, updateData);

                expect(mockedAxios.put).toHaveBeenCalledWith(
                    `/organizations/${orgId}`,
                    updateData
                );
                expect(result).toEqual(mockResponse.data.data);
            });

            it('should handle successful organization update response', async () => {
                mockedAxios.put.mockResolvedValue(mockResponse);

                const result = await organizationApi.updateOrganization(orgId, updateData);

                expect(result.id).toBe(orgId);
                expect(result.name).toBe('Updated Organization');
                expect(result.slug).toBe('updated-organization');
                expect(result.description).toBe('Updated organization description');
            });

            it('should handle organization not found error', async () => {
                const notFoundError = {
                    response: {
                        status: 404,
                        data: {
                            success: false,
                            error: {
                                code: 'ORGANIZATION_NOT_FOUND',
                                message: 'Organization not found'
                            }
                        }
                    }
                };

                mockedAxios.put.mockRejectedValue(notFoundError);

                await expect(organizationApi.updateOrganization(orgId, updateData)).rejects.toEqual(notFoundError);
            });

            it('should handle authorization errors', async () => {
                const authError = {
                    response: {
                        status: 403,
                        data: {
                            success: false,
                            error: {
                                code: 'INSUFFICIENT_PERMISSIONS',
                                message: 'You do not have permission to update this organization'
                            }
                        }
                    }
                };

                mockedAxios.put.mockRejectedValue(authError);

                await expect(organizationApi.updateOrganization(orgId, updateData)).rejects.toEqual(authError);
            });

            it('should handle partial organization update', async () => {
                const partialUpdate = { name: 'Only Name Update' };
                mockedAxios.put.mockResolvedValue(mockResponse);

                await organizationApi.updateOrganization(orgId, partialUpdate);

                expect(mockedAxios.put).toHaveBeenCalledWith(
                    `/organizations/${orgId}`,
                    partialUpdate
                );
            });
        });

        describe('getOrganizationById', () => {
            const orgId = 'org-456';

            it('should make GET request to correct endpoint', async () => {
                const mockResponse = {
                    data: {
                        success: true,
                        data: {
                            id: orgId,
                            name: 'Test Organization',
                            slug: 'test-organization',
                            description: 'Test description'
                        }
                    }
                };

                mockedAxios.get.mockResolvedValue(mockResponse);

                const result = await organizationApi.getOrganizationById(orgId);

                expect(mockedAxios.get).toHaveBeenCalledWith(`/organizations/${orgId}`);
                expect(result).toEqual(mockResponse.data.data);
            });

            it('should handle organization not found', async () => {
                const notFoundError = {
                    response: {
                        status: 404,
                        data: {
                            success: false,
                            error: {
                                code: 'ORGANIZATION_NOT_FOUND',
                                message: 'Organization not found'
                            }
                        }
                    }
                };

                mockedAxios.get.mockRejectedValue(notFoundError);

                await expect(organizationApi.getOrganizationById(orgId)).rejects.toEqual(notFoundError);
            });
        });

        describe('getOrganizations', () => {
            it('should make GET request with default pagination', async () => {
                const mockResponse = {
                    data: {
                        success: true,
                        data: [
                            { id: 'org-1', name: 'Organization 1' },
                            { id: 'org-2', name: 'Organization 2' }
                        ]
                    }
                };

                mockedAxios.get.mockResolvedValue(mockResponse);

                const result = await organizationApi.getOrganizations();

                expect(mockedAxios.get).toHaveBeenCalledWith('/organizations/', {
                    params: { limit: 100, offset: 0 }
                });
                expect(result).toEqual(mockResponse.data.data);
            });

            it('should make GET request with custom pagination', async () => {
                const mockResponse = {
                    data: {
                        success: true,
                        data: []
                    }
                };

                mockedAxios.get.mockResolvedValue(mockResponse);

                await organizationApi.getOrganizations(50, 25);

                expect(mockedAxios.get).toHaveBeenCalledWith('/organizations/', {
                    params: { limit: 50, offset: 25 }
                });
            });
        });
    });

    describe('Error Response Handling', () => {
        it('should handle malformed API responses', async () => {
            const malformedResponse = {
                data: {
                    // Missing success field and data field
                    message: 'Malformed response'
                }
            };

            mockedAxios.put.mockResolvedValue(malformedResponse);

            // This should handle gracefully or throw appropriate error
            await expect(userApi.updateUser('user-123', { name: 'Test' })).rejects.toThrow();
        });

        it('should handle server errors (5xx)', async () => {
            const serverError = {
                response: {
                    status: 500,
                    data: {
                        success: false,
                        error: {
                            code: 'INTERNAL_SERVER_ERROR',
                            message: 'Internal server error'
                        }
                    }
                }
            };

            mockedAxios.put.mockRejectedValue(serverError);

            await expect(userApi.updateUser('user-123', { name: 'Test' })).rejects.toEqual(serverError);
        });

        it('should handle timeout errors', async () => {
            const timeoutError = {
                code: 'ECONNABORTED',
                message: 'timeout of 30000ms exceeded'
            };

            mockedAxios.put.mockRejectedValue(timeoutError);

            await expect(userApi.updateUser('user-123', { name: 'Test' })).rejects.toEqual(timeoutError);
        });
    });
});
