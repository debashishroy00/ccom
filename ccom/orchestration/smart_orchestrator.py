#!/usr/bin/env python3
"""
Smart Auto-Orchestration System for CCOM v5.2+
Intelligent parallel execution with dependency management

This orchestrator automatically determines which agents can run in parallel,
manages dependencies between agents, and optimizes execution workflows.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils import Display, ErrorHandler
from ..sdk_integration import SDKIntegrationManager
from ..agents.sdk_agent_base import AgentResult


class ExecutionPhase(Enum):
    """Execution phases for agent orchestration"""
    ANALYSIS = "analysis"      # Independent analysis (parallel)
    PREPARATION = "preparation"  # Dependent on analysis
    EXECUTION = "execution"    # Dependent on preparation
    MONITORING = "monitoring"  # Post-execution monitoring


@dataclass
class AgentDependency:
    """Agent dependency specification"""
    agent_name: str
    depends_on: List[str]
    phase: ExecutionPhase
    can_fail: bool = False
    timeout_seconds: int = 300


@dataclass
class ExecutionPlan:
    """Execution plan with parallel optimization"""
    phases: Dict[ExecutionPhase, List[str]]
    dependencies: Dict[str, List[str]]
    parallel_groups: List[List[str]]
    estimated_duration: float


@dataclass
class OrchestrationResult:
    """Result of orchestrated execution"""
    success: bool
    results: Dict[str, AgentResult]
    execution_time: float
    parallel_efficiency: float
    failed_agents: List[str]
    recommendations: List[str]


class SmartOrchestrator:
    """
    Smart orchestration system that automatically:
    - Analyzes agent dependencies
    - Determines optimal parallel execution groups
    - Manages execution phases
    - Handles failures and recovery
    - Optimizes workflow performance
    """

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        self.project_root = project_root
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # SDK Integration
        self.sdk_manager = SDKIntegrationManager(project_root, config)

        # Agent dependencies configuration
        self.agent_dependencies = self._define_agent_dependencies()

        # Execution settings
        self.max_parallel_agents = config.get("max_parallel_agents", 4)
        self.default_timeout = config.get("default_timeout", 300)
        self.auto_recovery = config.get("auto_recovery", True)

        # Performance tracking
        self.orchestration_metrics = {
            "total_orchestrations": 0,
            "successful_orchestrations": 0,
            "parallel_efficiency_avg": 0.0,
            "time_saved_parallel": 0.0
        }

    def _define_agent_dependencies(self) -> Dict[str, AgentDependency]:
        """Define dependencies between agents"""

        dependencies = {
            # Analysis Phase - Independent (can run in parallel)
            "proactive-developer": AgentDependency(
                agent_name="proactive-developer",
                depends_on=[],
                phase=ExecutionPhase.ANALYSIS,
                can_fail=False
            ),
            "quality-enforcer": AgentDependency(
                agent_name="quality-enforcer",
                depends_on=[],
                phase=ExecutionPhase.ANALYSIS,
                can_fail=False
            ),
            "security-guardian": AgentDependency(
                agent_name="security-guardian",
                depends_on=[],
                phase=ExecutionPhase.ANALYSIS,
                can_fail=False
            ),

            # Preparation Phase - Depends on analysis
            "builder-agent": AgentDependency(
                agent_name="builder-agent",
                depends_on=["quality-enforcer", "security-guardian"],
                phase=ExecutionPhase.PREPARATION,
                can_fail=False
            ),

            # Execution Phase - Depends on preparation
            "deployment-specialist": AgentDependency(
                agent_name="deployment-specialist",
                depends_on=["builder-agent"],
                phase=ExecutionPhase.EXECUTION,
                can_fail=True
            )
        }

        return dependencies

    async def auto_orchestrate(self,
                             trigger_event: str,
                             context: Dict[str, Any] = None,
                             agent_selection: List[str] = None) -> OrchestrationResult:
        """
        Automatically orchestrate agents based on trigger event

        Args:
            trigger_event: Event that triggered orchestration
            context: Execution context
            agent_selection: Specific agents to run (None = auto-select)

        Returns:
            OrchestrationResult with execution details
        """

        try:
            Display.header(f"🚀 Smart Auto-Orchestration: {trigger_event}")
            start_time = datetime.now()

            # Phase 1: Determine which agents to run
            selected_agents = agent_selection or self._auto_select_agents(trigger_event, context)
            Display.info(f"📋 Selected agents: {', '.join(selected_agents)}")

            # Phase 2: Create execution plan with parallel optimization
            execution_plan = self._create_execution_plan(selected_agents)
            self._display_execution_plan(execution_plan)

            # Phase 3: Execute with intelligent orchestration
            results = await self._execute_orchestrated_plan(execution_plan, context or {})

            # Phase 4: Analyze results and performance
            execution_time = (datetime.now() - start_time).total_seconds()
            orchestration_result = self._analyze_orchestration_results(
                results, execution_time, execution_plan
            )

            # Phase 5: Update metrics and recommendations
            self._update_orchestration_metrics(orchestration_result)

            return orchestration_result

        except Exception as e:
            self.logger.error(f"Auto-orchestration failed: {e}")
            return OrchestrationResult(
                success=False,
                results={},
                execution_time=0.0,
                parallel_efficiency=0.0,
                failed_agents=[],
                recommendations=[f"Orchestration failed: {str(e)}"]
            )

    def _auto_select_agents(self, trigger_event: str, context: Dict[str, Any]) -> List[str]:
        """Automatically select agents based on trigger event"""

        if trigger_event == "code_changed":
            return ["proactive-developer", "quality-enforcer", "security-guardian"]

        elif trigger_event == "pre_commit":
            return ["quality-enforcer", "security-guardian"]

        elif trigger_event == "build_request":
            return ["quality-enforcer", "security-guardian", "builder-agent"]

        elif trigger_event == "deployment_request":
            return ["quality-enforcer", "security-guardian", "builder-agent", "deployment-specialist"]

        elif trigger_event == "full_pipeline":
            return list(self.agent_dependencies.keys())

        elif trigger_event == "security_scan":
            return ["security-guardian"]

        elif trigger_event == "quality_check":
            return ["quality-enforcer"]

        elif trigger_event == "generate_code":
            return ["proactive-developer"]

        else:
            # Default: comprehensive check
            return ["quality-enforcer", "security-guardian"]

    def _create_execution_plan(self, selected_agents: List[str]) -> ExecutionPlan:
        """Create optimized execution plan with parallel groups"""

        # Group agents by execution phase
        phases = {phase: [] for phase in ExecutionPhase}
        dependencies = {}

        for agent_name in selected_agents:
            if agent_name in self.agent_dependencies:
                dep = self.agent_dependencies[agent_name]
                phases[dep.phase].append(agent_name)
                dependencies[agent_name] = dep.depends_on

        # Create parallel groups within each phase
        parallel_groups = []
        for phase in ExecutionPhase:
            if phases[phase]:
                # All agents in same phase can run in parallel
                parallel_groups.append(phases[phase])

        # Estimate duration (parallel vs sequential)
        estimated_duration = self._estimate_execution_duration(parallel_groups)

        return ExecutionPlan(
            phases=phases,
            dependencies=dependencies,
            parallel_groups=parallel_groups,
            estimated_duration=estimated_duration
        )

    def _display_execution_plan(self, plan: ExecutionPlan) -> None:
        """Display the execution plan"""

        Display.section("📋 Execution Plan")

        for i, group in enumerate(plan.parallel_groups):
            if len(group) == 1:
                Display.info(f"Phase {i+1}: {group[0]} (sequential)")
            else:
                Display.info(f"Phase {i+1}: {', '.join(group)} (parallel)")

        Display.info(f"⏱️ Estimated duration: {plan.estimated_duration:.1f}s")

    async def _execute_orchestrated_plan(self,
                                       plan: ExecutionPlan,
                                       context: Dict[str, Any]) -> Dict[str, AgentResult]:
        """Execute the orchestrated plan with parallel optimization"""

        results = {}

        for phase_num, parallel_group in enumerate(plan.parallel_groups):
            Display.section(f"🔄 Executing Phase {phase_num + 1}")

            if len(parallel_group) == 1:
                # Sequential execution
                agent_name = parallel_group[0]
                Display.progress(f"Running {agent_name}...")
                result = await self._execute_single_agent(agent_name, context)
                results[agent_name] = result

                # Check if this agent is critical and failed
                if not result.success and not self.agent_dependencies[agent_name].can_fail:
                    Display.error(f"Critical agent {agent_name} failed, stopping pipeline")
                    break

            else:
                # Parallel execution
                Display.progress(f"Running {len(parallel_group)} agents in parallel...")
                parallel_results = await self._execute_parallel_agents(parallel_group, context)
                results.update(parallel_results)

                # Check for critical failures
                critical_failures = [
                    name for name, result in parallel_results.items()
                    if not result.success and not self.agent_dependencies[name].can_fail
                ]

                if critical_failures:
                    Display.error(f"Critical agents failed: {', '.join(critical_failures)}")
                    break

        return results

    async def _execute_single_agent(self, agent_name: str, context: Dict[str, Any]) -> AgentResult:
        """Execute a single agent"""
        try:
            result = await self.sdk_manager.invoke_agent(agent_name, context)

            if result.success:
                Display.success(f"✅ {agent_name} completed successfully")
            else:
                Display.warning(f"⚠️ {agent_name} completed with issues")

            return result

        except Exception as e:
            self.logger.error(f"Agent {agent_name} execution failed: {e}")
            return AgentResult(
                success=False,
                error=str(e),
                message=f"Agent {agent_name} execution failed"
            )

    async def _execute_parallel_agents(self,
                                     agent_names: List[str],
                                     context: Dict[str, Any]) -> Dict[str, AgentResult]:
        """Execute multiple agents in parallel"""

        # Create tasks for parallel execution
        tasks = {}
        for agent_name in agent_names:
            task = asyncio.create_task(
                self._execute_single_agent(agent_name, context),
                name=agent_name
            )
            tasks[agent_name] = task

        # Wait for all tasks to complete
        results = {}
        for agent_name, task in tasks.items():
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                self.logger.error(f"Parallel execution failed for {agent_name}: {e}")
                results[agent_name] = AgentResult(
                    success=False,
                    error=str(e),
                    message=f"Parallel execution failed for {agent_name}"
                )

        return results

    def _analyze_orchestration_results(self,
                                     results: Dict[str, AgentResult],
                                     execution_time: float,
                                     plan: ExecutionPlan) -> OrchestrationResult:
        """Analyze orchestration results and calculate metrics"""

        successful_agents = [name for name, result in results.items() if result.success]
        failed_agents = [name for name, result in results.items() if not result.success]

        # Calculate parallel efficiency
        sequential_time = len(results) * (execution_time / len(plan.parallel_groups))
        parallel_efficiency = min(100.0, (sequential_time / execution_time) * 100) if execution_time > 0 else 0.0

        # Generate recommendations
        recommendations = self._generate_orchestration_recommendations(
            results, execution_time, parallel_efficiency
        )

        return OrchestrationResult(
            success=len(failed_agents) == 0,
            results=results,
            execution_time=execution_time,
            parallel_efficiency=parallel_efficiency,
            failed_agents=failed_agents,
            recommendations=recommendations
        )

    def _generate_orchestration_recommendations(self,
                                              results: Dict[str, AgentResult],
                                              execution_time: float,
                                              parallel_efficiency: float) -> List[str]:
        """Generate intelligent recommendations based on orchestration results"""

        recommendations = []

        # Performance recommendations
        if parallel_efficiency > 80:
            recommendations.append("🚀 Excellent parallel efficiency achieved")
        elif parallel_efficiency > 60:
            recommendations.append("✅ Good parallel execution performance")
        else:
            recommendations.append("⚡ Consider optimizing agent dependencies for better parallelization")

        # Failure analysis recommendations
        failed_agents = [name for name, result in results.items() if not result.success]
        if failed_agents:
            recommendations.append(f"🔍 Review failed agents: {', '.join(failed_agents)}")

            # Specific recommendations based on failed agents
            if "security-guardian" in failed_agents:
                recommendations.append("🛡️ Address security issues before proceeding")
            if "quality-enforcer" in failed_agents:
                recommendations.append("📐 Fix code quality issues for better maintainability")
            if "builder-agent" in failed_agents:
                recommendations.append("🏗️ Resolve build issues before deployment")

        # Time-based recommendations
        if execution_time > 300:  # 5 minutes
            recommendations.append("⏱️ Consider agent optimization for faster execution")

        return recommendations

    def _update_orchestration_metrics(self, result: OrchestrationResult) -> None:
        """Update orchestration performance metrics"""

        self.orchestration_metrics["total_orchestrations"] += 1

        if result.success:
            self.orchestration_metrics["successful_orchestrations"] += 1

        # Update parallel efficiency average
        current_avg = self.orchestration_metrics["parallel_efficiency_avg"]
        total = self.orchestration_metrics["total_orchestrations"]
        self.orchestration_metrics["parallel_efficiency_avg"] = (
            (current_avg * (total - 1) + result.parallel_efficiency) / total
        )

    def _estimate_execution_duration(self, parallel_groups: List[List[str]]) -> float:
        """Estimate execution duration for parallel groups"""

        # Rough estimates based on agent complexity
        agent_times = {
            "proactive-developer": 30.0,
            "quality-enforcer": 45.0,
            "security-guardian": 60.0,
            "builder-agent": 90.0,
            "deployment-specialist": 120.0
        }

        total_time = 0.0
        for group in parallel_groups:
            # Parallel groups take time of slowest agent
            group_time = max(agent_times.get(agent, 30.0) for agent in group)
            total_time += group_time

        return total_time

    async def execute_enterprise_workflow(self, workflow_name: str, context: Dict[str, Any] = None) -> OrchestrationResult:
        """Execute predefined enterprise workflows"""

        workflow_mappings = {
            "enterprise_deployment": "deployment_request",
            "quality_improvement": "quality_check",
            "security_hardening": "security_scan",
            "full_pipeline": "full_pipeline",
            "development_cycle": "code_changed"
        }

        trigger_event = workflow_mappings.get(workflow_name, "full_pipeline")
        return await self.auto_orchestrate(trigger_event, context)

    def get_orchestration_metrics(self) -> Dict[str, Any]:
        """Get orchestration performance metrics"""

        success_rate = 0.0
        if self.orchestration_metrics["total_orchestrations"] > 0:
            success_rate = (
                self.orchestration_metrics["successful_orchestrations"] /
                self.orchestration_metrics["total_orchestrations"]
            ) * 100

        return {
            "total_orchestrations": self.orchestration_metrics["total_orchestrations"],
            "success_rate": success_rate,
            "parallel_efficiency_avg": self.orchestration_metrics["parallel_efficiency_avg"],
            "available_agents": len(self.agent_dependencies),
            "max_parallel_capacity": self.max_parallel_agents
        }

    async def smart_execute(self,
                          agent_groups: List[List[str]],
                          context: Dict[str, Any] = None) -> OrchestrationResult:
        """
        Execute agents with custom grouping for parallel execution

        Args:
            agent_groups: List of agent groups, each group runs in parallel
            context: Execution context
        """

        Display.header("🧠 Smart Execute: Custom Agent Orchestration")

        # Create custom execution plan
        execution_plan = ExecutionPlan(
            phases={ExecutionPhase.ANALYSIS: agent_groups[0] if agent_groups else []},
            dependencies={},
            parallel_groups=agent_groups,
            estimated_duration=self._estimate_execution_duration(agent_groups)
        )

        self._display_execution_plan(execution_plan)

        start_time = datetime.now()
        results = await self._execute_orchestrated_plan(execution_plan, context or {})
        execution_time = (datetime.now() - start_time).total_seconds()

        return self._analyze_orchestration_results(results, execution_time, execution_plan)