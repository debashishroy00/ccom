"""
CCOM v0.3 - Claude Code Orchestrator and Memory
Enterprise-grade development automation with natural language interface
"""

__version__ = "0.3.0"
__author__ = "CCOM Development Team"
__email__ = "support@ccom.dev"

from .orchestrator import CCOMOrchestrator
from .cli import main

__all__ = ["CCOMOrchestrator", "main"]