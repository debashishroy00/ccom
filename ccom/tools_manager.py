#!/usr/bin/env python3
"""
CCOM Tools Manager v0.3 - Automatic Tool Installation and Management
Handles installation, configuration, and management of development tools for quality validation
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ToolsManager:
    """Main orchestrator for development tool management"""

    REQUIRED_TOOLS = {
        "javascript": [
            "eslint",
            "@eslint/js",
            "globals",
            "eslint-plugin-import",
            "eslint-plugin-unused-imports",
            "prettier",
            "jshint",
        ],
        "typescript": [
            "typescript",
            "@typescript-eslint/parser",
            "@typescript-eslint/eslint-plugin",
        ],
        "python": ["black", "pylint", "flake8", "mypy"],
        "testing": ["jest", "pytest", "playwright"],
        "git": ["husky", "lint-staged"],
        "security": ["bandit", "safety"],
        "complexity": [
            "complexity-report",  # JavaScript complexity
            "radon",             # Python complexity
            "jscpd",             # Duplicate detection
            "madge",             # Dependency analysis
        ],
    }

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.tools_state_file = self.claude_dir / "tools.json"
        self.npm_installer = NpmToolInstaller(self.project_root)
        self.pip_installer = PipToolInstaller(self.project_root)
        self.config_generator = ToolConfigGenerator(self.project_root)
        self.tools_state = self.load_tools_state()

    def load_tools_state(self) -> Dict:
        """Load current tools state from .claude/tools.json"""
        if self.tools_state_file.exists():
            try:
                with open(self.tools_state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading tools state: {e}")

        return self.create_empty_tools_state()

    def create_empty_tools_state(self) -> Dict:
        """Create empty tools state structure"""
        return {
            "installed_tools": {},
            "tool_versions": {},
            "last_check": "",
            "project_type": self.detect_project_type(),
            "custom_tools": [],
            "configurations": {},
        }

    def save_tools_state(self) -> bool:
        """Save tools state to file"""
        try:
            self.claude_dir.mkdir(exist_ok=True)
            with open(self.tools_state_file, "w") as f:
                json.dump(self.tools_state, f, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Error saving tools state: {e}")
            return False

    def detect_project_type(self) -> str:
        """Detect project type based on files present"""
        if (self.project_root / "package.json").exists():
            # Check for specific frameworks
            try:
                with open(self.project_root / "package.json") as f:
                    pkg_data = json.load(f)
                    deps = {
                        **pkg_data.get("dependencies", {}),
                        **pkg_data.get("devDependencies", {}),
                    }

                    if "typescript" in deps or "@types/node" in deps:
                        return "typescript"
                    elif "react" in deps:
                        return "react"
                    elif "angular" in deps or "@angular/core" in deps:
                        return "angular"
                    elif "vue" in deps:
                        return "vue"
                    else:
                        return "javascript"
            except:
                return "javascript"

        elif any(
            (self.project_root / f).exists()
            for f in ["setup.py", "pyproject.toml", "requirements.txt"]
        ):
            return "python"

        elif (self.project_root / "index.html").exists():
            return "static"

        return "unknown"

    def get_tools_for_project(self) -> List[str]:
        """Get list of tools needed for current project type"""
        project_type = self.tools_state.get("project_type", "unknown")
        tools = []

        # Base tools for all projects
        if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
            tools.extend(self.REQUIRED_TOOLS["javascript"])
            if project_type == "typescript":
                tools.extend(self.REQUIRED_TOOLS["typescript"])

        elif project_type == "python":
            tools.extend(self.REQUIRED_TOOLS["python"])

        # Add testing tools if test files exist
        if self.has_test_files():
            if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
                tools.append("jest")
            elif project_type == "python":
                tools.append("pytest")

        # Add git hooks if .git exists
        if (self.project_root / ".git").exists():
            tools.extend(self.REQUIRED_TOOLS["git"])

        # Add security tools
        if project_type in ["javascript", "typescript", "react", "angular", "vue"]:
            # npm audit is built-in, no additional tools needed
            pass
        elif project_type == "python":
            tools.extend(self.REQUIRED_TOOLS["security"])

        # Add complexity analysis tools
        tools.extend(self.REQUIRED_TOOLS["complexity"])

        return list(set(tools))  # Remove duplicates

    def has_test_files(self) -> bool:
        """Check if project has test files"""
        test_patterns = [
            "**/*test*.js",
            "**/*spec*.js",
            "**/*test*.py",
            "**/test_*.py",
            "**/tests/**/*.py",
            "**/test/**/*.js",
        ]

        for pattern in test_patterns:
            if list(self.project_root.glob(pattern)):
                return True
        return False

    def check_tool_availability(self, force_refresh: bool = False) -> Dict:
        """Check which tools are installed and available"""
        if not force_refresh and self.tools_state.get("last_check"):
            # Check if last check was recent (within 1 hour)
            try:
                last_check = datetime.fromisoformat(self.tools_state["last_check"])
                if (datetime.now() - last_check).seconds < 3600:
                    return self.tools_state.get("installed_tools", {})
            except:
                pass

        print("🔍 Checking tool availability...")
        installed_tools = {}
        required_tools = self.get_tools_for_project()

        for tool in required_tools:
            status = self.check_single_tool(tool)
            installed_tools[tool] = status
            if status["installed"]:
                print(f"✅ {tool}: {status['version']}")
            else:
                print(f"❌ {tool}: Not installed")

        # Update state
        self.tools_state["installed_tools"] = installed_tools
        self.tools_state["last_check"] = datetime.now().isoformat()
        self.save_tools_state()

        return installed_tools

    def check_single_tool(self, tool_name: str) -> Dict:
        """Check if a single tool is installed"""
        try:
            # Determine if it's an npm or pip tool
            if tool_name in [
                "black",
                "pylint",
                "flake8",
                "mypy",
                "bandit",
                "safety",
                "pytest",
                "radon",
            ]:
                return self.pip_installer.check_tool(tool_name)
            else:
                return self.npm_installer.check_tool(tool_name)
        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    def install_missing_tools(self, force: bool = False) -> bool:
        """Install all missing tools for the project"""
        print("🔧 **CCOM TOOLS INSTALLER** – Setting up development environment...")

        # Check current status
        installed_tools = self.check_tool_availability(force_refresh=True)
        required_tools = self.get_tools_for_project()

        missing_tools = [
            tool
            for tool in required_tools
            if not installed_tools.get(tool, {}).get("installed", False)
        ]

        if not missing_tools:
            print("✅ All required tools are already installed!")

            # Still need to ensure configurations are properly set up
            print("⚙️ Verifying tool configurations...")
            self.config_generator.generate_all_configs(required_tools)

            # Add npm scripts to package.json if it's a Node.js project
            if self.tools_state.get("project_type") in [
                "javascript",
                "typescript",
                "react",
                "angular",
                "vue",
            ]:
                print("📝 Ensuring npm scripts are configured...")
                self.config_generator.add_npm_scripts()

            print("✅ Tool configurations verified!")
            return True

        print(f"📦 Installing {len(missing_tools)} missing tools...")

        # Separate tools by installer type
        npm_tools = []
        pip_tools = []

        for tool in missing_tools:
            if tool in [
                "black",
                "pylint",
                "flake8",
                "mypy",
                "bandit",
                "safety",
                "pytest",
                "radon",
            ]:
                pip_tools.append(tool)
            else:
                npm_tools.append(tool)

        success = True

        # Install npm tools
        if npm_tools:
            print(f"📦 Installing npm tools: {', '.join(npm_tools)}")
            if not self.npm_installer.install_tools(npm_tools):
                success = False

        # Install pip tools
        if pip_tools:
            print(f"📦 Installing pip tools: {', '.join(pip_tools)}")
            if not self.pip_installer.install_tools(pip_tools):
                success = False

        if success:
            print("✅ Tool installation completed!")

            # Generate configuration files
            print("⚙️ Generating configuration files...")
            self.config_generator.generate_all_configs(required_tools)

            # Add npm scripts to package.json if it's a Node.js project
            if self.tools_state.get("project_type") in [
                "javascript",
                "typescript",
                "react",
                "angular",
                "vue",
            ]:
                print("📝 Adding npm scripts to package.json...")
                self.config_generator.add_npm_scripts()

            # Update state
            self.check_tool_availability(force_refresh=True)

            print("🎉 Development environment setup complete!")
            return True
        else:
            print("❌ Some tools failed to install")
            print("🔧 Attempting to configure any available tools...")

            # Still try to configure tools that might be available
            available_tools = []
            installed_tools = self.check_tool_availability(force_refresh=True)
            for tool in required_tools:
                if installed_tools.get(tool, {}).get("installed", False):
                    available_tools.append(tool)

            if available_tools:
                print(
                    f"⚙️ Generating configurations for available tools: {', '.join(available_tools)}"
                )
                self.config_generator.generate_all_configs(available_tools)

                if self.tools_state.get("project_type") in [
                    "javascript",
                    "typescript",
                    "react",
                    "angular",
                    "vue",
                ]:
                    print("📝 Adding npm scripts for available tools...")
                    self.config_generator.add_npm_scripts()

                print("✅ Partial configuration completed")

            return False

    def get_installation_status(self) -> Dict:
        """Get comprehensive installation status report"""
        installed_tools = self.check_tool_availability()
        required_tools = self.get_tools_for_project()

        status = {
            "project_type": self.tools_state.get("project_type"),
            "total_required": len(required_tools),
            "installed_count": sum(
                1
                for t in required_tools
                if installed_tools.get(t, {}).get("installed", False)
            ),
            "missing_tools": [
                t
                for t in required_tools
                if not installed_tools.get(t, {}).get("installed", False)
            ],
            "installed_tools": [
                t
                for t in required_tools
                if installed_tools.get(t, {}).get("installed", False)
            ],
            "configurations": self.config_generator.check_existing_configs(),
        }

        return status


class NpmToolInstaller:
    """Handles npm/yarn tool installation and management"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.package_json = project_root / "package.json"

    def check_tool(self, tool_name: str) -> Dict:
        """Check if npm tool is installed"""
        try:
            # Special handling for ESLint plugins and packages that don't have CLI
            plugin_packages = [
                "@eslint/js",
                "globals",
                "eslint-plugin-import",
                "eslint-plugin-unused-imports",
                "@typescript-eslint/parser",
                "@typescript-eslint/eslint-plugin",
            ]

            if tool_name in plugin_packages:
                # Check if package exists in node_modules or package.json
                return self._check_package_existence(tool_name)

            # Check locally first for CLI tools
            result = subprocess.run(
                f"npx {tool_name} --version",
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
                shell=True,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return {"installed": True, "version": version, "scope": "local"}

            # Check globally
            result = subprocess.run(
                f"npm list -g {tool_name} --depth=0",
                capture_output=True,
                text=True,
                timeout=10,
                shell=True,
            )

            if result.returncode == 0 and tool_name in result.stdout:
                return {"installed": True, "version": "global", "scope": "global"}

            return {"installed": False, "version": None}

        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    def _check_package_existence(self, package_name: str) -> Dict:
        """Check if a package exists in node_modules or package.json"""
        try:
            # Check in package.json devDependencies first
            if self.package_json.exists():
                with open(self.package_json, "r") as f:
                    pkg_data = json.load(f)
                    dev_deps = pkg_data.get("devDependencies", {})
                    deps = pkg_data.get("dependencies", {})

                    if package_name in dev_deps:
                        return {
                            "installed": True,
                            "version": dev_deps[package_name],
                            "scope": "local",
                        }
                    elif package_name in deps:
                        return {
                            "installed": True,
                            "version": deps[package_name],
                            "scope": "local",
                        }

            # Check if package exists in node_modules
            node_modules_path = self.project_root / "node_modules" / package_name
            if node_modules_path.exists():
                # Try to read package.json from node_modules
                pkg_json = node_modules_path / "package.json"
                if pkg_json.exists():
                    with open(pkg_json, "r") as f:
                        pkg_info = json.load(f)
                        return {
                            "installed": True,
                            "version": pkg_info.get("version", "unknown"),
                            "scope": "local",
                        }
                else:
                    return {"installed": True, "version": "unknown", "scope": "local"}

            return {"installed": False, "version": None}

        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    def install_tools(self, tools: List[str]) -> bool:
        """Install npm tools as dev dependencies"""
        if not tools:
            return True

        try:
            # Ensure package.json exists
            if not self.package_json.exists():
                print("📦 Creating package.json...")
                self.create_package_json()

            # Install tools
            cmd_list = ["npm", "install", "--save-dev"] + tools
            cmd_str = " ".join(cmd_list)
            print(f"🔄 Running: {cmd_str}")

            result = subprocess.run(
                cmd_str,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
                shell=True,
            )

            if result.returncode == 0:
                print(f"✅ Successfully installed: {', '.join(tools)}")
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Installation timed out")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False

    def create_package_json(self):
        """Create a basic package.json if it doesn't exist"""
        basic_package = {
            "name": self.project_root.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "Project managed by CCOM",
            "main": "index.js",
            "scripts": {
                "test": 'echo "Error: no test specified" && exit 1',
                "lint": "eslint .",
                "lint:fix": "eslint . --fix",
                "format": "prettier --write .",
                "format:check": "prettier --check .",
            },
            "devDependencies": {},
        }

        with open(self.package_json, "w") as f:
            json.dump(basic_package, f, indent=2)


class PipToolInstaller:
    """Handles pip tool installation and management"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def check_tool(self, tool_name: str) -> Dict:
        """Check if pip tool is installed"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", tool_name, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip().split("\n")[0]
                return {"installed": True, "version": version}

            # Alternative check for some tools
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f"import {tool_name}; print({tool_name}.__version__)",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                return {"installed": True, "version": version}

            return {"installed": False, "version": None}

        except Exception as e:
            return {"installed": False, "version": None, "error": str(e)}

    def install_tools(self, tools: List[str]) -> bool:
        """Install pip tools"""
        if not tools:
            return True

        try:
            cmd = [sys.executable, "-m", "pip", "install"] + tools
            print(f"🔄 Running: {' '.join(cmd)}")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f"✅ Successfully installed: {', '.join(tools)}")
                return True
            else:
                print(f"❌ Installation failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Installation timed out")
            return False
        except Exception as e:
            print(f"❌ Installation error: {e}")
            return False


