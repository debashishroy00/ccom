#!/usr/bin/env python3
"""
Enhanced CCOM CLI v0.3 - Vibe Coder Interface
Advanced natural language processing and enterprise automation
"""

import sys
import argparse
from pathlib import Path
from ccom.orchestrator import CCOMOrchestrator
from ccom.tools_manager import ToolsManager


def create_enhanced_cli():
    """Create enhanced CLI with natural language support"""
    parser = argparse.ArgumentParser(
        description="CCOM v0.3 - Claude Code Orchestrator and Memory",
        epilog="Natural language examples: ccom deploy my app, ccom check security, ccom quality audit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Add natural language support
    parser.add_argument(
        "command", nargs="*", help="Natural language command or traditional command"
    )

    # Traditional commands
    parser.add_argument(
        "--status", action="store_true", help="Show CCOM and project status"
    )
    parser.add_argument("--memory", action="store_true", help="Show memory contents")
    parser.add_argument("--stats", action="store_true", help="Show memory statistics")
    parser.add_argument(
        "--remember", type=str, help='Remember a feature: --remember "auth system"'
    )
    parser.add_argument(
        "--init", action="store_true", help="Initialize CCOM in current directory"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force refresh CCOM configuration even if v0.3 exists",
    )

    # File monitoring commands
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Start file monitoring for real-time quality enforcement",
    )
    parser.add_argument(
        "--monitor-config",
        action="store_true",
        help="Show file monitoring configuration",
    )

    # Workflow commands
    parser.add_argument(
        "--workflow",
        type=str,
        choices=["quality", "security", "deploy", "full", "setup"],
        help="Run CCOM workflow automation",
    )

    # Tool management commands
    parser.add_argument(
        "--install-tools",
        action="store_true",
        help="Install all required development tools for the project",
    )
    parser.add_argument(
        "--check-tools",
        action="store_true",
        help="Check installation status of all development tools",
    )
    parser.add_argument(
        "--tools-status",
        action="store_true",
        help="Show comprehensive tools status report",
    )

    # Advanced options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output for debugging"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    return parser


def handle_traditional_commands(args, orchestrator):
    """Handle traditional flag-based commands"""
    if args.status:
        orchestrator.show_status()
        return True
    elif args.memory:
        orchestrator.show_memory()
        return True
    elif args.remember:
        orchestrator.handle_memory_command(f"remember {args.remember}")
        return True
    elif args.init:
        init_ccom_project(force=args.force)
        return True
    elif args.watch:
        orchestrator.start_file_monitoring()
        return True
    elif args.monitor_config:
        orchestrator.show_file_monitoring_config()
        return True
    elif args.workflow:
        orchestrator.run_workflow(args.workflow)
        return True
    elif args.install_tools:
        handle_install_tools_command(args.force)
        return True
    elif args.check_tools:
        handle_check_tools_command()
        return True
    elif args.tools_status:
        handle_tools_status_command()
        return True

    return False


def handle_install_tools_command(force=False):
    """Handle tool installation command"""
    try:
        print("🔧 **CCOM TOOLS INSTALLER** – Setting up development environment...")
        tools_manager = ToolsManager()

        success = tools_manager.install_missing_tools(force=force)

        if success:
            print("\n🎉 Tool installation completed successfully!")
            print(
                "💡 Your development environment is now ready for quality validation."
            )
        else:
            print(
                "\n❌ Some tools failed to install. Check the output above for details."
            )

    except Exception as e:
        print(f"❌ Tool installation error: {e}")


def handle_check_tools_command():
    """Handle tool checking command"""
    try:
        print("🔍 **CCOM TOOLS CHECKER** – Verifying tool installation...")
        tools_manager = ToolsManager()

        installed_tools = tools_manager.check_tool_availability(force_refresh=True)
        required_tools = tools_manager.get_tools_for_project()

        print(f"\n📊 Tool Status Report:")
        print(
            f"Project Type: {tools_manager.tools_state.get('project_type', 'unknown')}"
        )
        print(f"Required Tools: {len(required_tools)}")

        installed_count = sum(
            1
            for tool in required_tools
            if installed_tools.get(tool, {}).get("installed", False)
        )
        print(f"Installed: {installed_count}/{len(required_tools)}")

        if installed_count == len(required_tools):
            print("✅ All required tools are installed!")
        else:
            missing = [
                tool
                for tool in required_tools
                if not installed_tools.get(tool, {}).get("installed", False)
            ]
            print(f"❌ Missing tools: {', '.join(missing)}")
            print("💡 Run 'ccom --install-tools' to install missing tools")

    except Exception as e:
        print(f"❌ Tool check error: {e}")


