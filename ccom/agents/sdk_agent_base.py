#!/usr/bin/env python3
"""
SDK Agent Base Class for CCOM v5.0
Provides base functionality for Claude SDK-based agents
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, AsyncGenerator
from pathlib import Path
import json


@dataclass
class AgentResult:
    """Standardized agent execution result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None


@dataclass
class StreamingUpdate:
    """Streaming update from agent execution"""
    type: str  # 'progress', 'result', 'error', 'complete'
    content: str
    data: Optional[Dict[str, Any]] = None


class SDKAgentBase(ABC):
    """
    Base class for all CCOM SDK-based agents

    Provides standardized interface for:
    - Claude SDK integration
    - Streaming responses
    - Error handling and retry logic
    - Permissions and security
    - Metrics and monitoring
    """

    def __init__(self, project_root: Path, config: Optional[Dict[str, Any]] = None):
        self.project_root = project_root
        self.config = config or {}
        self.logger = logging.getLogger(f"ccom.agents.{self.__class__.__name__}")

        # Agent metadata
        self.name = self.__class__.__name__
        self.version = "5.0.0"
        self.capabilities = self._get_capabilities()

        # Execution state
        self.is_running = False
        self.current_operation = None

        # Metrics
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.last_execution_result = None

    @abstractmethod
    def _get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """Execute the agent's primary function"""
        pass

    async def execute_streaming(self, context: Dict[str, Any]) -> AsyncGenerator[StreamingUpdate, None]:
        """
        Execute with streaming updates for real-time feedback
        Default implementation wraps non-streaming execute
        """
        yield StreamingUpdate(
            type="progress",
            content=f"🤖 **{self.name}** starting execution...",
        )

        try:
            result = await self.execute(context)

            yield StreamingUpdate(
                type="result",
                content=result.message,
                data=result.data
            )

            if result.success:
                yield StreamingUpdate(
                    type="complete",
                    content=f"✅ **{self.name}** completed successfully",
                    data={"metrics": result.metrics}
                )
            else:
                yield StreamingUpdate(
                    type="error",
                    content=f"❌ **{self.name}** execution failed",
                    data={"errors": result.errors}
                )

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}")
            yield StreamingUpdate(
                type="error",
                content=f"❌ **{self.name}** encountered an error: {str(e)}"
            )

    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.capabilities,
            "is_running": self.is_running,
            "current_operation": self.current_operation,
            "metrics": {
                "execution_count": self.execution_count,
                "average_execution_time": (
                    self.total_execution_time / self.execution_count
                    if self.execution_count > 0 else 0
                ),
                "last_result": self.last_execution_result
            }
        }

    def validate_permissions(self, operation: str) -> bool:
        """
        Validate agent has permission to perform operation
        Override in subclasses for specific permission logic
        """
        allowed_operations = self.config.get("allowed_operations", [])
        if not allowed_operations:
            return True  # No restrictions configured

        return operation in allowed_operations

    def _update_metrics(self, execution_time: float, result: AgentResult):
        """Update agent execution metrics"""
        self.execution_count += 1
        self.total_execution_time += execution_time
        self.last_execution_result = {
            "success": result.success,
            "timestamp": self._get_timestamp(),
            "execution_time": execution_time
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()

    async def pre_execute_hook(self, context: Dict[str, Any]) -> bool:
        """
        Hook called before execution
        Return False to abort execution
        """
        operation = context.get("operation", "unknown")

        if not self.validate_permissions(operation):
            self.logger.warning(f"Permission denied for operation: {operation}")
            return False

        self.is_running = True
        self.current_operation = operation
        return True

    async def post_execute_hook(self, context: Dict[str, Any], result: AgentResult):
        """Hook called after execution"""
        self.is_running = False
        self.current_operation = None

    def get_configuration_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for agent configuration
        Override in subclasses to define specific config requirements
        """
        return {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether this agent is enabled"
                },
                "timeout": {
                    "type": "number",
                    "default": 300,
                    "description": "Execution timeout in seconds"
                },
                "retry_count": {
                    "type": "integer",
                    "default": 3,
                    "description": "Number of retry attempts on failure"
                },
                "allowed_operations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of allowed operations (empty = all allowed)"
                }
            }
        }