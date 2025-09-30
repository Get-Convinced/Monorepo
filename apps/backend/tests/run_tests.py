#!/usr/bin/env python3
"""
Simple Test Runner for Backend Tests

This replaces multiple complex test runners with a single, simple script.

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py --auth       # Run auth tests only
    python tests/run_tests.py --api        # Run API tests only
    python tests/run_tests.py --unit       # Run unit tests only
    python tests/run_tests.py --coverage   # Run with coverage
    python tests/run_tests.py --debug      # Run with debug output
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_pytest(test_paths, extra_args=None):
    """Run pytest with specified paths and arguments."""
    cmd = ["python", "-m", "pytest"]
    
    if extra_args:
        cmd.extend(extra_args)
    
    cmd.extend(test_paths)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Simple test runner for backend tests")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--debug", action="store_true", help="Run with debug output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Build pytest arguments
    extra_args = []
    
    if args.verbose or args.debug:
        extra_args.append("-v")
    
    if args.debug:
        extra_args.extend(["-s", "--tb=long"])
    
    if args.coverage:
        extra_args.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])
    
    # Determine which tests to run
    test_paths = []
    
    if args.auth:
        test_paths.append("tests/test_auth_sdk.py")
    elif args.api:
        test_paths.append("tests/api/")
    elif args.unit:
        test_paths.append("tests/unit/")
    else:
        # Run all tests
        test_paths.extend([
            "tests/test_auth_sdk.py",
            "tests/api/",
            "tests/unit/"
        ])
    
    print("🧪 Running Backend Tests")
    print("=" * 50)
    
    return run_pytest(test_paths, extra_args)


if __name__ == "__main__":
    sys.exit(main())