class ToolConfigGenerator:
    """Generates configuration files for development tools"""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate_all_configs(self, tools: List[str]):
        """Generate configuration files for all tools"""
        if "eslint" in tools:
            self.generate_eslint_config()

        if "prettier" in tools:
            self.generate_prettier_config()

        if any(tool in tools for tool in ["black", "pylint", "flake8", "mypy"]):
            self.generate_python_configs(tools)

        if "jest" in tools:
            self.generate_jest_config()

        if "husky" in tools:
            self.setup_git_hooks()

    def generate_eslint_config(self):
        """Generate eslint.config.mjs for ESLint v9 Flat Config"""
        config_file = self.project_root / "eslint.config.mjs"
        legacy_config = self.project_root / ".eslintrc.json"

        # Remove legacy config if it exists
        if legacy_config.exists():
            legacy_config.unlink()
            print(f"🗑️ Removed legacy ESLint config: {legacy_config}")

        if config_file.exists():
            print(f"ℹ️ ESLint v9 config already exists: {config_file}")
            return

        # Detect if TypeScript is used (excluding node_modules)
        has_typescript = (
            (self.project_root / "tsconfig.json").exists()
            or any(
                p
                for p in self.project_root.glob("**/*.ts")
                if "node_modules" not in str(p)
            )
            or any(
                p
                for p in self.project_root.glob("**/*.tsx")
                if "node_modules" not in str(p)
            )
        )

        config_content = """import js from '@eslint/js';
import globals from 'globals';
import importPlugin from 'eslint-plugin-import';
import unusedImports from 'eslint-plugin-unused-imports';

export default [
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      '.git/**',
      '.ccom/**',
      '.claude/**'
    ]
  },
  js.configs.recommended,
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
      ecmaVersion: 2021,
      sourceType: 'module',
    },
    plugins: {
      import: importPlugin,
      'unused-imports': unusedImports,
    },
    rules: {
      'no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'warn',
        {
          vars: 'all',
          varsIgnorePattern: '^_',
          args: 'after-used',
          argsIgnorePattern: '^_',
        },
      ],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      semi: ['error', 'always'],
      quotes: ['error', 'single'],
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            'sibling',
            'index',
          ],
          'newlines-between': 'always',
        },
      ],
    },
  },
  {
    files: ['.claude/**', '.ccom/**'],
    rules: {
      'no-console': 'off',
      'no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'off',
      'unused-imports/no-unused-vars': 'off'
    }
  }
];
"""

        if has_typescript:
            config_content = """import js from '@eslint/js';
import globals from 'globals';
import tseslint from '@typescript-eslint/eslint-plugin';
import tsparser from '@typescript-eslint/parser';
import importPlugin from 'eslint-plugin-import';
import unusedImports from 'eslint-plugin-unused-imports';

export default [
  {
    ignores: [
      'node_modules/**',
      'dist/**',
      'build/**',
      '.git/**',
      '.ccom/**',
      '.claude/**'
    ]
  },
  js.configs.recommended,
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsparser,
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
      ecmaVersion: 2021,
      sourceType: 'module',
    },
    plugins: {
      '@typescript-eslint': tseslint,
      import: importPlugin,
      'unused-imports': unusedImports,
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'error',
      'unused-imports/no-unused-vars': [
        'warn',
        {
          vars: 'all',
          varsIgnorePattern: '^_',
          args: 'after-used',
          argsIgnorePattern: '^_',
        },
      ],
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      semi: ['error', 'always'],
      quotes: ['error', 'single'],
    },
  },
  {
    files: ['.claude/**', '.ccom/**'],
    rules: {
      'no-console': 'off',
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      'unused-imports/no-unused-imports': 'off',
      'unused-imports/no-unused-vars': 'off'
    }
  }
];
"""

        with open(config_file, "w") as f:
            f.write(config_content)

        print(f"✅ Generated ESLint v9 config: {config_file}")

    def generate_prettier_config(self):
        """Generate .prettierrc.json and .prettierignore"""
        config_file = self.project_root / ".prettierrc.json"
        ignore_file = self.project_root / ".prettierignore"

        # Generate .prettierrc.json
        if not config_file.exists():
            config = {
                "semi": True,
                "trailingComma": "es5",
                "singleQuote": True,
                "printWidth": 80,
                "tabWidth": 2,
                "useTabs": False,
                "bracketSpacing": True,
                "arrowParens": "always",
            }

            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            print(f"✅ Generated Prettier config: {config_file}")
        else:
            print(f"ℹ️ Prettier config already exists: {config_file}")

        # Generate .prettierignore
        if not ignore_file.exists():
            ignore_content = """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist/
build/
.next/
out/

# Environment files
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db

# Logs
*.log

# Coverage
coverage/
.nyc_output/

# Package manager
package-lock.json
yarn.lock
pnpm-lock.yaml

# Generated files
*.min.js
*.min.css

# CCOM/Claude generated and scaffold files
.ccom/
.claude/
"""

            with open(ignore_file, "w") as f:
                f.write(ignore_content)

            print(f"✅ Generated Prettier ignore: {ignore_file}")
        else:
            print(f"ℹ️ Prettier ignore already exists: {ignore_file}")

    def generate_python_configs(self, tools: List[str]):
        """Generate Python tool configurations"""
        pyproject_file = self.project_root / "pyproject.toml"

        if pyproject_file.exists():
            print(f"ℹ️ Python config already exists: {pyproject_file}")
            return

        config_lines = [
            "[tool.black]",
            "line-length = 88",
            "target-version = ['py38']",
            "",
            "[tool.pylint.messages_control]",
            "disable = 'missing-docstring,too-few-public-methods'",
            "",
            "[tool.mypy]",
            "python_version = '3.8'",
            "warn_return_any = true",
            "warn_unused_configs = true",
            "",
        ]

        with open(pyproject_file, "w") as f:
            f.write("\n".join(config_lines))

        print(f"✅ Generated Python configs: {pyproject_file}")

    def generate_jest_config(self):
        """Generate jest.config.js"""
        config_file = self.project_root / "jest.config.js"

        if config_file.exists():
            print(f"ℹ️ Jest config already exists: {config_file}")
            return

        config = """module.exports = {
  testEnvironment: 'node',
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov'],
  testMatch: ['**/__tests__/**/*.js', '**/?(*.)+(spec|test).js']
};
"""

        with open(config_file, "w") as f:
            f.write(config)

        print(f"✅ Generated Jest config: {config_file}")

    def setup_git_hooks(self):
        """Setup git hooks with husky and lint-staged"""
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            return

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            # Add husky configuration
            if "husky" not in data:
                data["husky"] = {"hooks": {"pre-commit": "lint-staged"}}

            # Add lint-staged configuration
            if "lint-staged" not in data:
                data["lint-staged"] = {
                    "*.{js,jsx,ts,tsx}": ["eslint --fix", "prettier --write"],
                    "*.{py}": ["black", "pylint"],
                }

            with open(package_json, "w") as f:
                json.dump(data, f, indent=2)

            print("✅ Configured git hooks with husky and lint-staged")

        except Exception as e:
            print(f"⚠️ Error setting up git hooks: {e}")

    def check_existing_configs(self) -> Dict:
        """Check which configuration files already exist"""
        configs = {
            "eslint": (self.project_root / ".eslintrc.json").exists(),
            "prettier": (self.project_root / ".prettierrc").exists(),
            "python": (self.project_root / "pyproject.toml").exists(),
            "jest": (self.project_root / "jest.config.js").exists(),
            "git_hooks": self.check_git_hooks_setup(),
        }

        return configs

    def add_npm_scripts(self):
        """Add npm scripts to package.json for linting and formatting"""
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            print("⚠️ No package.json found - creating basic one...")
            self.create_basic_package_json()

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            # Add scripts if they don't exist
            if "scripts" not in data:
                data["scripts"] = {}

            scripts_to_add = {
                "lint": "eslint .",
                "lint:fix": "eslint . --fix",
                "format": "prettier --write .",
                "format:check": "prettier --check .",
                "test": (
                    "jest"
                    if "jest" in data.get("devDependencies", {})
                    else 'echo "Error: no test specified" && exit 1'
                ),
            }

            scripts_added = []
            for script_name, script_cmd in scripts_to_add.items():
                if script_name not in data["scripts"]:
                    data["scripts"][script_name] = script_cmd
                    scripts_added.append(script_name)

            if scripts_added:
                with open(package_json, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"✅ Added npm scripts: {', '.join(scripts_added)}")
            else:
                print("ℹ️ All npm scripts already exist")

        except Exception as e:
            print(f"⚠️ Error adding npm scripts: {e}")

    def create_basic_package_json(self):
        """Create a basic package.json if it doesn't exist"""
        package_json = self.project_root / "package.json"

        basic_package = {
            "name": self.project_root.name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": "Project managed by CCOM",
            "main": "index.js",
            "scripts": {
                "test": 'echo "Error: no test specified" && exit 1',
                "lint": "eslint .",
                "lint:fix": "eslint . --fix",
                "format": "prettier --write .",
                "format:check": "prettier --check .",
            },
            "devDependencies": {},
        }

        with open(package_json, "w") as f:
            json.dump(basic_package, f, indent=2)

    def check_git_hooks_setup(self) -> bool:
        """Check if git hooks are properly configured"""
        package_json = self.project_root / "package.json"

        if not package_json.exists():
            return False

        try:
            with open(package_json, "r") as f:
                data = json.load(f)

            return "husky" in data and "lint-staged" in data
        except:
            return False
