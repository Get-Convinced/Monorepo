/**
 * End-to-End tests for Settings functionality
 * 
 * Tests complete user workflows for settings management:
 * - Navigation to settings page
 * - User profile editing workflow
 * - Organization settings editing workflow
 * - Form validation and error handling
 * - Success feedback and data persistence
 */
import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
    test.beforeEach(async ({ page }) => {
        // Mock authentication - in real tests, you'd handle actual auth
        await page.goto('/login');

        // Mock successful login
        await page.evaluate(() => {
            window.localStorage.setItem('auth-token', 'mock-token');
            (window as any).__FRONTEGG_USER__ = {
                id: 'user-123',
                name: 'Test User',
                email: 'test@example.com',
                accessToken: 'mock-access-token',
                tenantId: 'org-456'
            };
        });

        await page.goto('/dashboard');
        await expect(page).toHaveURL('/dashboard');
    });

    test.describe('Navigation', () => {
        test('should navigate to settings page from sidebar', async ({ page }) => {
            // Click settings link in sidebar
            await page.click('[data-testid="settings-link"]');

            await expect(page).toHaveURL('/settings');
            await expect(page.locator('h1')).toContainText('Settings');
        });

        test('should show profile tab by default', async ({ page }) => {
            await page.goto('/settings');

            await expect(page.locator('[data-state="active"]')).toContainText('Profile');
            await expect(page.locator('input[value="Test User"]')).toBeVisible();
        });

        test('should navigate to organization tab via URL parameter', async ({ page }) => {
            await page.goto('/settings?tab=organization');

            await expect(page.locator('[data-state="active"]')).toContainText('Organization');
        });

        test('should switch between tabs', async ({ page }) => {
            await page.goto('/settings');

            // Click organization tab
            await page.click('text=Organization');
            await expect(page.locator('[data-state="active"]')).toContainText('Organization');

            // Click profile tab
            await page.click('text=Profile');
            await expect(page.locator('[data-state="active"]')).toContainText('Profile');
        });
    });

    test.describe('User Profile Settings', () => {
        test.beforeEach(async ({ page }) => {
            await page.goto('/settings');
        });

        test('should display current user information', async ({ page }) => {
            await expect(page.locator('input[value="Test User"]')).toBeVisible();
            await expect(page.locator('input[value="test@example.com"]')).toBeVisible();
            await expect(page.locator('input[value="test@example.com"]')).toBeDisabled();
        });

        test('should update user name successfully', async ({ page }) => {
            // Mock API response
            await page.route('**/api/users/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: {
                                id: 'user-123',
                                name: 'Updated User Name',
                                email: 'test@example.com'
                            }
                        })
                    });
                }
            });

            // Update name field
            await page.fill('input[value="Test User"]', 'Updated User Name');

            // Click save
            await page.click('text=Save Changes');

            // Check for success message
            await expect(page.locator('text=Profile updated successfully')).toBeVisible();
        });

        test('should update phone number successfully', async ({ page }) => {
            // Mock API response
            await page.route('**/api/users/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: {
                                id: 'user-123',
                                name: 'Test User',
                                email: 'test@example.com',
                                profile_data: {
                                    phone: '+1234567890'
                                }
                            }
                        })
                    });
                }
            });

            // Update phone field
            await page.fill('input[placeholder="Enter your phone number"]', '+1234567890');

            // Click save
            await page.click('text=Save Changes');

            // Check for success message
            await expect(page.locator('text=Profile updated successfully')).toBeVisible();
        });

        test('should handle save errors gracefully', async ({ page }) => {
            // Mock API error response
            await page.route('**/api/users/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 400,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: false,
                            error: {
                                code: 'VALIDATION_ERROR',
                                message: 'Invalid user data'
                            }
                        })
                    });
                }
            });

            // Try to save
            await page.click('text=Save Changes');

            // Check for error message
            await expect(page.locator('text=Failed to update profile')).toBeVisible();
        });

        test('should reset form to original values', async ({ page }) => {
            // Change form values
            await page.fill('input[value="Test User"]', 'Changed Name');
            await page.fill('input[placeholder="Enter your phone number"]', '+9876543210');

            // Click reset
            await page.click('text=Reset');

            // Check values are reset
            await expect(page.locator('input[value="Test User"]')).toBeVisible();
            await expect(page.locator('input[placeholder="Enter your phone number"]')).toHaveValue('');
        });

        test('should show loading state during save', async ({ page }) => {
            // Mock slow API response
            await page.route('**/api/users/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: { id: 'user-123', name: 'Test User' }
                        })
                    });
                }
            });

            // Click save
            await page.click('text=Save Changes');

            // Check for loading state
            await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
            await expect(page.locator('input[value="Test User"]')).toBeDisabled();
        });
    });

    test.describe('Organization Settings', () => {
        test.beforeEach(async ({ page }) => {
            await page.goto('/settings?tab=organization');

            // Mock organization data loading
            await page.route('**/api/organizations/*', async (route) => {
                if (route.request().method() === 'GET') {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: {
                                id: 'org-456',
                                name: 'Test Organization',
                                slug: 'test-organization',
                                description: 'A test organization'
                            }
                        })
                    });
                }
            });
        });

        test('should display current organization information', async ({ page }) => {
            await expect(page.locator('input[value="Test Organization"]')).toBeVisible();
            await expect(page.locator('input[value="test-organization"]')).toBeVisible();
            await expect(page.locator('textarea')).toContainText('A test organization');
        });

        test('should auto-generate slug from organization name', async ({ page }) => {
            // Change organization name
            await page.fill('input[value="Test Organization"]', 'My New Company Inc.');

            // Check that slug is auto-generated
            await expect(page.locator('input[value="my-new-company-inc"]')).toBeVisible();
        });

        test('should update organization successfully', async ({ page }) => {
            // Mock API response
            await page.route('**/api/organizations/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: {
                                id: 'org-456',
                                name: 'Updated Organization',
                                slug: 'updated-organization',
                                description: 'Updated description'
                            }
                        })
                    });
                }
            });

            // Update organization fields
            await page.fill('input[value="Test Organization"]', 'Updated Organization');
            await page.fill('textarea', 'Updated description');

            // Click save
            await page.click('text=Save Changes');

            // Check for success message
            await expect(page.locator('text=Organization updated successfully')).toBeVisible();
        });

        test('should validate required organization name', async ({ page }) => {
            // Clear organization name
            await page.fill('input[value="Test Organization"]', '');

            // Try to save
            await page.click('text=Save Changes');

            // Check for validation error
            await expect(page.locator('text=Organization name is required')).toBeVisible();
        });

        test('should handle organization update errors', async ({ page }) => {
            // Mock API error response
            await page.route('**/api/organizations/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 403,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: false,
                            error: {
                                code: 'INSUFFICIENT_PERMISSIONS',
                                message: 'You do not have permission to update this organization'
                            }
                        })
                    });
                }
            });

            // Try to save
            await page.click('text=Save Changes');

            // Check for error message
            await expect(page.locator('text=Failed to update organization')).toBeVisible();
        });
    });

    test.describe('Profile Edit Modal', () => {
        test('should open profile edit modal from user avatar', async ({ page }) => {
            await page.goto('/dashboard');

            // Click user avatar/profile
            await page.click('[data-testid="user-profile"]');
            await page.click('text=Edit Profile');

            // Check modal is open
            await expect(page.locator('[role="dialog"]')).toBeVisible();
            await expect(page.locator('text=Edit Profile')).toBeVisible();
        });

        test('should update profile via modal', async ({ page }) => {
            await page.goto('/dashboard');

            // Mock API response
            await page.route('**/api/users/*', async (route) => {
                if (route.request().method() === 'PUT') {
                    await route.fulfill({
                        status: 200,
                        contentType: 'application/json',
                        body: JSON.stringify({
                            success: true,
                            data: {
                                id: 'user-123',
                                name: 'Updated via Modal',
                                email: 'test@example.com'
                            }
                        })
                    });
                }
            });

            // Open modal
            await page.click('[data-testid="user-profile"]');
            await page.click('text=Edit Profile');

            // Update name
            await page.fill('input[value="Test User"]', 'Updated via Modal');

            // Save changes
            await page.click('text=Save Changes');

            // Check for success and modal closes
            await expect(page.locator('text=Profile updated successfully')).toBeVisible();
            await expect(page.locator('[role="dialog"]')).not.toBeVisible();
        });
    });

    test.describe('Organization Selector', () => {
        test('should navigate to organization settings from selector', async ({ page }) => {
            await page.goto('/dashboard');

            // Click organization selector
            await page.click('[data-testid="organization-selector"]');

            // Click organization settings
            await page.click('text=Organization Settings');

            // Should navigate to organization settings tab
            await expect(page).toHaveURL('/settings?tab=organization');
        });

        test('should switch organizations', async ({ page }) => {
            // Mock organizations list
            await page.route('**/api/organizations', async (route) => {
                await route.fulfill({
                    status: 200,
                    contentType: 'application/json',
                    body: JSON.stringify({
                        success: true,
                        data: [
                            { id: 'org-456', name: 'Current Org', role: 'Owner' },
                            { id: 'org-789', name: 'Other Org', role: 'Member' }
                        ]
                    })
                });
            });

            await page.goto('/dashboard');

            // Click organization selector
            await page.click('[data-testid="organization-selector"]');

            // Click different organization
            await page.click('text=Other Org');

            // Should switch organization context
            await expect(page.locator('text=Other Org')).toBeVisible();
        });
    });
});
