#!/usr/bin/env python3
"""
CCOM CLI Main Entry Point
Streamlined main function following Single Responsibility Principle

Handles:
- Argument parsing
- Command routing
- Error handling
- Exit codes
"""

import sys
import logging
from pathlib import Path
from typing import Optional, List

from .parser import create_argument_parser
from .handlers import (
    TraditionalHandler,
    MemoryHandler,
    ToolsHandler,
    ContextHandler,
    SDKHandler
)
from ..core.orchestrator import CCOMOrchestrator
from ..utils import Display, ErrorHandler


def main(args: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point

    Reduced from 400+ lines in original to focused coordination

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Parse arguments
        parser = create_argument_parser()
        parsed_args = parser.parse_args(args)

        # Set up logging
        _setup_logging(parsed_args.verbose)

        # Initialize orchestrator
        orchestrator = CCOMOrchestrator()

        # Route to appropriate handler
        success = _route_command(orchestrator, parsed_args)

        return 0 if success else 1

    except KeyboardInterrupt:
        Display.warning("Operation cancelled by user")
        return 1
    except Exception as e:
        Display.error(f"Unexpected error: {e}")
        logging.getLogger(__name__).exception("Unexpected error in main")
        return 1


def _setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stderr)]
    )


def _route_command(orchestrator: CCOMOrchestrator, args) -> bool:
    """
    Route command to appropriate handler

    Args:
        orchestrator: CCOM orchestrator instance
        args: Parsed command line arguments

    Returns:
        True if command executed successfully
    """
    # Initialize handlers
    traditional_handler = TraditionalHandler(orchestrator)
    memory_handler = MemoryHandler(orchestrator)
    tools_handler = ToolsHandler(orchestrator)
    context_handler = ContextHandler(orchestrator)
    sdk_handler = SDKHandler(orchestrator)

    # Route to handlers in order of priority
    handlers = [
        traditional_handler,
        memory_handler,
        tools_handler,
        context_handler,
        sdk_handler
    ]

    for handler in handlers:
        if handler.can_handle(args):
            return handler.handle(args)

    # If no handler can process, show help
    Display.error("No valid command specified")
    _show_quick_help()
    return False


def _show_quick_help() -> None:
    """Show quick help for common commands"""
    Display.section("Quick Help")
    Display.command_help({
        'ccom "deploy"': "Run deployment workflow",
        'ccom "quality"': "Run quality checks",
        'ccom --status': "Show project status",
        'ccom --memory': "Show project memory",
        'ccom --sdk-status': "Show SDK status",
        'ccom --help': "Full help"
    })


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)