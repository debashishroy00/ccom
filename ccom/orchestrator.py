#!/usr/bin/env python3
"""
CCOM Orchestrator v5.0 - Compatibility Wrapper
Maintains backward compatibility while using refactored architecture
"""

# Import the refactored orchestrator
from .core.orchestrator import CCOMOrchestrator

# Re-export for backward compatibility
__all__ = ['CCOMOrchestrator']

# This file maintains the original import path while using the refactored code