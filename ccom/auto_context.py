"""
Automatic Context Capture for CCOM
Seamlessly captures context from all CCOM operations
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from .mcp_bridge import MCPMemoryBridge


class AutoContextCapture:
    """Automatically captures context from CCOM operations"""

    def __init__(self, project_name: str = None):
        self.bridge = MCPMemoryBridge(project_name)
        self.enabled = True
        self.batch_mode = False
        self.batch_items = []

    def capture_command(self, command: str, args: List[str] = None):
        """Automatically capture command execution context"""
        if not self.enabled:
            return

        # Determine feature from command
        feature = self._extract_feature(command, args)

        # Save command execution
        self.bridge.save_context(
            feature,
            "progress",
            f"Executed: {command} {' '.join(args or [])}",
            "normal"
        )

    def capture_workflow(self, workflow_name: str, status: str, details: Dict = None):
        """Capture workflow execution"""
        if not self.enabled:
            return

        feature = f"workflow-{workflow_name}"

        if status == "started":
            self.bridge.save_context(
                feature,
                "progress",
                f"Started {workflow_name} workflow",
                "normal"
            )
        elif status == "completed":
            self.bridge.save_context(
                feature,
                "progress",
                f"Completed {workflow_name} workflow successfully",
                "normal"
            )
        elif status == "failed":
            error_msg = details.get('error', 'Unknown error') if details else 'Unknown error'
            self.bridge.save_context(
                feature,
                "issue",
                f"{workflow_name} workflow failed: {error_msg}",
                "high"
            )

    def capture_quality_results(self, results: Dict):
        """Automatically capture quality check results"""
        if not self.enabled:
            return

        feature = "quality"

        # Capture overall status
        if results.get('passed'):
            self.bridge.save_context(
                feature,
                "progress",
                f"Quality checks passed: {results.get('checks_passed', 0)}/{results.get('total_checks', 0)}",
                "normal"
            )
        else:
            self.bridge.save_context(
                feature,
                "issue",
                f"Quality issues found: {results.get('total_issues', 0)} issues in {results.get('files_affected', 0)} files",
                "high"
            )

        # Capture specific issues
        if results.get('errors'):
            for error in results['errors'][:5]:  # Top 5 errors
                self.bridge.save_context(
                    feature,
                    "issue",
                    f"Error: {error.get('message', '')} in {error.get('file', '')}",
                    "normal"
                )

        # Capture metrics
        if results.get('metrics'):
            metrics = results['metrics']
            if metrics.get('complexity_high'):
                self.bridge.save_context(
                    feature,
                    "issue",
                    f"High complexity detected: {metrics['complexity_high']} functions exceed threshold",
                    "normal"
                )

    def capture_security_results(self, results: Dict):
        """Automatically capture security scan results"""
        if not self.enabled:
            return

        feature = "security"

        # Capture vulnerabilities
        if results.get('vulnerabilities'):
            for vuln in results['vulnerabilities'][:3]:  # Top 3 vulnerabilities
                severity = vuln.get('severity', 'medium')
                priority = 'critical' if severity in ['critical', 'high'] else 'high'

                self.bridge.save_context(
                    feature,
                    "issue",
                    f"Security: {vuln.get('title', 'Unknown')} ({severity})",
                    priority
                )

        # Capture overall security status
        vuln_count = len(results.get('vulnerabilities', []))
        if vuln_count == 0:
            self.bridge.save_context(
                feature,
                "progress",
                "Security scan passed - no vulnerabilities found",
                "normal"
            )
        else:
            self.bridge.save_context(
                feature,
                "issue",
                f"Security scan found {vuln_count} vulnerabilities",
                "high"
            )

    def capture_deployment(self, status: str, details: Dict = None):
        """Capture deployment status"""
        if not self.enabled:
            return

        feature = "deployment"

        if status == "started":
            self.bridge.save_context(
                feature,
                "progress",
                f"Deployment started to {details.get('target', 'production')}",
                "normal"
            )
        elif status == "success":
            self.bridge.save_context(
                feature,
                "progress",
                f"Deployment successful to {details.get('target', 'production')}",
                "normal"
            )
            if details.get('url'):
                self.bridge.save_context(
                    feature,
                    "note",
                    f"Deployed URL: {details['url']}",
                    "normal"
                )
        elif status == "failed":
            self.bridge.save_context(
                feature,
                "issue",
                f"Deployment failed: {details.get('error', 'Unknown error')}",
                "critical"
            )

    def capture_file_changes(self, files: List[str], operation: str):
        """Capture file modification events"""
        if not self.enabled or not files:
            return

        feature = "files"

        if len(files) <= 3:
            file_list = ", ".join(files)
        else:
            file_list = f"{', '.join(files[:3])} and {len(files)-3} more"

        self.bridge.save_context(
            feature,
            "progress",
            f"{operation}: {file_list}",
            "low"
        )

    def capture_error(self, error: str, context: str = None):
        """Capture errors for debugging"""
        if not self.enabled:
            return

        feature = context or "general"

        self.bridge.save_context(
            feature,
            "error",
            error,
            "high"
        )

    def capture_decision(self, feature: str, decision: str):
        """Capture architectural or implementation decisions"""
        if not self.enabled:
            return

        self.bridge.save_context(
            feature,
            "decision",
            decision,
            "high"
        )

    def capture_todo(self, feature: str, todo: str):
        """Capture next steps or todos"""
        if not self.enabled:
            return

        self.bridge.save_context(
            feature,
            "next_step",
            todo,
            "normal"
        )

    def capture_evaluation(self, evaluation_data: Dict):
        """Capture comprehensive evaluation results"""
        if not self.enabled:
            return

        feature = "evaluation"

        # Capture the evaluation execution
        if evaluation_data.get('command'):
            self.bridge.save_context(
                feature,
                "progress",
                f"Executed: {evaluation_data['command']}",
                "normal"
            )

        # Capture overall grade/status
        if evaluation_data.get('grade'):
            self.bridge.save_context(
                feature,
                "note",
                f"Current Status: {evaluation_data['grade']} - {evaluation_data.get('summary', '')}",
                "high"
            )

        # Capture strengths
        if evaluation_data.get('strengths'):
            strengths_text = ", ".join(evaluation_data['strengths'][:5])
            self.bridge.save_context(
                feature,
                "decision",
                f"Strengths: {strengths_text}",
                "high"
            )

        # Capture improvements
        if evaluation_data.get('improvements'):
            improvements_text = ", ".join(evaluation_data['improvements'][:5])
            self.bridge.save_context(
                feature,
                "next_step",
                f"Improvements needed: {improvements_text}",
                "normal"
            )

        # Capture recommendations
        if evaluation_data.get('recommendation'):
            self.bridge.save_context(
                feature,
                "decision",
                evaluation_data['recommendation'],
                "high"
            )

    def start_batch(self):
        """Start batch mode for multiple operations"""
        self.batch_mode = True
        self.batch_items = []

    def end_batch(self):
        """End batch mode and save all items"""
        if not self.batch_mode:
            return

        # Save all batched items
        for item in self.batch_items:
            self.bridge.save_context(**item)

        self.batch_mode = False
        self.batch_items = []

    def _extract_feature(self, command: str, args: List[str] = None) -> str:
        """Extract feature name from command and arguments"""

        # Common command to feature mapping
        command_features = {
            'deploy': 'deployment',
            'build': 'build',
            'test': 'testing',
            'quality': 'quality',
            'security': 'security',
            'workflow': 'workflow',
            'monitor': 'monitoring',
            'watch': 'monitoring'
        }

        # Check command mapping
        for cmd, feature in command_features.items():
            if cmd in command.lower():
                return feature

        # Check arguments for feature indicators
        if args:
            for arg in args:
                if any(indicator in arg.lower() for indicator in ['auth', 'api', 'ui', 'database']):
                    return arg.lower()

        return "general"

    def get_summary(self, feature: str = None, hours: int = 24) -> str:
        """Get a summary of recent context"""

        # Get recent context
        context = self.bridge.get_context(feature, limit=50)

        # Filter by time
        cutoff = datetime.now().timestamp() - (hours * 3600)
        recent = []

        for item in context:
            try:
                item_time = datetime.fromisoformat(item.get('timestamp', '').replace('Z', '+00:00'))
                if item_time.timestamp() > cutoff:
                    recent.append(item)
            except:
                continue

        if not recent:
            return "No recent activity"

        # Summarize by category
        summary = []
        categories = {}

        for item in recent:
            cat = item.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        summary.append(f"Last {hours} hours activity:")
        for cat, count in sorted(categories.items()):
            summary.append(f"  • {cat}: {count}")

        return "\n".join(summary)


# Global instance for easy access
_auto_context = None


def get_auto_context(project_name: str = None) -> AutoContextCapture:
    """Get or create the global auto-context instance"""
    global _auto_context
    if _auto_context is None:
        _auto_context = AutoContextCapture(project_name)
    return _auto_context


def capture(context_type: str, feature: str, content: str, priority: str = "normal"):
    """Quick capture helper for seamless integration"""
    auto = get_auto_context()
    auto.bridge.save_context(feature, context_type, content, priority)