#!/usr/bin/env python3
"""
Development Hooks System for CCOM v5.2+
Real-time development assistance with proactive principle enforcement

This system provides hooks that trigger during development activities:
- File save hooks for real-time quality checks
- Function write hooks for principle validation
- Code generation hooks for proactive assistance
- Pre-commit hooks for quality gates
"""

import asyncio
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass
from enum import Enum
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

from ..utils import Display, ErrorHandler
from ..orchestration.smart_orchestrator import SmartOrchestrator
from ..agents.proactive_developer import ProactiveDeveloperAgent
from ..memory.advanced_memory_keeper import AdvancedMemoryKeeper


class HookTrigger(Enum):
    """Development hook triggers"""
    FILE_SAVE = "file_save"
    FUNCTION_WRITE = "function_write"
    CODE_GENERATION = "code_generation"
    PRE_COMMIT = "pre_commit"
    PROJECT_OPEN = "project_open"
    BUILD_START = "build_start"


@dataclass
class HookEvent:
    """Hook event data"""
    trigger: HookTrigger
    file_path: Optional[Path] = None
    content: Optional[str] = None
    context: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.context is None:
            self.context = {}


@dataclass
class HookConfig:
    """Hook configuration"""
    enabled: bool = True
    auto_fix: bool = False
    show_notifications: bool = True
    parallel_execution: bool = True
    file_patterns: List[str] = None
    excluded_paths: List[str] = None

    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
        if self.excluded_paths is None:
            self.excluded_paths = ["node_modules", "__pycache__", ".git", "dist", "build"]


class DevelopmentFileWatcher(FileSystemEventHandler):
    """File system watcher for development hooks"""

    def __init__(self, hooks_manager: 'DevelopmentHooksManager'):
        self.hooks_manager = hooks_manager
        self.logger = logging.getLogger(__name__)

        # Debouncing to avoid excessive triggers
        self.last_events = {}
        self.debounce_time = 1.0  # 1 second

    def on_modified(self, event):
        """Handle file modification events"""
        if isinstance(event, FileModifiedEvent) and not event.is_directory:
            file_path = Path(event.src_path)

            # Check if file should be watched
            if self._should_watch_file(file_path):
                # Debounce rapid events
                if self._should_process_event(file_path):
                    asyncio.create_task(
                        self.hooks_manager.trigger_hook(HookTrigger.FILE_SAVE, file_path=file_path)
                    )

    def _should_watch_file(self, file_path: Path) -> bool:
        """Check if file should be watched based on patterns"""

        # Check excluded paths
        for excluded in self.hooks_manager.config.excluded_paths:
            if excluded in str(file_path):
                return False

        # Check file patterns
        for pattern in self.hooks_manager.config.file_patterns:
            if file_path.match(pattern):
                return True

        return False

    def _should_process_event(self, file_path: Path) -> bool:
        """Check if event should be processed (debouncing)"""
        now = time.time()
        last_time = self.last_events.get(str(file_path), 0)

        if now - last_time < self.debounce_time:
            return False

        self.last_events[str(file_path)] = now
        return True


