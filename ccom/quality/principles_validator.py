#!/usr/bin/env python3
"""
Principles Validator - Software Engineering Principles Validation
RESTORED essential functionality from validators.py

Validates:
- KISS (Keep It Simple): Complexity, function length, nesting
- DRY (Don't Repeat Yourself): Code duplication detection
- SOLID: Single responsibility, proper architecture
- YAGNI (You Aren't Gonna Need It): Dead code detection
"""

import json
import ast
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..utils import SubprocessRunner, ErrorHandler, Display


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
        self.issues.append({
            "severity": severity,
            "message": message,
            "file": file_path,
            "timestamp": datetime.now().isoformat(),
        })

    def add_warning(self, message: str):
        """Add a warning to the results"""
        self.warnings.append(message)

    def add_fix(self, description: str):
        """Add a fix that was applied"""
        self.fixes_applied.append(description)


class PrinciplesValidator:
    """Software Engineering Principles validation (KISS, YAGNI, DRY, SOLID)"""

    def __init__(self, project_root: Path, target_files=None, max_files=100):
        self.project_root = project_root
        self.target_files = target_files
        self.max_files = max_files
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.subprocess_runner = SubprocessRunner()

        self.exclusion_patterns = [
            'node_modules/**', 'dist/**', 'build/**', '.git/**',
            'coverage/**', 'vendor/**', '*.min.js', '*.bundle.js',
            'lib/**', 'libs/**', '__pycache__/**', '.venv/**',
            'venv/**', '.env/**', 'legacy/**'
        ]

    def get_target_files(self, extensions=['*.js', '*.ts', '*.jsx', '*.tsx', '*.py']):
        """Get files to analyze with smart filtering and performance limits"""
        if self.target_files:
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
            main_files = [f for f in filtered_files if not any(test in str(f).lower()
                         for test in ['test', 'spec', '__test__'])]
            test_files = [f for f in filtered_files if any(test in str(f).lower()
                         for test in ['test', 'spec', '__test__'])]

            main_count = min(int(self.max_files * 0.8), len(main_files))
            test_count = min(self.max_files - main_count, len(test_files))

            filtered_files = main_files[:main_count] + test_files[:test_count]
            Display.info(f"⚡ Performance limit: Analyzing {len(filtered_files)} files (sampled from {len(files)} total)")

        return filtered_files

    def validate_all_principles(self) -> Dict[str, ValidationResult]:
        """Run all software engineering principles validation"""
        Display.section("📐 Software Engineering Principles Validation")

        results = {
            'kiss': self.validate_kiss(),
            'yagni': self.validate_yagni(),
            'dry': self.validate_dry(),
            'solid': self.validate_solid()
        }

        # Calculate overall score
        total_score = sum(r.score for r in results.values())
        avg_score = total_score / len(results) if results else 0

        Display.info(f"📊 Overall Principles Score: {avg_score:.0f}/100")

        return results

    def validate_kiss(self) -> ValidationResult:
        """KISS - Keep It Simple: Complexity and function length validation"""
        result = ValidationResult("KISS (Keep It Simple)")
        complexity_issues = []

        try:
            Display.progress("Analyzing code complexity...")

            # Check Python files for complexity
            python_files = [f for f in self.get_target_files(['*.py'])]
            for file_path in python_files:
                issues = self._analyze_python_complexity(file_path)
                complexity_issues.extend(issues)

            # Check JavaScript/TypeScript with jscpd if available
            js_files = [f for f in self.get_target_files(['*.js', '*.ts', '*.jsx', '*.tsx'])]
            if js_files:
                js_issues = self._analyze_js_complexity(js_files)
                complexity_issues.extend(js_issues)

            # Evaluate results
            if complexity_issues:
                for issue in complexity_issues:
                    result.add_issue("warning",
                        f"{issue['type']}: {issue.get('function', 'unknown')} in {issue['file']} "
                        f"({issue.get('complexity', issue.get('lines', 'N/A'))})",
                        issue['file'])

                result.score = max(0, 100 - (len(complexity_issues) * 5))
                result.success = result.score >= 70
            else:
                result.success = True
                result.score = 100

            return result

        except Exception as e:
            self.logger.error(f"KISS validation failed: {e}")
            result.add_issue("error", f"KISS validation error: {str(e)}")
            return result

    def validate_dry(self) -> ValidationResult:
        """DRY - Don't Repeat Yourself: Code duplication detection"""
        result = ValidationResult("DRY (Don't Repeat Yourself)")

        try:
            Display.progress("Detecting code duplication...")

            # Try jscpd for duplication detection
            duplication_result = self.subprocess_runner.run_command([
                "npx", "jscpd", ".", "--threshold", "3", "--format", "json"
            ], timeout=60)

            if duplication_result.returncode == 0 and duplication_result.stdout:
                try:
                    duplication_data = json.loads(duplication_result.stdout)
                    duplicates = duplication_data.get('duplicates', [])

                    if duplicates:
                        for dup in duplicates[:10]:  # Show first 10
                            result.add_issue("warning",
                                f"Code duplication detected: {dup.get('lines', 'N/A')} lines",
                                dup.get('firstFile', {}).get('name', 'unknown'))

                        duplication_percentage = len(duplicates) * 2  # Rough estimate
                        result.score = max(0, 100 - duplication_percentage)
                        result.success = result.score >= 70
                    else:
                        result.success = True
                        result.score = 100

                except json.JSONDecodeError:
                    result.add_warning("Could not parse duplication report")
                    result.score = 80  # Assume decent
                    result.success = True
            else:
                # Fallback: Simple text-based duplication check
                result = self._simple_duplication_check()

            return result

        except Exception as e:
            self.logger.error(f"DRY validation failed: {e}")
            result.add_issue("error", f"DRY validation error: {str(e)}")
            result.score = 60  # Assume moderate issues
            return result

    def validate_yagni(self) -> ValidationResult:
        """YAGNI - You Aren't Gonna Need It: Dead code detection"""
        result = ValidationResult("YAGNI (You Aren't Gonna Need It)")

        try:
            Display.progress("Detecting unused code...")

            # Check for unused imports and variables
            dead_code_issues = []
            python_files = self.get_target_files(['*.py'])

            for file_path in python_files:
                issues = self._analyze_python_unused_code(file_path)
                dead_code_issues.extend(issues)

            if dead_code_issues:
                for issue in dead_code_issues:
                    result.add_issue("info", issue['message'], issue['file'])

                result.score = max(0, 100 - (len(dead_code_issues) * 3))
                result.success = result.score >= 80
            else:
                result.success = True
                result.score = 100

            return result

        except Exception as e:
            self.logger.error(f"YAGNI validation failed: {e}")
            result.add_issue("error", f"YAGNI validation error: {str(e)}")
            result.score = 75
            return result

    def validate_solid(self) -> ValidationResult:
        """SOLID - Object-oriented design principles"""
        result = ValidationResult("SOLID Principles")

        try:
            Display.progress("Analyzing SOLID principles...")

            solid_issues = []
            python_files = self.get_target_files(['*.py'])

            for file_path in python_files:
                issues = self._analyze_solid_violations(file_path)
                solid_issues.extend(issues)

            if solid_issues:
                for issue in solid_issues:
                    result.add_issue("warning", issue['message'], issue['file'])

                result.score = max(0, 100 - (len(solid_issues) * 8))
                result.success = result.score >= 70
            else:
                result.success = True
                result.score = 100

            return result

        except Exception as e:
            self.logger.error(f"SOLID validation failed: {e}")
            result.add_issue("error", f"SOLID validation error: {str(e)}")
            result.score = 70
            return result

    def _analyze_python_complexity(self, file_path: Path) -> List[Dict]:
        """Analyze Python file complexity"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count lines in function
                    func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                    if func_lines > 50:
                        issues.append({
                            'file': str(file_path),
                            'function': node.name,
                            'lines': func_lines,
                            'type': 'Long function'
                        })

                elif isinstance(node, ast.ClassDef):
                    # Count methods in class
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 20:
                        issues.append({
                            'file': str(file_path),
                            'function': node.name,
                            'complexity': len(methods),
                            'type': 'Large class'
                        })

        except Exception as e:
            self.logger.warning(f"Could not analyze {file_path}: {e}")

        return issues

    def _analyze_js_complexity(self, js_files: List[Path]) -> List[Dict]:
        """Analyze JavaScript/TypeScript complexity"""
        issues = []

        # Check file sizes as proxy for complexity
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = sum(1 for _ in f)

                if lines > 300:  # Large file threshold
                    issues.append({
                        'file': str(file_path),
                        'lines': lines,
                        'type': 'Large file'
                    })

            except Exception as e:
                self.logger.warning(f"Could not analyze {file_path}: {e}")

        return issues

    def _simple_duplication_check(self) -> ValidationResult:
        """Simple text-based duplication detection fallback"""
        result = ValidationResult("DRY (Simple Check)")

        # Basic check for repeated patterns
        files = self.get_target_files()
        code_blocks = {}
        duplicates_found = 0

        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()

                # Check for repeated 5+ line blocks
                for i in range(len(lines) - 5):
                    block = ''.join(lines[i:i+5]).strip()
                    if len(block) > 100:  # Meaningful code block
                        if block in code_blocks:
                            duplicates_found += 1
                        else:
                            code_blocks[block] = file_path

            except Exception:
                continue

        if duplicates_found > 5:
            result.add_issue("warning", f"Found {duplicates_found} potential code duplications")
            result.score = max(0, 100 - (duplicates_found * 3))
        else:
            result.score = 95

        result.success = result.score >= 70
        return result

    def _analyze_python_unused_code(self, file_path: Path) -> List[Dict]:
        """Analyze Python file for unused code"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            # Simple checks for potential unused code
            if 'import' in content:
                lines = content.split('\n')
                imports = [line for line in lines if line.strip().startswith('import') or line.strip().startswith('from')]

                # Check if imports are used (basic check)
                for import_line in imports:
                    if 'import' in import_line:
                        module_name = import_line.split()[-1].split('.')[0]
                        if content.count(module_name) <= 1:  # Only appears in import
                            issues.append({
                                'file': str(file_path),
                                'message': f"Potentially unused import: {module_name}"
                            })

        except Exception as e:
            self.logger.warning(f"Could not analyze unused code in {file_path}: {e}")

        return issues

    def _analyze_solid_violations(self, file_path: Path) -> List[Dict]:
        """Analyze SOLID principle violations"""
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Single Responsibility: Large classes
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 15:
                        issues.append({
                            'file': str(file_path),
                            'message': f"Class '{node.name}' may violate Single Responsibility (${len(methods)} methods)"
                        })

        except Exception as e:
            self.logger.warning(f"Could not analyze SOLID violations in {file_path}: {e}")

        return issues

    def display_results(self, results: Dict[str, ValidationResult]) -> None:
        """Display comprehensive validation results"""
        Display.section("📊 Principles Validation Results")

        for principle, result in results.items():
            if result.success:
                Display.success(f"✅ {result.validator_name}: {result.score}/100")
            else:
                Display.warning(f"⚠️ {result.validator_name}: {result.score}/100")

            # Show top issues
            for issue in result.issues[:3]:
                print(f"    • {issue['message']}")

        # Overall assessment
        avg_score = sum(r.score for r in results.values()) / len(results)
        if avg_score >= 90:
            Display.success(f"🏆 Excellent principles compliance: {avg_score:.0f}/100")
        elif avg_score >= 70:
            Display.info(f"📈 Good principles compliance: {avg_score:.0f}/100")
        else:
            Display.warning(f"📉 Needs improvement: {avg_score:.0f}/100")