import { render, screen, fireEvent } from "@testing-library/react";
import { SourcesButton } from "../sources-button";
import { ChatSource } from "@/lib/api/chat";

const mockSources: ChatSource[] = [
    {
        id: "1",
        ragie_document_id: "doc-1",
        document_name: "test-document.pdf",
        page_number: 1,
        chunk_text: "This is a test chunk.",
        relevance_score: 0.95,
    },
    {
        id: "2",
        ragie_document_id: "doc-2",
        document_name: "another-document.pdf",
        page_number: 3,
        chunk_text: "Another test chunk.",
        relevance_score: 0.87,
    },
];

describe("SourcesButton", () => {
    const mockOnClick = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();
    });

    it("renders button with correct source count", () => {
        render(<SourcesButton sources={mockSources} onClick={mockOnClick} />);

        expect(screen.getByText("2 sources")).toBeInTheDocument();
    });

    it("renders singular form for single source", () => {
        const singleSource = [mockSources[0]];

        render(<SourcesButton sources={singleSource} onClick={mockOnClick} />);

        expect(screen.getByText("1 source")).toBeInTheDocument();
    });

    it("calls onClick when clicked", () => {
        render(<SourcesButton sources={mockSources} onClick={mockOnClick} />);

        const button = screen.getByRole("button");
        fireEvent.click(button);

        expect(mockOnClick).toHaveBeenCalledTimes(1);
    });

    it("does not render when sources array is empty", () => {
        const { container } = render(<SourcesButton sources={[]} onClick={mockOnClick} />);

        expect(container.firstChild).toBeNull();
    });

    it("does not render when sources is null", () => {
        const { container } = render(<SourcesButton sources={null as any} onClick={mockOnClick} />);

        expect(container.firstChild).toBeNull();
    });
});

