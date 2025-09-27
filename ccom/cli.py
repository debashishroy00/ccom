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
from ccom.mcp_native import get_mcp_integration
from ccom.mcp_integration import MCPDirectIntegration
import io
import contextlib


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
    parser.add_argument("--memory", action="store_true", help="Show MCP memory contents")
    parser.add_argument("--stats", action="store_true", help="Show MCP memory statistics")
    parser.add_argument("--mcp-context", action="store_true", help="Show MCP project context")
    parser.add_argument("--mcp-activity", action="store_true", help="Show MCP activity summary")
    parser.add_argument("--mcp-sessions", action="store_true", help="List recent MCP sessions")
    parser.add_argument("--mcp-start-session", type=str, nargs="?", const="auto", help="Start new MCP session")
    parser.add_argument("--mcp-continue", type=str, help="Continue from specific session ID")
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

    # Context management commands (MCP Memory Keeper integration)
    context_group = parser.add_argument_group("context commands", "Memory and context management")
    context_group.add_argument(
        "--context-note",
        nargs=2,
        metavar=("FEATURE", "NOTE"),
        help="Save a note about a feature: --context-note auth 'Using JWT tokens'",
    )
    context_group.add_argument(
        "--context-resume",
        type=str,
        metavar="FEATURE",
        help="Resume work on a feature with context: --context-resume auth",
    )
    context_group.add_argument(
        "--context-search",
        type=str,
        metavar="QUERY",
        help="Search context: --context-search 'JWT token'",
    )
    context_group.add_argument(
        "--context-checkpoint",
        nargs="?",
        const=True,
        metavar="NAME",
        help="Create a context checkpoint: --context-checkpoint [name]",
    )
    context_group.add_argument(
        "--context-status",
        action="store_true",
        help="Show memory status and statistics",
    )
    context_group.add_argument(
        "--context-summary",
        nargs="?",
        const=24,
        type=int,
        metavar="HOURS",
        help="Show intelligent summary of recent work (default: 24 hours)",
    )
    context_group.add_argument(
        "--universal-memory",
        action="store_true",
        help="Show recent memory (like mem0) - all captured interactions",
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
    elif args.mcp_context:
        handle_mcp_context_command()
        return True
    elif args.mcp_activity:
        handle_mcp_activity_command()
        return True
    elif args.mcp_sessions:
        handle_mcp_sessions_command()
        return True
    elif args.mcp_start_session:
        handle_mcp_start_session_command(args.mcp_start_session)
        return True
    elif args.mcp_continue:
        handle_mcp_continue_command(args.mcp_continue)
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

    # Handle context commands (MCP Memory Keeper integration)
    elif args.context_note:
        handle_context_note(args.context_note[0], args.context_note[1])
        return True
    elif args.context_resume:
        handle_context_resume(args.context_resume)
        return True
    elif args.context_search:
        handle_context_search(args.context_search)
        return True
    elif args.context_checkpoint:
        name = args.context_checkpoint if args.context_checkpoint != True else None
        handle_context_checkpoint(name)
        return True
    elif args.context_status:
        handle_context_status()
        return True
    elif args.context_summary is not None:
        handle_context_summary(args.context_summary)
        return True
    elif args.universal_memory:
        handle_universal_memory()
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


def handle_context_note(feature: str, note: str):
    """Save a note about a feature to memory (Phase 1: MCP Direct Integration)"""
    try:
        # Phase 1: Use MCP Direct Integration instead of bridge
        mcp_direct = MCPDirectIntegration()
        success = mcp_direct.save_context_note(feature, note, "note")

        if success:
            print(f"✅ Saved note for {feature}: {note}")
        else:
            print(f"❌ Failed to save note for {feature}")
    except Exception as e:
        print(f"❌ Error saving context: {e}")


def handle_context_resume(feature: str):
    """Resume work on a feature with full context (Phase 1: MCP Direct Integration)"""
    try:
        # Phase 1: Use MCP Direct Integration
        mcp_direct = MCPDirectIntegration()
        print(f"🧠 **Resuming work on: {feature}**\n")

        context = mcp_direct.get_feature_context(feature)
        # MCP Direct shows context via print statements to Claude
        print("💡 Claude should display the MCP context above.")
    except Exception as e:
        print(f"❌ Error retrieving context: {e}")


def handle_context_search(query: str):
    """Search context across all features"""
    try:
        bridge = MCPMemoryBridge()
        results = bridge.search_context(query, limit=10)

        if results:
            print(f"🔍 **Search results for: {query}**\n")
            for item in results:
                timestamp = item.get('timestamp', '')[:16].replace('T', ' ')
                category = item.get('category', 'note').upper()
                content = item.get('value', '')[:100] + ('...' if len(item.get('value', '')) > 100 else '')
                print(f"[{timestamp}] {category}: {content}")
        else:
            print(f"No results found for: {query}")
    except Exception as e:
        print(f"❌ Error searching context: {e}")


def handle_context_checkpoint(name: str = None):
    """Create a checkpoint of current context"""
    try:
        bridge = MCPMemoryBridge()
        checkpoint_name = bridge.create_checkpoint(name)

        if checkpoint_name:
            print(f"✅ Checkpoint created: {checkpoint_name}")
            print(f"💡 Use this key to restore: {checkpoint_name}")
        else:
            print("❌ Failed to create checkpoint")
    except Exception as e:
        print(f"❌ Error creating checkpoint: {e}")


def handle_context_status():
    """Show memory status and statistics"""
    try:
        bridge = MCPMemoryBridge()
        stats = bridge.get_statistics()

        print(f"💾 **Memory Status for {bridge.project_name}**\n")
        print(f"Total Items: {stats['total_items']}")

        if stats['categories']:
            print(f"\nBy Category:")
            for cat, count in sorted(stats['categories'].items()):
                print(f"  • {cat}: {count}")

        if stats['priorities']:
            print(f"\nBy Priority:")
            for pri, count in sorted(stats['priorities'].items()):
                print(f"  • {pri}: {count}")

        if stats['channels']:
            print(f"\nChannels: {', '.join(stats['channels'])}")

        if stats['checkpoints']:
            print(f"\nCheckpoints: {stats['checkpoints']}")

        if stats['total_items'] == 0:
            print("\n💡 Context will be captured automatically as you use CCOM commands")
            print("   Manual tracking: ccom --context-note <feature> '<note>'")
    except Exception as e:
        print(f"❌ Error getting status: {e}")


def handle_context_summary(hours: int = 24):
    """Show intelligent summary of recent work"""
    try:
        bridge = MCPMemoryBridge()
        summary = bridge.get_intelligent_summary(hours)
        print(summary)
    except Exception as e:
        print(f"❌ Error generating summary: {e}")


def handle_universal_memory():
    """Show universal memory like mem0 - all captured interactions"""
    try:
        universal = get_universal_capture()
        context = universal.get_recent_context(hours=24)

        print("🧠 **Universal Memory (Last 24h)** - Like mem0\n")

        print(f"📊 **Activity Overview:**")
        print(f"  Total interactions: {context['total_interactions']}")

        if context['features']:
            print(f"\n🎯 **Active Features:**")
            for feature, count in sorted(context['features'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {feature}: {count} interactions")

        if context['key_facts']:
            print(f"\n💡 **Key Facts:**")
            for fact in context['key_facts'][:5]:
                print(f"  • {fact}")

        if context['issues']:
            print(f"\n⚠️  **Issues Found:**")
            for issue in context['issues'][:3]:
                print(f"  • {issue}")

        if context['successes']:
            print(f"\n✅ **Recent Successes:**")
            for success in context['successes'][:3]:
                print(f"  • {success}")

        if context['total_interactions'] == 0:
            print("No interactions captured yet. Use CCOM commands to start building memory!")

    except Exception as e:
        print(f"❌ Error accessing universal memory: {e}")


def capture_command_execution(command_text: str, orchestrator):
    """
    Universal capture wrapper - captures ALL command output like mem0.
    No pattern matching needed - just capture everything!
    """
    # Capture stdout to get complete output
    captured_output = io.StringIO()

    try:
        # Redirect stdout to capture all output
        with contextlib.redirect_stdout(captured_output):
            # Execute the command
            result = orchestrator.handle_natural_language(command_text)

        # Get the captured output
        output_text = captured_output.getvalue()

        # If no output was captured, create a simple status message
        if not output_text.strip():
            output_text = "Command executed" if result else "Command failed"

        # Use MCP native integration to save everything
        mcp = get_mcp_integration()
        mcp.capture_interaction(
            input_text=command_text,
            output_text=output_text,
            metadata={
                'success': bool(result),
                'command_type': 'natural_language'
            }
        )

        # Print the output to user (since we captured it)
        print(output_text)

        return result

    except Exception as e:
        error_output = f"❌ Error executing command: {e}"
        print(error_output)

        # Still capture the error
        universal_capture = get_universal_capture()
        universal_capture.capture_interaction(
            input_text=command_text,
            output_text=error_output,
            metadata={
                'success': False,
                'error': str(e),
                'command_type': 'natural_language'
            }
        )

        return False


def setup_session_continuity(claude_dir):
    """Setup SessionStart hook for automatic context loading"""
    try:
        import shutil
        import json

        # Create hooks directory
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        # Copy session start hook template
        ccom_dir = Path(__file__).parent.parent
        template_file = ccom_dir / "ccom" / "templates" / "session_start_hook.py"
        hook_file = hooks_dir / "session_start.py"

        if template_file.exists():
            shutil.copy2(template_file, hook_file)
            # Make executable on Unix systems
            hook_file.chmod(0o755)
            print("✅ Installed SessionStart hook")
        else:
            print("⚠️ SessionStart hook template not found")

        # Update settings.local.json to include hook configuration
        settings_file = claude_dir / "settings.local.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
        else:
            settings = {}

        # Add SessionStart hook configuration
        if 'hooks' not in settings:
            settings['hooks'] = {}

        settings['hooks']['SessionStart'] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "python .claude/hooks/session_start.py"
                    }
                ]
            }
        ]

        # Write updated settings
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)

        print("✅ Configured automatic session continuity")
        print("💡 New Claude Code sessions will automatically load project context")

    except Exception as e:
        print(f"⚠️ Session continuity setup failed: {e}")

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

    # Create .ccom directory for MCP bridge and monitoring
    ccom_bridge_dir = current_dir / ".ccom"
    ccom_bridge_dir.mkdir(exist_ok=True)

    # Copy all CCOM files from installation
    ccom_dir = Path(__file__).parent.parent
    source_claude = ccom_dir / ".claude"
    templates_dir = ccom_dir / "ccom" / "templates"

    import shutil

    # Copy core CCOM JavaScript files
    core_files = ["ccom.js", "auto-load.js", "cco.js"]
    for file_name in core_files:
        template_file = templates_dir / file_name
        if template_file.exists():
            # Copy to .claude directory
            claude_dest = claude_dir / file_name
            shutil.copy2(template_file, claude_dest)

            # Also copy to .ccom directory for Claude Code compatibility
            ccom_dest = ccom_bridge_dir / file_name
            shutil.copy2(template_file, ccom_dest)

            print(f"✅ Installed {file_name} in both .claude and .ccom directories")
        else:
            print(f"⚠️ Template {file_name} not found")

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

    # Session continuity is available via 'ccom what did we discuss' - no automatic hooks
    # Users can enable SessionStart hooks manually if desired
    # setup_session_continuity(claude_dir)

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


