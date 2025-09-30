#!/usr/bin/env python3
"""
Quality Enforcer - Lightweight Quality Validation
Replaces the 1,176-line validators.py with focused functionality

Handles:
- Essential quality checks only
- Integration with existing SDK agents
- Simple, maintainable validation
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils import SubprocessRunner, ErrorHandler, Display
from .tools_checker import ToolsChecker


class QualityEnforcer:
    """
    Lightweight quality enforcement

    Replaces the oversized ValidationOrchestrator (1,176 lines) with essential functionality
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.subprocess_runner = SubprocessRunner()
        self.tools_checker = ToolsChecker(project_root)

    def run_quality_checks(self, auto_fix: bool = True) -> Dict[str, Any]:
        """Run essential quality checks"""
        results = {
            "overall_success": True,
            "checks": {}
        }

        # 1. Tool availability check
        Display.progress("Checking development tools...")
        tools_available = self._check_tools()
        results["checks"]["tools"] = tools_available

        # 2. ESLint check (if available)
        if tools_available.get("eslint", False):
            Display.progress("Running ESLint...")
            eslint_result = self._run_eslint(auto_fix)
            results["checks"]["eslint"] = eslint_result
            if not eslint_result["success"]:
                results["overall_success"] = False

        # 3. Prettier check (if available)
        if tools_available.get("prettier", False):
            Display.progress("Running Prettier...")
            prettier_result = self._run_prettier(auto_fix)
            results["checks"]["prettier"] = prettier_result
            if not prettier_result["success"]:
                results["overall_success"] = False

        # 4. File size check (simple validation)
        Display.progress("Checking file sizes...")
        size_check = self._check_file_sizes()
        results["checks"]["file_sizes"] = size_check
        if not size_check["success"]:
            results["overall_success"] = False

        return results

    def _check_tools(self) -> Dict[str, bool]:
        """Check tool availability"""
        return self.tools_checker.check_essential_tools()

    def _run_eslint(self, auto_fix: bool) -> Dict[str, Any]:
        """Run ESLint with optional auto-fix"""
        try:
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return {"success": True, "message": "No package.json - skipping ESLint", "skipped": True}

            # Try npm run lint first
            result = self.subprocess_runner.run_npm_command("lint", timeout=60)

            if result.returncode == 0:
                return {"success": True, "message": "✅ ESLint: No issues found"}
            else:
                # Try auto-fix if enabled
                if auto_fix:
                    fix_result = self.subprocess_runner.run_npm_command("lint", ["--fix"], timeout=120)
                    if fix_result.returncode == 0:
                        return {"success": True, "message": "🔧 ESLint: Issues auto-fixed"}

                return {
                    "success": False,
                    "message": "⚠️ ESLint: Issues found requiring manual attention",
                    "details": result.stderr[:200] if result.stderr else "See ESLint output"
                }

        except Exception as e:
            return {"success": False, "message": f"❌ ESLint execution failed: {str(e)}"}

    def _run_prettier(self, auto_fix: bool) -> Dict[str, Any]:
        """Run Prettier formatting"""
        try:
            # Check if prettier is configured
            if not self.tools_checker._check_tool_available("prettier"):
                return {"success": True, "message": "Prettier not available - skipping", "skipped": True}

            # Try direct prettier
            check_result = self.subprocess_runner.run_command(
                ["npx", "prettier", "--check", "."],
                timeout=60,
                shell=True
            )

            if check_result.returncode == 0:
                return {"success": True, "message": "✅ Prettier: Code formatting is consistent"}
            else:
                # Try auto-fix if enabled
                if auto_fix:
                    fix_result = self.subprocess_runner.run_command(
                        ["npx", "prettier", "--write", "."],
                        timeout=120,
                        shell=True
                    )
                    if fix_result.returncode == 0:
                        return {"success": True, "message": "🔧 Prettier: Code formatted automatically"}

                return {"success": False, "message": "⚠️ Prettier: Formatting issues found"}

        except Exception as e:
            return {"success": False, "message": f"❌ Prettier execution failed: {str(e)}"}

    def _check_file_sizes(self) -> Dict[str, Any]:
        """Check for oversized files (CCOM's own rule!)"""
        try:
            oversized_files = []
            python_files = list(self.project_root.rglob("*.py"))

            # Exclude certain directories
            exclude_patterns = ["node_modules", ".git", "__pycache__", ".venv", "legacy"]

            for file_path in python_files:
                # Skip excluded directories
                if any(pattern in str(file_path) for pattern in exclude_patterns):
                    continue

                # Check file size
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        line_count = sum(1 for _ in f)

                    if line_count > 500:  # CCOM's quality standard
                        oversized_files.append({
                            "file": str(file_path.relative_to(self.project_root)),
                            "lines": line_count
                        })
                except:
                    continue

            if oversized_files:
                return {
                    "success": False,
                    "message": f"⚠️ Found {len(oversized_files)} oversized files (>500 lines)",
                    "details": oversized_files[:5]  # Show first 5
                }
            else:
                return {"success": True, "message": "✅ All files under 500 lines"}

        except Exception as e:
            return {"success": False, "message": f"❌ File size check failed: {str(e)}"}

    def display_results(self, results: Dict[str, Any]) -> None:
        """Display quality check results"""
        Display.section("📊 Quality Check Results")

        if results["overall_success"]:
            Display.success("✅ All quality checks passed")
        else:
            Display.warning("⚠️ Some quality issues found")

        # Show individual check results
        for check_name, check_result in results["checks"].items():
            if isinstance(check_result, dict) and "message" in check_result:
                print(f"  {check_result['message']}")

                # Show details if available
                if "details" in check_result and check_result["details"]:
                    details = check_result["details"]
                    if isinstance(details, list):
                        for detail in details[:3]:  # Show first 3
                            if isinstance(detail, dict):
                                print(f"    • {detail.get('file', 'Unknown')}: {detail.get('lines', '?')} lines")
                            else:
                                print(f"    • {detail}")
                    else:
                        print(f"    Details: {details}")

    def get_quality_score(self, results: Dict[str, Any]) -> int:
        """Calculate simple quality score"""
        if not results["checks"]:
            return 0

        passed_checks = sum(1 for check in results["checks"].values()
                          if isinstance(check, dict) and check.get("success", False))
        total_checks = len(results["checks"])

        return int((passed_checks / total_checks) * 100) if total_checks > 0 else 0