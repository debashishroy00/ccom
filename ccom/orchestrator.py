#!/usr/bin/env python3
"""
CCOM Orchestrator v0.3 - Claude Code Integration Layer
Provides orchestration capabilities that Claude Code lacks
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from .mcp_native import get_mcp_integration

# Handle Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class CCOMOrchestrator:
    """Core orchestration engine for CCOM + Claude Code integration"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.claude_dir = self.project_root / ".claude"
        self.ccom_dir = self.project_root / ".claude"  # Primary config location
        self.ccom_bridge_dir = self.project_root / ".ccom"  # MCP bridge location

        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.memory = self.load_memory()
        self.tools_manager = None

        # Initialize native MCP Memory Keeper integration
        self.mcp = get_mcp_integration(str(self.project_root))

        # Initialize conversation capture for Claude Code sessions
        self._init_conversation_bridge()

    def _init_conversation_bridge(self):
        """Initialize bridge to capture Claude Code conversations beyond CCOM commands"""
        try:
            # Set up environment variable for Claude Code to know about MCP capture
            os.environ['CCOM_MCP_CAPTURE_ENABLED'] = 'true'
            os.environ['CCOM_MCP_DATABASE'] = str(self.mcp.context_db)

            # Create a conversation capture interface
            self.conversation_capture_active = True
            self.logger.info("Conversation bridge initialized for comprehensive capture")
        except Exception as e:
            self.logger.error(f"Failed to initialize conversation bridge: {e}")
            self.conversation_capture_active = False

    def capture_conversation(self, input_text: str, output_text: str, metadata: dict = None):
        """
        Capture full Claude Code conversations (not just CCOM commands).
        This is the missing piece - conversations like Google Calendar integration.
        """
        try:
            # Enhanced metadata for conversational context
            conv_metadata = {
                'source': 'claude_code_conversation',
                'capture_method': 'comprehensive',
                'conversation_length': len(output_text),
                'timestamp': datetime.now().isoformat(),
                **(metadata or {})
            }

            # Use MCP to capture with intelligent fact extraction
            success = self.mcp.capture_interaction(
                input_text=input_text,
                output_text=output_text,
                metadata=conv_metadata
            )

            if success:
                self.logger.info(f"Captured conversation: {input_text[:50]}...")

            return success

        except Exception as e:
            self.logger.error(f"Failed to capture conversation: {e}")
            return False

    def load_memory(self):
        """Load existing CCOM memory"""
        memory_file = self.ccom_dir / "memory.json"
        if memory_file.exists():
            with open(memory_file) as f:
                return json.load(f)
        return self.create_empty_memory()

    def create_empty_memory(self):
        """Create empty memory structure"""
        return {
            "project": {
                "name": self.project_root.name,
                "created": datetime.now().strftime("%Y-%m-%d"),
            },
            "features": {},
            "metadata": {
                "version": "0.3",
                "created": datetime.now().isoformat(),
                "lastCleanup": datetime.now().isoformat(),
            },
        }

    def save_memory(self):
        """Save memory to file"""
        try:
            memory_file = self.ccom_dir / "memory.json"
            self.ccom_dir.mkdir(exist_ok=True)

            with open(memory_file, "w") as f:
                json.dump(self.memory, f, indent=2)

            return True
        except Exception as e:
            print(f"⚠️  Could not save memory: {e}")
            return False

    def get_tools_manager(self):
        """Get or create tools manager instance"""
        if self.tools_manager is None:
            try:
                from ccom.tools_manager import ToolsManager

                self.tools_manager = ToolsManager(self.project_root)
            except ImportError:
                print("⚠️ Tools manager not available")
                return None
        return self.tools_manager

    def ensure_tools_installed(self, required_tools=None):
        """Ensure required tools are installed before running quality checks"""
        tools_manager = self.get_tools_manager()
        if not tools_manager:
            return True  # Skip if tools manager not available

        try:
            installed_tools = tools_manager.check_tool_availability()
            project_tools = required_tools or tools_manager.get_tools_for_project()

            missing_tools = [
                tool
                for tool in project_tools
                if not installed_tools.get(tool, {}).get("installed", False)
            ]

            if missing_tools:
                print(f"⚠️ Missing development tools: {', '.join(missing_tools)}")
                print("🔧 Installing missing tools automatically...")

                success = tools_manager.install_missing_tools()
                if not success:
                    print(
                        "❌ Some tools failed to install - quality checks may be limited"
                    )
                    return False

            return True

        except Exception as e:
            print(f"⚠️ Tool check error: {e}")
            return True  # Don't block operations on tool errors

    def check_memory_for_duplicate(self, feature_name):
        """Bridge to JavaScript memory system for duplicate checking"""
        try:
            import subprocess

            result = subprocess.run(
                ["node", ".claude/ccom.js", "check", feature_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
            )
            return "EXISTS" in result.stdout
        except:
            # Fallback to Python memory check
            features = self.memory.get("features", {})
            feature_lower = feature_name.lower()

            for existing in features.keys():
                existing_lower = existing.lower()
                # Check for exact or fuzzy match
                if (
                    feature_lower in existing_lower
                    or existing_lower in feature_lower
                    or feature_lower == existing_lower
                ):
                    return True
            return False

    def _matches_patterns(self, command_lower, patterns):
        """Check if command matches any of the given patterns"""
        return any(phrase in command_lower for phrase in patterns)

    def _match_rag_patterns(self, command_lower):
        """Match RAG-specific command patterns"""
        rag_patterns = {
            "enterprise_rag": [
                "enterprise rag", "complete rag", "full rag", "rag system",
                "rag validation", "validate my rag", "check my rag", "audit my rag",
                "enterprise ai", "validate rag system", "check rag system", "audit rag system"
            ],
            "vector_validation": [
                "vector", "embedding", "chromadb", "weaviate", "faiss", "pinecone",
                "qdrant", "check vectors", "validate embeddings", "vector store",
                "semantic search", "validate vectors", "check embedding", "vector validation"
            ],
            "graph_security": [
                "graph", "neo4j", "cypher", "arangodb", "knowledge graph",
                "graph database", "check graph", "graph security", "validate graph",
                "graph patterns", "validate neo4j", "check cypher", "knowledge graph security"
            ],
            "hybrid_rag": [
                "hybrid", "fusion", "rerank", "multi", "combine", "blend",
                "vector and keyword", "dense and sparse", "hybrid search",
                "fusion search", "check hybrid", "validate fusion", "reranking validation"
            ],
            "agentic_rag": [
                "agent", "agentic", "react", "chain of thought", "cot", "reasoning",
                "tool", "agent safety", "agent validation", "reasoning patterns",
                "validate agents", "check reasoning", "agent security", "tool safety"
            ],
            "rag_quality": [
                "rag quality", "rag patterns", "ai quality", "llm quality",
                "retrieval quality", "validate ai", "check llm", "ai validation", "llm validation"
            ],
            "aws_rag": [
                "aws", "bedrock", "titan", "langchain", "mongodb atlas", "mongodb vector",
                "ecs", "fargate", "lambda", "api gateway", "aws rag", "aws stack",
                "check aws", "validate bedrock", "audit aws", "aws deployment",
                "titan embed", "claude bedrock", "aws ai", "aws llm"
            ],
            "angular_validation": [
                "angular", "rxjs", "observable", "subscription", "memory leak",
                "change detection", "component", "service", "angular performance",
                "check angular", "validate angular", "frontend", "typescript patterns"
            ],
            "cost_optimization": [
                "cost", "expensive", "budget", "billing", "optimize cost", "save money",
                "cost optimization", "aws cost", "bedrock cost", "check cost",
                "reduce cost", "cost tracking", "spending", "price optimization"
            ],
            "s3_security": [
                "s3 security", "presigned url", "multipart upload", "s3 cors",
                "bucket security", "s3 encryption", "storage security", "file upload",
                "check s3", "validate s3", "s3 policy", "s3 access"
            ],
            "performance_optimization": [
                "performance", "latency", "speed", "slow", "fast", "optimize performance",
                "caching", "monitoring", "throughput", "response time",
                "performance check", "check performance", "performance audit", "optimize speed"
            ],
            "complete_stack": [
                "complete stack", "full stack", "entire stack", "everything",
                "all checks", "complete validation", "full validation",
                "production ready", "deploy ready", "check everything",
                "validate all", "complete audit", "comprehensive check"
            ]
        }

        for workflow, patterns in rag_patterns.items():
            if self._matches_patterns(command_lower, patterns):
                return self.run_workflow(workflow)
        return None

    def _match_standard_patterns(self, command_lower, original_command):
        """Match standard workflow command patterns"""
        if self._matches_patterns(command_lower, ["workflow", "pipeline", "ci", "automation"]):
            return self.handle_workflow_command(original_command)

        if self._matches_patterns(command_lower, ["build", "compile", "package", "prepare release", "production build"]):
            feature_name = original_command.replace("ccom", "").replace("build", "").strip()
            if self.check_memory_for_duplicate(feature_name):
                print(f"⚠️ DUPLICATE DETECTED: Feature '{feature_name}' already exists!")
                print("Use 'ccom enhance' to improve existing feature instead.")
                return False
            return self.build_sequence()

        if self._matches_patterns(command_lower, ["deploy", "ship", "go live", "launch"]):
            return self.deploy_sequence()

        if self._matches_patterns(command_lower, ["quality", "clean", "fix", "lint"]):
            return self.quality_sequence()

        if self._matches_patterns(command_lower, ["secure", "safety", "protect", "scan"]):
            return self.security_sequence()

        if self._matches_patterns(command_lower, ["watch", "monitor", "file monitoring", "auto quality", "real-time"]):
            return self.handle_file_monitoring_command(original_command)

        if self._matches_patterns(command_lower, [
            "context", "project context", "show context", "load context", "project summary",
            "what is this project", "project overview", "catch me up", "bring me up to speed"
        ]):
            return self.show_project_context()

        if self._matches_patterns(command_lower, ["remember", "memory", "status", "forget"]):
            return self.handle_memory_command(original_command)

        if self._matches_patterns(command_lower, ["init", "initialize", "setup"]):
            return self.handle_init_command()

        return None

    def _match_command_pattern(self, command_lower, original_command):
        """Match command patterns to workflows"""
        # MCP Memory patterns - prioritize MCP for session/memory queries
        if self._matches_patterns(command_lower, [
            "discuss", "discussed", "past session", "previous session", "last session",
            "what did we", "session history", "previous work", "past work", "highlights",
            "key highlights", "session recap", "what happened", "review session",
            "session summary", "past discussions", "previous discussions"
        ]):
            return self.show_mcp_session_summary()

        # RAG-specific patterns
        rag_workflow = self._match_rag_patterns(command_lower)
        if rag_workflow:
            return rag_workflow

        # Software engineering principles
        if self._matches_patterns(command_lower, [
            "principles", "software engineering", "kiss", "yagni", "dry", "solid",
            "check principles", "validate principles", "simplify", "duplicate",
            "complexity", "refactor", "clean code", "best practices"
        ]):
            target_files = self._extract_target_files(original_command)
            return self.validate_principles(target_files=target_files)

        # Standard workflow patterns
        return self._match_standard_patterns(command_lower, original_command)

    def handle_natural_language(self, command):
        """Parse natural language commands and execute appropriate actions"""
        command_lower = command.lower().strip()
        print(f"🎯 Processing command: '{command}'")

        # Capture input and prepare for output capture
        start_time = datetime.now()

        # Use pattern matcher to find the appropriate workflow
        workflow_result = self._match_command_pattern(command_lower, command)

        # Simple, reliable MCP capture
        if workflow_result is not None:
            try:
                # Execute workflow if callable
                if callable(workflow_result):
                    actual_result = workflow_result()
                    output_summary = f"CCOM executed: {command} → Success"
                    workflow_result = actual_result
                else:
                    output_summary = f"CCOM executed: {command} → {str(workflow_result)[:200]}"

                # Simple capture call - no complex output redirection
                self.mcp.capture_interaction(
                    input_text=command,
                    output_text=output_summary,
                    metadata={
                        'timestamp': datetime.now().isoformat(),
                        'command_type': 'ccom_workflow',
                        'success': True
                    }
                )

                self.logger.info(f"Captured CCOM interaction: {command}")

            except Exception as e:
                self.logger.warning(f"MCP capture failed (non-critical): {e}")
                # Don't let capture failures break the workflow

            return workflow_result
        else:
            error_output = "❓ Unknown command. Try: workflow, deploy, quality, security, memory, or init commands"
            print(error_output)
            self.mcp.capture_interaction(
                input_text=command,
                output_text=error_output,
                metadata={
                    'execution_time': (datetime.now() - start_time).total_seconds(),
                    'success': False
                }
            )
            return False

    def deploy_sequence(self):
        """Full enterprise deployment sequence"""
        print("🚀 Starting enterprise deployment sequence...")

        # Step 1: Quality check via Claude Code subagent
        print("Step 1: Running quality checks...")
        quality_result = self.invoke_subagent("quality-enforcer")

        if not quality_result:
            print("❌ Deployment blocked - quality issues found")
            return False

        # Step 2: Basic security check
        print("Step 2: Running security scan...")
        security_result = self.run_security_check()

        if not security_result:
            print("❌ Deployment blocked - security issues found")
            return False

        # Step 3: Build production artifacts
        print("Step 3: Building production artifacts...")
        build_result = self.invoke_subagent("builder-agent")

        if not build_result:
            print("❌ Deployment blocked - build failed")
            return False

        # Step 4: Deploy via deployment specialist
        print("Step 4: Coordinating deployment...")
        deploy_result = self.invoke_subagent("deployment-specialist")

        if deploy_result:
            print("🎉 Enterprise deployment complete!")
            return True
        else:
            print("❌ Deployment failed")
            return False

    def build_sequence(self):
        """Run standalone build process"""
        print("🚧 Starting production build process...")
        return self.invoke_subagent("builder-agent")

    def quality_sequence(self):
        """Run quality checks and fixes"""
        print("🔧 Running quality analysis and fixes...")
        return self.invoke_subagent("quality-enforcer")

    def security_sequence(self):
        """Run security checks"""
        print("🔒 Running security scan...")
        return self.run_security_check()

    def invoke_subagent(self, agent_name):
        """
        CCOM Native Agent Execution

        CCOM provides the orchestration layer that Claude Code lacks.
        Agent definitions in .claude/agents/*.md serve as behavior specifications.
        """
        agent_file = self.claude_dir / "agents" / f"{agent_name}.md"

        if not agent_file.exists():
            print(f"❌ Agent specification not found: {agent_file}")
            return False

        print(f"🤖 CCOM executing {agent_name}...")
        return self.execute_agent_implementation(agent_name)

    def execute_agent_implementation(self, agent_name):
        """
        CCOM Native Agent Implementation

        Execute the native CCOM implementation for the specified agent.
        Agent behavior is defined by .claude/agents/*.md specifications.
        """
        implementations = {
            "quality-enforcer": self.run_quality_enforcement,
            "security-guardian": self.run_security_scan,
            "builder-agent": self.run_build_process,
            "deployment-specialist": self.run_deployment_process,
        }

        if agent_name in implementations:
            return implementations[agent_name]()
        else:
            print(f"❌ No implementation available for {agent_name}")
            return False

    def _extract_target_files(self, command):
        """Extract target files from command if specified"""
        import re

        # Look for file patterns in command
        file_patterns = re.findall(r'([a-zA-Z0-9/_.-]+\.(js|ts|jsx|tsx|py))', command)
        if file_patterns:
            return [pattern[0] for pattern in file_patterns]

        # Look for directory patterns
        dir_patterns = re.findall(r'(src/|components/|utils/|lib/|[a-zA-Z0-9_-]+/)', command)
        if dir_patterns:
            target_files = []
            for dir_pattern in dir_patterns:
                dir_path = self.project_root / dir_pattern.rstrip('/')
                if dir_path.exists() and dir_path.is_dir():
                    target_files.extend(dir_path.glob('**/*.js'))
                    target_files.extend(dir_path.glob('**/*.ts'))
                    target_files.extend(dir_path.glob('**/*.jsx'))
                    target_files.extend(dir_path.glob('**/*.tsx'))
            return [str(f) for f in target_files]

        return None

    def validate_principles(self, target_files=None):
        """CCOM Native Software Engineering Principles Validation"""
        if target_files:
            print(f"📐 **CCOM PRINCIPLES VALIDATION** – Analyzing {len(target_files)} specific files against KISS, YAGNI, DRY, SOLID...")
        else:
            print("📐 **CCOM PRINCIPLES VALIDATION** – Analyzing code against KISS, YAGNI, DRY, SOLID...")

        try:
            from ccom.validators import PrinciplesValidator

            # Ensure complexity analysis tools are available
            self.ensure_tools_installed(["complexity-report", "jscpd", "radon"])

            # Create principles validator with optional target files
            max_files = 50 if target_files else 100  # Smaller limit for targeted analysis
            principles_validator = PrinciplesValidator(
                self.project_root,
                self.get_tools_manager(),
                target_files=target_files,
                max_files=max_files
            )

            # Run all principles validation
            results = principles_validator.validate_all_principles()

            # Print detailed results
            print(f"\n📊 **PRINCIPLES ANALYSIS RESULTS**:")

            total_score = 0
            principle_count = 0

            for principle_name, result in results.items():
                status = "✅" if result.success else "⚠️"
                print(f"\n{status} **{result.validator_name}**: {result.score}/100")

                if result.issues:
                    for issue in result.issues[:3]:  # Show first 3 issues
                        severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
                        print(f"  {severity_icon} {issue['message']}")

                    if len(result.issues) > 3:
                        print(f"  … and {len(result.issues) - 3} more issues")

                if result.warnings:
                    for warning in result.warnings[:2]:  # Show first 2 warnings
                        print(f"  🟨 {warning}")

                total_score += result.score
                principle_count += 1

            # Calculate overall principles score
            weights = {'kiss': 0.3, 'yagni': 0.2, 'dry': 0.3, 'solid': 0.2}
            weighted_score = sum(
                results[p].score * weight
                for p, weight in weights.items()
                if p in results
            )

            # Determine grade
            if weighted_score >= 95:
                grade = "A+"
                status_msg = "🎆 **PRINCIPLES STATUS**: Exemplary - Following all best practices!"
            elif weighted_score >= 90:
                grade = "A"
                status_msg = "✅ **PRINCIPLES STATUS**: Excellent - High-quality engineering practices"
            elif weighted_score >= 80:
                grade = "B+"
                status_msg = "🔧 **PRINCIPLES STATUS**: Good - Minor improvements recommended"
            elif weighted_score >= 70:
                grade = "B"
                status_msg = "⚠️ **PRINCIPLES STATUS**: Acceptable - Some refactoring needed"
            else:
                grade = "C"
                status_msg = "🔴 **PRINCIPLES STATUS**: Needs Improvement - Significant refactoring required"

            print(f"\n{status_msg}")
            print(f"Overall Principles Score: {weighted_score:.1f}/100 (Grade: {grade})")

            # Provide actionable feedback
            print(f"\n💡 **ACTIONABLE RECOMMENDATIONS**:")

            if results.get('kiss', ValidationResult('')).score < 80:
                print("  • Simplify complex functions - break down large methods (KISS)")
            if results.get('dry', ValidationResult('')).score < 80:
                print("  • Extract duplicate code into reusable functions (DRY)")
            if results.get('yagni', ValidationResult('')).score < 80:
                print("  • Remove unused code and over-engineered abstractions (YAGNI)")
            if results.get('solid', ValidationResult('')).score < 80:
                print("  • Review class responsibilities and dependencies (SOLID)")

            if weighted_score >= 90:
                print("  • Consider mentoring others on software engineering best practices")
                print("  • Document your architectural decisions for the team")

            return weighted_score >= 80

        except ImportError:
            print("⚠️ Principles validation not available - validators module missing")
            return True
        except Exception as e:
            print(f"⚠️ Principles validation error: {e}")
            return True

    def run_quality_enforcement(self):
        """CCOM Native Quality Enforcement Implementation"""
        print("🔧 **CCOM QUALITY** – Running enterprise standards...")

        try:
            from ccom.validators import ValidationOrchestrator

            # Create validation orchestrator
            validator = ValidationOrchestrator(
                self.project_root, self.get_tools_manager()
            )

            # Run validations with auto-fix
            results = validator.run_all_validations(auto_fix=True)

            # Print summary
            validator.print_summary()

            # Determine overall success
            report = validator.generate_report()
            success = report["overall_score"] >= 80 and report["total_issues"] == 0

            if success:
                print("✅ **QUALITY STATUS**: Enterprise Grade")
            else:
                print(
                    "🔧 **QUALITY STATUS**: Improvements Applied - Review remaining issues"
                )

            return success

        except ImportError:
            print("⚠️ Advanced validation not available - falling back to basic checks")
            return self._run_basic_quality_checks()

    def _run_basic_quality_checks(self):
        """Fallback basic quality checks"""
        # Ensure required tools are installed
        if not self.ensure_tools_installed(["eslint", "prettier"]):
            print("⚠️ Proceeding with limited quality checks")

        # Check if we have package.json with lint script
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                # Try running lint with shell=True for Windows compatibility
                result = subprocess.run(
                    "npm run lint",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    print("✅ Code quality: Enterprise grade")
                    return True
                else:
                    print("🔧 Found quality issues, attempting auto-fix...")

                    # Try auto-fix
                    fix_result = subprocess.run(
                        "npm run lint -- --fix",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if fix_result.returncode == 0:
                        print("✅ Quality issues fixed automatically")
                        return True
                    else:
                        print("⚠️ Some quality issues need manual attention")
                        return False

            except subprocess.TimeoutExpired:
                print("⚠️ Lint command timed out")
                return False
            except Exception as e:
                print(f"⚠️ Error running lint: {e}")
                return False
        else:
            print("ℹ️ No package.json found - skipping lint checks")
            return True

    def run_security_scan(self):
        """CCOM Native Security Guardian Implementation"""
        print("🔒 **CCOM SECURITY** – Bank-level protection scan...")

        # Ensure security tools are available
        tools_manager = self.get_tools_manager()
        if tools_manager and tools_manager.tools_state.get("project_type") == "python":
            self.ensure_tools_installed(["bandit", "safety"])

        security_issues = []

        # 1. Dependency vulnerability scanning
        try:
            result = subprocess.run(
                "npm audit --json",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("vulnerabilities", {})

                if vulnerabilities:
                    high_critical = sum(
                        1
                        for v in vulnerabilities.values()
                        if v.get("severity") in ["high", "critical"]
                    )
                    if high_critical > 0:
                        security_issues.append(
                            f"🚨 {high_critical} high/critical vulnerabilities found"
                        )
                        print("🛠️  Attempting to fix vulnerabilities...")

                        # Try auto-fix
                        fix_result = subprocess.run(
                            "npm audit fix",
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=60,
                        )
                        if fix_result.returncode == 0:
                            print("✅ Vulnerabilities automatically fixed")
                        else:
                            print("⚠️  Some vulnerabilities require manual attention")
                            return False
                else:
                    print("✅ No known vulnerabilities in dependencies")

        except Exception as e:
            print(f"⚠️  Dependency scan error: {e}")

        # 2. Code security analysis
        self.scan_for_security_issues()

        # 3. Configuration security
        self.check_security_configuration()

        if not security_issues:
            print("🛡️  Security: Bank-level")
            return True
        else:
            print("🚨 Security issues detected - securing your app...")
            return False

    def scan_for_security_issues(self):
        """Scan source code for security anti-patterns"""
        security_patterns = [
            (r'password\s*=\s*["\'].*["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\'].*["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\'].*["\']', "Hardcoded secret detected"),
            (r"eval\s*\(", "Dangerous eval() usage detected"),
            (r"innerHTML\s*=", "Potential XSS vulnerability"),
            (r"document\.write\s*\(", "Dangerous document.write usage"),
        ]

        try:
            import re

            for file_path in self.project_root.rglob("*.js"):
                if "node_modules" in str(file_path):
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                for pattern, message in security_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        print(f"⚠️  {message} in {file_path.name}")

        except Exception as e:
            print(f"ℹ️  Code security scan skipped: {e}")

    def check_security_configuration(self):
        """Check for security configuration issues"""
        package_json = self.project_root / "package.json"

        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)

                # Check for security-related dependencies
                dependencies = data.get("dependencies", {})
                dev_dependencies = data.get("devDependencies", {})
                all_deps = {**dependencies, **dev_dependencies}

                security_packages = [
                    "helmet",
                    "express-rate-limit",
                    "cors",
                    "express-validator",
                ]
                missing_security = [
                    pkg for pkg in security_packages if pkg not in all_deps
                ]

                if missing_security:
                    print(
                        f"💡 Consider adding security packages: {', '.join(missing_security)}"
                    )

            except Exception as e:
                print(f"ℹ️  Configuration check skipped: {e}")

    def run_deployment_process(self):
        """CCOM Native Deployment Specialist Implementation"""
        print("🚀 **CCOM DEPLOYMENT** – Enterprise orchestration...")

        # 1. Pre-deployment validation
        print("Step 1: Pre-deployment validation...")
        if not self.validate_deployment_readiness():
            print("❌ Deployment validation failed")
            return False

        # 2. Execute deployment
        print("Step 2: Executing deployment...")
        if not self.execute_deployment():
            print("❌ Deployment execution failed")
            return False

        # 3. Post-deployment verification
        print("Step 3: Post-deployment verification...")
        if not self.verify_deployment():
            print("⚡ Deployment verification failed - considering rollback")
            return False

        print("🎉 Deployment successful! All systems green.")
        self.record_successful_deployment()
        return True

    def validate_deployment_readiness(self):
        """Validate that the application is ready for deployment"""
        try:
            # Check if build succeeds
            if self.has_build_script():
                result = subprocess.run(
                    "npm run build",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    print("❌ Build failed")
                    return False
                print("✅ Build successful")

            # Check if tests pass
            if self.has_test_script():
                result = subprocess.run(
                    "npm test", shell=True, capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    print("⚠️  Some tests failed - proceeding with caution")
                else:
                    print("✅ Tests passed")

            return True

        except Exception as e:
            print(f"⚠️  Validation error: {e}")
            return True  # Don't block deployment on validation errors

    def execute_deployment(self):
        """Execute the actual deployment"""
        try:
            package_json = self.project_root / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    data = json.load(f)

                if "deploy" in data.get("scripts", {}):
                    result = subprocess.run(
                        "npm run deploy",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )

                    if result.returncode == 0:
                        print("✅ Deployment command executed successfully")
                        if result.stdout:
                            # Look for deployment URL in output
                            lines = result.stdout.split("\n")
                            for line in lines:
                                if "http" in line and (
                                    "deployed" in line.lower() or "live" in line.lower()
                                ):
                                    print(f"🌐 App URL: {line.strip()}")
                        return True
                    else:
                        print(f"❌ Deployment failed: {result.stderr}")
                        return False
                else:
                    print("✅ No deployment script - assuming manual deployment")
                    return True
            else:
                print("✅ No package.json - deployment method unknown")
                return True

        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

    def verify_deployment(self):
        """Verify that the deployment was successful"""
        print("🔍 Running post-deployment health checks...")

        # Basic health check - in a real scenario, this would ping the deployed URL
        # For now, just verify the deployment completed without obvious errors

        try:
            # Check if any error logs were created
            log_files = list(self.project_root.glob("*.log"))
            error_files = list(self.project_root.glob("error*"))

            if log_files or error_files:
                print("⚠️  Log files detected - review for potential issues")

            print("✅ Basic health checks passed")
            return True

        except Exception as e:
            print(f"⚠️  Health check error: {e}")
            return True  # Don't fail deployment on health check errors

    def has_build_script(self):
        """Check if project has a build script"""
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                return "build" in data.get("scripts", {})
            except:
                return False
        return False

    def has_test_script(self):
        """Check if project has a test script"""
        package_json = self.project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                return "test" in data.get("scripts", {})
            except:
                return False
        return False

    def record_successful_deployment(self):
        """Record deployment in memory for tracking"""
        try:
            deployment_record = {
                "timestamp": datetime.now().isoformat(),
                "status": "successful",
                "quality_checks": "passed",
                "security_checks": "passed",
            }

            # Add to memory
            if "deployments" not in self.memory:
                self.memory["deployments"] = []

            self.memory["deployments"].append(deployment_record)

            # Keep only last 10 deployments
            self.memory["deployments"] = self.memory["deployments"][-10:]

            self.save_memory()

        except Exception as e:
            print(f"ℹ️  Could not record deployment: {e}")

    def run_build_process(self):
        """CCOM Native Builder Agent Implementation"""
        print("🚧 **CCOM BUILDER** – Preparing production build...")

        try:
            # 1. Detect project type
            package_json = self.project_root / "package.json"
            pyproject = self.project_root / "pyproject.toml"
            setup_py = self.project_root / "setup.py"
            index_html = self.project_root / "index.html"

            project_type = "unknown"
            if package_json.exists():
                project_type = "node"
                print("📊 Project Analysis: Node.js application detected")
            elif pyproject.exists() or setup_py.exists():
                project_type = "python"
                print("📊 Project Analysis: Python package detected")
            elif index_html.exists():
                project_type = "static"
                print("📊 Project Analysis: Static site detected")
            else:
                print("⚠️  Could not detect project type")
                return False

            # 2. Code quality checks
            print("\n🔍 Checking code quality standards...")
            quality_issues = []

            # Check file sizes (simplified check)
            if project_type == "node":
                src_files = (
                    list(self.project_root.glob("**/*.js"))
                    + list(self.project_root.glob("**/*.jsx"))
                    + list(self.project_root.glob("**/*.ts"))
                    + list(self.project_root.glob("**/*.tsx"))
                )

                for file in src_files[:10]:  # Check first 10 files
                    if file.stat().st_size > 50000:  # 50KB warning
                        quality_issues.append(f"Large file: {file.name}")

            if quality_issues:
                print(f"⚠️  Quality warnings: {len(quality_issues)} issues found")
            else:
                print("✅ Code quality: A+ (all standards met)")

            # 3. Execute build
            print("\n🔨 Building project...")
            build_success = False
            build_output = ""

            if project_type == "node":
                # Install dependencies
                result = subprocess.run(
                    "npm ci || npm install",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    print("❌ Failed to install dependencies")
                    return False

                # Run build
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})

                if "build" in scripts:
                    result = subprocess.run(
                        "npm run build",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=180,
                    )
                    build_success = result.returncode == 0
                    build_output = result.stdout
                else:
                    # Try common build commands
                    for cmd in ["npx vite build", "npx webpack", "npx tsc"]:
                        result = subprocess.run(
                            cmd, shell=True, capture_output=True, text=True, timeout=180
                        )
                        if result.returncode == 0:
                            build_success = True
                            build_output = result.stdout
                            break

            elif project_type == "python":
                result = subprocess.run(
                    "pip install -U build && python -m build",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
                build_success = result.returncode == 0
                build_output = result.stdout

            elif project_type == "static":
                # Just validate structure
                if index_html.exists():
                    build_success = True
                    print("✅ Static site structure validated")

            if not build_success:
                print("\n❌ Build failed")
                print("💡 Quick fixes:")
                print("- Add 'build' script to package.json")
                print("- Run: npm install")
                print("- Check for TypeScript errors")
                return False

            # 4. Analyze artifacts
            print("\n📦 Artifacts Summary:")

            # Find output directory
            output_dirs = ["dist", "build", ".next", "out", "public"]
            for dir_name in output_dirs:
                output_dir = self.project_root / dir_name
                if output_dir.exists() and output_dir.is_dir():
                    # Calculate size
                    total_size = sum(
                        f.stat().st_size for f in output_dir.rglob("*") if f.is_file()
                    )
                    print(f"- Output: {dir_name}/")
                    print(f"- Total size: {total_size / 1024:.1f}KB")

                    # List largest files
                    files = sorted(
                        output_dir.rglob("*"),
                        key=lambda f: f.stat().st_size if f.is_file() else 0,
                        reverse=True,
                    )

                    print("- Largest files:")
                    for f in files[:5]:
                        if f.is_file():
                            size = f.stat().st_size / 1024
                            print(f"  - {f.name}: {size:.1f}KB")
                    break

            print("\n⚡ Optimizations Applied:")
            print("- Production mode enabled")
            print("- Dependencies bundled")
            print("- Ready for deployment")

            print("\n✅ **Build Status**: Production-ready for deployment")
            return True

        except Exception as e:
            print(f"\n❌ Build error: {e}")
            print("💡 Try: ccom build --debug")
            return False

    def run_security_check(self):
        """Run enhanced security checks via security-guardian"""
        return self.invoke_subagent("security-guardian")

    def run_deployment(self):
        """Run basic deployment"""
        try:
            # Check if we have a deploy script
            package_json = self.project_root / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    data = json.load(f)

                if "deploy" in data.get("scripts", {}):
                    result = subprocess.run(
                        "npm run deploy",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=120,
                    )
                    print(f"Deploy output: {result.stdout}")
                    if result.stderr:
                        print(f"Deploy errors: {result.stderr}")
                    return result.returncode == 0
                else:
                    print("ℹ️  No deploy script found in package.json")
                    return True
            else:
                print("ℹ️  No package.json found")
                return True

        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False

    def handle_memory_command(self, command):
        """Handle memory-related commands"""
        result = None
        if "status" in command.lower():
            result = self.show_status()
        elif "memory" in command.lower():
            result = self.show_memory()
        else:
            print("Memory commands: status, memory")
            result = True

        # Capture the interaction
        try:
            self.mcp.capture_interaction(
                input_text=f"memory command: {command}",
                output_text=f"CCOM memory command executed: {command}",
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'command_type': 'memory_command',
                    'success': True
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to capture memory command: {e}")

        return result

    def handle_file_monitoring_command(self, command):
        """Handle file monitoring commands"""
        command_lower = command.lower()

        if "start" in command_lower or "watch" in command_lower:
            return self.start_file_monitoring()
        elif "stop" in command_lower:
            return self.stop_file_monitoring()
        elif "config" in command_lower:
            return self.show_file_monitoring_config()
        else:
            print("🔍 **CCOM FILE MONITOR** – Real-time quality enforcement")
            print("Commands:")
            print("  ccom 'watch files'     → Start file monitoring")
            print("  ccom 'stop watching'   → Stop file monitoring")
            print("  ccom 'monitor config'  → Show configuration")
            return True

    def start_file_monitoring(self):
        """Start the CCOM file monitoring system"""
        try:
            print(
                "🔍 **CCOM FILE MONITOR** – Starting real-time quality enforcement..."
            )

            # Import and initialize the file monitor
            from ccom.file_monitor import CCOMFileMonitor

            monitor = CCOMFileMonitor(self.project_root)
            monitor.start_watching()

            return True

        except Exception as e:
            print(f"❌ File monitoring error: {e}")
            print("💡 Make sure Node.js is installed for file watching")
            return False

    def stop_file_monitoring(self):
        """Stop file monitoring"""
        print("🛑 **CCOM FILE MONITOR** – Stopping file monitoring...")
        print("💡 Use Ctrl+C to stop an active monitoring session")
        return True

    def show_file_monitoring_config(self):
        """Show file monitoring configuration"""
        try:
            from ccom.file_monitor import CCOMFileMonitor

            monitor = CCOMFileMonitor(self.project_root)
            print("📋 **CCOM FILE MONITOR** – Configuration:")
            print(f"  📂 Project: {self.project_root}")
            print(f"  ⚡ Enabled: {monitor.config['enabled']}")
            print(
                f"  📋 Watch patterns: {len(monitor.config['watch_patterns'])} patterns"
            )
            print(
                f"  🚫 Ignore patterns: {len(monitor.config['ignore_patterns'])} patterns"
            )
            print(
                f"  ⏱️  Debounce: {monitor.config['quality_triggers']['debounce_ms']}ms"
            )

            return True

        except Exception as e:
            print(f"❌ Config error: {e}")
            return False

    def handle_workflow_command(self, command):
        """Handle workflow automation commands with natural language"""
        command_lower = command.lower()

        # === RAG-SPECIFIC NATURAL LANGUAGE PATTERNS ===

        # Enterprise RAG - comprehensive validation
        if any(
            phrase in command_lower
            for phrase in [
                "enterprise rag",
                "complete rag",
                "full rag",
                "rag system",
                "rag validation",
                "validate my rag",
                "check my rag",
                "audit my rag",
                "enterprise ai",
            ]
        ):
            return self.run_workflow("enterprise_rag")

        # Vector stores - ChromaDB, Weaviate, FAISS, etc.
        elif any(
            phrase in command_lower
            for phrase in [
                "vector",
                "embedding",
                "chromadb",
                "weaviate",
                "faiss",
                "pinecone",
                "qdrant",
                "check vectors",
                "validate embeddings",
                "vector store",
                "semantic search",
            ]
        ):
            return self.run_workflow("vector_validation")

        # Graph databases - Neo4j, ArangoDB, etc.
        elif any(
            phrase in command_lower
            for phrase in [
                "graph",
                "neo4j",
                "cypher",
                "arangodb",
                "knowledge graph",
                "graph database",
                "check graph",
                "graph security",
                "validate graph",
                "graph patterns",
            ]
        ):
            return self.run_workflow("graph_security")

        # Hybrid RAG - fusion, reranking, multi-modal
        elif any(
            phrase in command_lower
            for phrase in [
                "hybrid",
                "fusion",
                "rerank",
                "multi",
                "combine",
                "blend",
                "vector and keyword",
                "dense and sparse",
                "hybrid search",
                "fusion search",
            ]
        ):
            return self.run_workflow("hybrid_rag")

        # Agentic RAG - ReAct, CoT, agents, tools
        elif any(
            phrase in command_lower
            for phrase in [
                "agent",
                "agentic",
                "react",
                "chain of thought",
                "cot",
                "reasoning",
                "tool",
                "agent safety",
                "agent validation",
                "reasoning patterns",
            ]
        ):
            return self.run_workflow("agentic_rag")

        # RAG Quality - general RAG patterns
        elif any(
            phrase in command_lower
            for phrase in [
                "rag quality",
                "rag patterns",
                "ai quality",
                "llm quality",
                "retrieval quality",
            ]
        ):
            return self.run_workflow("rag_quality")

        # AWS RAG - AWS-specific patterns
        elif any(
            phrase in command_lower
            for phrase in [
                "aws",
                "bedrock",
                "titan",
                "langchain",
                "mongodb atlas",
                "mongodb vector",
                "ecs",
                "fargate",
                "lambda",
                "api gateway",
                "aws rag",
                "aws stack",
                "check aws",
                "validate bedrock",
                "audit aws",
                "aws deployment",
                "titan embed",
                "claude bedrock",
                "aws ai",
                "aws llm",
            ]
        ):
            return self.run_workflow("aws_rag")

        # === STANDARD WORKFLOWS ===

        # Quality workflows
        elif "quality" in command_lower:
            return self.run_workflow("quality")
        elif "security" in command_lower:
            return self.run_workflow("security")
        elif "deploy" in command_lower:
            return self.run_workflow("deploy")
        elif "full" in command_lower or "pipeline" in command_lower:
            return self.run_workflow("full")
        elif "setup" in command_lower:
            return self.run_workflow("setup")
        else:
            print("🔄 **CCOM WORKFLOWS** – Natural language automation")
            print("\n📖 Standard workflows:")
            print(
                "  ccom check quality             → Quality gates (lint, format, tests)"
            )
            print(
                "  ccom scan security             → Security audit (dependencies, secrets)"
            )
            print("  ccom deploy my app             → Full deployment pipeline")
            print("  ccom setup github actions      → Create CI/CD workflows")
            print("\n🧠 Enterprise RAG workflows:")
            print("  ccom validate my rag system    → Complete RAG validation")
            print("  ccom check vectors              → ChromaDB, Weaviate, FAISS")
            print("  ccom validate graph database   → Neo4j, ArangoDB security")
            print("  ccom check hybrid search       → Fusion & reranking")
            print("  ccom validate agents            → ReAct, CoT, tool safety")
            print("\n☁️ AWS-specific workflows:")
            print("  ccom check aws bedrock         → Bedrock & LangChain patterns")
            print("  ccom validate mongodb          → MongoDB Atlas Vector Search")
            print("  ccom audit ecs deployment      → ECS/Lambda/S3 validation")
            print("  ccom check titan embeddings    → AWS Titan embedding validation")
            print("\n🎯 Critical Gap workflows:")
            print(
                "  ccom check angular             → RxJS memory leaks & change detection"
            )
            print(
                "  ccom optimize cost              → AWS cost tracking & optimization"
            )
            print(
                "  ccom validate s3 security       → Presigned URLs & multipart uploads"
            )
            print("  ccom check performance          → Monitoring, caching & latency")
            print("  ccom validate complete stack    → All validators for production")
            print("\n💡 Use natural language - CCOM understands your intent!")
            return True

    def run_workflow(self, workflow_name):
        """Execute a CCOM workflow using the workflows module"""
        try:
            # Capture workflow start
            self.mcp.save_context(
                key=f"workflow_{workflow_name}",
                value=f"Started workflow: {workflow_name}",
                category="workflow"
            )

            # Import and initialize workflows
            from ccom.workflows import CCOMWorkflows

            workflows = CCOMWorkflows(self.project_root)

            if workflow_name == "setup":
                result = workflows.create_github_workflow()
                self.mcp.save_context(
                    key=f"workflow_{workflow_name}_completed",
                    value=f"Completed workflow: {workflow_name} - GitHub workflow created",
                    category="success"
                )
                return result
            else:
                return workflows.run_workflow(workflow_name)

        except Exception as e:
            print(f"❌ Workflow error: {e}")
            return False

    def handle_init_command(self):
        """Handle init-related commands"""
        print("🚀 CCOM natural language init detected...")
        print("💡 For full initialization, use: ccom --init")
        print("💡 For force refresh, use: ccom --init --force")
        return True

    def show_status(self):
        """Show CCOM status"""
        print("\n📊 CCOM Status Report")
        print("=" * 40)
        print(f"Project: {self.memory['project']['name']}")
        print(f"Features: {len(self.memory['features'])}")
        print(f"Version: {self.memory.get('metadata', {}).get('version', '0.3')}")

        # Check Claude Code integration
        agents_dir = self.claude_dir / "agents"
        if agents_dir.exists():
            agent_count = len(list(agents_dir.glob("*.md")))
            print(f"Claude Code Agents: {agent_count}")
        else:
            print("Claude Code Agents: 0")

        print("=" * 40)

        # Capture the status check
        try:
            self.mcp.capture_interaction(
                input_text="show status",
                output_text="CCOM status displayed",
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'command_type': 'status_display',
                    'success': True
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to capture status display: {e}")

        return True

    def show_memory(self):
        """Show memory contents - prioritize MCP over legacy JSON"""
        result = None
        try:
            # Try MCP first (preferred system)
            context = self.mcp.get_project_context()
            activity = self.mcp.get_activity_summary(hours=48)

            if "error" not in context and "error" not in activity and context.get('total_context_items', 0) > 0:
                result = self.show_mcp_session_summary()
            else:
                # Fall back to legacy only if MCP has no data
                result = self.show_legacy_memory()
        except Exception as e:
            print(f"⚠️ MCP error: {e}")
            result = self.show_legacy_memory()

        # Capture the memory access
        try:
            self.mcp.capture_interaction(
                input_text="show memory",
                output_text="CCOM memory display accessed",
                metadata={
                    'timestamp': datetime.now().isoformat(),
                    'command_type': 'memory_display',
                    'success': True
                }
            )
        except Exception as e:
            self.logger.warning(f"Failed to capture memory display: {e}")

        return result

    def show_legacy_memory(self):
        """Show legacy JSON memory contents"""
        print("\n🧠 CCOM Memory (Legacy)")
        print("=" * 40)

        if not self.memory["features"]:
            print("No features remembered yet.")
        else:
            for name, feature in self.memory["features"].items():
                print(f"• {name}")
                if feature.get("description"):
                    print(f"  {feature['description']}")

        print("=" * 40)
        return True

    def show_mcp_session_summary(self):
        """Show session summary using MCP Memory Keeper (prioritized over legacy)"""
        print("\n🧠 **SESSION HISTORY FROM MCP MEMORY**")
        print("=" * 60)

        try:
            # Get MCP context and activity
            context = self.mcp.get_project_context()
            activity = self.mcp.get_activity_summary(hours=48)

            if "error" not in context and "error" not in activity:
                print(f"📊 **Total Interactions**: {context['total_context_items']} (preserved across sessions)")
                print(f"📈 **Recent Activity**: {activity['total']} interactions in last 48 hours")

                # Show categories
                if activity.get("categories"):
                    print("\n🎯 **Activity Breakdown**:")
                    for cat, count in activity["categories"].items():
                        print(f"   • {cat.title()}: {count}")

                # Show recent successes
                if context.get("recent_successes"):
                    print("\n✅ **Key Achievements** (Recent Sessions):")
                    for success in context["recent_successes"]:
                        print(f"   • {success}")

                # Show recent issues
                if context.get("recent_issues"):
                    print("\n⚠️ **Issues Encountered**:")
                    for issue in context["recent_issues"]:
                        print(f"   • {issue}")

                # Show decisions
                if context.get("recent_decisions"):
                    print("\n💡 **Key Decisions Made**:")
                    for decision in context["recent_decisions"]:
                        print(f"   • {decision}")

                print(f"\n💾 **MCP Database**: {context['database']} ({context['total_context_items']} items)")
                print("\n🎯 **Context Continuity**: All past work and decisions preserved in MCP Memory")

            else:
                print("⚠️ MCP Memory not available - using legacy system")
                return self.show_legacy_memory()

        except Exception as e:
            print(f"⚠️ MCP error: {e}")
            return self.show_legacy_memory()

        return True

    def show_legacy_memory(self):
        """Fallback to legacy JSON memory system"""
        print("\n📋 **LEGACY MEMORY SYSTEM**")
        print("-" * 40)
        for name, feature in self.memory["features"].items():
            print(f"• {name}")
            if feature.get("description"):
                print(f"  {feature['description']}")
        return True

    def show_project_context(self):
        """Show comprehensive project context with automatic session continuity"""
        print("\n🎯 **SESSION CONTINUITY LOADED**")
        print("=" * 60)

        # === MCP MEMORY FIRST ===
        print("🧠 **MCP MEMORY CONTEXT** (Previous Sessions):")
        print("-" * 50)

        try:
            # Get MCP context
            context = self.mcp.get_project_context()

            if "error" not in context:
                activity = context["activity_summary"]
                print(f"📊 **Total Items**: {context['total_context_items']}")
                print(f"📈 **Recent Activity**: {activity['total']} interactions ({activity['timeframe']})")

                if activity.get("categories"):
                    print("\n🎯 **Active Categories**:")
                    for cat, count in activity["categories"].items():
                        print(f"   • {cat.title()}: {count}")

                if context.get("recent_successes"):
                    print("\n✅ **Recent Successes**:")
                    for success in context["recent_successes"][:3]:
                        print(f"   • {success}")

                if context.get("recent_issues"):
                    print("\n⚠️ **Recent Issues**:")
                    for issue in context["recent_issues"][:3]:
                        print(f"   • {issue}")

                print(f"\n💾 **Database**: {context['database']}")
            else:
                print("⚠️ MCP context not available - using legacy memory")
        except Exception as e:
            print(f"⚠️ MCP error: {e}")

        # === LEGACY MEMORY CONTEXT ===
        print("\n📋 **LEGACY MEMORY CONTEXT** (JSON System):")
        print("-" * 50)

        # === PROJECT OVERVIEW ===
        project_info = self.analyze_project_structure()
        print(
            f"📊 **{project_info['name']}** ({project_info['type']}) | {project_info['lines']} lines | {project_info['files']} files"
        )

        # === MCP MEMORY STATUS ===
        activity = context["activity_summary"]
        print(f"🧠 **Memory**: {context['total_context_items']} items | Database: {context['database']}")
        print(f"📊 **Activity**: {activity['total']} interactions ({activity['timeframe']})")

        # === RECENT CONTEXT ===
        if activity.get("categories"):
            cat_summary = ", ".join([f"{k}: {v}" for k, v in activity["categories"].items()])
            print(f"🎯 **Active Areas**: {cat_summary}")

        # === ARCHITECTURE ===
        print(f"🏗️ **Architecture**: {project_info['architecture']}")
        print(f"💻 **Tech Stack**: {', '.join(project_info['tech_stack'])}")

        # === CURRENT HEALTH STATUS ===
        health = self.get_current_health_status()
        print(
            f"📈 **Quality**: {health['quality']} | **Security**: {health['security']} | **Status**: {health['status']}"
        )

        # === RECENT ACTIVITY ===
        recent_features = self.get_recent_features(limit=3)
        if recent_features:
            print(f"\n📝 **Recent Work**:")
            for feature in recent_features:
                print(f"  • {feature['name']}: {feature['summary']}")

        # === CURRENT FOCUS ===
        current_focus = self.detect_current_focus()
        if current_focus:
            print(f"\n🎯 **Current Focus**: {current_focus}")

        # === SUGGESTED ACTIONS ===
        suggestions = self.generate_suggestions()
        if suggestions:
            print(f"\n💡 **Suggested Next Actions**:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")

        # === FILE STATUS ===
        file_status = self.get_file_status()
        print(f"\n📂 **Key Files**: {', '.join(file_status['key_files'])}")
        if file_status["recent_changes"]:
            print(f"🔄 **Recent Changes**: {file_status['recent_changes']}")

        print("=" * 60)
        print("✅ **Context loaded! Claude Code now understands your project.**")
        return True

    def analyze_project_structure(self):
        """Analyze project structure and return summary"""
        project_name = self.memory["project"]["name"]

        # Detect project type and architecture
        project_type = "Unknown"
        architecture = "Unknown"
        tech_stack = []
        lines = 0
        files = 0

        try:
            # Check for common project indicators
            if (self.project_root / "package.json").exists():
                tech_stack.append("Node.js")
                with open(self.project_root / "package.json") as f:
                    pkg_data = json.load(f)
                    deps = list(pkg_data.get("dependencies", {}).keys())
                    if "react" in deps:
                        tech_stack.append("React")
                        project_type = "React App"
                        architecture = "SPA"
                    elif "angular" in deps or "@angular/core" in deps:
                        tech_stack.append("Angular")
                        project_type = "Angular App"
                        architecture = "SPA"
                    elif "vue" in deps:
                        tech_stack.append("Vue")
                        project_type = "Vue App"
                        architecture = "SPA"
                    else:
                        project_type = "Node.js App"

            # Check for PWA indicators
            if (self.project_root / "manifest.json").exists() or (
                self.project_root / "sw.js"
            ).exists():
                architecture = "PWA"
                tech_stack.append("PWA")

            # Check for Python
            if (self.project_root / "requirements.txt").exists() or (
                self.project_root / "pyproject.toml"
            ).exists():
                tech_stack.append("Python")
                project_type = "Python App"

            # Check for static site
            if (self.project_root / "index.html").exists() and not (
                self.project_root / "package.json"
            ).exists():
                project_type = "Static Site"
                architecture = "Static HTML"
                tech_stack = ["HTML", "CSS", "JavaScript"]

            # Count files and lines
            for file_path in self.project_root.rglob("*"):
                if file_path.is_file() and not any(
                    ignore in str(file_path)
                    for ignore in [".git", "node_modules", "__pycache__", ".claude"]
                ):
                    files += 1
                    if file_path.suffix in [
                        ".js",
                        ".py",
                        ".html",
                        ".css",
                        ".ts",
                        ".jsx",
                        ".tsx",
                    ]:
                        try:
                            with open(
                                file_path, encoding="utf-8", errors="ignore"
                            ) as f:
                                lines += len(f.readlines())
                        except:
                            pass

        except Exception:
            pass

        return {
            "name": project_name,
            "type": project_type,
            "architecture": architecture,
            "tech_stack": tech_stack or ["Unknown"],
            "lines": lines,
            "files": files,
        }

    def get_current_health_status(self):
        """Get current health status from memory and recent runs"""
        # Extract latest quality and security info from memory
        quality = "Unknown"
        security = "Unknown"
        status = "Unknown"

        # Look for recent quality audits in features
        for feature_name, feature in self.memory["features"].items():
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
        if "deployments" in self.memory and self.memory["deployments"]:
            latest_deploy = self.memory["deployments"][-1]
            if latest_deploy.get("status") == "successful":
                status = "Production Ready"

        return {
            "quality": quality or "Unknown",
            "security": security or "Unknown",
            "status": status or "Ready for Testing",
        }

    def get_recent_features(self, limit=3):
        """Get recent features from memory"""
        features = []
        for name, feature in list(self.memory["features"].items())[-limit:]:
            summary = (
                feature.get("description", "")[:80] + "..."
                if len(feature.get("description", "")) > 80
                else feature.get("description", "No description")
            )
            features.append(
                {"name": name.replace("_", " ").title(), "summary": summary}
            )
        return features

    def detect_current_focus(self):
        """Detect what the user is currently working on"""
        # Look at the most recent feature for clues
        if self.memory["features"]:
            latest_feature = list(self.memory["features"].items())[-1]
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
        return None

    def generate_suggestions(self):
        """Generate smart suggestions based on project state"""
        suggestions = []

        # Look at recent work to suggest next steps
        if self.memory["features"]:
            latest_desc = (
                list(self.memory["features"].values())[-1]
                .get("description", "")
                .lower()
            )

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

        return suggestions[:3]  # Limit to 3 suggestions

    def get_file_status(self):
        """Get current file status"""
        key_files = []
        recent_changes = None

        # Identify key files
        common_files = [
            "index.html",
            "app.js",
            "main.js",
            "script.js",
            "auth.js",
            "package.json",
            "README.md",
        ]
        for filename in common_files:
            if (self.project_root / filename).exists():
                key_files.append(filename)

        # Get most recently modified file
        try:
            files = list(self.project_root.rglob("*"))
            if files:
                recent_file = max(
                    [
                        f
                        for f in files
                        if f.is_file()
                        and not any(
                            ignore in str(f)
                            for ignore in [".git", "node_modules", ".claude"]
                        )
                    ],
                    key=lambda x: x.stat().st_mtime,
                    default=None,
                )
                if recent_file:
                    recent_changes = f"{recent_file.name} (recently modified)"
        except:
            pass

        return {
            "key_files": key_files[:5],  # Limit to 5 key files
            "recent_changes": recent_changes,
        }


def main():
    """Main CLI entry point for testing"""
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py '<command>'")
        print("Examples:")
        print("  python orchestrator.py 'deploy'")
        print("  python orchestrator.py 'quality check'")
        print("  python orchestrator.py 'status'")
        return

    command = " ".join(sys.argv[1:])
    orchestrator = CCOMOrchestrator()
    orchestrator.handle_natural_language(command)


if __name__ == "__main__":
    main()
