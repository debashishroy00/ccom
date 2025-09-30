#!/usr/bin/env python3
"""
Security Guardian Agent SDK Implementation v5.1
Comprehensive security scanning and hardening for modern development
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime

from .sdk_agent_base import SDKAgentBase, AgentResult, StreamingUpdate
from ..utils import SubprocessRunner, ErrorHandler, Display


class SecurityGuardianAgent(SDKAgentBase):
    """
    Security Guardian Agent - Full SDK Implementation v5.1

    Enterprise-grade security scanning with:
    - Dependency vulnerability scanning
    - Secret detection and remediation
    - Code security analysis
    - Configuration hardening
    - Compliance reporting
    """

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        super().__init__(project_root, config)
        self.subprocess_runner = SubprocessRunner()
        self.error_handler = ErrorHandler(self.logger)

        # Security scanning configuration
        self.security_config = {
            "scan_dependencies": True,
            "scan_secrets": True,
            "scan_code": True,
            "check_configs": True,
            "compliance_mode": config.get("compliance_mode", "standard"),
            "severity_threshold": config.get("severity_threshold", "medium")
        }

    def _get_capabilities(self) -> List[str]:
        return [
            "dependency_vulnerability_scanning",
            "secret_detection_and_remediation",
            "code_security_analysis",
            "configuration_hardening",
            "compliance_reporting",
            "security_metrics",
            "automated_remediation",
            "security_documentation"
        ]

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute comprehensive security scanning"""
        try:
            self.logger.info("Starting Security Guardian comprehensive scan")

            # Initialize results
            security_results = {
                "scan_id": f"security_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "scans": {},
                "overall_score": 0,
                "risk_level": "unknown",
                "recommendations": [],
                "metrics": {}
            }

            # Execute security scans
            security_results["scans"]["dependencies"] = await self._scan_dependencies()
            security_results["scans"]["secrets"] = await self._scan_secrets()
            security_results["scans"]["code_analysis"] = await self._analyze_code_security()
            security_results["scans"]["configurations"] = await self._check_security_configs()

            # Calculate overall security score
            security_results["overall_score"] = self._calculate_security_score(security_results["scans"])
            security_results["risk_level"] = self._determine_risk_level(security_results["overall_score"])
            security_results["recommendations"] = self._generate_recommendations(security_results["scans"])
            security_results["metrics"] = self._calculate_metrics(security_results["scans"])

            # Determine success based on risk level
            success = security_results["risk_level"] in ["low", "medium"]

            message = f"🛡️ Security Guardian: {security_results['risk_level'].upper()} risk level (Score: {security_results['overall_score']}/100)"

            return AgentResult(
                success=success,
                message=message,
                data=security_results,
                metrics=security_results["metrics"]
            )

        except Exception as e:
            self.logger.error(f"Security Guardian execution failed: {e}")
            return AgentResult(
                success=False,
                message=f"❌ Security Guardian failed: {str(e)}",
                data={"error": str(e), "scan_id": f"failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            )

    async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[StreamingUpdate, None]:
        """Execute security scanning with real-time streaming updates"""
        yield StreamingUpdate(
            type="progress",
            content="🛡️ **SECURITY GUARDIAN ACTIVATED** - Enterprise security scanning initiated"
        )

        yield StreamingUpdate(
            type="status",
            content="🔍 Phase 1/4: Dependency vulnerability scanning..."
        )

        # Stream dependency scan
        deps_result = await self._scan_dependencies()
        yield StreamingUpdate(
            type="result",
            content=f"📦 Dependencies: {deps_result['vulnerabilities_found']} vulnerabilities found"
        )

        yield StreamingUpdate(
            type="status",
            content="🕵️ Phase 2/4: Secret detection scanning..."
        )

        # Stream secret scan
        secrets_result = await self._scan_secrets()
        yield StreamingUpdate(
            type="result",
            content=f"🔐 Secrets: {secrets_result['secrets_found']} potential secrets detected"
        )

        yield StreamingUpdate(
            type="status",
            content="🔬 Phase 3/4: Code security analysis..."
        )

        # Stream code analysis
        code_result = await self._analyze_code_security()
        yield StreamingUpdate(
            type="result",
            content=f"⚡ Code Security: {code_result['issues_found']} security issues identified"
        )

        yield StreamingUpdate(
            type="status",
            content="⚙️ Phase 4/4: Configuration security check..."
        )

        # Stream config check
        config_result = await self._check_security_configs()
        yield StreamingUpdate(
            type="result",
            content=f"🔧 Configuration: {config_result['misconfigurations']} security misconfigurations"
        )

        # Calculate final results
        overall_score = self._calculate_security_score({
            "dependencies": deps_result,
            "secrets": secrets_result,
            "code_analysis": code_result,
            "configurations": config_result
        })

        risk_level = self._determine_risk_level(overall_score)

        yield StreamingUpdate(
            type="completion",
            content=f"✅ **SECURITY SCAN COMPLETE** - Risk Level: {risk_level.upper()} (Score: {overall_score}/100)"
        )

    async def _scan_dependencies(self) -> Dict[str, Any]:
        """Scan for dependency vulnerabilities"""
        result = {
            "scan_type": "dependency_vulnerabilities",
            "vulnerabilities_found": 0,
            "high_severity": 0,
            "medium_severity": 0,
            "low_severity": 0,
            "packages_scanned": 0,
            "details": []
        }

        try:
            # Check for package.json (npm audit)
            package_json = self.project_root / "package.json"
            if package_json.exists():
                npm_result = await self._run_npm_audit()
                result.update(npm_result)

            # Check for requirements.txt (safety check)
            requirements_txt = self.project_root / "requirements.txt"
            if requirements_txt.exists():
                python_result = await self._run_python_safety_check()
                result = self._merge_vulnerability_results(result, python_result)

            # Check for Pipfile (pipenv check)
            pipfile = self.project_root / "Pipfile"
            if pipfile.exists():
                pipenv_result = await self._run_pipenv_check()
                result = self._merge_vulnerability_results(result, pipenv_result)

        except Exception as e:
            self.logger.error(f"Dependency scanning failed: {e}")
            result["error"] = str(e)

        return result

    async def _run_npm_audit(self) -> Dict[str, Any]:
        """Run npm audit for JavaScript dependencies"""
        try:
            audit_result = self.subprocess_runner.run_command([
                "npm", "audit", "--json"
            ], timeout=120)

            if audit_result.returncode == 0 and audit_result.stdout:
                audit_data = json.loads(audit_result.stdout)

                return {
                    "vulnerabilities_found": audit_data.get("vulnerabilities", {}).get("total", 0),
                    "high_severity": audit_data.get("vulnerabilities", {}).get("high", 0),
                    "medium_severity": audit_data.get("vulnerabilities", {}).get("moderate", 0),
                    "low_severity": audit_data.get("vulnerabilities", {}).get("low", 0),
                    "packages_scanned": audit_data.get("metadata", {}).get("totalDependencies", 0),
                    "details": audit_data.get("advisories", {})
                }

            return {"vulnerabilities_found": 0, "packages_scanned": 0}

        except Exception as e:
            self.logger.warning(f"npm audit failed: {e}")
            return {"vulnerabilities_found": 0, "error": str(e)}

    async def _run_python_safety_check(self) -> Dict[str, Any]:
        """Run safety check for Python dependencies"""
        try:
            safety_result = self.subprocess_runner.run_command([
                "safety", "check", "--json"
            ], timeout=120)

            if safety_result.returncode == 0 and safety_result.stdout:
                safety_data = json.loads(safety_result.stdout)

                vulnerabilities = len(safety_data) if isinstance(safety_data, list) else 0

                return {
                    "vulnerabilities_found": vulnerabilities,
                    "high_severity": sum(1 for vuln in safety_data if vuln.get("severity", "").lower() == "high"),
                    "medium_severity": sum(1 for vuln in safety_data if vuln.get("severity", "").lower() == "medium"),
                    "low_severity": sum(1 for vuln in safety_data if vuln.get("severity", "").lower() == "low"),
                    "details": safety_data
                }

            return {"vulnerabilities_found": 0}

        except Exception as e:
            self.logger.warning(f"Python safety check failed: {e}")
            return {"vulnerabilities_found": 0, "error": str(e)}

    async def _run_pipenv_check(self) -> Dict[str, Any]:
        """Run pipenv check for Python dependencies"""
        try:
            pipenv_result = self.subprocess_runner.run_command([
                "pipenv", "check", "--json"
            ], timeout=120)

            if pipenv_result.returncode == 0 and pipenv_result.stdout:
                pipenv_data = json.loads(pipenv_result.stdout)
                vulnerabilities = len(pipenv_data) if isinstance(pipenv_data, list) else 0

                return {
                    "vulnerabilities_found": vulnerabilities,
                    "details": pipenv_data
                }

            return {"vulnerabilities_found": 0}

        except Exception as e:
            self.logger.warning(f"Pipenv check failed: {e}")
            return {"vulnerabilities_found": 0, "error": str(e)}

    async def _scan_secrets(self) -> Dict[str, Any]:
        """Scan for exposed secrets and credentials"""
        result = {
            "scan_type": "secret_detection",
            "secrets_found": 0,
            "high_risk_secrets": 0,
            "medium_risk_secrets": 0,
            "low_risk_secrets": 0,
            "files_scanned": 0,
            "patterns_detected": []
        }

        try:
            # Define secret patterns to search for
            secret_patterns = [
                (r'(?i)password\s*[:=]\s*["\']?[^"\'\s]{8,}', "password", "high"),
                (r'(?i)api[_-]?key\s*[:=]\s*["\']?[A-Za-z0-9]{20,}', "api_key", "high"),
                (r'(?i)secret\s*[:=]\s*["\']?[A-Za-z0-9]{16,}', "secret", "high"),
                (r'(?i)token\s*[:=]\s*["\']?[A-Za-z0-9]{20,}', "token", "medium"),
                (r'[A-Za-z0-9]{40}', "potential_hash", "low"),
                (r'(?i)private[_-]?key', "private_key", "high"),
                (r'-----BEGIN.*PRIVATE KEY-----', "private_key_content", "high")
            ]

            files_to_scan = [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.json",
                "*.yaml", "*.yml", "*.env", "*.config", "*.ini"
            ]

            files_scanned = 0
            for pattern in files_to_scan:
                for file_path in self.project_root.glob(f"**/{pattern}"):
                    if self._should_scan_file(file_path):
                        secrets_in_file = self._scan_file_for_secrets(file_path, secret_patterns)
                        result["patterns_detected"].extend(secrets_in_file)
                        files_scanned += 1

            result["files_scanned"] = files_scanned
            result["secrets_found"] = len(result["patterns_detected"])

            # Categorize by risk level
            for pattern in result["patterns_detected"]:
                risk_level = pattern["risk_level"]
                if risk_level == "high":
                    result["high_risk_secrets"] += 1
                elif risk_level == "medium":
                    result["medium_risk_secrets"] += 1
                else:
                    result["low_risk_secrets"] += 1

        except Exception as e:
            self.logger.error(f"Secret scanning failed: {e}")
            result["error"] = str(e)

        return result

    def _should_scan_file(self, file_path: Path) -> bool:
        """Determine if a file should be scanned for secrets"""
        # Skip certain directories and files
        skip_patterns = [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            "dist", "build", "coverage", ".min.", "legacy"
        ]

        file_str = str(file_path)
        return not any(pattern in file_str for pattern in skip_patterns)

    def _scan_file_for_secrets(self, file_path: Path, patterns: List) -> List[Dict]:
        """Scan individual file for secret patterns"""
        import re

        secrets_found = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            for pattern, secret_type, risk_level in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    secrets_found.append({
                        "file": str(file_path.relative_to(self.project_root)),
                        "type": secret_type,
                        "risk_level": risk_level,
                        "pattern": pattern[:50] + "..." if len(pattern) > 50 else pattern,
                        "line": content[:match.start()].count('\n') + 1
                    })

        except Exception as e:
            self.logger.warning(f"Could not scan {file_path}: {e}")

        return secrets_found

    async def _analyze_code_security(self) -> Dict[str, Any]:
        """Analyze code for security vulnerabilities"""
        result = {
            "scan_type": "code_security_analysis",
            "issues_found": 0,
            "high_severity_issues": 0,
            "medium_severity_issues": 0,
            "low_severity_issues": 0,
            "files_analyzed": 0,
            "security_issues": []
        }

        try:
            # Run bandit for Python security analysis
            python_files = list(self.project_root.glob("**/*.py"))
            if python_files:
                bandit_result = await self._run_bandit_analysis()
                result.update(bandit_result)

            # Add JavaScript/TypeScript security checks if needed
            js_files = list(self.project_root.glob("**/*.js")) + list(self.project_root.glob("**/*.ts"))
            if js_files:
                js_result = await self._analyze_js_security()
                result = self._merge_security_results(result, js_result)

        except Exception as e:
            self.logger.error(f"Code security analysis failed: {e}")
            result["error"] = str(e)

        return result

    async def _run_bandit_analysis(self) -> Dict[str, Any]:
        """Run bandit security analysis for Python code"""
        try:
            bandit_result = self.subprocess_runner.run_command([
                "bandit", "-r", ".", "-f", "json"
            ], timeout=120)

            if bandit_result.returncode in [0, 1] and bandit_result.stdout:
                bandit_data = json.loads(bandit_result.stdout)

                issues = bandit_data.get("results", [])

                return {
                    "issues_found": len(issues),
                    "high_severity_issues": sum(1 for issue in issues if issue.get("issue_severity") == "HIGH"),
                    "medium_severity_issues": sum(1 for issue in issues if issue.get("issue_severity") == "MEDIUM"),
                    "low_severity_issues": sum(1 for issue in issues if issue.get("issue_severity") == "LOW"),
                    "files_analyzed": len(set(issue.get("filename", "") for issue in issues)),
                    "security_issues": issues
                }

            return {"issues_found": 0, "files_analyzed": 0}

        except Exception as e:
            self.logger.warning(f"Bandit analysis failed: {e}")
            return {"issues_found": 0, "error": str(e)}

    async def _analyze_js_security(self) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript for security issues"""
        # This is a simplified analysis - in production, you'd use tools like ESLint security plugins
        result = {
            "issues_found": 0,
            "files_analyzed": 0,
            "security_issues": []
        }

        try:
            js_files = list(self.project_root.glob("**/*.js")) + list(self.project_root.glob("**/*.ts"))

            dangerous_patterns = [
                (r'eval\s*\(', "Use of eval() function", "HIGH"),
                (r'innerHTML\s*=', "Direct innerHTML assignment", "MEDIUM"),
                (r'document\.write\s*\(', "Use of document.write", "MEDIUM"),
                (r'setTimeout\s*\(\s*["\']', "String-based setTimeout", "MEDIUM")
            ]

            for file_path in js_files:
                if self._should_scan_file(file_path):
                    issues_in_file = self._scan_js_file_security(file_path, dangerous_patterns)
                    result["security_issues"].extend(issues_in_file)
                    result["files_analyzed"] += 1

            result["issues_found"] = len(result["security_issues"])

        except Exception as e:
            self.logger.warning(f"JavaScript security analysis failed: {e}")
            result["error"] = str(e)

        return result

    def _scan_js_file_security(self, file_path: Path, patterns: List) -> List[Dict]:
        """Scan JavaScript file for security patterns"""
        import re

        issues_found = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            for pattern, description, severity in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    issues_found.append({
                        "filename": str(file_path.relative_to(self.project_root)),
                        "issue_text": description,
                        "issue_severity": severity,
                        "line_number": content[:match.start()].count('\n') + 1,
                        "test_name": "js_security_scan"
                    })

        except Exception as e:
            self.logger.warning(f"Could not scan {file_path}: {e}")

        return issues_found

    async def _check_security_configs(self) -> Dict[str, Any]:
        """Check security configuration files"""
        result = {
            "scan_type": "security_configuration",
            "misconfigurations": 0,
            "critical_misconfigurations": 0,
            "configs_checked": 0,
            "configuration_issues": []
        }

        try:
            # Check common configuration files
            config_checks = [
                ("package.json", self._check_package_json_security),
                (".gitignore", self._check_gitignore_security),
                ("requirements.txt", self._check_requirements_security),
                ("Dockerfile", self._check_dockerfile_security)
            ]

            for config_file, check_function in config_checks:
                config_path = self.project_root / config_file
                if config_path.exists():
                    issues = check_function(config_path)
                    result["configuration_issues"].extend(issues)
                    result["configs_checked"] += 1

            result["misconfigurations"] = len(result["configuration_issues"])
            result["critical_misconfigurations"] = sum(
                1 for issue in result["configuration_issues"]
                if issue.get("severity") == "critical"
            )

        except Exception as e:
            self.logger.error(f"Configuration security check failed: {e}")
            result["error"] = str(e)

        return result

    def _check_package_json_security(self, package_path: Path) -> List[Dict]:
        """Check package.json for security issues"""
        issues = []
        try:
            with open(package_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            # Check for known vulnerable packages or configurations
            if "scripts" in package_data:
                scripts = package_data["scripts"]
                if any("rm -rf" in script for script in scripts.values()):
                    issues.append({
                        "file": "package.json",
                        "issue": "Dangerous rm -rf command in scripts",
                        "severity": "critical"
                    })

        except Exception as e:
            self.logger.warning(f"Could not check package.json: {e}")

        return issues

    def _check_gitignore_security(self, gitignore_path: Path) -> List[Dict]:
        """Check .gitignore for security issues"""
        issues = []
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check if sensitive files are properly ignored
            sensitive_patterns = [".env", "*.key", "*.pem", "config.json", "secrets.json"]
            missing_patterns = []

            for pattern in sensitive_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)

            if missing_patterns:
                issues.append({
                    "file": ".gitignore",
                    "issue": f"Missing sensitive file patterns: {', '.join(missing_patterns)}",
                    "severity": "medium"
                })

        except Exception as e:
            self.logger.warning(f"Could not check .gitignore: {e}")

        return issues

    def _check_requirements_security(self, requirements_path: Path) -> List[Dict]:
        """Check requirements.txt for security issues"""
        issues = []
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for unpinned versions
            lines = content.strip().split('\n')
            unpinned = []
            for line in lines:
                if line.strip() and not any(op in line for op in ['==', '>=', '<=', '~=', '!=']):
                    unpinned.append(line.strip())

            if unpinned:
                issues.append({
                    "file": "requirements.txt",
                    "issue": f"Unpinned package versions: {', '.join(unpinned[:5])}",
                    "severity": "medium"
                })

        except Exception as e:
            self.logger.warning(f"Could not check requirements.txt: {e}")

        return issues

    def _check_dockerfile_security(self, dockerfile_path: Path) -> List[Dict]:
        """Check Dockerfile for security issues"""
        issues = []
        try:
            with open(dockerfile_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for running as root
            if "USER root" in content or "USER 0" in content:
                issues.append({
                    "file": "Dockerfile",
                    "issue": "Container runs as root user",
                    "severity": "critical"
                })

            # Check for latest tag usage
            if "FROM " in content and ":latest" in content:
                issues.append({
                    "file": "Dockerfile",
                    "issue": "Using :latest tag in base image",
                    "severity": "medium"
                })

        except Exception as e:
            self.logger.warning(f"Could not check Dockerfile: {e}")

        return issues

    def _merge_vulnerability_results(self, result1: Dict, result2: Dict) -> Dict:
        """Merge two vulnerability scan results"""
        merged = result1.copy()
        merged["vulnerabilities_found"] += result2.get("vulnerabilities_found", 0)
        merged["high_severity"] += result2.get("high_severity", 0)
        merged["medium_severity"] += result2.get("medium_severity", 0)
        merged["low_severity"] += result2.get("low_severity", 0)
        merged["packages_scanned"] += result2.get("packages_scanned", 0)

        if "details" in result2:
            if "details" not in merged:
                merged["details"] = []
            merged["details"].extend(result2["details"])

        return merged

    def _merge_security_results(self, result1: Dict, result2: Dict) -> Dict:
        """Merge two security analysis results"""
        merged = result1.copy()
        merged["issues_found"] += result2.get("issues_found", 0)
        merged["files_analyzed"] += result2.get("files_analyzed", 0)
        merged["security_issues"].extend(result2.get("security_issues", []))
        return merged

    def _calculate_security_score(self, scans: Dict[str, Any]) -> int:
        """Calculate overall security score from scan results"""
        total_score = 0
        weight_sum = 0

        # Weight different scan types
        scan_weights = {
            "dependencies": 0.3,
            "secrets": 0.3,
            "code_analysis": 0.25,
            "configurations": 0.15
        }

        for scan_type, weight in scan_weights.items():
            if scan_type in scans:
                scan_result = scans[scan_type]
                score = self._calculate_scan_score(scan_result, scan_type)
                total_score += score * weight
                weight_sum += weight

        return int(total_score / weight_sum) if weight_sum > 0 else 0

    def _calculate_scan_score(self, scan_result: Dict, scan_type: str) -> int:
        """Calculate score for individual scan type"""
        if scan_type == "dependencies":
            total_vulns = scan_result.get("vulnerabilities_found", 0)
            high_vulns = scan_result.get("high_severity", 0)
            medium_vulns = scan_result.get("medium_severity", 0)

            if total_vulns == 0:
                return 100
            elif high_vulns > 0:
                return max(0, 100 - (high_vulns * 20 + medium_vulns * 10))
            else:
                return max(20, 100 - (total_vulns * 5))

        elif scan_type == "secrets":
            secrets_found = scan_result.get("secrets_found", 0)
            high_risk = scan_result.get("high_risk_secrets", 0)

            if secrets_found == 0:
                return 100
            elif high_risk > 0:
                return max(0, 100 - (high_risk * 30))
            else:
                return max(30, 100 - (secrets_found * 10))

        elif scan_type == "code_analysis":
            issues = scan_result.get("issues_found", 0)
            high_issues = scan_result.get("high_severity_issues", 0)

            if issues == 0:
                return 100
            elif high_issues > 0:
                return max(0, 100 - (high_issues * 25))
            else:
                return max(40, 100 - (issues * 5))

        elif scan_type == "configurations":
            misconfigs = scan_result.get("misconfigurations", 0)
            critical = scan_result.get("critical_misconfigurations", 0)

            if misconfigs == 0:
                return 100
            elif critical > 0:
                return max(0, 100 - (critical * 40))
            else:
                return max(50, 100 - (misconfigs * 10))

        return 50  # Default score

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level based on security score"""
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "high"
        else:
            return "critical"

    def _generate_recommendations(self, scans: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on scan results"""
        recommendations = []

        # Dependency recommendations
        deps = scans.get("dependencies", {})
        if deps.get("vulnerabilities_found", 0) > 0:
            recommendations.append("Update vulnerable dependencies: Run 'npm audit fix' or update requirements.txt")

        # Secret recommendations
        secrets = scans.get("secrets", {})
        if secrets.get("secrets_found", 0) > 0:
            recommendations.append("Remove exposed secrets: Use environment variables or secret management systems")

        # Code analysis recommendations
        code = scans.get("code_analysis", {})
        if code.get("issues_found", 0) > 0:
            recommendations.append("Fix code security issues: Review and remediate identified vulnerabilities")

        # Configuration recommendations
        configs = scans.get("configurations", {})
        if configs.get("misconfigurations", 0) > 0:
            recommendations.append("Harden security configurations: Review and update configuration files")

        if not recommendations:
            recommendations.append("Maintain current security practices and regular scanning")

        return recommendations

    def _calculate_metrics(self, scans: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate security metrics for monitoring"""
        return {
            "total_vulnerabilities": sum(scan.get("vulnerabilities_found", 0) for scan in scans.values()),
            "total_secrets": sum(scan.get("secrets_found", 0) for scan in scans.values()),
            "total_code_issues": sum(scan.get("issues_found", 0) for scan in scans.values()),
            "total_misconfigurations": sum(scan.get("misconfigurations", 0) for scan in scans.values()),
            "scan_duration": getattr(self, "_execution_time", 0),
            "scans_completed": len([scan for scan in scans.values() if not scan.get("error")])
        }