def handle_tools_status_command():
    """Handle comprehensive tools status command"""
    try:
        print(
            "📋 **CCOM TOOLS STATUS** – Comprehensive development environment report..."
        )
        tools_manager = ToolsManager()

        status = tools_manager.get_installation_status()

        print(f"\n🎯 Project Analysis:")
        print(f"  Type: {status['project_type']}")
        print(f"  Required Tools: {status['total_required']}")
        print(f"  Installed: {status['installed_count']}/{status['total_required']}")

        completion = (
            (status["installed_count"] / status["total_required"] * 100)
            if status["total_required"] > 0
            else 0
        )
        print(f"  Completion: {completion:.0f}%")

        if status["installed_tools"]:
            print(f"\n✅ Installed Tools ({len(status['installed_tools'])}):")
            for tool in status["installed_tools"]:
                print(f"  • {tool}")

        if status["missing_tools"]:
            print(f"\n❌ Missing Tools ({len(status['missing_tools'])}):")
            for tool in status["missing_tools"]:
                print(f"  • {tool}")

        print(f"\n⚙️ Configuration Files:")
        configs = status["configurations"]
        for config_name, exists in configs.items():
            status_icon = "✅" if exists else "❌"
            print(f"  {status_icon} {config_name}")

        if status["missing_tools"]:
            print(f"\n💡 Next Steps:")
            print(f"  Run: ccom --install-tools")
            print(f"  This will install missing tools and generate config files")
        else:
            print(f"\n🎉 Development environment is fully configured!")

    except Exception as e:
        print(f"❌ Status report error: {e}")


def init_ccom_project(force=False):
    """Initialize CCOM v0.3 in current project"""
    print("🚀 Initializing CCOM v0.3 in current project...")

    current_dir = Path.cwd()
    claude_dir = current_dir / ".claude"

    # Create directories
    claude_dir.mkdir(exist_ok=True)
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    configs_dir = claude_dir / "configs"
    configs_dir.mkdir(exist_ok=True)
    validators_dir = claude_dir / "validators"
    validators_dir.mkdir(exist_ok=True)

    # Copy all CCOM files from installation
    ccom_dir = Path(__file__).parent.parent
    source_claude = ccom_dir / ".claude"

    import shutil

    # Copy agents
    source_agents = source_claude / "agents"
    if source_agents.exists():
        for agent_file in source_agents.glob("*.md"):
            dest_file = agents_dir / agent_file.name
            shutil.copy2(agent_file, dest_file)
            print(f"✅ Installed agent: {agent_file.name}")

    # Copy RAG configurations
    source_configs = source_claude / "configs"
    if source_configs.exists():
        for config_file in source_configs.glob("*"):
            if config_file.is_file():
                dest_file = configs_dir / config_file.name
                shutil.copy2(config_file, dest_file)
                print(f"✅ Installed RAG config: {config_file.name}")

    # Copy RAG validators
    source_validators = source_claude / "validators"
    if source_validators.exists():
        for validator_file in source_validators.glob("*"):
            if validator_file.is_file():
                dest_file = validators_dir / validator_file.name
                shutil.copy2(validator_file, dest_file)
                print(f"✅ Installed RAG validator: {validator_file.name}")

    # Handle CLAUDE.md - backup existing and create v0.3
    claude_md = current_dir / "CLAUDE.md"
    if claude_md.exists():
        # Check if it's already v0.3
        try:
            with open(claude_md, "r", encoding="utf-8") as f:
                content = f.read()

            if "CCOM Integration for Claude Code v0.3" in content and not force:
                print(
                    "✅ CLAUDE.md already v0.3 configuration (use --force to refresh)"
                )
            else:
                # Backup existing file
                backup_path = current_dir / "CLAUDE.md.bak"
                import shutil

                shutil.copy2(claude_md, backup_path)
                print(f"⚠️  Backed up existing CLAUDE.md to CLAUDE.md.bak")

                # Create v0.3 configuration
                create_enhanced_claude_md(claude_md)
                print("✅ Updated CLAUDE.md to v0.3 configuration")
        except Exception as e:
            print(f"⚠️  Error reading CLAUDE.md: {e}")
            # Backup existing file before creating new one
            backup_path = current_dir / "CLAUDE.md.bak"
            import shutil

            shutil.copy2(claude_md, backup_path)
            print(f"⚠️  Backed up existing CLAUDE.md to CLAUDE.md.bak")

            create_enhanced_claude_md(claude_md)
            print("✅ Created new CLAUDE.md v0.3 configuration")
    else:
        create_enhanced_claude_md(claude_md)
        print("✅ Created CLAUDE.md v0.3 configuration")

    # Initialize memory
    orchestrator = CCOMOrchestrator()
    orchestrator.save_memory()
    print("✅ Initialized memory system")

    # Install development tools
    print("\n🔧 Setting up development tools...")
    try:
        tools_manager = ToolsManager(current_dir)
        tools_manager.install_missing_tools(force=False)
        print("✅ Development tools configured")
    except Exception as e:
        print(f"⚠️ Tool setup encountered issues: {e}")
        print("💡 Run 'ccom --install-tools' later to complete setup")

    print("\n🎉 CCOM v0.3 initialized successfully!")
    print("\n📖 Try these CCOM commands:")
    print("  ccom deploy my app")
    print("  ccom check security")
    print("  ccom quality audit")
    print("  ccom --status")
    print("\n🧠 NEW: Enterprise RAG workflows (natural language):")
    print("  ccom validate my rag system       # Complete RAG validation")
    print("  ccom check vectors                # ChromaDB, Weaviate, FAISS")
    print("  ccom validate graph database      # Neo4j, ArangoDB security")
    print("  ccom check hybrid search          # Fusion & reranking")
    print("  ccom validate agents              # ReAct, CoT, tool safety")
    print(
        "\n💡 CCOM only activates with 'ccom' prefix - regular Claude Code otherwise!"
    )


