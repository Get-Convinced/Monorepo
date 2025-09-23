"""
Setup script for shared database package.
"""

from setuptools import setup, find_packages

setup(
    name="shared-database",
    version="0.1.0",
    description="Shared database models and utilities for AI Knowledge Agent",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10,<3.13",
    install_requires=[
        "sqlalchemy==2.0.23",
        "alembic==1.12.1",
        "psycopg2-binary==2.9.9",
        "asyncpg==0.29.0",
        "pydantic==2.9.2",
        "python-dotenv==1.0.1",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.4",
            "pytest-asyncio==0.21.1",
            "pytest-mock==3.12.0",
            "black==23.9.1",
            "isort==5.12.0",
            "mypy==1.6.1",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)


