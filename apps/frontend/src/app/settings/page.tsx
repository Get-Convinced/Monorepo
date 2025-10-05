"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UserSettingsForm } from "@/components/settings/user-settings-form";
import { OrganizationSettingsForm } from "@/components/settings/organization-settings-form";
import { User, Building2 } from "lucide-react";

function SettingsContent() {
    const searchParams = useSearchParams();
    const [activeTab, setActiveTab] = useState("profile");

    console.log("🏠 SettingsPage component mounted");

    // Handle URL tab parameter
    useEffect(() => {
        const tab = searchParams?.get("tab");
        console.log("🏠 SettingsPage: URL tab parameter:", tab);
        if (tab === "organization") {
            setActiveTab("organization");
        }
    }, [searchParams]);

    return (
        <div className="container px-4 py-6 mx-auto">
            <div className="mb-6">
                <h1 className="text-3xl font-bold">Settings</h1>
                <p className="text-muted-foreground">Manage your account and organization settings</p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="grid grid-cols-2 w-full">
                    <TabsTrigger value="profile" className="flex gap-2 items-center">
                        <User className="w-4 h-4" />
                        Profile
                    </TabsTrigger>
                    <TabsTrigger value="organization" className="flex gap-2 items-center">
                        <Building2 className="w-4 h-4" />
                        Organization
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="profile">
                    <Card>
                        <CardHeader>
                            <CardTitle>Profile Settings</CardTitle>
                            <CardDescription>Update your personal information and preferences</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <UserSettingsForm />
                        </CardContent>
                    </Card>
                </TabsContent>

                <TabsContent value="organization">
                    <Card>
                        <CardHeader>
                            <CardTitle>Organization Settings</CardTitle>
                            <CardDescription>Manage your organization details and preferences</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <OrganizationSettingsForm />
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}

export default function SettingsPage() {
    return (
        <Suspense fallback={<div>Loading settings...</div>}>
            <SettingsContent />
        </Suspense>
    );
}
