#!/usr/bin/env python3
"""
Comprehensive Validator Orchestrator
Integrates all validation capabilities with proper tool management and fallbacks

Provides:
- Tool-based validation (ESLint, Prettier, Black, Pylint, etc.)
- Software engineering principles (KISS, DRY, SOLID, YAGNI)
- Security validation (Bandit, Safety, npm audit)
- Auto-fix capabilities
- Comprehensive reporting with enterprise-grade metrics
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..utils import Display, ErrorHandler
from ..legacy.tools_manager import ToolsManager
from .principles_validator import PrinciplesValidator, ValidationResult
from ..memory.advanced_memory_keeper import AdvancedMemoryKeeper


class ComprehensiveValidator:
    """World-class validator orchestrator for CCOM"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Initialize tools manager for comprehensive tool integration
        self.tools_manager = ToolsManager(project_root)

        # Initialize specialized validators
        self.principles_validator = PrinciplesValidator(project_root)

        # Initialize advanced memory keeper
        self.memory_keeper = AdvancedMemoryKeeper(project_root)

        # Validation results storage
        self.validation_results = []
        self.validation_session_id = f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def run_comprehensive_validation(self, auto_fix: bool = False, target_scope: str = "all") -> Dict[str, Any]:
        """
        Run comprehensive validation across all dimensions

        Args:
            auto_fix: Whether to apply auto-fixes where possible
            target_scope: 'all', 'principles', 'quality', 'security'

        Returns:
            Comprehensive validation report
        """
        Display.header("🔍 CCOM Comprehensive Validation")
        Display.info(f"Session ID: {self.validation_session_id}")

        # Detect project type for targeted validation
        project_type = self._detect_project_type()
        Display.info(f"Project type: {project_type}")

        # Clear previous results
        self.validation_results = []

        try:
            # Phase 1: Software Engineering Principles
            if target_scope in ["all", "principles"]:
                Display.section("📐 Software Engineering Principles")
                principles_results = self._run_principles_validation()
                self.validation_results.extend(principles_results)

            # Phase 2: Code Quality (Tool-based)
            if target_scope in ["all", "quality"]:
                Display.section("🔧 Code Quality Validation")
                quality_results = self._run_quality_validation(project_type, auto_fix)
                self.validation_results.extend(quality_results)

            # Phase 3: Security Validation
            if target_scope in ["all", "security"]:
                Display.section("🛡️ Security Validation")
                security_results = self._run_security_validation(project_type)
                self.validation_results.extend(security_results)

            # Phase 4: Generate comprehensive report
            report = self._generate_comprehensive_report()

            # Phase 5: Advanced memory capture
            self._capture_session_to_memory(report)

            # Phase 6: Display results with memory insights
            self._display_validation_summary(report)

            return report

        except Exception as e:
            self.logger.error(f"Comprehensive validation failed: {e}")
            Display.error(f"Validation error: {str(e)}")
            return {"success": False, "error": str(e)}

    def _run_principles_validation(self) -> List[ValidationResult]:
        """Run software engineering principles validation"""
        results = []

        try:
            Display.progress("Validating software engineering principles...")

            # Run all principles
            principles_results = self.principles_validator.validate_all_principles()

            for principle_name, result in principles_results.items():
                results.append(result)

                # Display immediate feedback
                status = "✅" if result.success else "⚠️"
                Display.info(f"{status} {result.validator_name}: {result.score}/100")

        except Exception as e:
            self.logger.error(f"Principles validation failed: {e}")
            error_result = ValidationResult("Principles Validation")
            error_result.add_issue("error", f"Principles validation failed: {str(e)}")
            results.append(error_result)

        return results

    def _run_quality_validation(self, project_type: str, auto_fix: bool = False) -> List[ValidationResult]:
        """Run code quality validation using appropriate tools"""
        results = []

        try:
            # JavaScript/TypeScript quality validation
            if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
                results.extend(self._validate_js_quality(auto_fix))

            # Python quality validation
            elif project_type == "python":
                results.extend(self._validate_python_quality(auto_fix))

            # Generic quality checks
            results.extend(self._validate_generic_quality())

        except Exception as e:
            self.logger.error(f"Quality validation failed: {e}")
            error_result = ValidationResult("Quality Validation")
            error_result.add_issue("error", f"Quality validation failed: {str(e)}")
            results.append(error_result)

        return results

    def _validate_js_quality(self, auto_fix: bool = False) -> List[ValidationResult]:
        """Validate JavaScript/TypeScript code quality"""
        results = []

        # ESLint validation
        eslint_result = self._run_eslint_validation(auto_fix)
        results.append(eslint_result)

        # Prettier validation
        prettier_result = self._run_prettier_validation(auto_fix)
        results.append(prettier_result)

        return results

    def _run_eslint_validation(self, auto_fix: bool = False) -> ValidationResult:
        """Run ESLint validation with auto-fix support"""
        result = ValidationResult("ESLint")

        try:
            if not self._check_tool_available("eslint"):
                result.add_warning("ESLint not available - skipping JavaScript/TypeScript validation")
                result.score = 90
                result.success = True
                return result

            # Auto-fix first if requested
            if auto_fix:
                Display.progress("Running ESLint auto-fix...")
                fix_exit_code, fix_stdout, fix_stderr = self._run_tool_command([
                    "npx", "eslint", ".", "--fix"
                ])

                if fix_exit_code == 0:
                    result.add_fix("Applied ESLint auto-fixes")

            # Run ESLint validation
            Display.progress("Running ESLint validation...")
            exit_code, stdout, stderr = self._run_tool_command([
                "npx", "eslint", ".", "--format", "json"
            ])

            if exit_code == 0:
                result.success = True
                result.score = 100
                result.add_warning("No ESLint issues found")
            else:
                try:
                    if stdout:
                        lint_results = json.loads(stdout)
                        error_count = 0
                        warning_count = 0

                        for file_result in lint_results:
                            file_path = file_result.get("filePath", "unknown")
                            for message in file_result.get("messages", []):
                                severity = "error" if message.get("severity") == 2 else "warning"

                                result.add_issue(
                                    severity=severity,
                                    message=f"Line {message.get('line', '?')}: {message.get('message', 'Unknown error')}",
                                    file_path=file_path
                                )

                                if severity == "error":
                                    error_count += 1
                                else:
                                    warning_count += 1

                        # Calculate score
                        if error_count == 0 and warning_count == 0:
                            result.score = 100
                        elif error_count == 0:
                            result.score = max(80, 100 - warning_count * 2)
                        else:
                            result.score = max(0, 100 - error_count * 10 - warning_count * 2)

                        result.success = error_count == 0

                except json.JSONDecodeError:
                    result.add_issue("error", f"ESLint output parsing failed: {stderr}")
                    result.score = 50

        except Exception as e:
            self.logger.error(f"ESLint validation failed: {e}")
            result.add_issue("error", f"ESLint execution failed: {str(e)}")
            result.score = 40

        return result

    def _run_prettier_validation(self, auto_fix: bool = False) -> ValidationResult:
        """Run Prettier validation with auto-fix support"""
        result = ValidationResult("Prettier")

        try:
            if not self._check_tool_available("prettier"):
                result.add_warning("Prettier not available - skipping format validation")
                result.score = 90
                result.success = True
                return result

            # Auto-fix first if requested
            if auto_fix:
                Display.progress("Running Prettier auto-format...")
                fix_exit_code, fix_stdout, fix_stderr = self._run_tool_command([
                    "npx", "prettier", "--write", "."
                ])

                if fix_exit_code == 0:
                    result.add_fix("Applied Prettier formatting")

            # Run Prettier validation
            Display.progress("Running Prettier validation...")
            exit_code, stdout, stderr = self._run_tool_command([
                "npx", "prettier", "--check", "."
            ])

            if exit_code == 0:
                result.success = True
                result.score = 100
            else:
                # Parse prettier output for unformatted files
                unformatted_files = [
                    line.strip() for line in stdout.split("\n")
                    if line.strip() and not line.startswith("[")
                ]

                for file_path in unformatted_files[:10]:  # Show first 10
                    result.add_issue("warning", "File needs formatting", file_path)

                result.score = max(70, 100 - len(unformatted_files) * 5)
                result.success = len(unformatted_files) == 0

        except Exception as e:
            self.logger.error(f"Prettier validation failed: {e}")
            result.add_issue("error", f"Prettier execution failed: {str(e)}")
            result.score = 40

        return result

    def _validate_python_quality(self, auto_fix: bool = False) -> List[ValidationResult]:
        """Validate Python code quality"""
        results = []

        # Black formatting
        black_result = self._run_black_validation(auto_fix)
        results.append(black_result)

        # Pylint analysis
        pylint_result = self._run_pylint_validation()
        results.append(pylint_result)

        return results

    def _run_black_validation(self, auto_fix: bool = False) -> ValidationResult:
        """Run Black validation with auto-fix support"""
        result = ValidationResult("Black")

        try:
            if not self._check_tool_available("black"):
                result.add_warning("Black not available - skipping Python format validation")
                result.score = 90
                result.success = True
                return result

            # Auto-fix first if requested
            if auto_fix:
                Display.progress("Running Black auto-format...")
                fix_exit_code, fix_stdout, fix_stderr = self._run_tool_command([
                    sys.executable, "-m", "black", "."
                ])

                if fix_exit_code == 0:
                    result.add_fix("Applied Black formatting")

            # Run Black validation
            Display.progress("Running Black validation...")
            exit_code, stdout, stderr = self._run_tool_command([
                sys.executable, "-m", "black", "--check", "."
            ])

            if exit_code == 0:
                result.success = True
                result.score = 100
            else:
                result.add_issue("warning", f"Python files need Black formatting: {stdout}")
                result.score = 80

        except Exception as e:
            self.logger.error(f"Black validation failed: {e}")
            result.add_issue("error", f"Black execution failed: {str(e)}")
            result.score = 40

        return result

    def _run_pylint_validation(self) -> ValidationResult:
        """Run Pylint validation"""
        result = ValidationResult("Pylint")

        try:
            if not self._check_tool_available("pylint"):
                result.add_warning("Pylint not available - skipping Python quality validation")
                result.score = 90
                result.success = True
                return result

            # Find Python files
            py_files = list(self.project_root.glob("**/*.py"))
            if not py_files:
                result.success = True
                result.score = 100
                return result

            Display.progress("Running Pylint analysis...")
            exit_code, stdout, stderr = self._run_tool_command([
                sys.executable, "-m", "pylint",
                "--output-format=json",
                "--disable=missing-docstring,too-few-public-methods"
            ] + [str(f) for f in py_files[:10]])  # Limit to first 10 files

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
                            file_path=path
                        )

                        if severity in ["error", "fatal"]:
                            error_count += 1
                        else:
                            warning_count += 1

                    # Calculate score
                    if error_count == 0 and warning_count == 0:
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

        except Exception as e:
            self.logger.error(f"Pylint validation failed: {e}")
            result.add_issue("error", f"Pylint execution failed: {str(e)}")
            result.score = 40

        return result

    def _validate_generic_quality(self) -> List[ValidationResult]:
        """Run generic quality checks applicable to all project types"""
        results = []

        # File structure analysis
        structure_result = self._analyze_project_structure()
        results.append(structure_result)

        return results

    def _analyze_project_structure(self) -> ValidationResult:
        """Analyze project structure for quality indicators"""
        result = ValidationResult("Project Structure")

        try:
            Display.progress("Analyzing project structure...")

            issues = []

            # Check for essential files
            essential_files = {
                "README.md": "Project documentation",
                ".gitignore": "Version control hygiene",
                "package.json": "Node.js dependency management" if (self.project_root / "package.json").exists() else None,
                "requirements.txt": "Python dependency management" if any((self.project_root / f).exists() for f in ["*.py"]) else None
            }

            missing_files = []
            for file_name, description in essential_files.items():
                if description and not (self.project_root / file_name).exists():
                    missing_files.append(f"{file_name} ({description})")

            if missing_files:
                for missing in missing_files:
                    result.add_issue("warning", f"Missing essential file: {missing}")

            # Check directory structure
            large_root_files = [
                f for f in self.project_root.iterdir()
                if f.is_file() and f.stat().st_size > 50000  # > 50KB files in root
            ]

            for large_file in large_root_files:
                result.add_issue("info", f"Large file in root directory: {large_file.name}")

            # Calculate score
            structure_score = 100
            structure_score -= len(missing_files) * 10
            structure_score -= len(large_root_files) * 5

            result.score = max(60, structure_score)
            result.success = result.score >= 80

        except Exception as e:
            self.logger.error(f"Structure analysis failed: {e}")
            result.add_issue("error", f"Structure analysis failed: {str(e)}")
            result.score = 70

        return result

    def _run_security_validation(self, project_type: str) -> List[ValidationResult]:
        """Run security validation"""
        results = []

        try:
            # Dependency security
            dep_result = self._validate_dependency_security(project_type)
            results.append(dep_result)

            # Python-specific security
            if project_type == "python":
                bandit_result = self._run_bandit_validation()
                results.append(bandit_result)

        except Exception as e:
            self.logger.error(f"Security validation failed: {e}")
            error_result = ValidationResult("Security Validation")
            error_result.add_issue("error", f"Security validation failed: {str(e)}")
            results.append(error_result)

        return results

    def _validate_dependency_security(self, project_type: str) -> ValidationResult:
        """Validate dependency security"""
        result = ValidationResult("Dependency Security")

        try:
            if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
                # npm audit
                if (self.project_root / "package.json").exists():
                    Display.progress("Running npm security audit...")
                    exit_code, stdout, stderr = self._run_tool_command([
                        "npm", "audit", "--json"
                    ])

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
                                        severity="error" if severity == "critical" else "warning",
                                        message=f"{severity.title()} vulnerability in {vuln.get('name', 'unknown package')}"
                                    )

                            if high_critical == 0:
                                result.success = True
                                result.score = 100
                            else:
                                result.score = max(0, 100 - high_critical * 20)

                    except json.JSONDecodeError:
                        result.add_warning("Could not parse npm audit output")
                        result.score = 90
                        result.success = True

            elif project_type == "python":
                # Safety check
                if self._check_tool_available("safety"):
                    Display.progress("Running Python security audit...")
                    exit_code, stdout, stderr = self._run_tool_command([
                        sys.executable, "-m", "safety", "check", "--json"
                    ])

                    try:
                        if stdout and stdout.strip() != "[]":
                            safety_results = json.loads(stdout)

                            for vuln in safety_results:
                                result.add_issue(
                                    severity="error",
                                    message=f"Vulnerable package: {vuln.get('package', 'unknown')} - {vuln.get('advisory', 'No details')}"
                                )

                            result.score = max(0, 100 - len(safety_results) * 25)
                        else:
                            result.success = True
                            result.score = 100

                    except json.JSONDecodeError:
                        result.add_warning("Could not parse safety check output")
                        result.score = 90
                        result.success = True

        except Exception as e:
            self.logger.error(f"Dependency security validation failed: {e}")
            result.add_issue("error", f"Dependency security check failed: {str(e)}")
            result.score = 50

        return result

    def _run_bandit_validation(self) -> ValidationResult:
        """Run Bandit security validation for Python"""
        result = ValidationResult("Bandit Security")

        try:
            if not self._check_tool_available("bandit"):
                result.add_warning("Bandit not available - skipping Python security validation")
                result.score = 90
                result.success = True
                return result

            py_files = list(self.project_root.glob("**/*.py"))
            if not py_files:
                result.success = True
                result.score = 100
                return result

            Display.progress("Running Bandit security analysis...")
            exit_code, stdout, stderr = self._run_tool_command([
                sys.executable, "-m", "bandit", "-r", ".", "-f", "json"
            ])

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
                            file_path=filename
                        )

                    high_issues = sum(
                        1 for issue in bandit_results.get("results", [])
                        if issue.get("issue_severity") == "HIGH"
                    )
                    medium_issues = sum(
                        1 for issue in bandit_results.get("results", [])
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

        except Exception as e:
            self.logger.error(f"Bandit validation failed: {e}")
            result.add_issue("error", f"Bandit execution failed: {str(e)}")
            result.score = 40

        return result

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_score = 0
        successful_validations = 0
        total_issues = 0
        total_warnings = 0

        # Separate results by category
        principles_results = {}
        quality_results = []
        security_results = []

        for result in self.validation_results:
            total_score += result.score
            if result.success:
                successful_validations += 1
            total_issues += len([i for i in result.issues if i["severity"] == "error"])
            total_warnings += len([i for i in result.issues if i["severity"] == "warning"])
            total_warnings += len(result.warnings)

            # Categorize results
            if result.validator_name in ['KISS (Keep It Simple)', 'YAGNI (You Aren\'t Gonna Need It)',
                                      'DRY (Don\'t Repeat Yourself)', 'SOLID Principles']:
                principle_key = result.validator_name.split(' ')[0].lower()
                principles_results[principle_key] = {
                    'score': result.score,
                    'success': result.success,
                    'issues': len(result.issues)
                }
            elif result.validator_name in ['Bandit Security', 'Dependency Security']:
                security_results.append(result)
            else:
                quality_results.append(result)

        avg_score = total_score / len(self.validation_results) if self.validation_results else 0

        # Calculate grades
        overall_grade = self._calculate_grade(avg_score)

        # Principles scoring
        principle_weights = {'kiss': 0.3, 'yagni': 0.2, 'dry': 0.3, 'solid': 0.2}
        principle_total = sum(
            principles_results.get(p, {}).get('score', 0) * weight
            for p, weight in principle_weights.items()
        )
        principle_grade = self._calculate_grade(principle_total)

        return {
            "session_id": self.validation_session_id,
            "timestamp": datetime.now().isoformat(),
            "overall": {
                "score": round(avg_score, 1),
                "grade": overall_grade,
                "successful_validations": successful_validations,
                "total_validations": len(self.validation_results),
                "total_issues": total_issues,
                "total_warnings": total_warnings
            },
            "principles": {
                "score": round(principle_total, 1),
                "grade": principle_grade,
                "breakdown": principles_results,
                "weights": principle_weights
            },
            "quality": {
                "results": quality_results,
                "score": sum(r.score for r in quality_results) / len(quality_results) if quality_results else 100
            },
            "security": {
                "results": security_results,
                "score": sum(r.score for r in security_results) / len(security_results) if security_results else 100
            },
            "validation_results": self.validation_results,
            "recommendations": self._generate_recommendations(avg_score, principles_results, total_issues, total_warnings)
        }

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C+'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    def _generate_recommendations(self, overall_score: float, principles: Dict, issues: int, warnings: int) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Overall recommendations
        if overall_score >= 95:
            recommendations.append("🎉 Exceptional code quality! Consider setting up automated quality gates.")
        elif overall_score >= 80:
            recommendations.append("🔧 Good code quality. Focus on addressing remaining warnings.")
        else:
            recommendations.append("⚠️ Code quality needs improvement. Prioritize fixing errors first.")

        # Principles-specific recommendations
        if principles.get('kiss', {}).get('score', 100) < 80:
            recommendations.append("📐 Simplify complex functions and reduce file sizes (KISS principle)")

        if principles.get('dry', {}).get('score', 100) < 80:
            recommendations.append("🔄 Extract duplicate code into reusable functions (DRY principle)")

        if principles.get('solid', {}).get('score', 100) < 80:
            recommendations.append("🏗️ Review class responsibilities and dependencies (SOLID principles)")

        if principles.get('yagni', {}).get('score', 100) < 80:
            recommendations.append("🧹 Remove unused code and over-engineered abstractions (YAGNI principle)")

        # Action-oriented recommendations
        if issues > 0:
            recommendations.append(f"🚨 Address {issues} critical errors immediately")

        if warnings > 10:
            recommendations.append(f"📝 Review and resolve {warnings} warnings for better code health")

        return recommendations

    def _display_validation_summary(self, report: Dict[str, Any]) -> None:
        """Display comprehensive validation summary"""
        Display.header("📊 CCOM Validation Summary")

        overall = report['overall']
        principles = report['principles']

        # Overall status
        Display.section("Overall Quality Status")
        Display.key_value_table({
            "Overall Score": f"{overall['score']}/100 (Grade: {overall['grade']})",
            "Successful Validations": f"{overall['successful_validations']}/{overall['total_validations']}",
            "Critical Issues": overall['total_issues'],
            "Warnings": overall['total_warnings']
        })

        # Principles breakdown
        if principles['breakdown']:
            Display.section("📐 Software Engineering Principles")
            Display.info(f"Principles Score: {principles['score']}/100 (Grade: {principles['grade']})")

            for principle, weight in principles['weights'].items():
                if principle in principles['breakdown']:
                    result = principles['breakdown'][principle]
                    status = "✅" if result['success'] else "⚠️"
                    Display.info(f"  {status} {principle.upper()}: {result['score']}/100 (weight: {int(weight*100)}%)")

        # Quality status indicator
        if overall['total_issues'] == 0 and overall['total_warnings'] == 0:
            Display.success("✅ **ENTERPRISE GRADE** - No issues found!")
        elif overall['total_issues'] == 0:
            Display.warning(f"🟡 **GOOD QUALITY** - {overall['total_warnings']} warnings to review")
        else:
            Display.error(f"🔴 **NEEDS ATTENTION** - {overall['total_issues']} errors, {overall['total_warnings']} warnings")

        # Recommendations with memory insights
        Display.section("💡 Recommendations")
        for rec in report['recommendations']:
            Display.info(f"  • {rec}")

        # Memory insights
        memory_insights = self._get_memory_insights()
        if memory_insights and memory_insights.get("intelligent_recommendations"):
            Display.section("🧠 Memory Intelligence")
            quality_status = memory_insights.get("project_quality_status", {})
            if quality_status:
                Display.info(f"Quality Trend: {quality_status.get('trending', 'stable').title()}")
                Display.info(f"Total Validations: {quality_status.get('validation_count', 0)}")

            for insight_rec in memory_insights["intelligent_recommendations"]:
                Display.info(f"  • {insight_rec}")

            memory_stats = memory_insights.get("memory_insights", {})
            if memory_stats:
                Display.info(f"Learning: {memory_stats.get('patterns_learned', 0)} patterns, {memory_stats.get('improvements_tracked', 0)} improvements tracked")

    def _detect_project_type(self) -> str:
        """Detect project type for targeted validation"""
        return self.tools_manager.detect_project_type()

    def _check_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available"""
        try:
            installed_tools = self.tools_manager.check_tool_availability()
            return installed_tools.get(tool_name, {}).get("installed", False)
        except Exception:
            return False

    def _run_tool_command(self, cmd: List[str], timeout: int = 60) -> tuple:
        """Run a tool command with proper error handling"""
        try:
            import subprocess
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def _capture_session_to_memory(self, report: Dict[str, Any]) -> None:
        """Capture validation session to advanced memory system"""
        try:
            self.memory_keeper.capture_validation_session(report)
        except Exception as e:
            self.logger.warning(f"Memory capture failed: {e}")

    def _get_memory_insights(self) -> Dict[str, Any]:
        """Get memory insights for enhanced recommendations"""
        try:
            return self.memory_keeper.get_context_summary()
        except Exception as e:
            self.logger.warning(f"Failed to get memory insights: {e}")
            return {}