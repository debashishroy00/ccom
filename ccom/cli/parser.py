#!/usr/bin/env python3
"""
CCOM CLI Argument Parser
Extracted from cli.py to follow Single Responsibility Principle

Handles:
- Command line argument definitions
- Help text organization
- Validation rules
"""

import argparse
from typing import Optional


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create comprehensive argument parser for CCOM

    Reduced from 200+ lines in original cli.py to focused parser creation
    """
    parser = argparse.ArgumentParser(
        description="CCOM v5.0 - Claude Code Orchestrator and Memory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_examples_text()
    )

    # Add argument groups for better organization
    _add_basic_commands(parser)
    _add_memory_commands(parser)
    _add_tool_commands(parser)
    _add_context_commands(parser)
    _add_sdk_commands(parser)
    _add_advanced_options(parser)

    return parser


def _add_basic_commands(parser: argparse.ArgumentParser) -> None:
    """Add basic CCOM commands"""
    basic_group = parser.add_argument_group("basic commands", "Core CCOM functionality")

    basic_group.add_argument(
        "command",
        nargs="*",
        help="Natural language command for CCOM (e.g., 'deploy', 'quality check', 'validate principles')"
    )

    basic_group.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show comprehensive CCOM status"
    )

    basic_group.add_argument(
        "--init",
        action="store_true",
        help="Initialize CCOM in current project"
    )

    basic_group.add_argument(
        "--force",
        action="store_true",
        help="Force initialization (overwrite existing)"
    )


def _add_memory_commands(parser: argparse.ArgumentParser) -> None:
    """Add memory management commands"""
    memory_group = parser.add_argument_group("memory management", "Project memory and context")

    memory_group.add_argument(
        "--memory", "-m",
        action="store_true",
        help="Show project memory and features"
    )

    memory_group.add_argument(
        "--remember",
        type=str,
        metavar="FEATURE",
        help="Remember a feature or accomplishment"
    )

    memory_group.add_argument(
        "--forget",
        type=str,
        metavar="FEATURE",
        help="Remove a feature from memory"
    )


def _add_tool_commands(parser: argparse.ArgumentParser) -> None:
    """Add tool management commands"""
    tools_group = parser.add_argument_group("tool management", "Development tools and dependencies")

    tools_group.add_argument(
        "--install-tools",
        action="store_true",
        help="Install all required development tools"
    )

    tools_group.add_argument(
        "--check-tools",
        action="store_true",
        help="Check installation status of tools"
    )

    tools_group.add_argument(
        "--tools-status",
        action="store_true",
        help="Show comprehensive tools report"
    )


def _add_context_commands(parser: argparse.ArgumentParser) -> None:
    """Add context management commands"""
    context_group = parser.add_argument_group("context management", "Project context and analysis")

    context_group.add_argument(
        "--context",
        action="store_true",
        help="Show comprehensive project context"
    )

    context_group.add_argument(
        "--context-summary",
        type=int,
        metavar="HOURS",
        help="Show context summary for last N hours"
    )

    context_group.add_argument(
        "--universal-memory",
        action="store_true",
        help="Show universal memory (mem0-style) - all captured interactions"
    )


def _add_sdk_commands(parser: argparse.ArgumentParser) -> None:
    """Add SDK integration commands"""
    sdk_group = parser.add_argument_group("sdk integration", "Modern SDK-based agent features")

    sdk_group.add_argument(
        "--sdk-status",
        action="store_true",
        help="Show SDK integration status and performance metrics"
    )

    sdk_group.add_argument(
        "--migration-recommendations",
        action="store_true",
        help="Get recommendations for migrating to SDK agents"
    )

    sdk_group.add_argument(
        "--set-agent-mode",
        type=str,
        choices=["sdk", "markdown", "hybrid"],
        help="Set agent execution mode (sdk/markdown/hybrid)"
    )

    sdk_group.add_argument(
        "--migrate-to-sdk",
        action="store_true",
        help="Migrate to full SDK mode (when all agents ready)"
    )

    sdk_group.add_argument(
        "--force-sdk",
        action="store_true",
        help="Force SDK mode for this command"
    )

    sdk_group.add_argument(
        "--force-legacy",
        action="store_true",
        help="Force legacy mode for this command"
    )

    sdk_group.add_argument(
        "--streaming",
        action="store_true",
        help="Enable streaming output for real-time feedback"
    )


def _add_advanced_options(parser: argparse.ArgumentParser) -> None:
    """Add advanced options"""
    advanced_group = parser.add_argument_group("advanced options", "Debugging and development")

    advanced_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output for debugging"
    )

    advanced_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )

    advanced_group.add_argument(
        "--version",
        action="version",
        version="CCOM v5.0.0"
    )


def _get_examples_text() -> str:
    """Get examples text for help"""
    return """
Examples:
  ccom deploy my app                → Enterprise deployment pipeline
  ccom check security               → Comprehensive security audit
  ccom quality audit                → Code quality analysis
  ccom validate principles          → Software engineering principles validation
  ccom check tools                  → Development tools status
  ccom install tools                → Install missing development tools
  ccom run workflow quality         → Execute quality workflow
  ccom rag quality                  → RAG system validation
  ccom --status                     → Show project status
  ccom --memory                     → Show remembered features
  ccom --sdk-status                 → Show SDK integration status

Principles Validation:
  ccom validate principles          → All principles (KISS, DRY, SOLID, YAGNI)
  ccom check kiss                   → Keep It Simple validation
  ccom validate dry                 → Don't Repeat Yourself validation
  ccom check solid                  → SOLID principles validation

Workflow Management:
  ccom run workflow quality         → Quality workflow
  ccom full pipeline               → Complete development pipeline
  ccom rag quality                 → RAG system validation
  ccom aws rag                     → AWS RAG deployment

Tools Management:
  ccom check tools                 → Check tool availability
  ccom install tools               → Install missing tools
  ccom tools status                → Comprehensive tools report

SDK Migration Path:
  1. ccom --sdk-status              → Check current status
  2. ccom quality --force-sdk       → Test SDK agent
  3. ccom --migration-recommendations → Get guidance
  4. ccom --migrate-to-sdk          → Full migration

For more info: See MIGRATION_GUIDE_v5.md
"""