class DevelopmentHooksManager:
    """
    Development Hooks Manager for real-time development assistance

    Features:
    - File save hooks for automatic quality checks
    - Function write validation for principle compliance
    - Code generation assistance with proactive guidance
    - Pre-commit quality gates
    - Real-time notifications and auto-fixing
    """

    def __init__(self, project_root: Path, config: Dict[str, Any] = None):
        self.project_root = project_root
        self.config = HookConfig(**(config or {}))
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Core components
        self.smart_orchestrator = SmartOrchestrator(project_root, config)
        self.proactive_developer = ProactiveDeveloperAgent(project_root, config)
        self.memory_keeper = AdvancedMemoryKeeper(project_root)

        # Hook registry
        self.hook_handlers: Dict[HookTrigger, List[Callable]] = {
            trigger: [] for trigger in HookTrigger
        }

        # File watcher
        self.file_watcher = None
        self.observer = None

        # Performance tracking
        self.hook_metrics = {
            "total_triggers": 0,
            "successful_hooks": 0,
            "auto_fixes_applied": 0,
            "principles_violations_prevented": 0
        }

        # Register default hooks
        self._register_default_hooks()

    def _register_default_hooks(self) -> None:
        """Register default development hooks"""

        # File save hooks
        self.register_hook(HookTrigger.FILE_SAVE, self._on_file_save)

        # Function write hooks
        self.register_hook(HookTrigger.FUNCTION_WRITE, self._on_function_write)

        # Code generation hooks
        self.register_hook(HookTrigger.CODE_GENERATION, self._on_code_generation)

        # Pre-commit hooks
        self.register_hook(HookTrigger.PRE_COMMIT, self._on_pre_commit)

        # Project open hooks
        self.register_hook(HookTrigger.PROJECT_OPEN, self._on_project_open)

    def register_hook(self, trigger: HookTrigger, handler: Callable) -> None:
        """Register a hook handler for a trigger"""
        self.hook_handlers[trigger].append(handler)
        self.logger.info(f"Registered hook handler for {trigger.value}")

    def start_watching(self) -> None:
        """Start file system watching for development hooks"""
        if self.config.enabled and not self.observer:
            try:
                self.file_watcher = DevelopmentFileWatcher(self)
                self.observer = Observer()
                self.observer.schedule(
                    self.file_watcher,
                    str(self.project_root),
                    recursive=True
                )
                self.observer.start()

                if self.config.show_notifications:
                    Display.info("🔍 Development hooks active - real-time assistance enabled")

                self.logger.info("Development hooks file watcher started")

            except Exception as e:
                self.logger.error(f"Failed to start file watcher: {e}")

    def stop_watching(self) -> None:
        """Stop file system watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.file_watcher = None

            if self.config.show_notifications:
                Display.info("🔍 Development hooks deactivated")

            self.logger.info("Development hooks file watcher stopped")

    async def trigger_hook(self, trigger: HookTrigger, **kwargs) -> List[Any]:
        """Trigger a development hook"""
        try:
            self.hook_metrics["total_triggers"] += 1

            # Create hook event
            hook_event = HookEvent(
                trigger=trigger,
                file_path=kwargs.get("file_path"),
                content=kwargs.get("content"),
                context=kwargs.get("context", {})
            )

            # Execute handlers
            results = []
            handlers = self.hook_handlers.get(trigger, [])

            if self.config.parallel_execution and len(handlers) > 1:
                # Execute handlers in parallel
                tasks = [handler(hook_event) for handler in handlers]
                results = await asyncio.gather(*tasks, return_exceptions=True)
            else:
                # Execute handlers sequentially
                for handler in handlers:
                    try:
                        result = await handler(hook_event)
                        results.append(result)
                    except Exception as e:
                        self.logger.error(f"Hook handler failed: {e}")
                        results.append(e)

            # Update metrics
            successful_results = [r for r in results if not isinstance(r, Exception)]
            if successful_results:
                self.hook_metrics["successful_hooks"] += 1

            return results

        except Exception as e:
            self.logger.error(f"Hook trigger failed: {e}")
            return [e]

    async def _on_file_save(self, event: HookEvent) -> Dict[str, Any]:
        """Handle file save events with real-time quality checks"""

        if not event.file_path:
            return {"success": False, "reason": "No file path provided"}

        try:
            # Read file content
            content = event.file_path.read_text(encoding='utf-8')

            # Quick principle validation
            validation_result = await self._quick_principle_validation(content, event.file_path)

            # Auto-fix if enabled and issues found
            if self.config.auto_fix and validation_result.get("violations", []):
                fixed_content = await self._auto_fix_principles(content, validation_result["violations"])

                if fixed_content != content:
                    # Write fixed content back
                    event.file_path.write_text(fixed_content, encoding='utf-8')
                    self.hook_metrics["auto_fixes_applied"] += 1

                    if self.config.show_notifications:
                        Display.success(f"🔧 Auto-fixed {len(validation_result['violations'])} issues in {event.file_path.name}")

            # Show validation results
            if self.config.show_notifications and validation_result.get("violations"):
                self._show_validation_notification(event.file_path, validation_result)

            # Capture in memory
            self.memory_keeper.capture_command_execution(
                f"file_save_hook",
                {"file_path": str(event.file_path), "auto_fix": self.config.auto_fix},
                {"success": True, "violations_found": len(validation_result.get("violations", []))}
            )

            return {
                "success": True,
                "file_path": str(event.file_path),
                "validation_result": validation_result,
                "auto_fix_applied": self.config.auto_fix
            }

        except Exception as e:
            self.logger.error(f"File save hook failed: {e}")
            return {"success": False, "error": str(e)}

    async def _on_function_write(self, event: HookEvent) -> Dict[str, Any]:
        """Handle function write events for principle validation"""

        if not event.content:
            return {"success": False, "reason": "No content provided"}

        try:
            # Real-time principle checking during function writing
            complexity = self._calculate_complexity(event.content)

            recommendations = []
            violations_prevented = 0

            # KISS principle check
            if complexity > 10:
                recommendations.append("🔄 Consider simplifying this function (complexity > 10)")
                violations_prevented += 1

            # Function length check
            line_count = len(event.content.splitlines())
            if line_count > 50:
                recommendations.append("📏 Function is getting long (> 50 lines) - consider breaking it down")
                violations_prevented += 1

            # Parameter count check
            param_count = self._count_parameters(event.content)
            if param_count > 5:
                recommendations.append("📝 Too many parameters (> 5) - consider using a configuration object")
                violations_prevented += 1

            # Show real-time recommendations
            if self.config.show_notifications and recommendations:
                self._show_function_recommendations(recommendations)

            self.hook_metrics["principles_violations_prevented"] += violations_prevented

            return {
                "success": True,
                "complexity": complexity,
                "line_count": line_count,
                "parameter_count": param_count,
                "recommendations": recommendations,
                "violations_prevented": violations_prevented
            }

        except Exception as e:
            self.logger.error(f"Function write hook failed: {e}")
            return {"success": False, "error": str(e)}

    async def _on_code_generation(self, event: HookEvent) -> Dict[str, Any]:
        """Handle code generation events with proactive assistance"""

        try:
            # Use proactive developer agent for code generation
            generation_context = event.context or {}
            generation_context.update({
                "purpose": generation_context.get("purpose", "Generate function"),
                "language": generation_context.get("language", "python"),
                "enforce_principles": True
            })

            result = await self.proactive_developer.execute(generation_context)

            if result.success and self.config.show_notifications:
                Display.success("🏗️ Code generated with principle compliance")

            return {
                "success": result.success,
                "generated_code": result.data.get("generated_code") if result.data else None,
                "principles_score": result.data.get("principles_score") if result.data else None
            }

        except Exception as e:
            self.logger.error(f"Code generation hook failed: {e}")
            return {"success": False, "error": str(e)}

    async def _on_pre_commit(self, event: HookEvent) -> Dict[str, Any]:
        """Handle pre-commit events with quality gates"""

        try:
            # Run quality and security checks in parallel
            result = await self.smart_orchestrator.auto_orchestrate("pre_commit")

            # Block commit if critical issues found
            if not result.success:
                critical_failures = [agent for agent in result.failed_agents
                                   if agent in ["quality-enforcer", "security-guardian"]]

                if critical_failures:
                    if self.config.show_notifications:
                        Display.error(f"🚫 Commit blocked - critical issues in: {', '.join(critical_failures)}")

                    return {
                        "success": False,
                        "block_commit": True,
                        "failed_agents": critical_failures,
                        "recommendations": result.recommendations
                    }

            if self.config.show_notifications:
                Display.success("✅ Pre-commit checks passed")

            return {
                "success": True,
                "block_commit": False,
                "parallel_efficiency": result.parallel_efficiency,
                "recommendations": result.recommendations
            }

        except Exception as e:
            self.logger.error(f"Pre-commit hook failed: {e}")
            return {"success": False, "error": str(e)}

    async def _on_project_open(self, event: HookEvent) -> Dict[str, Any]:
        """Handle project open events with context loading"""

        try:
            # Load project context and show intelligent summary
            context_summary = self.memory_keeper.get_context_summary()

            if self.config.show_notifications and context_summary:
                quality_status = context_summary.get("project_quality_status", {})
                if quality_status.get("validation_count", 0) > 0:
                    grade = quality_status.get("current_grade", "N/A")
                    Display.info(f"📊 Project Quality: {grade} | Development hooks active")

            return {
                "success": True,
                "context_loaded": True,
                "quality_status": context_summary.get("project_quality_status", {})
            }

        except Exception as e:
            self.logger.error(f"Project open hook failed: {e}")
            return {"success": False, "error": str(e)}

    async def _quick_principle_validation(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Quick principle validation for real-time feedback"""

        violations = []

        # Quick complexity check
        complexity = self._calculate_complexity(content)
        if complexity > 15:
            violations.append({
                "principle": "KISS",
                "issue": f"High complexity detected ({complexity})",
                "suggestion": "Consider breaking down complex functions"
            })

        # Quick duplication check
        if self._has_obvious_duplication(content):
            violations.append({
                "principle": "DRY",
                "issue": "Potential code duplication detected",
                "suggestion": "Extract common patterns to reduce duplication"
            })

        # Quick function length check
        long_functions = self._find_long_functions(content)
        if long_functions:
            violations.append({
                "principle": "KISS",
                "issue": f"Long functions found: {', '.join(long_functions)}",
                "suggestion": "Break down long functions into smaller, focused ones"
            })

        return {
            "file_path": str(file_path),
            "violations": violations,
            "complexity": complexity,
            "score": max(0, 100 - len(violations) * 20)
        }

    async def _auto_fix_principles(self, content: str, violations: List[Dict]) -> str:
        """Auto-fix principle violations where possible"""

        fixed_content = content

        for violation in violations:
            if violation["principle"] == "KISS" and "complexity" in violation["issue"].lower():
                # Auto-extract complex conditions
                fixed_content = self._extract_complex_conditions(fixed_content)

            # Add more auto-fixes as needed

        return fixed_content

    def _show_validation_notification(self, file_path: Path, validation_result: Dict) -> None:
        """Show validation notification"""
        violations = validation_result.get("violations", [])
        score = validation_result.get("score", 100)

        if violations:
            Display.warning(f"⚠️ {file_path.name}: {len(violations)} principle violations (Score: {score})")
            for violation in violations[:3]:  # Show first 3
                Display.info(f"  • {violation['principle']}: {violation['suggestion']}")

    def _show_function_recommendations(self, recommendations: List[str]) -> None:
        """Show function writing recommendations"""
        Display.info("💡 Real-time recommendations:")
        for rec in recommendations:
            Display.info(f"  {rec}")

    def _calculate_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity"""
        # Simple complexity calculation
        complexity = 1
        complexity += content.count("if ")
        complexity += content.count("elif ")
        complexity += content.count("while ")
        complexity += content.count("for ")
        complexity += content.count("try:")
        complexity += content.count("except")
        complexity += content.count(" and ")
        complexity += content.count(" or ")
        return complexity

    def _count_parameters(self, content: str) -> int:
        """Count function parameters"""
        # Simple parameter counting
        import re
        func_match = re.search(r'def\s+\w+\s*\(([^)]*)\)', content)
        if func_match:
            params = func_match.group(1).split(',')
            return len([p.strip() for p in params if p.strip() and p.strip() != 'self'])
        return 0

    def _has_obvious_duplication(self, content: str) -> bool:
        """Check for obvious code duplication"""
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        # Simple duplication check
        for i, line in enumerate(lines):
            for j, other_line in enumerate(lines[i+3:], i+3):  # Check lines at least 3 apart
                if line == other_line and len(line) > 20:
                    return True
        return False

    def _find_long_functions(self, content: str) -> List[str]:
        """Find functions longer than 50 lines"""
        import re

        long_functions = []
        functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)

        # Simple heuristic - count lines between function definitions
        lines = content.splitlines()
        current_function = None
        function_start = 0

        for i, line in enumerate(lines):
            if line.strip().startswith('def '):
                if current_function and (i - function_start) > 50:
                    long_functions.append(current_function)

                # Extract function name
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    current_function = match.group(1)
                    function_start = i

        return long_functions

    def _extract_complex_conditions(self, content: str) -> str:
        """Extract complex conditions to helper methods"""
        # Simple auto-fix for complex conditions
        lines = content.splitlines()
        fixed_lines = []

        for line in lines:
            # If line has too many 'and'/'or' operators, suggest extraction
            if line.count(' and ') + line.count(' or ') > 3:
                # Add comment suggesting extraction
                fixed_lines.append(line)
                fixed_lines.append("    # TODO: Consider extracting this complex condition to a helper method")
            else:
                fixed_lines.append(line)

        return "\n".join(fixed_lines)

    def get_hook_metrics(self) -> Dict[str, Any]:
        """Get hook performance metrics"""

        success_rate = 0.0
        if self.hook_metrics["total_triggers"] > 0:
            success_rate = (self.hook_metrics["successful_hooks"] / self.hook_metrics["total_triggers"]) * 100

        return {
            "total_triggers": self.hook_metrics["total_triggers"],
            "success_rate": success_rate,
            "auto_fixes_applied": self.hook_metrics["auto_fixes_applied"],
            "violations_prevented": self.hook_metrics["principles_violations_prevented"],
            "watching_enabled": self.observer is not None,
            "config": {
                "enabled": self.config.enabled,
                "auto_fix": self.config.auto_fix,
                "parallel_execution": self.config.parallel_execution
            }
        }

    def configure_hooks(self, **kwargs) -> None:
        """Configure hook settings"""

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Hook config updated: {key} = {value}")

        # Restart watching if configuration changed
        if self.observer:
            self.stop_watching()
            self.start_watching()

    def __enter__(self):
        """Context manager entry"""
        self.start_watching()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_watching()