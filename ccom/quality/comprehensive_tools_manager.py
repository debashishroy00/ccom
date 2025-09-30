#!/usr/bin/env python3
"""
Comprehensive Tools Manager - Essential Tool Installation and Management
RESTORED functionality from tools_manager.py with proper structure

Handles:
- Automatic tool installation for JavaScript, TypeScript, Python
- Tool configuration and management
- Security tools, testing tools, complexity analysis tools
- Cross-platform compatibility
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from ..utils import SubprocessRunner, ErrorHandler, Display


class ComprehensiveToolsManager:
    """Advanced tool management with installation capabilities"""

    REQUIRED_TOOLS = {
        "javascript": [
            "eslint", "@eslint/js", "globals", "eslint-plugin-import",
            "eslint-plugin-unused-imports", "prettier", "jshint"
        ],
        "typescript": [
            "typescript", "@typescript-eslint/parser", "@typescript-eslint/eslint-plugin"
        ],
        "python": ["black", "pylint", "flake8", "mypy", "bandit"],
        "testing": ["jest", "pytest", "playwright"],
        "git": ["husky", "lint-staged"],
        "security": ["bandit", "safety"],
        "complexity": [
            "complexity-report",  # JavaScript complexity
            "radon",             # Python complexity
            "jscpd",             # Duplicate detection
            "madge"              # Dependency analysis
        ]
    }

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.tools_state_file = self.claude_dir / "tools.json"
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.subprocess_runner = SubprocessRunner()

        # Ensure .claude directory exists
        self.claude_dir.mkdir(exist_ok=True)

    def check_tool_availability(self) -> Dict[str, Dict]:
        """Check availability and status of all development tools"""
        Display.progress("Checking tool availability...")

        tools_status = {}

        # Check Node.js tools
        for category, tools in self.REQUIRED_TOOLS.items():
            tools_status[category] = {}

            if category in ["javascript", "typescript", "testing", "git", "complexity"]:
                # Node.js tools
                for tool in tools:
                    tools_status[category][tool] = self._check_npm_tool(tool)

            elif category == "python":
                # Python tools
                for tool in tools:
                    tools_status[category][tool] = self._check_python_tool(tool)

            elif category == "security":
                # Security tools (mixed)
                for tool in tools:
                    if tool in ["bandit"]:
                        tools_status[category][tool] = self._check_python_tool(tool)
                    else:
                        tools_status[category][tool] = self._check_python_tool(tool)

        # Save status
        self._save_tools_status(tools_status)

        return tools_status

    def _check_npm_tool(self, tool: str) -> Dict:
        """Check if an npm tool is installed"""
        try:
            # Check global installation
            result = self.subprocess_runner.run_command(["npm", "list", "-g", tool], timeout=10)
            if result.returncode == 0:
                return {"installed": True, "type": "npm_global", "location": "global"}

            # Check local installation
            result = self.subprocess_runner.run_command(["npm", "list", tool], timeout=10)
            if result.returncode == 0:
                return {"installed": True, "type": "npm_local", "location": "local"}

            # Check if available via npx
            result = self.subprocess_runner.run_command(["npx", "--help"], timeout=5)
            if result.returncode == 0:
                return {"installed": False, "type": "npm", "available_via_npx": True}

            return {"installed": False, "type": "npm", "available_via_npx": False}

        except Exception as e:
            self.logger.warning(f"Could not check npm tool {tool}: {e}")
            return {"installed": False, "type": "npm", "error": str(e)}

    def _check_python_tool(self, tool: str) -> Dict:
        """Check if a Python tool is installed"""
        try:
            result = self.subprocess_runner.run_command([tool, "--version"], timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                return {"installed": True, "type": "python", "version": version}

            # Try with python -m
            result = self.subprocess_runner.run_command(["python", "-m", tool, "--version"], timeout=10)
            if result.returncode == 0:
                version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
                return {"installed": True, "type": "python_module", "version": version}

            return {"installed": False, "type": "python"}

        except Exception as e:
            self.logger.warning(f"Could not check Python tool {tool}: {e}")
            return {"installed": False, "type": "python", "error": str(e)}

    def install_missing_tools(self, force: bool = False, categories: List[str] = None) -> bool:
        """Install missing development tools"""
        Display.section("🔧 Installing Development Tools")

        if not categories:
            categories = list(self.REQUIRED_TOOLS.keys())

        success = True
        installed_count = 0

        # Check what's already available
        current_status = self.check_tool_availability()

        for category in categories:
            if category not in self.REQUIRED_TOOLS:
                Display.warning(f"Unknown tool category: {category}")
                continue

            Display.progress(f"Installing {category} tools...")

            tools = self.REQUIRED_TOOLS[category]
            category_success = self._install_category_tools(category, tools, current_status.get(category, {}), force)

            if category_success:
                installed_count += len(tools)
                Display.success(f"✅ {category} tools installed")
            else:
                Display.error(f"❌ Failed to install some {category} tools")
                success = False

        if success:
            Display.success(f"🎉 Successfully installed {installed_count} tools")
        else:
            Display.warning("⚠️ Some tools failed to install")

        return success

    def _install_category_tools(self, category: str, tools: List[str], current_status: Dict, force: bool) -> bool:
        """Install tools for a specific category"""
        success = True

        if category in ["javascript", "typescript", "testing", "git", "complexity"]:
            # Node.js tools
            success = self._install_npm_tools(tools, current_status, force)

        elif category == "python":
            # Python tools
            success = self._install_python_tools(tools, current_status, force)

        elif category == "security":
            # Mixed security tools
            success = self._install_security_tools(tools, current_status, force)

        return success

    def _install_npm_tools(self, tools: List[str], current_status: Dict, force: bool) -> bool:
        """Install npm tools"""
        # Check if package.json exists
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            Display.info("Creating package.json for tool installation...")
            self._create_basic_package_json()

        # Install as dev dependencies
        tools_to_install = []
        for tool in tools:
            if force or not current_status.get(tool, {}).get("installed", False):
                tools_to_install.append(tool)

        if not tools_to_install:
            Display.info("All npm tools already installed")
            return True

        Display.progress(f"Installing npm tools: {', '.join(tools_to_install)}")

        result = self.subprocess_runner.run_command([
            "npm", "install", "--save-dev"
        ] + tools_to_install, timeout=300)

        if result.returncode == 0:
            Display.success(f"✅ Installed npm tools: {', '.join(tools_to_install)}")
            return True
        else:
            Display.error(f"❌ Failed to install npm tools: {result.stderr}")
            return False

    def _install_python_tools(self, tools: List[str], current_status: Dict, force: bool) -> bool:
        """Install Python tools"""
        tools_to_install = []
        for tool in tools:
            if force or not current_status.get(tool, {}).get("installed", False):
                tools_to_install.append(tool)

        if not tools_to_install:
            Display.info("All Python tools already installed")
            return True

        Display.progress(f"Installing Python tools: {', '.join(tools_to_install)}")

        result = self.subprocess_runner.run_command([
            "pip", "install"
        ] + tools_to_install, timeout=300)

        if result.returncode == 0:
            Display.success(f"✅ Installed Python tools: {', '.join(tools_to_install)}")
            return True
        else:
            Display.error(f"❌ Failed to install Python tools: {result.stderr}")
            return False

    def _install_security_tools(self, tools: List[str], current_status: Dict, force: bool) -> bool:
        """Install security tools"""
        success = True

        for tool in tools:
            if not force and current_status.get(tool, {}).get("installed", False):
                continue

            Display.progress(f"Installing security tool: {tool}")

            if tool == "bandit":
                result = self.subprocess_runner.run_command(["pip", "install", tool], timeout=120)
            else:
                result = self.subprocess_runner.run_command(["pip", "install", tool], timeout=120)

            if result.returncode == 0:
                Display.success(f"✅ Installed {tool}")
            else:
                Display.error(f"❌ Failed to install {tool}")
                success = False

        return success

    def _create_basic_package_json(self) -> None:
        """Create a basic package.json if it doesn't exist"""
        package_json = {
            "name": self.project_root.name,
            "version": "1.0.0",
            "description": "Project with CCOM development tools",
            "scripts": {
                "lint": "eslint .",
                "lint:fix": "eslint . --fix",
                "format": "prettier --write .",
                "format:check": "prettier --check ."
            },
            "devDependencies": {},
            "private": True
        }

        package_json_file = self.project_root / "package.json"
        with open(package_json_file, 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)

        Display.info(f"Created package.json with basic development scripts")

    def get_installation_status(self) -> Dict:
        """Get comprehensive installation status report"""
        status = self.check_tool_availability()

        summary = {
            "total_categories": len(status),
            "categories": {},
            "overall_health": "unknown",
            "missing_tools": [],
            "timestamp": datetime.now().isoformat()
        }

        total_tools = 0
        installed_tools = 0

        for category, tools in status.items():
            category_installed = 0
            category_total = len(tools)
            category_missing = []

            for tool, tool_status in tools.items():
                total_tools += 1
                if tool_status.get("installed", False):
                    installed_tools += 1
                    category_installed += 1
                else:
                    category_missing.append(tool)
                    summary["missing_tools"].append(f"{category}.{tool}")

            summary["categories"][category] = {
                "installed": category_installed,
                "total": category_total,
                "percentage": (category_installed / category_total * 100) if category_total > 0 else 0,
                "missing": category_missing
            }

        # Calculate overall health
        overall_percentage = (installed_tools / total_tools * 100) if total_tools > 0 else 0
        if overall_percentage >= 90:
            summary["overall_health"] = "excellent"
        elif overall_percentage >= 70:
            summary["overall_health"] = "good"
        elif overall_percentage >= 50:
            summary["overall_health"] = "fair"
        else:
            summary["overall_health"] = "poor"

        summary["overall_percentage"] = overall_percentage

        return summary

    def _save_tools_status(self, status: Dict) -> None:
        """Save tools status to file"""
        try:
            status_data = {
                "timestamp": datetime.now().isoformat(),
                "tools": status
            }

            with open(self.tools_state_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2)

        except Exception as e:
            self.logger.warning(f"Could not save tools status: {e}")

    def display_comprehensive_status(self) -> None:
        """Display comprehensive tools status report"""
        Display.header("🔧 Comprehensive Development Tools Status")

        status = self.get_installation_status()

        # Overall health
        health_emoji = {
            "excellent": "🟢",
            "good": "🟡",
            "fair": "🟠",
            "poor": "🔴"
        }

        Display.key_value_table({
            "Overall Health": f"{health_emoji.get(status['overall_health'], '⚪')} {status['overall_health'].title()} ({status['overall_percentage']:.0f}%)",
            "Categories": status['total_categories'],
            "Missing Tools": len(status['missing_tools'])
        })

        # Category breakdown
        for category, category_status in status["categories"].items():
            status_icon = "✅" if category_status["percentage"] == 100 else "⚠️" if category_status["percentage"] >= 50 else "❌"
            print(f"{status_icon} {category}: {category_status['installed']}/{category_status['total']} ({category_status['percentage']:.0f}%)")

        # Show missing tools if any
        if status["missing_tools"]:
            Display.section("Missing Tools")
            for missing in status["missing_tools"][:10]:  # Show first 10
                print(f"  ❌ {missing}")

            if len(status["missing_tools"]) > 10:
                print(f"  ... and {len(status['missing_tools']) - 10} more")

    def create_tool_configs(self) -> bool:
        """Create essential tool configuration files"""
        Display.progress("Creating tool configuration files...")

        configs_created = 0

        # ESLint config
        if self._create_eslint_config():
            configs_created += 1

        # Prettier config
        if self._create_prettier_config():
            configs_created += 1

        # Python tool configs
        if self._create_python_configs():
            configs_created += 1

        Display.success(f"✅ Created {configs_created} configuration files")
        return configs_created > 0

    def _create_eslint_config(self) -> bool:
        """Create ESLint configuration"""
        eslint_config = self.project_root / "eslint.config.js"
        if eslint_config.exists():
            return False

        config_content = '''import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      }
    },
    rules: {
      'no-unused-vars': 'warn',
      'no-console': 'warn'
    }
  }
];'''

        try:
            with open(eslint_config, 'w', encoding='utf-8') as f:
                f.write(config_content)
            return True
        except Exception as e:
            self.logger.warning(f"Could not create ESLint config: {e}")
            return False

    def _create_prettier_config(self) -> bool:
        """Create Prettier configuration"""
        prettier_config = self.project_root / ".prettierrc"
        if prettier_config.exists():
            return False

        config = {
            "semi": true,
            "trailingComma": "es5",
            "singleQuote": true,
            "printWidth": 80,
            "tabWidth": 2
        }

        try:
            with open(prettier_config, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            self.logger.warning(f"Could not create Prettier config: {e}")
            return False

    def _create_python_configs(self) -> bool:
        """Create Python tool configurations"""
        configs_created = False

        # Pylint config
        pylintrc = self.project_root / ".pylintrc"
        if not pylintrc.exists():
            try:
                with open(pylintrc, 'w', encoding='utf-8') as f:
                    f.write("""[MESSAGES CONTROL]
disable=C0103,R0903,R0913

[FORMAT]
max-line-length=88
""")
                configs_created = True
            except Exception as e:
                self.logger.warning(f"Could not create .pylintrc: {e}")

        return configs_created