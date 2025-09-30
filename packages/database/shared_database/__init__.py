"""
Shared Database Package for AI Knowledge Agent

This package provides shared database models, migrations, and utilities
for both the backend and document-processor applications.
"""

from .models import *
from .database import DatabaseClient, get_db_client
from .config import DatabaseConfig

__version__ = "0.1.0"
__all__ = [
    "DatabaseClient",
    "get_db_client", 
    "DatabaseConfig",
]


