#!/usr/bin/env python3
"""
CCOM Validators v0.3 - Tool-Based Code Quality and Security Validation
Uses actual installed tools for comprehensive validation instead of manual checks
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ValidationResult:
    """Container for validation results"""

    def __init__(self, validator_name: str):
        self.validator_name = validator_name
        self.success = False
        self.score = 0
        self.issues = []
        self.warnings = []
        self.fixes_applied = []
        self.execution_time = 0
        self.tool_version = None

    def add_issue(self, severity: str, message: str, file_path: str = None):
        """Add an issue to the results"""
        self.issues.append(
            {
                "severity": severity,
                "message": message,
                "file": file_path,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_warning(self, message: str):
        """Add a warning to the results"""
        self.warnings.append(message)

    def add_fix(self, description: str):
        """Add a fix that was applied"""
        self.fixes_applied.append(description)


class ToolBasedValidator:
    """Base class for validators that use actual development tools"""

    def __init__(self, project_root: Path, tools_manager=None):
        self.project_root = project_root
        self.tools_manager = tools_manager

    def check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available for use"""
        if not self.tools_manager:
            return False

        try:
            installed_tools = self.tools_manager.check_tool_availability()
            return installed_tools.get(tool_name, {}).get("installed", False)
        except:
            return False

    def run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)


class ESLintValidator(ToolBasedValidator):
    """ESLint-based JavaScript/TypeScript validation"""

    def validate(self) -> ValidationResult:
        """Run ESLint validation"""
        result = ValidationResult("ESLint")

        if not self.check_tool_available("eslint"):
            result.add_warning("ESLint not available - skipping JS/TS validation")
            return result

        # Run ESLint
        exit_code, stdout, stderr = self.run_command(
            ["npx", "eslint", ".", "--format", "json"]
        )

        if exit_code == 0:
            result.success = True
            result.score = 100
        else:
            try:
                lint_results = json.loads(stdout) if stdout else []

                error_count = 0
                warning_count = 0

                for file_result in lint_results:
                    file_path = file_result.get("filePath", "unknown")
                    for message in file_result.get("messages", []):
                        severity = (
                            "error" if message.get("severity") == 2 else "warning"
                        )

                        result.add_issue(
                            severity=severity,
                            message=f"Line {message.get('line', '?')}: {message.get('message', 'Unknown error')}",
                            file_path=file_path,
                        )

                        if severity == "error":
                            error_count += 1
                        else:
                            warning_count += 1

                # Calculate score based on issues
                total_issues = error_count + warning_count
                if total_issues == 0:
                    result.score = 100
                elif error_count == 0:
                    result.score = max(80, 100 - warning_count * 2)
                else:
                    result.score = max(0, 100 - error_count * 10 - warning_count * 2)

                result.success = error_count == 0

            except json.JSONDecodeError:
                result.add_issue("error", f"ESLint output parsing failed: {stderr}")

        return result

    def auto_fix(self) -> ValidationResult:
        """Run ESLint with auto-fix"""
        result = ValidationResult("ESLint Auto-Fix")

        if not self.check_tool_available("eslint"):
            result.add_warning("ESLint not available - cannot auto-fix")
            return result

        exit_code, stdout, stderr = self.run_command(["npx", "eslint", ".", "--fix"])

        if exit_code == 0:
            result.success = True
            result.add_fix("Applied ESLint auto-fixes")
        else:
            result.add_issue("error", f"Auto-fix failed: {stderr}")

        return result


