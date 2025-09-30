#!/usr/bin/env python3
"""
CCOM SDK Integration Manager v5.0
Manages the transition from markdown agents to SDK-based agents
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from enum import Enum

from .agents import (
    SDKAgentBase,
    QualityEnforcerAgent,
    SecurityGuardianAgent,
    BuilderAgent,
    DeploymentSpecialistAgent
)
from .agents.sdk_agent_base import AgentResult, StreamingUpdate


class AgentMode(Enum):
    """Agent execution mode"""
    MARKDOWN_LEGACY = "markdown"  # Old .claude/agents/*.md approach
    SDK_NATIVE = "sdk"           # New SDK-based agents
    HYBRID = "hybrid"            # Both modes available, SDK preferred


class SDKIntegrationManager:
    """
    Manages the integration between legacy markdown agents and new SDK agents

    Features:
    - Seamless transition from markdown to SDK agents
    - Backward compatibility during migration
    - Performance monitoring and comparison
    - Configuration management
    - Error handling and fallback
    """

    def __init__(self, project_root: Path, config: Optional[Dict[str, Any]] = None):
        self.project_root = project_root
        self.config = config or {}
        self.logger = logging.getLogger("ccom.sdk_integration")

        # Execution mode
        self.mode = AgentMode(self.config.get("agent_mode", "hybrid"))

        # Initialize SDK agents
        self.sdk_agents = self._initialize_sdk_agents()

        # Legacy orchestrator (for fallback)
        self.legacy_orchestrator = None

        # Performance tracking
        self.execution_metrics = {
            "sdk_executions": 0,
            "legacy_executions": 0,
            "sdk_success_rate": 0.0,
            "legacy_success_rate": 0.0,
            "average_sdk_time": 0.0,
            "average_legacy_time": 0.0
        }

    def _initialize_sdk_agents(self) -> Dict[str, SDKAgentBase]:
        """Initialize all SDK-based agents"""
        agents = {}

        try:
            # Quality Enforcer
            agents["quality-enforcer"] = QualityEnforcerAgent(
                self.project_root,
                self.config.get("quality_enforcer", {})
            )

            # Security Guardian - SDK Implementation (v5.1)
            agents["security-guardian"] = SecurityGuardianAgent(
                self.project_root,
                self.config.get("security_guardian", {})
            )

            # Builder Agent - SDK Implementation (v5.1)
            agents["builder-agent"] = BuilderAgent(
                self.project_root,
                self.config.get("builder_agent", {})
            )

            # Deployment Specialist - SDK Implementation (v5.2)
            agents["deployment-specialist"] = DeploymentSpecialistAgent(
                self.project_root,
                self.config.get("deployment_specialist", {})
            )

            self.logger.info(f"Initialized {len(agents)} SDK agents")

        except Exception as e:
            self.logger.error(f"Failed to initialize SDK agents: {e}")

        return agents

    async def invoke_agent(
        self,
        agent_name: str,
        context: Optional[Dict[str, Any]] = None,
        streaming: bool = False
    ) -> Union[AgentResult, AsyncGenerator[StreamingUpdate, None]]:
        """
        Invoke an agent with intelligent routing between SDK and legacy modes

        Args:
            agent_name: Name of the agent to invoke
            context: Execution context
            streaming: Whether to use streaming mode

        Returns:
            AgentResult or AsyncGenerator for streaming
        """
        context = context or {}
        context["operation"] = context.get("operation", agent_name)

        # Determine execution method
        use_sdk = self._should_use_sdk(agent_name)

        if use_sdk and agent_name in self.sdk_agents:
            return await self._invoke_sdk_agent(agent_name, context, streaming)
        else:
            return await self._invoke_legacy_agent(agent_name, context, streaming)

    def _should_use_sdk(self, agent_name: str) -> bool:
        """Determine whether to use SDK or legacy agent"""
        if self.mode == AgentMode.SDK_NATIVE:
            return True
        elif self.mode == AgentMode.MARKDOWN_LEGACY:
            return False
        elif self.mode == AgentMode.HYBRID:
            # Prefer SDK if available and enabled
            return (
                agent_name in self.sdk_agents and
                self.config.get("enable_sdk_agents", True)
            )
        return False

    async def _invoke_sdk_agent(
        self,
        agent_name: str,
        context: Dict[str, Any],
        streaming: bool
    ) -> Union[AgentResult, AsyncGenerator[StreamingUpdate, None]]:
        """Invoke SDK-based agent"""
        agent = self.sdk_agents[agent_name]

        try:
            start_time = asyncio.get_event_loop().time()

            if streaming:
                return agent.execute_streaming(context)
            else:
                result = await agent.execute(context)

                # Update metrics
                execution_time = asyncio.get_event_loop().time() - start_time
                self._update_sdk_metrics(execution_time, result.success)

                return result

        except Exception as e:
            self.logger.error(f"SDK agent {agent_name} failed: {e}")

            # Fallback to legacy if enabled
            if self.config.get("fallback_to_legacy", True):
                self.logger.info(f"Falling back to legacy agent for {agent_name}")
                return await self._invoke_legacy_agent(agent_name, context, streaming)
            else:
                return AgentResult(
                    success=False,
                    message=f"❌ SDK agent {agent_name} failed: {str(e)}",
                    errors=[str(e)]
                )

    async def _invoke_legacy_agent(
        self,
        agent_name: str,
        context: Dict[str, Any],
        streaming: bool
    ) -> AgentResult:
        """Invoke legacy markdown-based agent"""
        try:
            # Initialize legacy orchestrator if needed
            if self.legacy_orchestrator is None:
                from .orchestrator import CCOMOrchestrator
                self.legacy_orchestrator = CCOMOrchestrator()

            start_time = asyncio.get_event_loop().time()

            # Execute legacy agent
            success = await asyncio.get_event_loop().run_in_executor(
                None,
                self.legacy_orchestrator.execute_agent_implementation,
                agent_name
            )

            execution_time = asyncio.get_event_loop().time() - start_time
            self._update_legacy_metrics(execution_time, success)

            if success:
                return AgentResult(
                    success=True,
                    message=f"✅ Legacy {agent_name} completed successfully",
                    metrics={"execution_time": execution_time, "mode": "legacy"}
                )
            else:
                return AgentResult(
                    success=False,
                    message=f"❌ Legacy {agent_name} execution failed",
                    metrics={"execution_time": execution_time, "mode": "legacy"}
                )

        except Exception as e:
            self.logger.error(f"Legacy agent {agent_name} failed: {e}")
            return AgentResult(
                success=False,
                message=f"❌ Legacy agent {agent_name} failed: {str(e)}",
                errors=[str(e)]
            )

    def _update_sdk_metrics(self, execution_time: float, success: bool):
        """Update SDK execution metrics"""
        self.execution_metrics["sdk_executions"] += 1

        # Update success rate
        total_executions = self.execution_metrics["sdk_executions"]
        current_successes = (
            self.execution_metrics["sdk_success_rate"] * (total_executions - 1)
        )
        if success:
            current_successes += 1

        self.execution_metrics["sdk_success_rate"] = current_successes / total_executions

        # Update average execution time
        current_total_time = (
            self.execution_metrics["average_sdk_time"] * (total_executions - 1)
        )
        self.execution_metrics["average_sdk_time"] = (
            current_total_time + execution_time
        ) / total_executions

    def _update_legacy_metrics(self, execution_time: float, success: bool):
        """Update legacy execution metrics"""
        self.execution_metrics["legacy_executions"] += 1

        # Update success rate
        total_executions = self.execution_metrics["legacy_executions"]
        current_successes = (
            self.execution_metrics["legacy_success_rate"] * (total_executions - 1)
        )
        if success:
            current_successes += 1

        self.execution_metrics["legacy_success_rate"] = current_successes / total_executions

        # Update average execution time
        current_total_time = (
            self.execution_metrics["average_legacy_time"] * (total_executions - 1)
        )
        self.execution_metrics["average_legacy_time"] = (
            current_total_time + execution_time
        ) / total_executions

    def get_agent_status(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get status of agents"""
        if agent_name:
            if agent_name in self.sdk_agents:
                return {
                    "agent": agent_name,
                    "type": "sdk",
                    "status": self.sdk_agents[agent_name].get_status()
                }
            else:
                return {
                    "agent": agent_name,
                    "type": "legacy",
                    "status": "Available via legacy orchestrator"
                }
        else:
            # Return status of all agents
            status = {
                "mode": self.mode.value,
                "sdk_agents": {
                    name: agent.get_status()
                    for name, agent in self.sdk_agents.items()
                },
                "legacy_agents": [
                    "quality-enforcer",
                    "security-guardian",
                    "builder-agent",
                    "deployment-specialist"
                ],
                "metrics": self.execution_metrics
            }
            return status

    def get_migration_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for SDK migration"""
        recommendations = []

        # Check SDK vs Legacy performance
        if (self.execution_metrics["sdk_executions"] > 0 and
            self.execution_metrics["legacy_executions"] > 0):

            sdk_perf = (
                self.execution_metrics["sdk_success_rate"] * 100 /
                max(self.execution_metrics["average_sdk_time"], 0.1)
            )
            legacy_perf = (
                self.execution_metrics["legacy_success_rate"] * 100 /
                max(self.execution_metrics["average_legacy_time"], 0.1)
            )

            if sdk_perf > legacy_perf * 1.2:  # 20% better
                recommendations.append({
                    "type": "performance",
                    "message": "SDK agents showing 20%+ better performance - consider full migration",
                    "priority": "high"
                })

        # Check agent availability
        available_sdk_agents = len(self.sdk_agents)
        total_agents = 4  # Total expected agents

        if available_sdk_agents >= total_agents:
            recommendations.append({
                "type": "feature_parity",
                "message": "All agents available in SDK - ready for full migration",
                "priority": "high"
            })
        elif available_sdk_agents >= total_agents * 0.5:
            recommendations.append({
                "type": "partial_migration",
                "message": f"{available_sdk_agents}/{total_agents} agents ready - consider hybrid mode",
                "priority": "medium"
            })

        # Mode recommendations
        if self.mode == AgentMode.HYBRID:
            recommendations.append({
                "type": "mode",
                "message": "Currently in hybrid mode - monitor performance for full SDK migration",
                "priority": "low"
            })

        return {
            "current_mode": self.mode.value,
            "sdk_agents_available": available_sdk_agents,
            "total_agents": total_agents,
            "recommendations": recommendations,
            "performance_comparison": {
                "sdk_success_rate": f"{self.execution_metrics['sdk_success_rate']*100:.1f}%",
                "legacy_success_rate": f"{self.execution_metrics['legacy_success_rate']*100:.1f}%",
                "sdk_avg_time": f"{self.execution_metrics['average_sdk_time']:.2f}s",
                "legacy_avg_time": f"{self.execution_metrics['average_legacy_time']:.2f}s"
            }
        }

    async def migrate_to_sdk_mode(self) -> bool:
        """Migrate to full SDK mode"""
        try:
            # Verify all required agents are available
            required_agents = ["quality-enforcer", "security-guardian", "builder-agent", "deployment-specialist"]
            missing_agents = [agent for agent in required_agents if agent not in self.sdk_agents]

            if missing_agents:
                self.logger.warning(f"Cannot migrate - missing SDK agents: {missing_agents}")
                return False

            # Update mode
            self.mode = AgentMode.SDK_NATIVE
            self.logger.info("Successfully migrated to SDK native mode")
            return True

        except Exception as e:
            self.logger.error(f"Migration to SDK mode failed: {e}")
            return False

    def set_agent_mode(self, mode: str) -> bool:
        """Set agent execution mode"""
        try:
            self.mode = AgentMode(mode)
            self.logger.info(f"Agent mode set to: {mode}")
            return True
        except ValueError:
            self.logger.error(f"Invalid agent mode: {mode}")
            return False