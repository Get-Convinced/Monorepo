"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UserSettingsForm } from "@/components/settings/user-settings-form";
import { OrganizationSettingsForm } from "@/components/settings/organization-settings-form";
import { User, Building2 } from "lucide-react";

export default function SettingsPage() {
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
        <div className="container mx-auto py-6 px-4">
            <div className="mb-6">
                <h1 className="text-3xl font-bold">Settings</h1>
                <p className="text-muted-foreground">Manage your account and organization settings</p>
            </div>

            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="profile" className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        Profile
                    </TabsTrigger>
                    <TabsTrigger value="organization" className="flex items-center gap-2">
                        <Building2 className="h-4 w-4" />
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
