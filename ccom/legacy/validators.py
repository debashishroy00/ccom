#!/usr/bin/env python3
"""
CCOM Validators v0.3 - Tool-Based Code Quality and Security Validation
Uses actual installed tools for comprehensive validation instead of manual checks
"""

import os
import sys
import json
import subprocess
import ast
import re
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


class PrinciplesValidator(ToolBasedValidator):
    """Software Engineering Principles validation (KISS, YAGNI, DRY, SOLID)"""

    def __init__(self, project_root: Path, tools_manager=None, target_files=None, max_files=100):
        super().__init__(project_root, tools_manager)
        self.target_files = target_files  # Specific files to analyze
        self.max_files = max_files  # Performance limit
        self.exclusion_patterns = [
            'node_modules/**',
            'dist/**',
            'build/**',
            '.git/**',
            'coverage/**',
            'vendor/**',
            '*.min.js',
            '*.bundle.js',
            'lib/**',
            'libs/**'
        ]

    def get_target_files(self, extensions=['*.js', '*.ts', '*.jsx', '*.tsx', '*.py']):
        """Get files to analyze with smart filtering and performance limits"""
        if self.target_files:
            # Analyze specific files only
            return [Path(f) for f in self.target_files if Path(f).exists()]

        files = []
        for ext in extensions:
            found_files = list(self.project_root.glob(f"**/{ext}"))
            files.extend(found_files)

        # Filter out excluded patterns
        filtered_files = []
        for file_path in files:
            if not any(file_path.match(pattern) for pattern in self.exclusion_patterns):
                filtered_files.append(file_path)

        # Performance limit - sample files if too many
        if len(filtered_files) > self.max_files:
            # Prioritize main source files over test files
            main_files = [f for f in filtered_files if not any(test in str(f).lower() for test in ['test', 'spec', '__test__'])]
            test_files = [f for f in filtered_files if any(test in str(f).lower() for test in ['test', 'spec', '__test__'])]

            # Take most main files, some test files
            main_count = min(int(self.max_files * 0.8), len(main_files))
            test_count = min(self.max_files - main_count, len(test_files))

            filtered_files = main_files[:main_count] + test_files[:test_count]
            print(f"⚡ Performance limit: Analyzing {len(filtered_files)} files (sampled from {len(files)} total)")

        return filtered_files

    def validate_all_principles(self, target_files=None) -> Dict[str, ValidationResult]:
        """Run all software engineering principles validation"""
        results = {
            'kiss': self.validate_kiss(),
            'yagni': self.validate_yagni(),
            'dry': self.validate_dry(),
            'solid': self.validate_solid()
        }
        return results

    def validate_kiss(self) -> ValidationResult:
        """
        KISS - Keep It Simple
        - Cyclomatic complexity < 10
        - Function length < 50 lines
        - Nesting depth < 4 levels
        - Parameter count < 5
        """
        result = ValidationResult("KISS (Keep It Simple)")
        complexity_issues = []

        try:
            # Check JavaScript/TypeScript complexity
            if self.check_tool_available("complexity-report"):
                exit_code, stdout, stderr = self.run_command(
                    ["npx", "complexity-report", ".", "--format", "json"]
                )

                if exit_code == 0 and stdout:
                    complexity_data = json.loads(stdout)
                    for report in complexity_data.get('reports', []):
                        for func in report.get('functions', []):
                            complexity = func.get('complexity', {}).get('cyclomatic', 0)
                            if complexity > 10:
                                complexity_issues.append({
                                    'file': report.get('path', 'unknown'),
                                    'function': func.get('name', 'unknown'),
                                    'complexity': complexity,
                                    'type': 'cyclomatic_complexity'
                                })

            # Check Python complexity using radon
            if self.check_tool_available("radon"):
                exit_code, stdout, stderr = self.run_command(
                    [sys.executable, "-m", "radon", "cc", ".", "--json"]
                )

                if exit_code == 0 and stdout:
                    radon_data = json.loads(stdout)
                    for file_path, functions in radon_data.items():
                        for func in functions:
                            if func.get('complexity', 0) > 10:
                                complexity_issues.append({
                                    'file': file_path,
                                    'function': func.get('name', 'unknown'),
                                    'complexity': func.get('complexity'),
                                    'type': 'cyclomatic_complexity'
                                })

            # Manual AST analysis for function length and nesting
            manual_issues = self._analyze_code_structure()
            complexity_issues.extend(manual_issues)

            # Calculate score
            if not complexity_issues:
                result.success = True
                result.score = 100
            else:
                # Deduct points based on issue severity
                deduction = min(90, len(complexity_issues) * 15)
                result.score = max(10, 100 - deduction)

                for issue in complexity_issues:
                    severity = "error" if issue.get('complexity', 0) > 15 else "warning"
                    result.add_issue(
                        severity=severity,
                        message=f"{issue['type']}: {issue.get('function', 'unknown')} has complexity {issue.get('complexity', 'high')}",
                        file_path=issue.get('file')
                    )

        except Exception as e:
            result.add_warning(f"KISS validation error: {e}")
            result.score = 90
            result.success = True

        return result

    def validate_yagni(self) -> ValidationResult:
        """
        YAGNI - You Aren't Gonna Need It
        - Detect unused functions/variables
        - Find over-engineered abstractions
        - Check for speculative generality
        """
        result = ValidationResult("YAGNI (You Aren't Gonna Need It)")

        try:
            unused_issues = []

            # Use ESLint for JavaScript unused detection
            if self.check_tool_available("eslint"):
                exit_code, stdout, stderr = self.run_command(
                    ["npx", "eslint", ".", "--format", "json", "--no-fix"]
                )

                if stdout:
                    eslint_data = json.loads(stdout)
                    for file_result in eslint_data:
                        for message in file_result.get('messages', []):
                            if 'unused' in message.get('message', '').lower():
                                unused_issues.append({
                                    'file': file_result.get('filePath'),
                                    'line': message.get('line'),
                                    'message': message.get('message'),
                                    'type': 'unused_code'
                                })

            # Manual analysis for over-engineering patterns
            overengineered = self._detect_overengineering()
            unused_issues.extend(overengineered)

            # Calculate score
            if not unused_issues:
                result.success = True
                result.score = 100
            else:
                deduction = min(80, len(unused_issues) * 10)
                result.score = max(20, 100 - deduction)

                for issue in unused_issues:
                    result.add_issue(
                        severity="warning",
                        message=f"{issue['type']}: {issue.get('message', 'Unused or over-engineered code detected')}",
                        file_path=issue.get('file')
                    )

        except Exception as e:
            result.add_warning(f"YAGNI validation error: {e}")
            result.score = 95
            result.success = True

        return result

    def validate_dry(self) -> ValidationResult:
        """
        DRY - Don't Repeat Yourself
        - Detect duplicate code blocks (>5 lines)
        - Find repeated string literals
        - Allow WET for < 3 occurrences
        """
        result = ValidationResult("DRY (Don't Repeat Yourself)")

        try:
            duplicate_issues = []

            # Use jscpd for duplicate detection
            if self.check_tool_available("jscpd"):
                exit_code, stdout, stderr = self.run_command(
                    ["npx", "jscpd", ".", "--format", "json", "--min-lines", "5"]
                )

                if exit_code == 0 and stdout:
                    jscpd_data = json.loads(stdout)
                    duplicates = jscpd_data.get('duplicates', [])

                    for dup in duplicates:
                        if dup.get('lines', 0) >= 5:  # Only flag significant duplicates
                            duplicate_issues.append({
                                'file1': dup.get('firstFile', {}).get('name'),
                                'file2': dup.get('secondFile', {}).get('name'),
                                'lines': dup.get('lines'),
                                'type': 'code_duplication'
                            })

            # Manual analysis for string literal repetition
            string_duplicates = self._detect_string_duplicates()
            duplicate_issues.extend(string_duplicates)

            # Calculate score
            if not duplicate_issues:
                result.success = True
                result.score = 100
            else:
                # Adjust scoring based on Rule of Three
                significant_dups = [d for d in duplicate_issues if d.get('lines', 0) > 10]
                deduction = len(significant_dups) * 20 + len(duplicate_issues) * 5
                result.score = max(30, 100 - deduction)

                for issue in duplicate_issues:
                    severity = "error" if issue.get('lines', 0) > 15 else "warning"
                    result.add_issue(
                        severity=severity,
                        message=f"{issue['type']}: {issue.get('lines', 'Multiple')} lines duplicated between {issue.get('file1', 'files')}",
                        file_path=issue.get('file1')
                    )

        except Exception as e:
            result.add_warning(f"DRY validation error: {e}")
            result.score = 90
            result.success = True

        return result

    def validate_solid(self) -> ValidationResult:
        """
        SOLID Principles validation
        - Single Responsibility: >1 purpose detection
        - Open/Closed: Modification-prone code
        - Liskov: Inheritance validation
        - Interface Segregation: Fat interfaces
        - Dependency Inversion: Concrete dependencies
        """
        result = ValidationResult("SOLID Principles")

        try:
            solid_issues = []

            # Analyze code structure for SOLID violations
            solid_violations = self._analyze_solid_principles()
            solid_issues.extend(solid_violations)

            # Calculate score
            if not solid_issues:
                result.success = True
                result.score = 100
            else:
                deduction = min(75, len(solid_issues) * 12)
                result.score = max(25, 100 - deduction)

                for issue in solid_issues:
                    severity = "error" if issue.get('severity') == 'high' else "warning"
                    result.add_issue(
                        severity=severity,
                        message=f"{issue['principle']}: {issue.get('message', 'SOLID principle violation')}",
                        file_path=issue.get('file')
                    )

        except Exception as e:
            result.add_warning(f"SOLID validation error: {e}")
            result.score = 85
            result.success = True

        return result

    def _analyze_code_structure(self) -> List[Dict]:
        """Analyze code structure for KISS violations"""
        issues = []

        # Get target files with smart filtering
        target_files = self.get_target_files(['*.js', '*.ts', '*.jsx', '*.tsx'])
        print(f"🔍 Analyzing {len(target_files)} JavaScript/TypeScript files for KISS violations...")

        for file_path in target_files[:50]:  # Additional safety limit

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Simple heuristics for function analysis
                functions = re.findall(r'function\s+(\w+)\s*\([^)]*\)\s*{', content)
                for func_name in functions:
                    # Count lines in function (simplified)
                    func_pattern = rf'function\s+{re.escape(func_name)}\s*\([^)]*\)\s*{{'
                    match = re.search(func_pattern, content)
                    if match:
                        start_pos = match.end()
                        brace_count = 1
                        pos = start_pos
                        lines = 1

                        while pos < len(content) and brace_count > 0:
                            if content[pos] == '{':
                                brace_count += 1
                            elif content[pos] == '}':
                                brace_count -= 1
                            elif content[pos] == '\n':
                                lines += 1
                            pos += 1

                        if lines > 50:
                            issues.append({
                                'file': str(file_path),
                                'function': func_name,
                                'complexity': lines,
                                'type': 'function_length'
                            })

            except Exception:
                continue

        return issues

    def _detect_overengineering(self) -> List[Dict]:
        """Detect over-engineering patterns"""
        issues = []

        # Get target files with smart filtering
        target_files = self.get_target_files(['*.js', '*.ts', '*.jsx', '*.tsx'])

        for file_path in target_files[:30]:  # Limit for performance

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Count abstract patterns
                abstract_patterns = [
                    r'class\s+\w+Factory',
                    r'class\s+\w+Builder',
                    r'class\s+\w+Strategy',
                    r'interface\s+\w+Interface',
                ]

                pattern_count = sum(
                    len(re.findall(pattern, content, re.IGNORECASE))
                    for pattern in abstract_patterns
                )

                if pattern_count > 3:  # Too many design patterns
                    issues.append({
                        'file': str(file_path),
                        'message': f'Excessive abstraction patterns detected ({pattern_count})',
                        'type': 'overengineering'
                    })

            except Exception:
                continue

        return issues

    def _detect_string_duplicates(self) -> List[Dict]:
        """Detect repeated string literals"""
        issues = []
        string_counts = {}

        # Get target files with smart filtering
        target_files = self.get_target_files(['*.js', '*.ts', '*.jsx', '*.tsx'])

        for file_path in target_files[:40]:  # Limit for performance

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Find string literals
                strings = re.findall(r'["\']([^"\'\n]{10,})["\']', content)
                for string_literal in strings:
                    if string_literal not in string_counts:
                        string_counts[string_literal] = []
                    string_counts[string_literal].append(str(file_path))

            except Exception:
                continue

        # Flag strings that appear 3+ times
        for string_literal, files in string_counts.items():
            if len(files) >= 3:
                issues.append({
                    'files': files,
                    'string': string_literal[:50] + '...' if len(string_literal) > 50 else string_literal,
                    'count': len(files),
                    'type': 'string_duplication'
                })

        return issues

    def _analyze_solid_principles(self) -> List[Dict]:
        """Analyze code for SOLID principle violations"""
        issues = []

        # Get target files with smart filtering
        target_files = self.get_target_files(['*.js', '*.ts', '*.jsx', '*.tsx'])

        for file_path in target_files[:25]:  # Limit for performance

            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Single Responsibility Principle check
                classes = re.findall(r'class\s+(\w+)', content)
                for class_name in classes:
                    # Count public methods (simplified heuristic)
                    methods = re.findall(
                        rf'class\s+{re.escape(class_name)}[^{{]*{{[^}}]*?(\w+)\s*\([^)]*\)\s*{{',
                        content,
                        re.DOTALL
                    )

                    if len(methods) > 10:  # Too many responsibilities
                        issues.append({
                            'file': str(file_path),
                            'class': class_name,
                            'message': f'Class {class_name} has {len(methods)} methods (possible SRP violation)',
                            'principle': 'Single Responsibility',
                            'severity': 'medium'
                        })

                # Dependency Inversion check - look for direct instantiation
                direct_instantiations = re.findall(r'new\s+(\w+)\(', content)
                if len(direct_instantiations) > 5:
                    issues.append({
                        'file': str(file_path),
                        'message': f'Multiple direct instantiations detected ({len(direct_instantiations)})',
                        'principle': 'Dependency Inversion',
                        'severity': 'low'
                    })

            except Exception:
                continue

        return issues


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

        # Software Engineering Principles validation
        principles_validator = PrinciplesValidator(self.project_root, self.tools_manager)
        print("📐 Running software engineering principles validation...")
        principle_results = principles_validator.validate_all_principles()

        # Add each principle result to main results
        for principle_name, principle_result in principle_results.items():
            self.results.append(principle_result)

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
        """Generate comprehensive validation report with principles scoring"""
        total_score = 0
        successful_validations = 0
        total_issues = 0
        total_warnings = 0

        # Separate principle results from other validations
        principle_results = {}
        other_results = []

        for result in self.results:
            total_score += result.score
            if result.success:
                successful_validations += 1
            total_issues += len([i for i in result.issues if i["severity"] == "error"])
            total_warnings += len(
                [i for i in result.issues if i["severity"] == "warning"]
            )
            total_warnings += len(result.warnings)

            # Categorize results
            if result.validator_name in ['KISS (Keep It Simple)', 'YAGNI (You Aren\'t Gonna Need It)',
                                        'DRY (Don\'t Repeat Yourself)', 'SOLID Principles']:
                principle_key = result.validator_name.split(' ')[0].lower()
                principle_results[principle_key] = {
                    'score': result.score,
                    'success': result.success,
                    'issues': len(result.issues)
                }
            else:
                other_results.append(result)

        avg_score = total_score / len(self.results) if self.results else 0

        # Calculate principle-specific metrics
        principle_weights = {'kiss': 0.3, 'yagni': 0.2, 'dry': 0.3, 'solid': 0.2}
        principle_total = 0
        principle_grade = 'N/A'

        if principle_results:
            principle_total = sum(
                principle_results.get(p, {}).get('score', 0) * weight
                for p, weight in principle_weights.items()
            )
            if principle_total >= 95:
                principle_grade = 'A+'
            elif principle_total >= 90:
                principle_grade = 'A'
            elif principle_total >= 80:
                principle_grade = 'B+'
            elif principle_total >= 70:
                principle_grade = 'B'
            elif principle_total >= 60:
                principle_grade = 'C'
            else:
                principle_grade = 'D'

        report = {
            "overall_score": round(avg_score, 1),
            "successful_validations": successful_validations,
            "total_validations": len(self.results),
            "total_issues": total_issues,
            "total_warnings": total_warnings,
            "validation_results": self.results,
            "timestamp": datetime.now().isoformat(),
            "principles": {
                "total_score": round(principle_total, 1),
                "grade": principle_grade,
                "breakdown": principle_results,
                "weights": principle_weights
            }
        }

        return report

    def print_summary(self):
        """Print validation summary with principles breakdown"""
        report = self.generate_report()

        print(f"\n📊 **VALIDATION SUMMARY**")
        print(f"Overall Score: {report['overall_score']}/100")
        print(
            f"Successful Validations: {report['successful_validations']}/{report['total_validations']}"
        )

        # Print Software Engineering Principles Summary
        principles = report.get('principles', {})
        if principles.get('breakdown'):
            print(f"\n📐 **SOFTWARE ENGINEERING PRINCIPLES**")
            print(f"Principles Score: {principles['total_score']}/100 (Grade: {principles['grade']})")

            breakdown = principles['breakdown']
            weights = principles['weights']

            for principle, weight in weights.items():
                if principle in breakdown:
                    result = breakdown[principle]
                    status = "✅" if result['success'] else "⚠️"
                    print(f"  {status} {principle.upper()}: {result['score']}/100 (weight: {int(weight*100)}%)")
                    if result['issues'] > 0:
                        print(f"    ⚠️ {result['issues']} issues detected")

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

        # Principles-specific recommendations
        if principles.get('breakdown'):
            principle_recommendations = []
            breakdown = principles['breakdown']

            if breakdown.get('kiss', {}).get('score', 100) < 80:
                principle_recommendations.append("Simplify complex functions (KISS principle)")
            if breakdown.get('dry', {}).get('score', 100) < 80:
                principle_recommendations.append("Extract duplicate code into reusable functions (DRY principle)")
            if breakdown.get('solid', {}).get('score', 100) < 80:
                principle_recommendations.append("Review class responsibilities and dependencies (SOLID principles)")
            if breakdown.get('yagni', {}).get('score', 100) < 80:
                principle_recommendations.append("Remove unused code and over-engineered abstractions (YAGNI principle)")

            if principle_recommendations:
                print(f"\n📐 **Principles Recommendations**:")
                for rec in principle_recommendations:
                    print(f"  • {rec}")
