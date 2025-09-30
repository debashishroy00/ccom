#!/usr/bin/env python3
"""
CCOM Orchestrator v5.0 - Refactored for Quality Standards
Streamlined orchestration that coordinates focused modules

Now follows SOLID principles with proper separation of concerns
Reduced from 2,135 lines to ~200 lines by extracting responsibilities
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .memory_manager import MemoryManager
from .agent_manager import AgentManager
from .context_manager import ContextManager
from ccom.utils import ErrorHandler, Display
from ccom.auto_context import get_auto_context

# Handle Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        # Python < 3.7 fallback
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')


class CCOMOrchestrator:
    """
    Streamlined orchestration engine following SOLID principles

    Responsibilities (Single Responsibility):
    - Coordinate between focused managers
    - Handle natural language command parsing
    - Provide unified interface for CCOM operations

    Dependencies are injected (Dependency Inversion)
    """

    def __init__(self, project_root: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        self.project_root = project_root or Path.cwd()
        self.config = config or {}

        # Initialize logger
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Initialize focused managers (Dependency Injection)
        self.memory_manager = MemoryManager(self.project_root)
        self.agent_manager = AgentManager(self.project_root, self.memory_manager, self.config)
        self.context_manager = ContextManager(self.project_root, self.memory_manager)

        # Initialize auto-context capture
        self._init_auto_context()

    def _init_auto_context(self) -> None:
        """Initialize auto-context capture system"""
        try:
            self.auto_context = get_auto_context()
            self.logger.info("Auto-context initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize auto-context: {e}")
            self.auto_context = None

    # === COMMAND ROUTING ===

    def handle_natural_language(self, command: str) -> bool:
        """
        Parse natural language commands and route to appropriate handlers

        Simplified from original 200+ line method to focused routing
        """
        command_lower = command.lower().strip()
        Display.progress(f"Processing command: '{command}'")

        try:
            # Route to appropriate handler based on command patterns
            result = self._route_command(command_lower, command)

            # Capture interaction for context
            self._capture_interaction(command, result)

            return result if isinstance(result, bool) else bool(result)

        except Exception as e:
            self.logger.error(f"Command handling failed: {e}")
            Display.error(f"Command execution failed: {str(e)}")
            return False

    def _route_command(self, command_lower: str, original_command: str) -> bool:
        """Route command to appropriate handler"""
        # Agent execution patterns
        if self._matches_patterns(command_lower, ["quality", "clean", "fix", "lint"]):
            return self.agent_manager.invoke_quality_enforcer()

        if self._matches_patterns(command_lower, ["secure", "safety", "protect", "scan"]):
            return self.agent_manager.invoke_security_guardian()

        if self._matches_patterns(command_lower, ["build", "compile", "package"]):
            return self.agent_manager.invoke_builder_agent()

        if self._matches_patterns(command_lower, ["deploy", "ship", "go live", "launch"]):
            return self.agent_manager.invoke_deployment_specialist()

        # Principles validation patterns
        if self._matches_patterns(command_lower, [
            "principles", "validate principles", "kiss", "dry", "solid", "yagni",
            "complexity", "validate complexity", "check principles"
        ]):
            return self._handle_principles_validation(original_command)

        # Workflow patterns
        if self._matches_patterns(command_lower, [
            "workflow", "run workflow", "rag quality", "vector validation",
            "aws rag", "enterprise rag", "full pipeline"
        ]):
            return self._handle_workflow_command(original_command)

        # Tools management patterns
        if self._matches_patterns(command_lower, [
            "install tools", "check tools", "tools status", "setup tools"
        ]):
            return self._handle_tools_command(original_command)

        # Context patterns
        if self._matches_patterns(command_lower, [
            "context", "project context", "show context", "project summary",
            "what is this project", "catch me up", "bring me up to speed"
        ]):
            return self.context_manager.show_project_context()

        # Memory patterns
        if self._matches_patterns(command_lower, ["remember", "memory", "status"]):
            return self._handle_memory_command(original_command)

        # Default: unknown command
        Display.warning("❓ Unknown command. Try: quality, security, deploy, principles, workflow, tools, context, memory")
        return False

    def _matches_patterns(self, command_lower: str, patterns: list) -> bool:
        """Check if command matches any of the given patterns"""
        return any(phrase in command_lower for phrase in patterns)

    def _handle_memory_command(self, command: str) -> bool:
        """Handle memory-related commands"""
        command_lower = command.lower()

        if "status" in command_lower:
            self.memory_manager.display_memory_summary()
            return True
        elif "memory" in command_lower or "show" in command_lower:
            self.memory_manager.display_memory_summary()
            return True
        else:
            Display.info("Memory commands: status, memory")
            return True

    def _handle_principles_validation(self, command: str) -> bool:
        """Handle software engineering principles validation"""
        try:
            from ..quality import PrinciplesValidator

            Display.section("📐 Software Engineering Principles Validation")
            validator = PrinciplesValidator(self.project_root)

            command_lower = command.lower()

            if "kiss" in command_lower:
                result = validator.validate_kiss()
                validator.display_results({"kiss": result})
            elif "dry" in command_lower:
                result = validator.validate_dry()
                validator.display_results({"dry": result})
            elif "solid" in command_lower:
                result = validator.validate_solid()
                validator.display_results({"solid": result})
            elif "yagni" in command_lower:
                result = validator.validate_yagni()
                validator.display_results({"yagni": result})
            else:
                # Run all principles validation
                results = validator.validate_all_principles()
                validator.display_results(results)

            return True

        except Exception as e:
            self.logger.error(f"Principles validation failed: {e}")
            Display.error(f"Principles validation error: {str(e)}")
            return False

    def _handle_workflow_command(self, command: str) -> bool:
        """Handle workflow execution commands"""
        try:
            from ..quality import ComprehensiveWorkflowManager

            workflow_manager = ComprehensiveWorkflowManager(self.project_root)
            command_lower = command.lower()

            # Extract workflow name from command
            workflow_name = self._extract_workflow_name(command_lower)

            if not workflow_name:
                # Show available workflows
                workflow_manager.list_workflows()
                return True

            # Execute the workflow
            result = workflow_manager.run_workflow(workflow_name)
            workflow_manager.display_workflow_results(result)

            return result.success

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            Display.error(f"Workflow error: {str(e)}")
            return False

    def _handle_tools_command(self, command: str) -> bool:
        """Handle tools management commands"""
        try:
            from ..quality import ComprehensiveToolsManager

            tools_manager = ComprehensiveToolsManager(self.project_root)
            command_lower = command.lower()

            if "install" in command_lower:
                Display.progress("Installing development tools...")
                success = tools_manager.install_missing_tools()
                if success:
                    Display.success("✅ Tools installation completed")
                return success
            elif "status" in command_lower or "check" in command_lower:
                tools_manager.display_comprehensive_status()
                return True
            else:
                Display.info("Tools commands: install tools, check tools, tools status")
                return True

        except Exception as e:
            self.logger.error(f"Tools management failed: {e}")
            Display.error(f"Tools error: {str(e)}")
            return False

    def _extract_workflow_name(self, command_lower: str) -> str:
        """Extract workflow name from command"""
        # Map command patterns to workflow names
        workflow_mappings = {
            "quality": "quality",
            "security": "security",
            "deploy": "deploy",
            "full pipeline": "full",
            "rag quality": "rag_quality",
            "vector validation": "vector_validation",
            "aws rag": "aws_rag",
            "enterprise rag": "enterprise_rag",
            "angular": "angular_validation",
            "cost optimization": "cost_optimization",
            "s3 security": "s3_security",
            "performance": "performance_optimization",
            "complete stack": "complete_stack"
        }

        for pattern, workflow_name in workflow_mappings.items():
            if pattern in command_lower:
                return workflow_name

        return ""

    def _capture_interaction(self, command: str, result: Any) -> None:
        """Capture interaction for context building"""
        if self.auto_context:
            try:
                output_summary = f"CCOM executed: {command} → {'Success' if result else 'Failed'}"
                self.auto_context.capture_interaction(command, output_summary)
                self.logger.debug(f"Captured interaction: {command}")
            except Exception as e:
                self.logger.warning(f"Failed to capture interaction: {e}")

    # === WORKFLOW SEQUENCES ===

    def deploy_sequence(self) -> bool:
        """Full enterprise deployment sequence"""
        Display.workflow_start("Deployment")

        try:
            # Step 1: Quality check
            Display.progress("Step 1: Running quality checks...")
            if not self.agent_manager.invoke_quality_enforcer():
                Display.error("Deployment blocked - quality issues found")
                return False

            # Step 2: Security check
            Display.progress("Step 2: Running security scan...")
            if not self.agent_manager.invoke_security_guardian():
                Display.error("Deployment blocked - security issues found")
                return False

            # Step 3: Build
            Display.progress("Step 3: Building production artifacts...")
            if not self.agent_manager.invoke_builder_agent():
                Display.error("Deployment blocked - build failed")
                return False

            # Step 4: Deploy
            Display.progress("Step 4: Coordinating deployment...")
            if not self.agent_manager.invoke_deployment_specialist():
                Display.error("Deployment failed")
                return False

            Display.workflow_complete("Deployment", True)
            return True

        except Exception as e:
            self.logger.error(f"Deployment sequence failed: {e}")
            Display.workflow_complete("Deployment", False)
            return False

    def quality_sequence(self) -> bool:
        """Run quality checks and fixes"""
        Display.workflow_start("Quality Enforcement")
        result = self.agent_manager.invoke_quality_enforcer()
        Display.workflow_complete("Quality Enforcement", result)
        return result

    def security_sequence(self) -> bool:
        """Run security checks"""
        Display.workflow_start("Security Scan")
        result = self.agent_manager.invoke_security_guardian()
        Display.workflow_complete("Security Scan", result)
        return result

    def build_sequence(self) -> bool:
        """Run standalone build process"""
        Display.workflow_start("Build Process")
        result = self.agent_manager.invoke_builder_agent()
        Display.workflow_complete("Build Process", result)
        return result

    # === STATUS AND INFORMATION ===

    def show_status(self) -> bool:
        """Show comprehensive CCOM status"""
        try:
            Display.header("📊 CCOM Status Report")

            # Memory stats
            memory_stats = self.memory_manager.get_memory_stats()
            Display.section("🧠 Memory")
            Display.key_value_table({
                "Project": memory_stats.get("project_name", "Unknown"),
                "Features": memory_stats.get("total_features", 0),
                "Version": memory_stats.get("version", "5.0")
            })

            # Agent status
            self.agent_manager.show_agent_status()

            return True

        except Exception as e:
            self.logger.error(f"Failed to show status: {e}")
            Display.error("Failed to display status")
            return False

    def show_memory(self) -> bool:
        """Show memory contents"""
        self.memory_manager.display_memory_summary()
        return True

    # === SDK INTEGRATION METHODS ===

    def get_agent_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of SDK and legacy agents"""
        return self.agent_manager.get_agent_status(agent_name)

    def get_migration_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for migrating to SDK agents"""
        return self.agent_manager.get_migration_recommendations()

    def set_agent_mode(self, mode: str) -> bool:
        """Set agent execution mode (sdk, markdown, hybrid)"""
        return self.agent_manager.set_agent_mode(mode)

    async def migrate_to_sdk_mode(self) -> bool:
        """Migrate to full SDK mode"""
        return await self.agent_manager.migrate_to_sdk_mode()

    def show_sdk_status(self) -> bool:
        """Show comprehensive SDK integration status"""
        return self.agent_manager.show_agent_status()

    def show_project_context(self) -> bool:
        """Show comprehensive project context"""
        return self.context_manager.show_project_context()

    # === LEGACY COMPATIBILITY ===

    def invoke_subagent(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Legacy compatibility method for agent invocation"""
        return self.agent_manager.invoke_subagent(agent_name, context)

    @property
    def memory(self) -> Dict[str, Any]:
        """Legacy compatibility property for memory access"""
        return self.memory_manager.memory

    def save_memory(self) -> bool:
        """Legacy compatibility method for memory saving"""
        return self.memory_manager.save_memory()

    def load_memory(self) -> Dict[str, Any]:
        """Legacy compatibility method for memory loading"""
        return self.memory_manager.memory

    def check_memory_for_duplicate(self, feature_name: str) -> bool:
        """Legacy compatibility method for duplicate checking"""
        return self.memory_manager.check_duplicate_feature(feature_name)


def main():
    """Main CLI entry point for testing"""
    if len(sys.argv) < 2:
        Display.header("CCOM v5.0 - Refactored Architecture")
        Display.info("Usage: python orchestrator.py '<command>'")
        Display.bullet_list([
            "python orchestrator.py 'deploy'",
            "python orchestrator.py 'quality check'",
            "python orchestrator.py 'status'"
        ])
        return

    command = " ".join(sys.argv[1:])
    orchestrator = CCOMOrchestrator()
    orchestrator.handle_natural_language(command)


if __name__ == "__main__":
    main()