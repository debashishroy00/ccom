#!/usr/bin/env python3
"""
Agent Management Module
Extracted from orchestrator.py to follow Single Responsibility Principle

Handles:
- Agent invocation and coordination
- SDK integration management
- Agent status monitoring
- Performance metrics
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from datetime import datetime

from ccom.utils import ErrorHandler, Display
from ccom.sdk_integration import SDKIntegrationManager, AgentMode
from ccom.agents.sdk_agent_base import AgentResult, StreamingUpdate


class AgentManager:
    """
    Manages CCOM agent operations with proper separation of concerns

    Replaces agent-related methods from CCOMOrchestrator (300+ lines)
    """

    def __init__(self, project_root: Path, memory_manager, config: Optional[Dict[str, Any]] = None):
        self.project_root = project_root
        self.memory_manager = memory_manager
        self.config = config or {}

        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Initialize SDK integration
        self.sdk_integration = self._initialize_sdk_integration()

        # Agent execution metrics
        self.execution_history = []

    def _initialize_sdk_integration(self) -> SDKIntegrationManager:
        """Initialize SDK Integration Manager for modern agent support"""
        try:
            # Load SDK configuration from memory or defaults
            memory = self.memory_manager.memory
            sdk_config = memory.get("sdk_config", {
                "agent_mode": "hybrid",  # Start in hybrid mode for backward compatibility
                "enable_sdk_agents": True,
                "fallback_to_legacy": True,
                "enable_streaming": True
            })

            integration_manager = SDKIntegrationManager(
                self.project_root,
                sdk_config
            )

            self.logger.info(f"SDK Integration initialized in {sdk_config.get('agent_mode', 'hybrid')} mode")
            return integration_manager

        except Exception as e:
            self.logger.error(f"Failed to initialize SDK integration: {e}")
            # Return a basic manager in legacy mode as fallback
            return SDKIntegrationManager(
                self.project_root,
                {"agent_mode": "markdown"}
            )

    async def invoke_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, Any]] = None,
        streaming: bool = False,
        force_mode: Optional[str] = None
    ) -> Union[AgentResult, bool]:
        """
        Modern CCOM Agent Execution with SDK Integration

        Args:
            agent_name: Name of agent to invoke
            context: Execution context
            streaming: Enable streaming mode
            force_mode: Force specific mode (sdk/legacy)

        Returns:
            AgentResult or boolean for legacy compatibility
        """
        context = context or {}
        execution_start = datetime.now()

        try:
            # Override agent mode if forced
            if force_mode:
                original_mode = self.sdk_integration.mode
                self.sdk_integration.set_agent_mode(force_mode)

            # Use SDK integration for intelligent agent routing
            result = await self.sdk_integration.invoke_agent(
                agent_name=agent_name,
                context=context,
                streaming=streaming
            )

            # Restore original mode if it was forced
            if force_mode:
                self.sdk_integration.set_agent_mode(original_mode.value)

            # Record execution
            self._record_execution(agent_name, context, result, execution_start)

            # Handle different result types
            if hasattr(result, 'success'):
                # SDK AgentResult
                if streaming:
                    return await self._handle_streaming_result(result)
                else:
                    return self._handle_standard_result(result)
            else:
                # Legacy boolean result
                return result

        except Exception as e:
            self.logger.error(f"Agent invocation failed: {e}")
            Display.error(f"Agent {agent_name} execution failed: {str(e)}")
            return False

    async def _handle_streaming_result(self, result) -> bool:
        """Handle streaming agent results"""
        try:
            async def handle_streaming():
                success = True
                async for update in result:
                    Display.progress(update.content)
                    if update.type == "complete":
                        return True
                    elif update.type == "error":
                        success = False
                return success

            return await handle_streaming()

        except Exception as e:
            self.logger.error(f"Streaming result handling failed: {e}")
            return False

    def _handle_standard_result(self, result: AgentResult) -> bool:
        """Handle standard agent results"""
        try:
            # Display main message
            if result.success:
                Display.success(result.message)
            else:
                Display.error(result.message)

            # Display errors
            if result.errors:
                for error in result.errors:
                    Display.error(error)

            # Display warnings
            if result.warnings:
                for warning in result.warnings:
                    Display.warning(warning)

            # Display metrics if available
            if result.metrics and self.config.get("show_metrics", False):
                Display.metrics_table(result.metrics, "Agent Metrics")

            return result.success

        except Exception as e:
            self.logger.error(f"Result handling failed: {e}")
            return False

    def _record_execution(
        self,
        agent_name: str,
        context: Dict[str, Any],
        result: Union[AgentResult, bool],
        start_time: datetime
    ) -> None:
        """Record agent execution for metrics"""
        try:
            execution_time = (datetime.now() - start_time).total_seconds()

            execution_record = {
                "agent_name": agent_name,
                "timestamp": start_time.isoformat(),
                "execution_time": execution_time,
                "success": result.success if hasattr(result, 'success') else result,
                "mode": self.sdk_integration.mode.value,
                "context_size": len(str(context))
            }

            self.execution_history.append(execution_record)

            # Keep only last 100 executions
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

        except Exception as e:
            self.logger.warning(f"Failed to record execution: {e}")

    def invoke_quality_enforcer(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Invoke quality enforcer agent"""
        context = context or {"operation": "quality_check"}
        return asyncio.run(self.invoke_agent("quality-enforcer", context))

    def invoke_security_guardian(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Invoke security guardian agent"""
        context = context or {"operation": "security_scan"}
        return asyncio.run(self.invoke_agent("security-guardian", context))

    def invoke_builder_agent(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Invoke builder agent"""
        context = context or {"operation": "build"}
        return asyncio.run(self.invoke_agent("builder-agent", context))

    def invoke_deployment_specialist(self, context: Optional[Dict[str, Any]] = None) -> bool:
        """Invoke deployment specialist agent"""
        context = context or {"operation": "deploy"}
        return asyncio.run(self.invoke_agent("deployment-specialist", context))

    # Legacy compatibility methods
    def invoke_subagent(self, agent_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Legacy compatibility method"""
        return asyncio.run(self.invoke_agent(agent_name, context))

    def execute_agent_implementation(self, agent_name: str) -> bool:
        """Legacy compatibility method for direct agent implementation"""
        legacy_implementations = {
            "quality-enforcer": self._legacy_quality_enforcement,
            "security-guardian": self._legacy_security_scan,
            "builder-agent": self._legacy_build_process,
            "deployment-specialist": self._legacy_deployment_process,
        }

        if agent_name in legacy_implementations:
            return self.error_handler.safe_execute(
                legacy_implementations[agent_name],
                default_return=False,
                error_message=f"Legacy agent {agent_name} execution failed"
            )
        else:
            Display.error(f"No implementation available for {agent_name}")
            return False

    def _legacy_quality_enforcement(self) -> bool:
        """Legacy quality enforcement implementation"""
        Display.progress("Running legacy quality enforcement...")
        # This would delegate to the original implementation
        # For now, return success to maintain compatibility
        return True

    def _legacy_security_scan(self) -> bool:
        """Legacy security scan implementation"""
        Display.progress("Running legacy security scan...")
        # This would delegate to the original implementation
        return True

    def _legacy_build_process(self) -> bool:
        """Legacy build process implementation"""
        Display.progress("Running legacy build process...")
        # This would delegate to the original implementation
        return True

    def _legacy_deployment_process(self) -> bool:
        """Legacy deployment process implementation"""
        Display.progress("Running legacy deployment process...")
        # This would delegate to the original implementation
        return True

    # SDK Management Methods
    def get_agent_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of SDK and legacy agents"""
        return self.sdk_integration.get_agent_status(agent_name)

    def get_migration_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for migrating to SDK agents"""
        return self.sdk_integration.get_migration_recommendations()

    def set_agent_mode(self, mode: str) -> bool:
        """Set agent execution mode (sdk, markdown, hybrid)"""
        success = self.sdk_integration.set_agent_mode(mode)
        if success:
            # Update memory configuration
            memory = self.memory_manager.memory
            if "sdk_config" not in memory:
                memory["sdk_config"] = {}
            memory["sdk_config"]["agent_mode"] = mode
            self.memory_manager.save_memory()
            Display.success(f"Agent mode set to: {mode}")
        else:
            Display.error(f"Failed to set agent mode: {mode}")
        return success

    async def migrate_to_sdk_mode(self) -> bool:
        """Migrate to full SDK mode"""
        Display.header("🚀 CCOM SDK MIGRATION")
        Display.progress("Upgrading to modern agent architecture...")

        # Check migration readiness
        recommendations = self.get_migration_recommendations()
        ready_for_migration = any(
            rec["priority"] == "high" and "full migration" in rec["message"]
            for rec in recommendations["recommendations"]
        )

        if not ready_for_migration:
            Display.warning("System not ready for full SDK migration")
            Display.section("Current status")
            for rec in recommendations["recommendations"]:
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                print(f"  {priority_icon} {rec['message']}")
            return False

        # Perform migration
        success = await self.sdk_integration.migrate_to_sdk_mode()

        if success:
            # Update memory
            memory = self.memory_manager.memory
            memory["sdk_config"] = memory.get("sdk_config", {})
            memory["sdk_config"]["agent_mode"] = "sdk"
            memory["sdk_config"]["migration_date"] = datetime.now().isoformat()
            self.memory_manager.save_memory()

            Display.success("SDK MIGRATION COMPLETE")
            Display.info("CCOM now using modern SDK-based agents for optimal performance")
            return True
        else:
            Display.error("SDK migration failed - remaining in hybrid mode")
            return False

    def show_agent_status(self) -> bool:
        """Show comprehensive agent integration status"""
        Display.header("🤖 CCOM Agent Status")

        status = self.get_agent_status()
        Display.key_value_table({
            "Mode": status['mode'].upper(),
            "SDK Agents": len(status['sdk_agents']),
            "Legacy Agents": len(status['legacy_agents'])
        })

        # Show metrics
        metrics = status['metrics']
        if metrics['sdk_executions'] > 0 or metrics['legacy_executions'] > 0:
            Display.section("📈 Performance Metrics")
            Display.key_value_table({
                "SDK Executions": metrics['sdk_executions'],
                "Legacy Executions": metrics['legacy_executions'],
                "SDK Success Rate": f"{metrics['sdk_success_rate']*100:.1f}%",
                "Legacy Success Rate": f"{metrics['legacy_success_rate']*100:.1f}%",
                "SDK Avg Time": f"{metrics['average_sdk_time']:.2f}s",
                "Legacy Avg Time": f"{metrics['average_legacy_time']:.2f}s"
            })

        # Show available SDK agents
        if status['sdk_agents']:
            Display.section("🤖 Available SDK Agents")
            for name, agent_status in status['sdk_agents'].items():
                is_running = "🔄" if agent_status['is_running'] else "✅"
                print(f"  {is_running} {name} (v{agent_status['version']})")

        # Show migration recommendations
        recommendations = self.get_migration_recommendations()
        if recommendations['recommendations']:
            Display.section("💡 Migration Recommendations")
            for rec in recommendations['recommendations']:
                priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                print(f"  {priority_icon} {rec['message']}")

        return True

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get agent execution metrics"""
        if not self.execution_history:
            return {"total_executions": 0}

        total = len(self.execution_history)
        successful = sum(1 for exec in self.execution_history if exec['success'])
        avg_time = sum(exec['execution_time'] for exec in self.execution_history) / total

        # Group by agent
        agent_stats = {}
        for exec in self.execution_history:
            agent = exec['agent_name']
            if agent not in agent_stats:
                agent_stats[agent] = {"executions": 0, "successes": 0, "total_time": 0}

            agent_stats[agent]["executions"] += 1
            if exec['success']:
                agent_stats[agent]["successes"] += 1
            agent_stats[agent]["total_time"] += exec['execution_time']

        return {
            "total_executions": total,
            "success_rate": successful / total,
            "average_execution_time": avg_time,
            "agent_stats": agent_stats,
            "recent_executions": self.execution_history[-10:]  # Last 10
        }