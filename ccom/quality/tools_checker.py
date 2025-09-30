#!/usr/bin/env python3
"""
Tools Checker - Lightweight Tool Management
Replaces the 1,060-line tools_manager.py with focused functionality

Handles:
- Basic tool availability checking
- Simple installation verification
- Essential tools only
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..utils import SubprocessRunner, ErrorHandler, Display


class ToolsChecker:
    """
    Lightweight tool availability checker

    Replaces the oversized ToolsManager (1,060 lines) with essential functionality only
    """

    # Essential tools only - no bloat
    ESSENTIAL_TOOLS = {
        "node": ["node", "npm"],
        "python": ["python", "pip"],
        "git": ["git"],
        "quality": ["eslint", "prettier"] # Only if package.json exists
    }

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.subprocess_runner = SubprocessRunner()

    def check_essential_tools(self) -> Dict[str, bool]:
        """Check availability of essential tools only"""
        results = {}

        # Always check core tools
        for tool in ["node", "npm", "python", "pip", "git"]:
            results[tool] = self._check_tool_available(tool)

        # Check quality tools only if package.json exists
        if (self.project_root / "package.json").exists():
            for tool in ["eslint", "prettier"]:
                results[tool] = self._check_tool_available(tool)

        return results

    def _check_tool_available(self, tool: str) -> bool:
        """Check if a single tool is available"""
        return self.subprocess_runner.check_command_exists(tool)

    def get_tool_status_summary(self) -> Dict[str, str]:
        """Get simple tool status summary"""
        tools = self.check_essential_tools()
        summary = {}

        for tool, available in tools.items():
            if available:
                version = self._get_tool_version(tool)
                summary[tool] = f"✅ {version}" if version else "✅ Available"
            else:
                summary[tool] = "❌ Not found"

        return summary

    def _get_tool_version(self, tool: str) -> Optional[str]:
        """Get tool version (simple implementation)"""
        try:
            # Common version commands
            version_args = {
                "node": ["--version"],
                "npm": ["--version"],
                "python": ["--version"],
                "pip": ["--version"],
                "git": ["--version"],
                "eslint": ["--version"],
                "prettier": ["--version"]
            }

            if tool not in version_args:
                return None

            result = self.subprocess_runner.run_command(
                [tool] + version_args[tool],
                timeout=5
            )

            if result.returncode == 0:
                # Extract version from output
                output = result.stdout.strip()
                if tool == "python":
                    # "Python 3.11.0" -> "3.11.0"
                    return output.split()[-1] if "Python" in output else output
                elif tool == "git":
                    # "git version 2.41.0" -> "2.41.0"
                    return output.split()[-1] if "version" in output else output
                else:
                    # Most tools just output version number
                    return output.replace("v", "")

        except Exception:
            pass

        return None

    def display_tools_status(self) -> None:
        """Display tools status using centralized display"""
        Display.section("🔧 Development Tools Status")

        summary = self.get_tool_status_summary()
        if summary:
            Display.key_value_table(summary)
        else:
            Display.info("No tools found")

    def install_missing_tools(self) -> bool:
        """Basic tool installation (placeholder)"""
        Display.info("Tool installation: Use your system package manager")
        Display.bullet_list([
            "Node.js: Download from https://nodejs.org",
            "Python: Download from https://python.org",
            "Git: Download from https://git-scm.com"
        ])

        # Check if package.json exists for quality tools
        if (self.project_root / "package.json").exists():
            Display.info("For quality tools, run: npm install eslint prettier --save-dev")

        return True  # Always return success for simplicity