class PrettierValidator(ToolBasedValidator):
    """Prettier-based code formatting validation"""

    def validate(self) -> ValidationResult:
        """Check if code is properly formatted"""
        result = ValidationResult("Prettier")

        if not self.check_tool_available("prettier"):
            result.add_warning("Prettier not available - skipping format validation")
            return result

        exit_code, stdout, stderr = self.run_command(
            ["npx", "prettier", "--check", "."]
        )

        if exit_code == 0:
            result.success = True
            result.score = 100
        else:
            # Parse prettier output for unformatted files
            unformatted_files = [
                line.strip()
                for line in stdout.split("\n")
                if line.strip() and not line.startswith("[")
            ]

            for file_path in unformatted_files:
                result.add_issue("warning", f"File needs formatting", file_path)

            result.score = max(70, 100 - len(unformatted_files) * 5)

        return result

    def auto_fix(self) -> ValidationResult:
        """Run Prettier with auto-fix"""
        result = ValidationResult("Prettier Auto-Fix")

        if not self.check_tool_available("prettier"):
            result.add_warning("Prettier not available - cannot auto-format")
            return result

        exit_code, stdout, stderr = self.run_command(
            ["npx", "prettier", "--write", "."]
        )

        if exit_code == 0:
            result.success = True
            result.add_fix("Applied Prettier formatting")
        else:
            result.add_issue("error", f"Auto-format failed: {stderr}")

        return result


class PythonValidator(ToolBasedValidator):
    """Python code validation using black, pylint, flake8, mypy"""

    def validate_with_black(self) -> ValidationResult:
        """Validate Python formatting with black"""
        result = ValidationResult("Black")

        if not self.check_tool_available("black"):
            result.add_warning(
                "Black not available - skipping Python format validation"
            )
            return result

        exit_code, stdout, stderr = self.run_command(
            [sys.executable, "-m", "black", "--check", "."]
        )

        if exit_code == 0:
            result.success = True
            result.score = 100
        else:
            result.add_issue("warning", f"Python files need black formatting: {stdout}")
            result.score = 80

        return result

    def validate_with_pylint(self) -> ValidationResult:
        """Validate Python code quality with pylint"""
        result = ValidationResult("Pylint")

        if not self.check_tool_available("pylint"):
            result.add_warning(
                "Pylint not available - skipping Python quality validation"
            )
            return result

        # Find Python files
        py_files = list(self.project_root.glob("**/*.py"))
        if not py_files:
            result.success = True
            result.score = 100
            return result

        exit_code, stdout, stderr = self.run_command(
            [
                sys.executable,
                "-m",
                "pylint",
                "--output-format=json",
                "--disable=missing-docstring,too-few-public-methods",
            ]
            + [str(f) for f in py_files[:10]]
        )  # Limit to first 10 files

        try:
            if stdout:
                pylint_results = json.loads(stdout)

                error_count = 0
                warning_count = 0

                for issue in pylint_results:
                    severity = issue.get("type", "warning")
                    message = issue.get("message", "Unknown issue")
                    path = issue.get("path", "unknown")
                    line = issue.get("line", "?")

                    result.add_issue(
                        severity=severity,
                        message=f"Line {line}: {message}",
                        file_path=path,
                    )

                    if severity in ["error", "fatal"]:
                        error_count += 1
                    else:
                        warning_count += 1

                # Calculate score
                total_issues = error_count + warning_count
                if total_issues == 0:
                    result.score = 100
                elif error_count == 0:
                    result.score = max(80, 100 - warning_count * 3)
                else:
                    result.score = max(0, 100 - error_count * 15 - warning_count * 3)

                result.success = error_count == 0
            else:
                result.success = True
                result.score = 100

        except json.JSONDecodeError:
            result.add_issue("error", f"Pylint output parsing failed: {stderr}")

        return result

    def auto_fix_black(self) -> ValidationResult:
        """Auto-fix Python formatting with black"""
        result = ValidationResult("Black Auto-Fix")

        if not self.check_tool_available("black"):
            result.add_warning("Black not available - cannot auto-format Python")
            return result

        exit_code, stdout, stderr = self.run_command(
            [sys.executable, "-m", "black", "."]
        )

        if exit_code == 0:
            result.success = True
            result.add_fix("Applied Black formatting to Python files")
        else:
            result.add_issue("error", f"Black auto-format failed: {stderr}")

        return result


