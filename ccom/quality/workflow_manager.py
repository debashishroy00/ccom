#!/usr/bin/env python3
"""
Workflow Manager - Lightweight Workflow Orchestration
Replaces the 1,131-line workflows.py with essential functionality

Handles:
- Basic workflow execution patterns
- Quality-deployment-security sequences
- Simple coordination without bloat
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..utils import SubprocessRunner, ErrorHandler, Display


class WorkflowManager:
    """
    Lightweight workflow orchestration

    Replaces the oversized workflows.py (1,131 lines) with essential coordination only
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.subprocess_runner = SubprocessRunner()

    def run_quality_deployment_workflow(self) -> Dict[str, Any]:
        """Standard quality → deployment workflow"""
        results = {
            "workflow_name": "Quality Deployment",
            "steps": [],
            "overall_success": True
        }

        try:
            # Step 1: Quality check
            Display.progress("Step 1/3: Running quality checks...")
            quality_result = self._run_workflow_step("quality", ["npm", "run", "lint"])
            results["steps"].append(quality_result)

            if not quality_result["success"]:
                results["overall_success"] = False
                return results

            # Step 2: Build
            Display.progress("Step 2/3: Building production...")
            build_result = self._run_workflow_step("build", ["npm", "run", "build"])
            results["steps"].append(build_result)

            if not build_result["success"]:
                results["overall_success"] = False
                return results

            # Step 3: Deploy (if deploy script exists)
            Display.progress("Step 3/3: Deploying...")
            deploy_result = self._run_workflow_step("deploy", ["npm", "run", "deploy"])
            results["steps"].append(deploy_result)

            if not deploy_result["success"]:
                results["overall_success"] = False

            return results

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
            return results

    def run_security_workflow(self) -> Dict[str, Any]:
        """Security-focused workflow"""
        results = {
            "workflow_name": "Security Scan",
            "steps": [],
            "overall_success": True
        }

        try:
            # Security audit
            Display.progress("Running security audit...")
            audit_result = self._run_workflow_step("security_audit", ["npm", "audit"])
            results["steps"].append(audit_result)

            if not audit_result["success"]:
                results["overall_success"] = False

            return results

        except Exception as e:
            self.logger.error(f"Security workflow failed: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
            return results

    def _run_workflow_step(self, step_name: str, command: List[str]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            result = self.subprocess_runner.run_command(command, timeout=120)

            return {
                "step": step_name,
                "success": result.returncode == 0,
                "command": " ".join(command),
                "message": f"✅ {step_name} completed" if result.returncode == 0 else f"❌ {step_name} failed"
            }

        except Exception as e:
            return {
                "step": step_name,
                "success": False,
                "command": " ".join(command),
                "message": f"❌ {step_name} error: {str(e)}"
            }

    def get_available_workflows(self) -> List[str]:
        """Get list of available workflow patterns"""
        return [
            "quality_deployment",
            "security_scan",
            "full_enterprise"  # All three: quality + security + deployment
        ]

    def run_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Run named workflow pattern"""
        if workflow_name == "quality_deployment":
            return self.run_quality_deployment_workflow()
        elif workflow_name == "security_scan":
            return self.run_security_workflow()
        elif workflow_name == "full_enterprise":
            return self._run_full_enterprise_workflow()
        else:
            return {
                "workflow_name": workflow_name,
                "overall_success": False,
                "error": f"Unknown workflow: {workflow_name}"
            }

    def _run_full_enterprise_workflow(self) -> Dict[str, Any]:
        """Complete enterprise workflow: quality + security + deployment"""
        results = {
            "workflow_name": "Full Enterprise",
            "steps": [],
            "overall_success": True
        }

        try:
            # Run security first
            security_result = self.run_security_workflow()
            results["steps"].extend(security_result["steps"])

            if not security_result["overall_success"]:
                results["overall_success"] = False
                return results

            # Then quality deployment
            deployment_result = self.run_quality_deployment_workflow()
            results["steps"].extend(deployment_result["steps"])

            if not deployment_result["overall_success"]:
                results["overall_success"] = False

            return results

        except Exception as e:
            self.logger.error(f"Full enterprise workflow failed: {e}")
            results["overall_success"] = False
            results["error"] = str(e)
            return results

    def display_workflow_results(self, results: Dict[str, Any]) -> None:
        """Display workflow execution results"""
        Display.section(f"🔄 Workflow: {results['workflow_name']}")

        if results["overall_success"]:
            Display.success(f"✅ {results['workflow_name']} completed successfully")
        else:
            Display.error(f"❌ {results['workflow_name']} failed")

        # Show step details
        for step in results.get("steps", []):
            print(f"  {step['message']}")

        if "error" in results:
            Display.error(f"Error: {results['error']}")