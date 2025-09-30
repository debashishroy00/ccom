#!/usr/bin/env python3
"""
Advanced Memory Keeper for CCOM
World-class memory and context intelligence system

Features:
- Semantic validation result capturing
- Intelligent context building from validation patterns
- Learning from code quality improvements
- Memory-driven recommendations
- Enterprise-grade interaction tracking
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from ..utils import Display, ErrorHandler


class AdvancedMemoryKeeper:
    """Advanced memory system with validation intelligence"""

    def __init__(self, project_root: Path, memory_manager=None):
        self.project_root = project_root
        self.memory_manager = memory_manager
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)

        # Memory storage paths
        self.validation_history_file = self.project_root / ".claude" / "validation_history.json"
        self.pattern_learning_file = self.project_root / ".claude" / "pattern_learning.json"
        self.context_intelligence_file = self.project_root / ".claude" / "context_intelligence.json"
        self.command_history_file = self.project_root / ".claude" / "command_history.json"
        self.session_continuity_file = self.project_root / ".claude" / "session_continuity.json"

        # Initialize memory structures
        self.validation_history = self._load_validation_history()
        self.pattern_learning = self._load_pattern_learning()
        self.context_intelligence = self._load_context_intelligence()
        self.command_history = self._load_command_history()
        self.session_continuity = self._load_session_continuity()

        # Auto-load context for new sessions
        self._auto_load_session_context()

    def capture_validation_session(self, validation_report: Dict[str, Any]) -> None:
        """Capture comprehensive validation session with intelligent analysis"""
        try:
            session_data = {
                "session_id": validation_report.get("session_id"),
                "timestamp": validation_report.get("timestamp"),
                "overall_score": validation_report.get("overall", {}).get("score", 0),
                "overall_grade": validation_report.get("overall", {}).get("grade", "N/A"),
                "principles_score": validation_report.get("principles", {}).get("score", 0),
                "principles_grade": validation_report.get("principles", {}).get("grade", "N/A"),
                "quality_score": validation_report.get("quality", {}).get("score", 0),
                "security_score": validation_report.get("security", {}).get("score", 0),
                "total_issues": validation_report.get("overall", {}).get("total_issues", 0),
                "total_warnings": validation_report.get("overall", {}).get("total_warnings", 0),
                "recommendations": validation_report.get("recommendations", []),
                "validation_results": self._extract_key_metrics(validation_report.get("validation_results", []))
            }

            # Add to validation history
            self.validation_history.append(session_data)

            # Keep only last 50 sessions for performance
            if len(self.validation_history) > 50:
                self.validation_history = self.validation_history[-50:]

            # Analyze patterns and learn
            self._analyze_validation_patterns(session_data)
            self._update_context_intelligence(session_data)

            # Save all memory structures
            self._save_all_memory()

            # Update main memory manager if available
            if self.memory_manager:
                self._update_main_memory(session_data)

            Display.info(f"🧠 Validation session captured: {session_data['session_id']}")

        except Exception as e:
            self.logger.error(f"Failed to capture validation session: {e}")

    def _extract_key_metrics(self, validation_results: List) -> List[Dict]:
        """Extract key metrics from validation results"""
        key_metrics = []

        for result in validation_results:
            if hasattr(result, 'validator_name'):
                metric = {
                    "validator": result.validator_name,
                    "score": result.score,
                    "success": result.success,
                    "issues_count": len(result.issues),
                    "warnings_count": len(result.warnings),
                    "fixes_applied": len(result.fixes_applied) if hasattr(result, 'fixes_applied') else 0
                }
                key_metrics.append(metric)

        return key_metrics

    def _analyze_validation_patterns(self, session_data: Dict[str, Any]) -> None:
        """Analyze validation patterns for learning"""
        try:
            validator_name = session_data.get("session_id", "unknown")

            # Track score trends
            self._track_score_trends(session_data)

            # Identify recurring issues
            self._identify_recurring_issues(session_data)

            # Learn improvement patterns
            self._learn_improvement_patterns(session_data)

        except Exception as e:
            self.logger.warning(f"Pattern analysis failed: {e}")

    def _track_score_trends(self, session_data: Dict[str, Any]) -> None:
        """Track score trends over time"""
        trends = self.pattern_learning.get("score_trends", {})

        # Overall score trend
        overall_scores = trends.get("overall", [])
        overall_scores.append({
            "timestamp": session_data["timestamp"],
            "score": session_data["overall_score"],
            "grade": session_data["overall_grade"]
        })

        # Keep last 20 scores
        trends["overall"] = overall_scores[-20:]

        # Principles score trend
        principles_scores = trends.get("principles", [])
        principles_scores.append({
            "timestamp": session_data["timestamp"],
            "score": session_data["principles_score"],
            "grade": session_data["principles_grade"]
        })

        trends["principles"] = principles_scores[-20:]

        self.pattern_learning["score_trends"] = trends

    def _identify_recurring_issues(self, session_data: Dict[str, Any]) -> None:
        """Identify recurring validation issues"""
        recurring = self.pattern_learning.get("recurring_issues", {})

        # Track issue types
        for result in session_data.get("validation_results", []):
            validator = result.get("validator", "unknown")
            if result.get("issues_count", 0) > 0:
                if validator not in recurring:
                    recurring[validator] = {"count": 0, "last_seen": None}

                recurring[validator]["count"] += 1
                recurring[validator]["last_seen"] = session_data["timestamp"]

        self.pattern_learning["recurring_issues"] = recurring

    def _learn_improvement_patterns(self, session_data: Dict[str, Any]) -> None:
        """Learn from improvement patterns"""
        improvements = self.pattern_learning.get("improvements", [])

        # Compare with previous session if available
        if len(self.validation_history) > 1:
            previous = self.validation_history[-2]
            current = session_data

            # Check for score improvements
            if current["overall_score"] > previous["overall_score"]:
                improvement = {
                    "timestamp": current["timestamp"],
                    "type": "overall_improvement",
                    "from_score": previous["overall_score"],
                    "to_score": current["overall_score"],
                    "improvement": current["overall_score"] - previous["overall_score"]
                }
                improvements.append(improvement)

            # Check for issue reductions
            if current["total_issues"] < previous["total_issues"]:
                improvement = {
                    "timestamp": current["timestamp"],
                    "type": "issue_reduction",
                    "from_issues": previous["total_issues"],
                    "to_issues": current["total_issues"],
                    "reduction": previous["total_issues"] - current["total_issues"]
                }
                improvements.append(improvement)

        # Keep last 20 improvements
        self.pattern_learning["improvements"] = improvements[-20:]

    def _update_context_intelligence(self, session_data: Dict[str, Any]) -> None:
        """Update context intelligence based on validation session"""
        try:
            # Project quality profile
            quality_profile = self.context_intelligence.get("quality_profile", {})
            quality_profile.update({
                "last_validation": session_data["timestamp"],
                "current_overall_score": session_data["overall_score"],
                "current_overall_grade": session_data["overall_grade"],
                "current_principles_score": session_data["principles_score"],
                "trending_up": self._is_trending_up(),
                "top_issues": self._get_top_issues(),
                "validation_count": len(self.validation_history)
            })

            self.context_intelligence["quality_profile"] = quality_profile

            # Development patterns
            dev_patterns = self.context_intelligence.get("development_patterns", {})
            dev_patterns.update({
                "validation_frequency": self._calculate_validation_frequency(),
                "improvement_velocity": self._calculate_improvement_velocity(),
                "issue_resolution_patterns": self._analyze_issue_resolution()
            })

            self.context_intelligence["development_patterns"] = dev_patterns

        except Exception as e:
            self.logger.warning(f"Context intelligence update failed: {e}")

    def _is_trending_up(self) -> bool:
        """Check if quality scores are trending upward"""
        if len(self.validation_history) < 3:
            return False

        recent_scores = [session["overall_score"] for session in self.validation_history[-3:]]
        return recent_scores[-1] > recent_scores[0]

    def _get_top_issues(self) -> List[str]:
        """Get most common issue types"""
        recurring = self.pattern_learning.get("recurring_issues", {})
        sorted_issues = sorted(recurring.items(), key=lambda x: x[1]["count"], reverse=True)
        return [issue[0] for issue in sorted_issues[:5]]

    def _calculate_validation_frequency(self) -> float:
        """Calculate validation frequency (validations per day)"""
        if len(self.validation_history) < 2:
            return 0.0

        first_timestamp = datetime.fromisoformat(self.validation_history[0]["timestamp"])
        last_timestamp = datetime.fromisoformat(self.validation_history[-1]["timestamp"])

        days_span = (last_timestamp - first_timestamp).days
        if days_span == 0:
            days_span = 1

        return len(self.validation_history) / days_span

    def _calculate_improvement_velocity(self) -> float:
        """Calculate rate of quality improvement"""
        improvements = self.pattern_learning.get("improvements", [])
        if not improvements:
            return 0.0

        score_improvements = [imp for imp in improvements if imp["type"] == "overall_improvement"]
        if not score_improvements:
            return 0.0

        total_improvement = sum(imp["improvement"] for imp in score_improvements)
        return total_improvement / len(score_improvements)

    def _analyze_issue_resolution(self) -> Dict[str, Any]:
        """Analyze issue resolution patterns"""
        recent_sessions = self.validation_history[-10:] if len(self.validation_history) >= 10 else self.validation_history

        if not recent_sessions:
            return {}

        total_issues = sum(session["total_issues"] for session in recent_sessions)
        total_warnings = sum(session["total_warnings"] for session in recent_sessions)

        return {
            "avg_issues_per_session": total_issues / len(recent_sessions),
            "avg_warnings_per_session": total_warnings / len(recent_sessions),
            "resolution_trend": "improving" if self._is_trending_up() else "stable"
        }

    def get_intelligent_recommendations(self) -> List[str]:
        """Generate intelligent recommendations based on learned patterns"""
        recommendations = []

        try:
            # Based on recurring issues
            recurring = self.pattern_learning.get("recurring_issues", {})
            for validator, data in recurring.items():
                if data["count"] >= 3:  # Recurring issue
                    recommendations.append(f"🔄 {validator} issues are recurring - consider systematic refactoring")

            # Based on trends
            if not self._is_trending_up() and len(self.validation_history) >= 5:
                recommendations.append("📈 Quality scores are stagnating - consider fresh validation approaches")

            # Based on validation frequency
            freq = self._calculate_validation_frequency()
            if freq < 0.2:  # Less than once per 5 days
                recommendations.append("⏰ Consider more frequent validation for better code health")

            # Based on improvement velocity
            velocity = self._calculate_improvement_velocity()
            if velocity > 5:  # Good improvement rate
                recommendations.append("🚀 Excellent improvement velocity - maintain current practices")

        except Exception as e:
            self.logger.warning(f"Failed to generate intelligent recommendations: {e}")

        return recommendations

    # === NEW SESSION CONTINUITY & COMMAND MEMORY METHODS ===

    def _load_command_history(self) -> Dict[str, Any]:
        """Load command execution history"""
        try:
            if self.command_history_file.exists():
                with open(self.command_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load command history: {e}")

        return {
            "sessions": {},
            "global_commands": {},
            "last_session": None,
            "tool_installations": {},
            "build_history": [],
            "deployment_history": []
        }

    def _load_session_continuity(self) -> Dict[str, Any]:
        """Load session continuity data"""
        try:
            if self.session_continuity_file.exists():
                with open(self.session_continuity_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load session continuity: {e}")

        return {
            "current_session_id": None,
            "session_start_time": None,
            "loaded_context": {},
            "session_memory": {},
            "continuity_enabled": True
        }

    def _auto_load_session_context(self) -> None:
        """Automatically load context for new sessions"""
        try:
            # Generate new session ID
            current_time = datetime.now()
            session_id = f"session_{current_time.strftime('%Y%m%d_%H%M%S')}"

            # Update session continuity
            self.session_continuity.update({
                "current_session_id": session_id,
                "session_start_time": current_time.isoformat(),
                "loaded_context": self.get_context_summary(),
                "session_memory": {}
            })

            # Save updated continuity
            self._save_session_continuity()

            self.logger.info(f"Session context auto-loaded: {session_id}")

        except Exception as e:
            self.logger.warning(f"Auto-load session context failed: {e}")

    def capture_command_execution(self, command: str, context: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Capture command execution for memory and continuity"""
        try:
            session_id = self.session_continuity.get("current_session_id", "unknown_session")
            timestamp = datetime.now().isoformat()

            # Add to session commands
            if session_id not in self.command_history["sessions"]:
                self.command_history["sessions"][session_id] = []

            command_record = {
                "command": command,
                "timestamp": timestamp,
                "context": context,
                "result": result,
                "success": result.get("success", False)
            }

            self.command_history["sessions"][session_id].append(command_record)

            # Update global command tracking
            self._update_global_command_tracking(command, command_record)

            # Update session memory
            self._update_session_memory(command, command_record)

            # Save command history
            self._save_command_history()

            self.logger.info(f"Command captured: {command} (session: {session_id})")

        except Exception as e:
            self.logger.warning(f"Command capture failed: {e}")

    def _update_global_command_tracking(self, command: str, record: Dict[str, Any]) -> None:
        """Update global command tracking"""
        global_commands = self.command_history["global_commands"]

        if command not in global_commands:
            global_commands[command] = {
                "count": 0,
                "last_executed": None,
                "last_result": None,
                "success_rate": 0.0,
                "executions": []
            }

        cmd_data = global_commands[command]
        cmd_data["count"] += 1
        cmd_data["last_executed"] = record["timestamp"]
        cmd_data["last_result"] = record["result"]
        cmd_data["executions"].append({
            "timestamp": record["timestamp"],
            "success": record["success"]
        })

        # Keep last 10 executions
        cmd_data["executions"] = cmd_data["executions"][-10:]

        # Calculate success rate
        successes = sum(1 for exe in cmd_data["executions"] if exe["success"])
        cmd_data["success_rate"] = successes / len(cmd_data["executions"]) if cmd_data["executions"] else 0.0

    def _update_session_memory(self, command: str, record: Dict[str, Any]) -> None:
        """Update session-specific memory"""
        session_memory = self.session_continuity["session_memory"]

        # Track tools installations in this session
        if "install" in command.lower() and "tool" in command.lower():
            session_memory["tools_installed"] = session_memory.get("tools_installed", []) + [{
                "timestamp": record["timestamp"],
                "success": record["success"],
                "command": command
            }]

        # Track validations in this session
        if "validate" in command.lower() or "check" in command.lower():
            session_memory["validations_run"] = session_memory.get("validations_run", []) + [{
                "timestamp": record["timestamp"],
                "command": command,
                "result": record.get("result", {})
            }]

        # Track builds in this session
        if "build" in command.lower() or "deploy" in command.lower():
            session_memory["builds_run"] = session_memory.get("builds_run", []) + [{
                "timestamp": record["timestamp"],
                "command": command,
                "success": record["success"]
            }]

    def query_command_memory(self, command_pattern: str, timeframe_hours: int = 24) -> Dict[str, Any]:
        """Query command memory to check if similar commands were executed recently"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
            recent_commands = []

            # Check global command history
            for cmd, data in self.command_history["global_commands"].items():
                if command_pattern.lower() in cmd.lower():
                    last_exec = data.get("last_executed")
                    if last_exec:
                        last_time = datetime.fromisoformat(last_exec)
                        if last_time > cutoff_time:
                            recent_commands.append({
                                "command": cmd,
                                "last_executed": last_exec,
                                "success_rate": data.get("success_rate", 0.0),
                                "count": data.get("count", 0),
                                "last_result": data.get("last_result", {})
                            })

            # Check current session memory
            session_memory = self.session_continuity.get("session_memory", {})

            return {
                "recent_commands": recent_commands,
                "session_context": session_memory,
                "has_recent_execution": len(recent_commands) > 0,
                "recommendations": self._generate_memory_recommendations(command_pattern, recent_commands)
            }

        except Exception as e:
            self.logger.warning(f"Command memory query failed: {e}")
            return {
                "recent_commands": [],
                "session_context": {},
                "has_recent_execution": False,
                "recommendations": []
            }

    def _generate_memory_recommendations(self, command_pattern: str, recent_commands: List[Dict]) -> List[str]:
        """Generate intelligent recommendations based on command memory"""
        recommendations = []

        if not recent_commands:
            return recommendations

        # Check for recent tool installations
        if "install" in command_pattern.lower() and "tool" in command_pattern.lower():
            for cmd in recent_commands:
                if cmd["success_rate"] > 0.8:  # Recent successful installation
                    recommendations.append(f"🔍 Tools were recently installed successfully. Consider checking current status first.")
                    break

        # Check for recent validations
        if "validate" in command_pattern.lower() or "check" in command_pattern.lower():
            recent_validation = max(recent_commands, key=lambda x: x["last_executed"], default=None)
            if recent_validation:
                recommendations.append(f"📊 Recent validation completed. Review results before re-running.")

        # Check for repeated failures
        failed_commands = [cmd for cmd in recent_commands if cmd["success_rate"] < 0.5]
        if failed_commands:
            recommendations.append(f"⚠️ Previous attempts had low success rate. Review configuration before retrying.")

        return recommendations

    def get_session_intelligence(self) -> Dict[str, Any]:
        """Get intelligent session context for Claude Code"""
        try:
            session_id = self.session_continuity.get("current_session_id")
            session_memory = self.session_continuity.get("session_memory", {})

            # Get recent session commands
            recent_commands = []
            if session_id and session_id in self.command_history["sessions"]:
                recent_commands = self.command_history["sessions"][session_id][-5:]  # Last 5 commands

            return {
                "session_id": session_id,
                "session_start_time": self.session_continuity.get("session_start_time"),
                "loaded_context": self.session_continuity.get("loaded_context", {}),
                "session_memory": session_memory,
                "recent_commands": recent_commands,
                "context_summary": self.get_context_summary(),
                "intelligent_recommendations": self.get_intelligent_recommendations()
            }

        except Exception as e:
            self.logger.warning(f"Session intelligence failed: {e}")
            return {}

    def _save_command_history(self) -> None:
        """Save command history to file"""
        try:
            self.command_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.command_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.command_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to save command history: {e}")

    def _save_session_continuity(self) -> None:
        """Save session continuity to file"""
        try:
            self.session_continuity_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_continuity_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_continuity, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.warning(f"Failed to save session continuity: {e}")

    def get_context_summary(self) -> Dict[str, Any]:
        """Get intelligent context summary for Claude Code"""
        try:
            quality_profile = self.context_intelligence.get("quality_profile", {})
            dev_patterns = self.context_intelligence.get("development_patterns", {})

            return {
                "project_quality_status": {
                    "current_grade": quality_profile.get("current_overall_grade", "N/A"),
                    "current_score": quality_profile.get("current_overall_score", 0),
                    "trending": "up" if quality_profile.get("trending_up", False) else "stable",
                    "validation_count": quality_profile.get("validation_count", 0)
                },
                "development_intelligence": {
                    "validation_frequency": dev_patterns.get("validation_frequency", 0),
                    "improvement_velocity": dev_patterns.get("improvement_velocity", 0),
                    "top_issues": quality_profile.get("top_issues", [])
                },
                "intelligent_recommendations": self.get_intelligent_recommendations(),
                "last_validation": quality_profile.get("last_validation"),
                "memory_insights": {
                    "total_sessions": len(self.validation_history),
                    "patterns_learned": len(self.pattern_learning.get("recurring_issues", {})),
                    "improvements_tracked": len(self.pattern_learning.get("improvements", []))
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to generate context summary: {e}")
            return {"error": str(e)}

    def _update_main_memory(self, session_data: Dict[str, Any]) -> None:
        """Update main memory manager with validation insights"""
        try:
            if not self.memory_manager:
                return

            # Remember significant quality milestones
            if session_data["overall_grade"] in ["A+", "A"]:
                self.memory_manager.remember_feature(
                    f"quality_milestone_{session_data['overall_grade'].lower()}",
                    f"Achieved {session_data['overall_grade']} code quality grade with {session_data['overall_score']}/100 score"
                )

            # Remember recurring issues
            top_issues = self._get_top_issues()
            if top_issues:
                self.memory_manager.remember_feature(
                    "quality_focus_areas",
                    f"Top quality focus areas: {', '.join(top_issues[:3])}"
                )

        except Exception as e:
            self.logger.warning(f"Failed to update main memory: {e}")

    def _load_validation_history(self) -> List[Dict]:
        """Load validation history from file"""
        try:
            if self.validation_history_file.exists():
                with open(self.validation_history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load validation history: {e}")
        return []

    def _load_pattern_learning(self) -> Dict:
        """Load pattern learning data from file"""
        try:
            if self.pattern_learning_file.exists():
                with open(self.pattern_learning_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load pattern learning: {e}")
        return {
            "score_trends": {},
            "recurring_issues": {},
            "improvements": []
        }

    def _load_context_intelligence(self) -> Dict:
        """Load context intelligence from file"""
        try:
            if self.context_intelligence_file.exists():
                with open(self.context_intelligence_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Failed to load context intelligence: {e}")
        return {
            "quality_profile": {},
            "development_patterns": {}
        }

    def _save_all_memory(self) -> None:
        """Save all memory structures to files"""
        try:
            # Ensure .claude directory exists
            self.validation_history_file.parent.mkdir(exist_ok=True)

            # Save validation history
            with open(self.validation_history_file, 'w') as f:
                json.dump(self.validation_history, f, indent=2)

            # Save pattern learning
            with open(self.pattern_learning_file, 'w') as f:
                json.dump(self.pattern_learning, f, indent=2)

            # Save context intelligence
            with open(self.context_intelligence_file, 'w') as f:
                json.dump(self.context_intelligence, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save memory structures: {e}")