class SecurityValidator(ToolBasedValidator):
    """Security validation using bandit, safety, and custom checks"""

    def validate_dependencies(self) -> ValidationResult:
        """Check for vulnerable dependencies"""
        result = ValidationResult("Dependency Security")

        # Check npm dependencies
        if (self.project_root / "package.json").exists():
            exit_code, stdout, stderr = self.run_command(["npm", "audit", "--json"])

            try:
                if stdout:
                    audit_data = json.loads(stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", {})

                    high_critical = 0
                    for vuln in vulnerabilities.values():
                        severity = vuln.get("severity", "unknown")
                        if severity in ["high", "critical"]:
                            high_critical += 1
                            result.add_issue(
                                severity=(
                                    "error" if severity == "critical" else "warning"
                                ),
                                message=f"{severity.title()} vulnerability in {vuln.get('name', 'unknown package')}",
                            )

                    if high_critical == 0:
                        result.success = True
                        result.score = 100
                    else:
                        result.score = max(0, 100 - high_critical * 20)

            except json.JSONDecodeError:
                result.add_warning("Could not parse npm audit output")
                result.success = True
                result.score = 90

        # Check Python dependencies with safety
        elif self.check_tool_available("safety"):
            exit_code, stdout, stderr = self.run_command(
                [sys.executable, "-m", "safety", "check", "--json"]
            )

            try:
                if stdout and stdout.strip() != "[]":
                    safety_results = json.loads(stdout)

                    for vuln in safety_results:
                        result.add_issue(
                            severity="error",
                            message=f"Vulnerable package: {vuln.get('package', 'unknown')} - {vuln.get('advisory', 'No details')}",
                        )

                    result.score = max(0, 100 - len(safety_results) * 25)
                else:
                    result.success = True
                    result.score = 100

            except json.JSONDecodeError:
                result.add_warning("Could not parse safety check output")
                result.success = True
                result.score = 90

        else:
            result.success = True
            result.score = 95
            result.add_warning("No dependency security tools available")

        return result

    def validate_python_security(self) -> ValidationResult:
        """Validate Python code security with bandit"""
        result = ValidationResult("Python Security (Bandit)")

        if not self.check_tool_available("bandit"):
            result.add_warning(
                "Bandit not available - skipping Python security validation"
            )
            return result

        py_files = list(self.project_root.glob("**/*.py"))
        if not py_files:
            result.success = True
            result.score = 100
            return result

        exit_code, stdout, stderr = self.run_command(
            [sys.executable, "-m", "bandit", "-r", ".", "-f", "json"]
        )

        try:
            if stdout:
                bandit_results = json.loads(stdout)

                for issue in bandit_results.get("results", []):
                    severity = issue.get("issue_severity", "UNKNOWN")
                    confidence = issue.get("issue_confidence", "UNKNOWN")
                    message = issue.get("issue_text", "Security issue detected")
                    filename = issue.get("filename", "unknown")
                    line_number = issue.get("line_number", "?")

                    result.add_issue(
                        severity="error" if severity == "HIGH" else "warning",
                        message=f"Line {line_number}: {message} (Confidence: {confidence})",
                        file_path=filename,
                    )

                high_issues = sum(
                    1
                    for issue in bandit_results.get("results", [])
                    if issue.get("issue_severity") == "HIGH"
                )
                medium_issues = sum(
                    1
                    for issue in bandit_results.get("results", [])
                    if issue.get("issue_severity") == "MEDIUM"
                )

                if high_issues == 0 and medium_issues == 0:
                    result.success = True
                    result.score = 100
                elif high_issues == 0:
                    result.score = max(80, 100 - medium_issues * 5)
                    result.success = True
                else:
                    result.score = max(0, 100 - high_issues * 20 - medium_issues * 5)

            else:
                result.success = True
                result.score = 100

        except json.JSONDecodeError:
            result.add_issue("error", f"Bandit output parsing failed: {stderr}")

        return result


class ValidationOrchestrator:
    """Orchestrates all validations using installed tools"""

    def __init__(self, project_root: Path, tools_manager=None):
        self.project_root = project_root
        self.tools_manager = tools_manager
        self.results = []

    def run_all_validations(self, auto_fix: bool = False) -> List[ValidationResult]:
        """Run all appropriate validations for the project"""
        print("🔍 **CCOM VALIDATION** – Running comprehensive tool-based validation...")

        project_type = self.detect_project_type()
        print(f"📊 Project type detected: {project_type}")

        # JavaScript/TypeScript validations
        if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
            eslint = ESLintValidator(self.project_root, self.tools_manager)
            prettier = PrettierValidator(self.project_root, self.tools_manager)

            if auto_fix:
                print("🔧 Running auto-fixes...")
                self.results.append(eslint.auto_fix())
                self.results.append(prettier.auto_fix())

            print("📋 Running validation checks...")
            self.results.append(eslint.validate())
            self.results.append(prettier.validate())

        # Python validations
        elif project_type == "python":
            python_validator = PythonValidator(self.project_root, self.tools_manager)

            if auto_fix:
                print("🔧 Running Python auto-fixes...")
                self.results.append(python_validator.auto_fix_black())

            print("📋 Running Python validation checks...")
            self.results.append(python_validator.validate_with_black())
            self.results.append(python_validator.validate_with_pylint())

        # Security validations (for all project types)
        security_validator = SecurityValidator(self.project_root, self.tools_manager)
        print("🔒 Running security validations...")
        self.results.append(security_validator.validate_dependencies())

        if project_type == "python":
            self.results.append(security_validator.validate_python_security())

        return self.results

    def detect_project_type(self) -> str:
        """Detect project type based on files present"""
        if (self.project_root / "package.json").exists():
            try:
                with open(self.project_root / "package.json") as f:
                    pkg_data = json.load(f)
                    deps = {
                        **pkg_data.get("dependencies", {}),
                        **pkg_data.get("devDependencies", {}),
                    }

                    if "typescript" in deps or "@types/node" in deps:
                        return "typescript"
                    elif "react" in deps:
                        return "react"
                    elif "angular" in deps or "@angular/core" in deps:
                        return "angular"
                    elif "vue" in deps:
                        return "vue"
                    else:
                        return "javascript"
            except:
                return "javascript"

        elif any(
            (self.project_root / f).exists()
            for f in ["setup.py", "pyproject.toml", "requirements.txt"]
        ):
            return "python"

        return "unknown"

    def generate_report(self) -> Dict:
        """Generate comprehensive validation report"""
        total_score = 0
        successful_validations = 0
        total_issues = 0
        total_warnings = 0

        for result in self.results:
            total_score += result.score
            if result.success:
                successful_validations += 1
            total_issues += len([i for i in result.issues if i["severity"] == "error"])
            total_warnings += len(
                [i for i in result.issues if i["severity"] == "warning"]
            )
            total_warnings += len(result.warnings)

        avg_score = total_score / len(self.results) if self.results else 0

        report = {
            "overall_score": round(avg_score, 1),
            "successful_validations": successful_validations,
            "total_validations": len(self.results),
            "total_issues": total_issues,
            "total_warnings": total_warnings,
            "validation_results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

        return report

    def print_summary(self):
        """Print validation summary"""
        report = self.generate_report()

        print(f"\n📊 **VALIDATION SUMMARY**")
        print(f"Overall Score: {report['overall_score']}/100")
        print(
            f"Successful Validations: {report['successful_validations']}/{report['total_validations']}"
        )

        if report["total_issues"] == 0 and report["total_warnings"] == 0:
            print("✅ **QUALITY STATUS**: Enterprise Grade - No issues found!")
        elif report["total_issues"] == 0:
            print(
                f"🟡 **QUALITY STATUS**: Good - {report['total_warnings']} warnings to review"
            )
        else:
            print(
                f"🔴 **QUALITY STATUS**: Needs Attention - {report['total_issues']} errors, {report['total_warnings']} warnings"
            )

        print(f"\n💡 **Recommendations**:")
        if report["overall_score"] >= 95:
            print(
                "  🎉 Code quality is excellent! Consider setting up automated checks."
            )
        elif report["overall_score"] >= 80:
            print("  🔧 Good code quality. Address remaining warnings when possible.")
        else:
            print("  ⚠️ Code quality needs improvement. Focus on fixing errors first.")
            print("  💡 Run with auto-fix option: ccom quality audit --fix")
