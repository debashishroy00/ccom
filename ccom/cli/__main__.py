#!/usr/bin/env python3
"""
CCOM CLI Package Entry Point
Enables execution with: python -m ccom.cli
"""

from .main import main

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)