def handle_mcp_memory_command():
    """Handle MCP memory display command"""
    try:
        mcp = get_mcp_integration()
        context = mcp.get_context(limit=20)

        if not context:
            print("🧠 **MCP Memory**: No context stored yet")
            return

        print("\n🧠 **MCP MEMORY** (Recent Context)")
        print("=" * 50)

        for item in context:
            timestamp = item.get('created_at', 'Unknown')[:16]
            category = item.get('category', 'unknown').title()
            key = item.get('key', 'Unknown')
            value = item.get('value', '')[:100]

            print(f"📝 [{timestamp}] {category}: {key}")
            print(f"   💬 {value}...")
            print()

    except Exception as e:
        print(f"❌ Error accessing MCP memory: {e}")

def handle_mcp_context_command():
    """Handle MCP project context command"""
    try:
        mcp = get_mcp_integration()
        context = mcp.get_project_context()

        print("\n🎯 **MCP PROJECT CONTEXT**")
        print("=" * 50)

        if "error" in context:
            print(f"❌ Error: {context['error']}")
            return

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

    except Exception as e:
        print(f"❌ Error accessing MCP context: {e}")

def handle_mcp_activity_command():
    """Handle MCP activity summary command"""
    try:
        mcp = get_mcp_integration()
        activity = mcp.get_activity_summary(hours=24)

        print("\n📊 **MCP ACTIVITY SUMMARY** (Last 24h)")
        print("=" * 50)

        if "error" in activity:
            print(f"❌ Error: {activity['error']}")
            return

        print(f"📈 **Total Interactions**: {activity['total']}")

        if activity.get("categories"):
            print("\n🎯 **By Category**:")
            for cat, count in activity["categories"].items():
                print(f"   • {cat.title()}: {count}")

        if activity.get("recent_successes"):
            print("\n✅ **Recent Successes**:")
            for success in activity["recent_successes"]:
                print(f"   • {success}")

        if activity.get("recent_errors"):
            print("\n❌ **Recent Errors**:")
            for error in activity["recent_errors"]:
                print(f"   • {error}")

    except Exception as e:
        print(f"❌ Error accessing MCP activity: {e}")

