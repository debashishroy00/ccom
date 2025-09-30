#!/usr/bin/env python3
"""
CCOM CLI v5.0 - Compatibility Wrapper
Maintains backward compatibility while using refactored CLI architecture
"""

# Import the refactored CLI main
from .cli.main import main

# Re-export for backward compatibility
__all__ = ['main']

# This file maintains the original import path while using the refactored code