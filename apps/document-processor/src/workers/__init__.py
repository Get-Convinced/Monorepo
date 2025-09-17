"""
Background workers for document processing.
"""

try:
    from .docling_document_worker import DoclingDocumentWorker
    from .ingestion_worker import IngestionWorker

    # Backward-compat alias for legacy imports
    DocumentWorker = DoclingDocumentWorker
    
    __all__ = [
        "DoclingDocumentWorker",
        "DocumentWorker",
        "IngestionWorker",
    ]
except ImportError:
    # If relative imports fail, define empty __all__
    __all__ = []
