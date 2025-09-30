#!/usr/bin/env python3
"""
Context Management Module
Extracted from orchestrator.py to follow Single Responsibility Principle

Handles:
- Project context analysis
- File status monitoring
- Project health assessment
- Context display and reporting
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from ccom.utils import FileUtils, ErrorHandler, Display, SubprocessRunner


class ContextManager:
    """
    Manages CCOM project context with proper separation of concerns

    Replaces context-related methods from CCOMOrchestrator (400+ lines)
    """

    def __init__(self, project_root: Path, memory_manager):
        self.project_root = project_root
        self.memory_manager = memory_manager

        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.file_utils = FileUtils()
        self.subprocess_runner = SubprocessRunner()

    def analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and return comprehensive summary"""
        return self.error_handler.safe_execute(
            self._do_analyze_project,
            default_return=self._default_project_info(),
            error_message="Failed to analyze project structure"
        )

    def _do_analyze_project(self) -> Dict[str, Any]:
        """Actual project analysis implementation"""
        project_name = self.project_root.name

        # Detect project type and architecture
        project_type = "Unknown"
        architecture = "Unknown"
        tech_stack = []
        lines = 0
        files = 0

        # Check for common project indicators
        if (self.project_root / "package.json").exists():
            tech_stack.append("Node.js")
            project_info = self._analyze_nodejs_project()
            project_type = project_info["type"]
            architecture = project_info["architecture"]
            tech_stack.extend(project_info["additional_tech"])

        # Check for Python
        if (self.project_root / "requirements.txt").exists() or (self.project_root / "pyproject.toml").exists():
            tech_stack.append("Python")
            project_type = "Python App"

        # Check for static site
        if (self.project_root / "index.html").exists() and not (self.project_root / "package.json").exists():
            project_type = "Static Site"
            architecture = "Static HTML"
            tech_stack = ["HTML", "CSS", "JavaScript"]

        # Count files and lines
        file_stats = self._count_project_files()
        lines = file_stats["lines"]
        files = file_stats["files"]

        return {
            "name": project_name,
            "type": project_type,
            "architecture": architecture,
            "tech_stack": tech_stack or ["Unknown"],
            "lines": lines,
            "files": files,
            "size_category": self._categorize_project_size(lines, files)
        }

    def _analyze_nodejs_project(self) -> Dict[str, Any]:
        """Analyze Node.js specific project details"""
        try:
            package_json = self.file_utils.safe_read_json(self.project_root / "package.json", {})
            deps = list(package_json.get("dependencies", {}).keys())
            dev_deps = list(package_json.get("devDependencies", {}).keys())
            all_deps = deps + dev_deps

            project_type = "Node.js App"
            architecture = "Unknown"
            additional_tech = []

            if "react" in deps:
                additional_tech.append("React")
                project_type = "React App"
                architecture = "SPA"
            elif any("angular" in dep or "@angular" in dep for dep in deps):
                additional_tech.append("Angular")
                project_type = "Angular App"
                architecture = "SPA"
            elif "vue" in deps:
                additional_tech.append("Vue")
                project_type = "Vue App"
                architecture = "SPA"
            elif "next" in deps:
                additional_tech.append("Next.js")
                project_type = "Next.js App"
                architecture = "SSR/SSG"
            elif "express" in deps:
                additional_tech.append("Express")
                project_type = "Express Server"
                architecture = "REST API"

            # Check for PWA indicators
            if (self.project_root / "manifest.json").exists() or (self.project_root / "sw.js").exists():
                architecture = "PWA"
                additional_tech.append("PWA")

            # Check for TypeScript
            if "typescript" in all_deps or (self.project_root / "tsconfig.json").exists():
                additional_tech.append("TypeScript")

            return {
                "type": project_type,
                "architecture": architecture,
                "additional_tech": additional_tech
            }

        except Exception as e:
            self.logger.warning(f"Failed to analyze Node.js project: {e}")
            return {"type": "Node.js App", "architecture": "Unknown", "additional_tech": []}

    def _count_project_files(self) -> Dict[str, int]:
        """Count project files and lines"""
        lines = 0
        files = 0

        exclude_patterns = [".git", "node_modules", "__pycache__", ".claude", "dist", "build", ".venv"]

        try:
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not any(pattern in str(file_path) for pattern in exclude_patterns):
                    files += 1
                    if file_path.suffix in [".js", ".py", ".html", ".css", ".ts", ".jsx", ".tsx", ".md"]:
                        try:
                            with open(file_path, encoding="utf-8", errors="ignore") as f:
                                lines += len(f.readlines())
                        except:
                            pass

        except Exception as e:
            self.logger.warning(f"Failed to count project files: {e}")

        return {"lines": lines, "files": files}

    def _categorize_project_size(self, lines: int, files: int) -> str:
        """Categorize project size"""
        if lines > 10000 or files > 100:
            return "Large"
        elif lines > 2000 or files > 20:
            return "Medium"
        else:
            return "Small"

    def _default_project_info(self) -> Dict[str, Any]:
        """Default project info when analysis fails"""
        return {
            "name": self.project_root.name,
            "type": "Unknown",
            "architecture": "Unknown",
            "tech_stack": ["Unknown"],
            "lines": 0,
            "files": 0,
            "size_category": "Unknown"
        }

    def get_current_health_status(self) -> Dict[str, str]:
        """Get current health status from memory and analysis"""
        quality = "Unknown"
        security = "Unknown"
        status = "Unknown"

        try:
            # Extract latest quality and security info from memory
            memory = self.memory_manager.memory
            features = memory.get("features", {})

            # Look for recent quality audits in features
            for feature_name, feature in features.items():
                desc = feature.get("description", "").lower()
                if "quality" in desc:
                    if "a+" in desc or "99/100" in desc or "98/100" in desc:
                        quality = "A+ (99/100)"
                    elif "grade" in desc:
                        quality = "Enterprise Grade"
                if "security" in desc:
                    if "bank-level" in desc or "bank level" in desc:
                        security = "Bank-level"
                    elif "zero vulnerabilities" in desc:
                        security = "Secure"

            # Check deployment status
            deployments = memory.get("deployments", [])
            if deployments:
                latest_deploy = deployments[-1]
                if latest_deploy.get("status") == "successful":
                    status = "Production Ready"

        except Exception as e:
            self.logger.warning(f"Failed to get health status: {e}")

        return {
            "quality": quality or "Unknown",
            "security": security or "Unknown",
            "status": status or "Ready for Testing",
        }

    def get_recent_features(self, limit: int = 3) -> List[Dict[str, str]]:
        """Get recent features for context display"""
        try:
            recent = self.memory_manager.get_recent_features(limit)
            formatted_features = []

            for feature in recent:
                name = feature.get("name", "Unknown")
                desc = feature.get("description", "")
                summary = desc[:80] + "..." if len(desc) > 80 else desc or "No description"

                formatted_features.append({
                    "name": name.replace("_", " ").title(),
                    "summary": summary
                })

            return formatted_features

        except Exception as e:
            self.logger.warning(f"Failed to get recent features: {e}")
            return []

    def detect_current_focus(self) -> Optional[str]:
        """Detect what the user is currently working on"""
        try:
            features = self.memory_manager.memory.get("features", {})
            if not features:
                return None

            # Get most recent feature
            latest_feature = list(features.items())[-1]
            desc = latest_feature[1].get("description", "").lower()

            if "password reset" in desc or "email" in desc:
                return "Password reset and email integration"
            elif "auth" in desc or "authentication" in desc:
                return "Authentication system enhancement"
            elif "deployment" in desc or "production" in desc:
                return "Production deployment"
            elif "quality" in desc or "audit" in desc:
                return "Code quality improvement"
            else:
                return latest_feature[0].replace("_", " ").title()

        except Exception as e:
            self.logger.warning(f"Failed to detect current focus: {e}")
            return None

    def generate_suggestions(self) -> List[str]:
        """Generate smart suggestions based on project state"""
        suggestions = []

        try:
            memory = self.memory_manager.memory
            features = memory.get("features", {})

            # Analyze recent work to suggest next steps
            if features:
                latest_desc = list(features.values())[-1].get("description", "").lower()

                if "auth" in latest_desc and "password reset" not in latest_desc:
                    suggestions.append("Add password reset functionality")
                if "quality" in latest_desc and "deploy" not in latest_desc:
                    suggestions.append("Run deployment workflow")
                if "security" in latest_desc:
                    suggestions.append("Review and fix any security findings")

            # Check if GitHub Actions is set up
            if not (self.project_root / ".github" / "workflows").exists():
                suggestions.append("Set up GitHub Actions with 'ccom workflow setup'")

            # Always suggest testing workflows
            suggestions.append("Run 'ccom complete stack' for full validation")

        except Exception as e:
            self.logger.warning(f"Failed to generate suggestions: {e}")

        return suggestions[:3]  # Limit to 3 suggestions

    def get_file_status(self) -> Dict[str, Any]:
        """Get current file status and recent changes"""
        key_files = []
        recent_changes = None

        try:
            # Identify key files
            common_files = [
                "index.html", "app.js", "main.js", "script.js", "auth.js",
                "package.json", "README.md", "pyproject.toml", "requirements.txt"
            ]

            for filename in common_files:
                if (self.project_root / filename).exists():
                    key_files.append(filename)

            # Get most recently modified file
            files = list(self.project_root.rglob("*"))
            if files:
                exclude_patterns = [".git", "node_modules", ".claude", "__pycache__"]
                valid_files = [
                    f for f in files
                    if f.is_file() and not any(pattern in str(f) for pattern in exclude_patterns)
                ]

                if valid_files:
                    recent_file = max(valid_files, key=lambda x: x.stat().st_mtime)
                    recent_changes = f"{recent_file.name} (recently modified)"

        except Exception as e:
            self.logger.warning(f"Failed to get file status: {e}")

        return {
            "key_files": key_files[:5],  # Limit to 5 key files
            "recent_changes": recent_changes,
        }

    def get_git_info(self) -> Dict[str, Any]:
        """Get Git repository information"""
        return self.subprocess_runner.get_git_info(self.project_root)

    def show_project_context(self) -> bool:
        """Show comprehensive project context with session continuity"""
        try:
            Display.header("🎯 SESSION CONTINUITY LOADED")

            # Memory Context
            memory_stats = self.memory_manager.get_memory_stats()
            Display.section("🧠 MEMORY CONTEXT (Previous Sessions)")

            Display.key_value_table({
                "Total Features": memory_stats.get("total_features", 0),
                "Project Created": memory_stats.get("created", "Unknown"),
                "Last Update": memory_stats.get("last_update", "Never")
            })

            features = self.get_recent_features(5)
            if features:
                Display.section("📋 Recent Features")
                for feature in features:
                    print(f"   • {feature['name']}: {feature['summary']}")

            # Project Overview
            project_info = self.analyze_project_structure()
            Display.section("📊 Project Overview")
            Display.key_value_table({
                "Name": project_info['name'],
                "Type": project_info['type'],
                "Architecture": project_info['architecture'],
                "Tech Stack": ', '.join(project_info['tech_stack']),
                "Size": f"{project_info['lines']} lines, {project_info['files']} files ({project_info['size_category']})"
            })

            # Current Health Status
            health = self.get_current_health_status()
            Display.section("📈 Current Status")
            Display.key_value_table({
                "Quality": health['quality'],
                "Security": health['security'],
                "Status": health['status']
            })

            # Current Focus
            current_focus = self.detect_current_focus()
            if current_focus:
                Display.section("🎯 Current Focus")
                print(f"  {current_focus}")

            # Suggested Actions
            suggestions = self.generate_suggestions()
            if suggestions:
                Display.section("💡 Suggested Next Actions")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")

            # File Status
            file_status = self.get_file_status()
            Display.section("📂 File Status")
            if file_status["key_files"]:
                print(f"  Key Files: {', '.join(file_status['key_files'])}")
            if file_status["recent_changes"]:
                print(f"  Recent Changes: {file_status['recent_changes']}")

            # Git Info
            git_info = self.get_git_info()
            if git_info['is_git_repo']:
                Display.section("🔀 Git Status")
                Display.key_value_table({
                    "Branch": git_info.get('branch', 'Unknown'),
                    "Commit": git_info.get('commit', 'Unknown'),
                    "Status": git_info.get('status', 'Unknown')
                })

            Display.success("Context loaded! Claude Code now understands your project.")
            return True

        except Exception as e:
            self.logger.error(f"Failed to show project context: {e}")
            Display.error("Failed to load project context")
            return False

    def export_context(self, export_path: Path) -> bool:
        """Export comprehensive project context"""
        try:
            context_data = {
                "exported": datetime.now().isoformat(),
                "project_info": self.analyze_project_structure(),
                "health_status": self.get_current_health_status(),
                "recent_features": self.get_recent_features(10),
                "file_status": self.get_file_status(),
                "git_info": self.get_git_info(),
                "memory_stats": self.memory_manager.get_memory_stats(),
                "suggestions": self.generate_suggestions()
            }

            return self.file_utils.safe_write_json(export_path, context_data, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to export context: {e}")
            return False