def handle_mcp_sessions_command():
    """Handle MCP sessions list command"""
    try:
        mcp = get_mcp_integration()
        sessions = mcp.list_sessions(limit=10)

        print("\n📅 **MCP SESSIONS** (Recent)")
        print("=" * 50)

        if not sessions:
            print("🔍 No sessions found")
            return

        for session in sessions:
            session_id = session.get('id', 'Unknown')[:8]
            name = session.get('name', 'Unnamed Session')
            created = session.get('created_at', 'Unknown')[:16]

            print(f"📝 [{session_id}] {name}")
            print(f"   📅 Created: {created}")
            print()

        print(f"💡 **Use**: ccom --mcp-continue <session_id> to restore context")

    except Exception as e:
        print(f"❌ Error listing MCP sessions: {e}")

def handle_mcp_start_session_command(session_name):
    """Handle MCP start session command"""
    try:
        mcp = get_mcp_integration()

        if session_name == "auto":
            session_name = None  # Use auto-generated name

        result = mcp.start_session(session_name)

        if "error" not in result:
            print("✅ **MCP Session Started Successfully**")
            if result.get("id"):
                print(f"🆔 **Session ID**: {result['id'][:8]}...")
                print(f"📅 **Created**: {result.get('created_at', 'Now')[:16]}")
        else:
            print(f"❌ Failed to start session: {result['error']}")

    except Exception as e:
        print(f"❌ Error starting MCP session: {e}")

def handle_mcp_continue_command(session_id):
    """Handle MCP continue session command"""
    try:
        mcp = get_mcp_integration()

        # Start new session continuing from the specified one
        result = mcp.start_session(
            session_name=f"Continued Session",
            continue_from=session_id
        )

        if "error" not in result:
            print("📖 **MCP Session Continued Successfully**")
            print(f"🔗 **Continuing from**: {session_id}")
            if result.get("id"):
                print(f"🆔 **New Session ID**: {result['id'][:8]}...")

            # Show restored context
            context = mcp.get_session_context(session_id)
            if context.get("context_items"):
                print(f"📊 **Restored**: {len(context['context_items'])} context items")
        else:
            print(f"❌ Failed to continue session: {result['error']}")

    except Exception as e:
        print(f"❌ Error continuing MCP session: {e}")

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

            # Universal capture - capture EVERYTHING like mem0
            captured_output = capture_command_execution(command_text, orchestrator)
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
