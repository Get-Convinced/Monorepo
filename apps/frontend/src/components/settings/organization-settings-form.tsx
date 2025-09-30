"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Building2 } from "lucide-react";
import { useAuth } from "@frontegg/nextjs";
import { useOrganization, useUpdateOrganization } from "@/hooks/use-organization-queries";

interface OrganizationFormData {
    name: string;
    slug: string;
    description?: string;
}

export function OrganizationSettingsForm() {
    const { user } = useAuth();
    const updateOrganizationMutation = useUpdateOrganization();
    const [formData, setFormData] = useState<OrganizationFormData>({
        name: "",
        slug: "",
        description: "",
    });

    // Get organization data using React Query
    const { data: organization, isLoading: loading } = useOrganization(user?.tenantId || "");
    const saving = updateOrganizationMutation.isPending;

    console.log("🏢 OrganizationSettingsForm component rendered:", {
        user: user
            ? {
                  id: user.sub,
                  name: user.name,
                  email: user.email,
                  tenantIds: user.tenantIds,
              }
            : null,
        loading,
        saving,
    });

    // Update form data when organization data loads
    useEffect(() => {
        if (organization) {
            setFormData({
                name: organization.name || "",
                slug: organization.slug || "",
                description: organization.description || "",
            });
        }
    }, [organization]);

    const handleInputChange = (field: keyof OrganizationFormData, value: string) => {
        setFormData((prev) => ({
            ...prev,
            [field]: value,
        }));

        // Auto-generate slug from name
        if (field === "name") {
            const slug = value
                .toLowerCase()
                .replace(/[^a-z0-9]+/g, "-")
                .replace(/(^-|-$)/g, "");
            setFormData((prev) => ({
                ...prev,
                slug: slug,
            }));
        }
    };

    const handleSave = async () => {
        console.log("Organization save button clicked!", { organization, formData });

        if (!user?.tenantId) {
            console.log("No organization ID found:", user?.tenantId);
            return;
        }

        if (!formData.name.trim()) {
            return;
        }

        updateOrganizationMutation.mutate({
            orgId: user.tenantId,
            data: {
                name: formData.name,
                slug: formData.slug,
                description: formData.description,
            },
        });
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center py-8">
                <Loader2 className="w-8 h-8 animate-spin" />
            </div>
        );
    }

    if (!user?.tenantId) {
        return (
            <div className="flex flex-col justify-center items-center py-8 text-center">
                <Building2 className="mb-4 w-12 h-12 text-muted-foreground" />
                <h3 className="mb-2 text-lg font-semibold">No Organization Selected</h3>
                <p className="text-muted-foreground">Please select an organization to manage its settings.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Organization Info */}
            <div className="flex items-center p-4 space-x-3 rounded-lg bg-muted/50">
                <Building2 className="w-8 h-8 text-primary" />
                <div>
                    <h3 className="font-semibold">Current Organization</h3>
                    <p className="text-sm text-muted-foreground">Managing settings for your organization</p>
                </div>
            </div>

            {/* Form Fields */}
            <div className="grid gap-4">
                <div className="grid gap-2">
                    <Label htmlFor="org-name">Organization Name</Label>
                    <Input
                        id="org-name"
                        value={formData.name}
                        onChange={(e) => handleInputChange("name", e.target.value)}
                        placeholder="Enter organization name"
                    />
                </div>

                <div className="grid gap-2">
                    <Label htmlFor="org-slug">Organization Slug</Label>
                    <Input
                        id="org-slug"
                        value={formData.slug}
                        onChange={(e) => handleInputChange("slug", e.target.value)}
                        placeholder="organization-slug"
                    />
                    <p className="text-xs text-muted-foreground">
                        This will be used in URLs and must be unique. Only lowercase letters, numbers, and hyphens are allowed.
                    </p>
                </div>

                <div className="grid gap-2">
                    <Label htmlFor="org-description">Description</Label>
                    <Textarea
                        id="org-description"
                        value={formData.description}
                        onChange={(e) => handleInputChange("description", e.target.value)}
                        placeholder="Describe your organization"
                        rows={3}
                    />
                </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end pt-4 space-x-2">
                <Button
                    variant="outline"
                    onClick={() => {
                        // Reset to original values
                        if (organization) {
                            setFormData({
                                name: organization.name || "",
                                slug: organization.slug || "",
                                description: organization.description || "",
                            });
                        }
                    }}
                    disabled={saving}
                >
                    Reset
                </Button>
                <Button onClick={handleSave} disabled={updateOrganizationMutation.isPending}>
                    {updateOrganizationMutation.isPending && <Loader2 className="mr-2 w-4 h-4 animate-spin" />}
                    Save Changes
                </Button>
            </div>
        </div>
    );
}
