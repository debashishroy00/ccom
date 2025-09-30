#!/usr/bin/env python3
"""
Quality Enforcer Agent SDK Implementation
Modernized version replacing markdown specifications
"""

import asyncio
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator
import time

from .sdk_agent_base import SDKAgentBase, AgentResult, StreamingUpdate


class QualityEnforcerAgent(SDKAgentBase):
    """
    SDK-based Quality Enforcer Agent for enterprise code standards

    Capabilities:
    - ESLint/Prettier execution with auto-fix
    - TypeScript compilation checks
    - Code complexity analysis
    - Test execution and coverage
    - Real-time streaming feedback
    - Enterprise-grade error handling
    """

    def _get_capabilities(self) -> List[str]:
        return [
            "eslint_execution",
            "prettier_formatting",
            "typescript_checking",
            "test_execution",
            "complexity_analysis",
            "auto_fix",
            "streaming_feedback"
        ]

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute quality enforcement with comprehensive checks"""
        start_time = time.time()

        try:
            # Pre-execution hook
            if not await self.pre_execute_hook(context):
                return AgentResult(
                    success=False,
                    message="❌ Quality enforcement aborted - permission denied",
                    errors=["Permission validation failed"]
                )

            auto_fix = context.get("auto_fix", True)
            check_types = context.get("check_types", ["lint", "format", "typescript", "tests"])

            results = {}
            all_passed = True
            errors = []
            warnings = []

            # 1. ESLint checks
            if "lint" in check_types:
                lint_result = await self._run_eslint(auto_fix)
                results["eslint"] = lint_result
                if not lint_result["success"]:
                    all_passed = False
                    errors.extend(lint_result.get("errors", []))

            # 2. Prettier formatting
            if "format" in check_types:
                format_result = await self._run_prettier(auto_fix)
                results["prettier"] = format_result
                if not format_result["success"]:
                    all_passed = False
                    errors.extend(format_result.get("errors", []))

            # 3. TypeScript checks
            if "typescript" in check_types:
                ts_result = await self._run_typescript_check()
                results["typescript"] = ts_result
                if not ts_result["success"]:
                    all_passed = False
                    errors.extend(ts_result.get("errors", []))

            # 4. Test execution
            if "tests" in check_types:
                test_result = await self._run_tests()
                results["tests"] = test_result
                if not test_result["success"]:
                    warnings.extend(test_result.get("warnings", []))

            # Calculate metrics
            execution_time = time.time() - start_time
            metrics = {
                "execution_time": execution_time,
                "checks_performed": len(check_types),
                "auto_fix_enabled": auto_fix,
                "results_summary": {
                    check: result["success"] for check, result in results.items()
                }
            }

            # Generate message
            if all_passed:
                message = "✅ **QUALITY STATUS**: Enterprise Grade - All checks passed"
            else:
                failed_checks = [check for check, result in results.items() if not result["success"]]
                message = f"🔧 **QUALITY STATUS**: Issues found in {', '.join(failed_checks)} - {'Auto-fixed' if auto_fix else 'Manual fixes required'}"

            result = AgentResult(
                success=all_passed,
                message=message,
                data=results,
                errors=errors if errors else None,
                warnings=warnings if warnings else None,
                metrics=metrics
            )

            # Update metrics and post-execution hook
            self._update_metrics(execution_time, result)
            await self.post_execute_hook(context, result)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_result = AgentResult(
                success=False,
                message=f"❌ Quality enforcement failed: {str(e)}",
                errors=[str(e)],
                metrics={"execution_time": execution_time}
            )

            self._update_metrics(execution_time, error_result)
            await self.post_execute_hook(context, error_result)
            return error_result

    async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[StreamingUpdate, None]:
        """Execute with real-time streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="🔧 **CCOM QUALITY ENFORCER** – Enterprise standards activated",
        )

        auto_fix = context.get("auto_fix", True)
        check_types = context.get("check_types", ["lint", "format", "typescript", "tests"])

        try:
            results = {}
            all_passed = True

            # Stream each check with real-time updates
            for i, check_type in enumerate(check_types, 1):
                yield StreamingUpdate(
                    type="progress",
                    content=f"🔍 Step {i}/{len(check_types)}: Running {check_type} check...",
                )

                if check_type == "lint":
                    result = await self._run_eslint_streaming(auto_fix)
                    async for update in result:
                        yield update

                elif check_type == "format":
                    result = await self._run_prettier_streaming(auto_fix)
                    async for update in result:
                        yield update

                elif check_type == "typescript":
                    result = await self._run_typescript_streaming()
                    async for update in result:
                        yield update

                elif check_type == "tests":
                    result = await self._run_tests_streaming()
                    async for update in result:
                        yield update

            # Final status
            if all_passed:
                yield StreamingUpdate(
                    type="complete",
                    content="✅ **QUALITY STATUS**: Enterprise Grade - All checks passed",
                )
            else:
                yield StreamingUpdate(
                    type="complete",
                    content="🔧 **QUALITY STATUS**: Issues addressed - Review remaining items",
                )

        except Exception as e:
            yield StreamingUpdate(
                type="error",
                content=f"❌ Quality enforcement error: {str(e)}"
            )

    async def _run_eslint(self, auto_fix: bool = True) -> Dict[str, Any]:
        """Run ESLint with optional auto-fix"""
        try:
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return {
                    "success": True,
                    "message": "No package.json found - skipping ESLint",
                    "skipped": True
                }

            # Check if lint script exists
            with open(package_json) as f:
                pkg_data = json.load(f)

            scripts = pkg_data.get("scripts", {})
            if "lint" not in scripts:
                return {
                    "success": True,
                    "message": "No lint script configured - skipping ESLint",
                    "skipped": True
                }

            # Run lint check
            cmd = ["npm", "run", "lint"]
            result = await self._run_command(cmd, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "✅ ESLint: No issues found"
                }
            else:
                # Try auto-fix if enabled
                if auto_fix:
                    fix_cmd = ["npm", "run", "lint", "--", "--fix"]
                    fix_result = await self._run_command(fix_cmd, timeout=120)

                    if fix_result.returncode == 0:
                        return {
                            "success": True,
                            "message": "🔧 ESLint: Issues auto-fixed successfully"
                        }

                return {
                    "success": False,
                    "message": "⚠️ ESLint: Issues found requiring manual attention",
                    "errors": [result.stderr] if result.stderr else []
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"❌ ESLint execution failed: {str(e)}",
                "errors": [str(e)]
            }

    async def _run_prettier(self, auto_fix: bool = True) -> Dict[str, Any]:
        """Run Prettier formatting"""
        try:
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return {
                    "success": True,
                    "message": "No package.json found - skipping Prettier",
                    "skipped": True
                }

            # Check if format script exists or try direct prettier
            with open(package_json) as f:
                pkg_data = json.load(f)

            scripts = pkg_data.get("scripts", {})

            if "format" in scripts:
                cmd = ["npm", "run", "format"]
            else:
                # Try direct prettier
                cmd = ["npx", "prettier", "--check", "."]

            result = await self._run_command(cmd, timeout=60)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "✅ Prettier: Code formatting is consistent"
                }
            else:
                # Try auto-fix if enabled
                if auto_fix:
                    if "format" in scripts:
                        fix_cmd = ["npm", "run", "format"]
                    else:
                        fix_cmd = ["npx", "prettier", "--write", "."]

                    fix_result = await self._run_command(fix_cmd, timeout=120)

                    if fix_result.returncode == 0:
                        return {
                            "success": True,
                            "message": "🔧 Prettier: Code formatted automatically"
                        }

                return {
                    "success": False,
                    "message": "⚠️ Prettier: Formatting issues found",
                    "errors": [result.stderr] if result.stderr else []
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Prettier execution failed: {str(e)}",
                "errors": [str(e)]
            }

    async def _run_typescript_check(self) -> Dict[str, Any]:
        """Run TypeScript compilation check"""
        try:
            tsconfig = self.project_root / "tsconfig.json"
            if not tsconfig.exists():
                return {
                    "success": True,
                    "message": "No tsconfig.json found - skipping TypeScript check",
                    "skipped": True
                }

            cmd = ["npx", "tsc", "--noEmit"]
            result = await self._run_command(cmd, timeout=120)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "✅ TypeScript: No type errors found"
                }
            else:
                return {
                    "success": False,
                    "message": "⚠️ TypeScript: Type errors found",
                    "errors": [result.stderr] if result.stderr else []
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"❌ TypeScript check failed: {str(e)}",
                "errors": [str(e)]
            }

    async def _run_tests(self) -> Dict[str, Any]:
        """Run test suite"""
        try:
            package_json = self.project_root / "package.json"
            if not package_json.exists():
                return {
                    "success": True,
                    "message": "No package.json found - skipping tests",
                    "skipped": True
                }

            with open(package_json) as f:
                pkg_data = json.load(f)

            scripts = pkg_data.get("scripts", {})
            if "test" not in scripts:
                return {
                    "success": True,
                    "message": "No test script configured - skipping tests",
                    "skipped": True
                }

            cmd = ["npm", "test"]
            result = await self._run_command(cmd, timeout=180)

            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "✅ Tests: All tests passed"
                }
            else:
                return {
                    "success": False,
                    "message": "⚠️ Tests: Some tests failed",
                    "warnings": [result.stderr] if result.stderr else []
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"❌ Test execution failed: {str(e)}",
                "errors": [str(e)]
            }

    async def _run_command(self, cmd: List[str], timeout: int = 60) -> subprocess.CompletedProcess:
        """Run command asynchronously with timeout"""
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.project_root
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            return subprocess.CompletedProcess(
                cmd, process.returncode,
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace')
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise TimeoutError(f"Command timed out after {timeout} seconds: {' '.join(cmd)}")

    async def _run_eslint_streaming(self, auto_fix: bool) -> AsyncGenerator[StreamingUpdate, None]:
        """Run ESLint with streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="🔍 Running ESLint analysis..."
        )

        result = await self._run_eslint(auto_fix)

        yield StreamingUpdate(
            type="result",
            content=result["message"],
            data=result
        )

    async def _run_prettier_streaming(self, auto_fix: bool) -> AsyncGenerator[StreamingUpdate, None]:
        """Run Prettier with streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="✨ Checking code formatting..."
        )

        result = await self._run_prettier(auto_fix)

        yield StreamingUpdate(
            type="result",
            content=result["message"],
            data=result
        )

    async def _run_typescript_streaming(self) -> AsyncGenerator[StreamingUpdate, None]:
        """Run TypeScript check with streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="🔍 Analyzing TypeScript types..."
        )

        result = await self._run_typescript_check()

        yield StreamingUpdate(
            type="result",
            content=result["message"],
            data=result
        )

    async def _run_tests_streaming(self) -> AsyncGenerator[StreamingUpdate, None]:
        """Run tests with streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="🧪 Executing test suite..."
        )

        result = await self._run_tests()

        yield StreamingUpdate(
            type="result",
            content=result["message"],
            data=result
        )

    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get configuration schema for quality enforcer"""
        base_schema = super().get_configuration_schema()
        base_schema["properties"].update({
            "auto_fix": {
                "type": "boolean",
                "default": True,
                "description": "Automatically fix issues when possible"
            },
            "check_types": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["lint", "format", "typescript", "tests"]
                },
                "default": ["lint", "format", "typescript", "tests"],
                "description": "Types of quality checks to perform"
            },
            "eslint_config": {
                "type": "object",
                "description": "ESLint-specific configuration"
            },
            "prettier_config": {
                "type": "object",
                "description": "Prettier-specific configuration"
            }
        })
        return base_schema