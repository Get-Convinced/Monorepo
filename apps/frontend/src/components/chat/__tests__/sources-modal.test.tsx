import { render, screen, fireEvent } from "@testing-library/react";
import { SourcesModal } from "../sources-modal";
import { ChatSource } from "@/lib/api/chat";

const mockSources: ChatSource[] = [
    {
        id: "1",
        ragie_document_id: "doc-1",
        document_name: "test-document.pdf",
        page_number: 1,
        chunk_text: "This is a test chunk from the document.",
        relevance_score: 0.95,
    },
    {
        id: "2",
        ragie_document_id: "doc-2",
        document_name: "another-document.pdf",
        page_number: 3,
        chunk_text: "Another test chunk with relevant information.",
        relevance_score: 0.87,
    },
];

describe("SourcesModal", () => {
    const mockOnClose = jest.fn();
    const mockMessageContent = "This is a test response with sources.";

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it("renders modal when open", () => {
        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={mockSources} messageContent={mockMessageContent} />);

        expect(screen.getByText("Sources & Citations")).toBeInTheDocument();
        expect(screen.getByText("2 sources found:")).toBeInTheDocument();
        expect(screen.getByText("test-document.pdf")).toBeInTheDocument();
        expect(screen.getByText("another-document.pdf")).toBeInTheDocument();
    });

    it("shows page numbers when available", () => {
        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={mockSources} messageContent={mockMessageContent} />);

        expect(screen.getByText("Page 1")).toBeInTheDocument();
        expect(screen.getByText("Page 3")).toBeInTheDocument();
    });

    it("shows relevance scores", () => {
        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={mockSources} messageContent={mockMessageContent} />);

        expect(screen.getByText("95%")).toBeInTheDocument();
        expect(screen.getByText("87%")).toBeInTheDocument();
    });

    it("calls onClose when close button is clicked", () => {
        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={mockSources} messageContent={mockMessageContent} />);

        const closeButtons = screen.getAllByRole("button");
        // Click the first close button (our custom one)
        fireEvent.click(closeButtons[0]);

        expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it("displays message content preview", () => {
        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={mockSources} messageContent={mockMessageContent} />);

        expect(screen.getByText("Response:")).toBeInTheDocument();
        expect(screen.getByText(mockMessageContent)).toBeInTheDocument();
    });

    it("handles sources without page numbers", () => {
        const sourcesWithoutPages = mockSources.map((source) => ({
            ...source,
            page_number: undefined,
        }));

        render(<SourcesModal isOpen={true} onClose={mockOnClose} sources={sourcesWithoutPages} messageContent={mockMessageContent} />);

        expect(screen.queryByText("Page 1")).not.toBeInTheDocument();
        expect(screen.queryByText("Page 3")).not.toBeInTheDocument();
    });
});