def create_enhanced_claude_md(claude_md_path):
    """Create enhanced CLAUDE.md by copying from the CCOM development template"""
    from pathlib import Path
    import os

    # Find the CCOM package installation directory
    try:
        # Try to find the source CLAUDE.md from the development directory
        current_file = Path(__file__).resolve()
        ccom_dev_dir = (
            current_file.parent.parent
        )  # Go up from ccom/cli.py to project root
        source_claude_md = ccom_dev_dir / "CLAUDE.md"

        if source_claude_md.exists():
            # Read the actual CLAUDE.md from development repo
            with open(source_claude_md, "r", encoding="utf-8") as f:
                content = f.read()

            # Write to destination
            with open(claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"📋 Copied CLAUDE.md from: {source_claude_md}")
        else:
            # Fallback: Use a minimal template if source not found
            content = """# CCOM Integration for Claude Code v0.3

**ARCHITECTURE**: CCOM provides the orchestration layer that Claude Code lacks.
- **Claude Code**: Context, templates, interactive assistance, agent specifications
- **CCOM**: Native execution, orchestration, automation, enterprise workflows

**IMPORTANT**: Only activate CCOM functionality when user message starts with "ccom" (case-insensitive).

## CCOM Command Processing

For full documentation, see the CCOM development repository.
"""
            with open(claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"⚠️  Using fallback template - source not found: {source_claude_md}")

    except Exception as e:
        print(f"❌ Error creating CLAUDE.md: {e}")
        # Create minimal working version
        content = '# CCOM Integration for Claude Code v0.3\n\n**IMPORTANT**: Only activate CCOM functionality when user message starts with "ccom".'
        with open(claude_md_path, "w", encoding="utf-8") as f:
            f.write(content)


def show_help():
    """Show enhanced help with examples"""
    print(
        """
🚀 CCOM v0.3 - Claude Code Orchestrator and Memory

🎯 PREFIX-BASED ACTIVATION:
  Only commands starting with "ccom" activate CCOM functionality
  All other commands use regular Claude Code behavior

NATURAL LANGUAGE COMMANDS (Recommended):
  ccom deploy my app                → Enterprise deployment pipeline
  ccom check security               → Comprehensive security audit
  ccom quality audit                → Code quality analysis
  ccom make it secure               → Security hardening
  ccom ship it to production        → Full deployment sequence

TRADITIONAL COMMANDS:
  ccom --status                     → Show project status
  ccom --memory                     → Show remembered features
  ccom --remember "feature name"    → Add feature to memory
  ccom --init                       → Initialize/refresh CCOM in project

TOOL MANAGEMENT:
  ccom --install-tools              → Install all required development tools
  ccom --check-tools                → Check tool installation status
  ccom --tools-status               → Show comprehensive tools report

EXAMPLES:
  ccom "deploy"                     → Quick deployment
  ccom "security scan"              → Security check
  ccom "fix quality issues"         → Auto-fix code quality
  ccom --status                     → Traditional status check

ENTERPRISE FEATURES:
  ✅ Claude Code native integration (prefix-based activation)
  ✅ Visual engagement indicators (clear CCOM vs regular CC)
  ✅ Multi-agent orchestration (quality, security, deployment)
  ✅ TodoWrite integration (systematic workflow tracking)
  ✅ Memory system (cross-session feature tracking)
  ✅ Enterprise security scanning (vulnerability detection)
  ✅ Production deployment pipeline (zero-downtime)

For more info: https://github.com/your-repo/ccom
"""
    )


def main():
    """Enhanced main CLI entry point"""
    parser = create_enhanced_cli()

    # Handle no arguments
    if len(sys.argv) == 1:
        show_help()
        return

    args = parser.parse_args()

    try:
        orchestrator = CCOMOrchestrator()

        # Handle traditional commands first
        if handle_traditional_commands(args, orchestrator):
            return

        # Handle natural language commands
        if args.command:
            command_text = " ".join(args.command)

            if args.verbose:
                print(f"🔍 Processing: '{command_text}'")

            if args.dry_run:
                print(f"🧪 Dry run: Would execute '{command_text}'")
                return

            orchestrator.handle_natural_language(command_text)
        else:
            print("❓ No command provided. Use 'ccom --help' for usage.")

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    main()
