export type Organization = {
    id: string;
    name: string;
    createdAt: string;
};

export type DocumentMetadata = {
    id: string;
    organizationId: string;
    title: string;
    source: string;
    createdAt: string;
};

export type ChatMessage = {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    createdAt: string;
};
