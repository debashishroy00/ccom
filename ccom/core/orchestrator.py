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
from ..memory.advanced_memory_keeper import AdvancedMemoryKeeper

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

        # Initialize advanced memory keeper for session continuity
        self.advanced_memory = AdvancedMemoryKeeper(self.project_root, self.memory_manager)

        # Initialize auto-context capture
        self._init_auto_context()

        # Display session intelligence on startup (quiet)
        self._show_session_intelligence()

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

        # Enterprise workflow patterns
        if self._matches_patterns(command_lower, [
            "enterprise deployment", "deploy enterprise", "deployment pipeline",
            "quality improvement", "continuous improvement", "improve quality",
            "security hardening", "harden security", "security pipeline",
            "performance optimization", "optimize performance", "performance pipeline"
        ]):
            return self._handle_enterprise_workflow(original_command)

        # Legacy workflow patterns
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
        """Handle software engineering principles validation using comprehensive validator"""
        try:
            from ..quality.comprehensive_validator import ComprehensiveValidator

            validator = ComprehensiveValidator(self.project_root)
            command_lower = command.lower()

            # Determine scope based on command
            if "kiss" in command_lower or "dry" in command_lower or "solid" in command_lower or "yagni" in command_lower:
                # Run specific principle or all principles
                scope = "principles"
            elif "quality" in command_lower:
                # Run comprehensive quality check
                scope = "all"
            else:
                # Default to principles validation
                scope = "principles"

            # Auto-fix if requested
            auto_fix = "fix" in command_lower or "auto" in command_lower

            # Execute comprehensive validation
            report = validator.run_comprehensive_validation(auto_fix=auto_fix, target_scope=scope)

            return report.get("overall", {}).get("successful_validations", 0) > 0

        except Exception as e:
            self.logger.error(f"Principles validation failed: {e}")
            Display.error(f"Validation error: {str(e)}")
            return False

    def _handle_enterprise_workflow(self, command: str) -> bool:
        """Handle enterprise workflow execution"""
        try:
            from ..orchestration.enterprise_workflows import EnterpriseWorkflowOrchestrator

            orchestrator = EnterpriseWorkflowOrchestrator(self.project_root)
            command_lower = command.lower()

            # Determine workflow type
            workflow_name = None
            if any(pattern in command_lower for pattern in ["enterprise deployment", "deploy enterprise", "deployment pipeline"]):
                workflow_name = "enterprise_deployment"
            elif any(pattern in command_lower for pattern in ["quality improvement", "continuous improvement", "improve quality"]):
                workflow_name = "quality_improvement"
            elif any(pattern in command_lower for pattern in ["security hardening", "harden security", "security pipeline"]):
                workflow_name = "security_hardening"
            elif any(pattern in command_lower for pattern in ["performance optimization", "optimize performance", "performance pipeline"]):
                workflow_name = "performance_optimization"

            if workflow_name:
                # Execute the enterprise workflow
                import asyncio
                report = asyncio.run(orchestrator.execute_workflow(workflow_name))
                return report.get("overall_success", False)
            else:
                # List available workflows
                orchestrator.list_available_workflows()
                return True

        except Exception as e:
            self.logger.error(f"Enterprise workflow execution failed: {e}")
            Display.error(f"Enterprise workflow error: {str(e)}")
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
        """Handle tools management commands with memory intelligence"""
        try:
            command_lower = command.lower()

            if "install" in command_lower:
                # Use memory intelligence for tool installation
                return self._handle_install_tools_with_memory()
            elif "status" in command_lower or "check" in command_lower:
                # Use memory intelligence for tool checking
                return self._handle_check_tools_with_memory()
            else:
                Display.info("Tools commands: install tools, check tools, tools status")
                return True

        except Exception as e:
            self.logger.error(f"Tools management failed: {e}")
            Display.error(f"Tools error: {str(e)}")
            return False

    def _handle_install_tools_with_memory(self) -> bool:
        """Handle install tools with memory intelligence"""
        try:
            Display.header("🧠 CCOM Intelligence: Checking Memory Before Installation")

            # Query memory for recent tool installations
            memory_query = self.advanced_memory.query_command_memory("install tools", timeframe_hours=24)

            # Check if tools were recently installed successfully
            if memory_query["has_recent_execution"]:
                Display.section("🔍 Memory Intelligence Found Recent Activity")

                for cmd in memory_query["recent_commands"]:
                    if cmd["success_rate"] > 0.8:  # Recent successful installation
                        Display.warning(f"⚠️  Tools were successfully installed recently: {cmd['last_executed']}")
                        Display.info(f"📊 Success Rate: {cmd['success_rate']:.1%} ({cmd['count']} attempts)")

                        # Check current tool status first
                        Display.progress("Checking current tool status...")
                        from ..legacy.tools_manager import ToolsManager
                        tools_manager = ToolsManager(self.project_root)
                        installed_tools = tools_manager.check_tool_availability()
                        required_tools = tools_manager.get_tools_for_project()

                        missing_count = len([t for t in required_tools if not installed_tools.get(t, {}).get("installed", False)])

                        if missing_count == 0:
                            Display.success("✅ All required tools are already installed")
                            Display.info("💡 Memory Intelligence: No installation needed")

                            # Capture this decision in memory
                            self.advanced_memory.capture_command_execution(
                                "install tools",
                                {"memory_check": True, "tools_already_installed": True},
                                {"success": True, "action": "skipped_unnecessary_installation", "missing_tools": 0}
                            )

                            return True
                        else:
                            Display.info(f"📋 Found {missing_count} missing tools - proceeding with installation")
                            break

                # Show memory recommendations
                if memory_query["recommendations"]:
                    Display.section("🧠 Memory Recommendations")
                    for rec in memory_query["recommendations"]:
                        Display.info(f"  {rec}")

            # Proceed with installation using the comprehensive tools manager
            Display.progress("Installing development tools...")
            from ..quality import ComprehensiveToolsManager
            tools_manager = ComprehensiveToolsManager(self.project_root)
            success = tools_manager.install_missing_tools()

            # Capture command execution in memory
            context = {
                "memory_check_performed": True,
                "had_recent_execution": memory_query["has_recent_execution"]
            }

            if success:
                Display.success("✅ Tools installation completed")
                # Capture successful installation
                self.advanced_memory.capture_command_execution(
                    "install tools",
                    context,
                    {"success": True, "installation_completed": True}
                )
            else:
                # Capture failed installation
                self.advanced_memory.capture_command_execution(
                    "install tools",
                    context,
                    {"success": False, "error": "installation_failed"}
                )

            return success

        except Exception as e:
            self.logger.error(f"Tool installation with memory failed: {e}")
            Display.error(f"Tool installation failed: {str(e)}")
            return False

    def _handle_check_tools_with_memory(self) -> bool:
        """Handle check tools with memory intelligence"""
        try:
            from ..quality import ComprehensiveToolsManager
            tools_manager = ComprehensiveToolsManager(self.project_root)
            result = tools_manager.display_comprehensive_status()

            # Capture tool check in memory
            self.advanced_memory.capture_command_execution(
                "check tools",
                {"orchestrator_check": True},
                {"success": True, "status_displayed": True}
            )

            return True

        except Exception as e:
            self.logger.error(f"Tool check with memory failed: {e}")
            Display.error(f"Tool check failed: {str(e)}")
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

        # Also capture in advanced memory for session continuity
        try:
            self.advanced_memory.capture_command_execution(
                command,
                {"orchestrator_execution": True},
                {"success": bool(result), "result_type": type(result).__name__}
            )
        except Exception as e:
            self.logger.debug(f"Advanced memory capture failed: {e}")

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

    def _show_session_intelligence(self) -> None:
        """Show quiet session intelligence on startup (non-intrusive)"""
        try:
            # Only show if there's meaningful session continuity
            session_intel = self.advanced_memory.get_session_intelligence()

            if session_intel and session_intel.get("recent_commands"):
                # Only show minimal intelligence to avoid clutter
                context_summary = session_intel.get("context_summary", {})
                quality_status = context_summary.get("project_quality_status", {})

                if quality_status.get("validation_count", 0) > 0:
                    grade = quality_status.get("current_grade", "N/A")
                    # Quiet intelligence notice - no intrusive display
                    self.logger.info(f"Session context loaded: {grade} quality profile, {len(session_intel['recent_commands'])} recent commands")

        except Exception as e:
            # Fail silently - don't disrupt startup for memory issues
            self.logger.debug(f"Session intelligence display failed: {e}")

    def get_session_intelligence(self) -> Dict[str, Any]:
        """Get current session intelligence for external access"""
        try:
            return self.advanced_memory.get_session_intelligence()
        except Exception as e:
            self.logger.warning(f"Failed to get session intelligence: {e}")
            return {}

    def query_command_memory(self, command_pattern: str, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Query command memory for intelligent decision making"""
        try:
            return self.advanced_memory.query_command_memory(command_pattern, timeframe_hours)
        except Exception as e:
            self.logger.warning(f"Command memory query failed: {e}")
            return {"has_recent_execution": False, "recent_commands": [], "recommendations": []}

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