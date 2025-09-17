"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

interface MarkdownRendererProps {
    content: string;
    className?: string;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
    const isInverted = className.includes("prose-invert");

    return (
        <div className={`prose prose-sm max-w-none ${className}`}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                    // Customize heading styles
                    h1: ({ children }) => (
                        <h1 className={`text-lg font-bold mb-2 ${isInverted ? "text-primary-foreground" : "text-foreground"}`}>
                            {children}
                        </h1>
                    ),
                    h2: ({ children }) => (
                        <h2 className={`text-base font-semibold mb-2 ${isInverted ? "text-primary-foreground" : "text-foreground"}`}>
                            {children}
                        </h2>
                    ),
                    h3: ({ children }) => (
                        <h3 className={`text-sm font-semibold mb-1 ${isInverted ? "text-primary-foreground" : "text-foreground"}`}>
                            {children}
                        </h3>
                    ),
                    // Customize paragraph styles
                    p: ({ children }) => (
                        <p className={`mb-2 text-sm leading-relaxed ${isInverted ? "text-primary-foreground" : "text-foreground"}`}>
                            {children}
                        </p>
                    ),
                    // Customize list styles
                    ul: ({ children }) => (
                        <ul
                            className={`list-disc list-inside mb-2 space-y-1 text-sm ${
                                isInverted ? "text-primary-foreground" : "text-foreground"
                            }`}
                        >
                            {children}
                        </ul>
                    ),
                    ol: ({ children }) => (
                        <ol
                            className={`list-decimal list-inside mb-2 space-y-1 text-sm ${
                                isInverted ? "text-primary-foreground" : "text-foreground"
                            }`}
                        >
                            {children}
                        </ol>
                    ),
                    li: ({ children }) => (
                        <li className={`text-sm ${isInverted ? "text-primary-foreground" : "text-foreground"}`}>{children}</li>
                    ),
                    // Customize code styles
                    code: ({ children, className }) => {
                        const isInline = !className;
                        if (isInline) {
                            return (
                                <code
                                    className={`px-1 py-0.5 rounded text-xs font-mono ${
                                        isInverted ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-foreground"
                                    }`}
                                >
                                    {children}
                                </code>
                            );
                        }
                        return <code className={className}>{children}</code>;
                    },
                    pre: ({ children }) => (
                        <pre
                            className={`p-3 rounded-lg overflow-x-auto text-xs font-mono mb-2 ${
                                isInverted ? "bg-primary-foreground/20 text-primary-foreground" : "bg-muted text-foreground"
                            }`}
                        >
                            {children}
                        </pre>
                    ),
                    // Customize blockquote styles
                    blockquote: ({ children }) => (
                        <blockquote
                            className={`border-l-4 pl-4 italic text-sm mb-2 ${
                                isInverted
                                    ? "border-primary-foreground/30 text-primary-foreground/80"
                                    : "border-muted-foreground text-muted-foreground"
                            }`}
                        >
                            {children}
                        </blockquote>
                    ),
                    // Customize link styles
                    a: ({ children, href }) => (
                        <a
                            href={href}
                            className={`hover:underline text-sm ${
                                isInverted
                                    ? "text-primary-foreground hover:text-primary-foreground/80"
                                    : "text-primary hover:text-primary/80"
                            }`}
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            {children}
                        </a>
                    ),
                    // Customize table styles
                    table: ({ children }) => (
                        <div className="overflow-x-auto mb-2">
                            <table
                                className={`min-w-full border-collapse border text-xs ${
                                    isInverted ? "border-primary-foreground/30" : "border-border"
                                }`}
                            >
                                {children}
                            </table>
                        </div>
                    ),
                    th: ({ children }) => (
                        <th
                            className={`border px-2 py-1 text-left font-semibold ${
                                isInverted
                                    ? "border-primary-foreground/30 bg-primary-foreground/20 text-primary-foreground"
                                    : "border-border bg-muted text-foreground"
                            }`}
                        >
                            {children}
                        </th>
                    ),
                    td: ({ children }) => (
                        <td
                            className={`border px-2 py-1 ${
                                isInverted ? "border-primary-foreground/30 text-primary-foreground" : "border-border text-foreground"
                            }`}
                        >
                            {children}
                        </td>
                    ),
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
