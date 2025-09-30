#!/usr/bin/env python3
"""
Traditional Commands Handler
Handles basic CCOM commands and natural language processing
"""

from .base import BaseHandler
from ...utils import Display
from ...legacy.tools_manager import ToolsManager


class TraditionalHandler(BaseHandler):
    """
    Handles traditional CCOM commands

    Responsibilities:
    - Natural language command processing
    - Basic status and initialization
    - Legacy command compatibility
    """

    def can_handle(self, args) -> bool:
        """Check if this handler can process the arguments"""
        return (
            (args.command is not None and len(args.command) > 0) or
            args.status or
            args.init
        )

    def handle(self, args) -> bool:
        """Handle traditional commands"""
        try:
            # Natural language command
            if args.command and len(args.command) > 0:
                # Join command arguments into a single string
                command_string = " ".join(args.command)
                return self._handle_natural_language(command_string, args)

            # Status command
            if args.status:
                return self.orchestrator.show_status()

            # Initialization command
            if args.init:
                return self._handle_init(args)

            return False

        except Exception as e:
            self.logger.error(f"Traditional command handling failed: {e}")
            Display.error(f"Command execution failed: {str(e)}")
            return False

    def _handle_natural_language(self, command: str, args) -> bool:
        """Handle natural language command with optional modifiers"""
        # Apply command modifiers
        context = self._build_context_from_args(args)

        # Handle streaming mode
        if hasattr(args, 'streaming') and args.streaming:
            context['streaming'] = True
            Display.info("Streaming mode enabled - real-time feedback")

        # Handle forced modes
        if hasattr(args, 'force_sdk') and args.force_sdk:
            context['force_mode'] = 'sdk'
            Display.info("Forcing SDK agent mode")
        elif hasattr(args, 'force_legacy') and args.force_legacy:
            context['force_mode'] = 'legacy'
            Display.info("Forcing legacy agent mode")

        # Execute natural language command
        return self.orchestrator.handle_natural_language(command)

    def _handle_init(self, args) -> bool:
        """Handle initialization command"""
        Display.workflow_start("Initialization")

        try:
            force = getattr(args, 'force', False)

            if force:
                Display.warning("Force initialization - existing configuration will be overwritten")

            # Enhanced initialization logic
            config_created = self._create_basic_config(force)
            memory_initialized = self._initialize_memory(force)
            tools_installed = self._install_development_tools(force)

            if config_created and memory_initialized and tools_installed:
                Display.workflow_complete("Initialization", True)
                Display.success("CCOM initialized successfully")
                Display.info("Use 'ccom --status' to verify configuration")
                Display.info("Use 'ccom check tools' to verify tool installation")
                return True
            else:
                Display.workflow_complete("Initialization", False)
                return False

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            Display.workflow_complete("Initialization", False)
            return False

    def _create_basic_config(self, force: bool = False) -> bool:
        """Create basic CCOM configuration"""
        try:
            claude_dir = self.orchestrator.project_root / ".claude"

            # Check if already exists
            if claude_dir.exists() and not force:
                Display.info("CCOM configuration already exists")
                return True

            # Create directory structure
            claude_dir.mkdir(exist_ok=True)
            (claude_dir / "agents").mkdir(exist_ok=True)

            Display.success("Configuration directory created")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create config: {e}")
            Display.error("Failed to create configuration")
            return False

    def _initialize_memory(self, force: bool = False) -> bool:
        """Initialize memory system"""
        try:
            # Memory is automatically initialized by MemoryManager
            memory_stats = self.orchestrator.memory_manager.get_memory_stats()

            if memory_stats.get("total_features", 0) > 0 and not force:
                Display.info("Memory system already contains data")
            else:
                Display.success("Memory system initialized")

            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize memory: {e}")
            Display.error("Failed to initialize memory")
            return False

    def _install_development_tools(self, force: bool = False) -> bool:
        """Install development tools using the legacy tools manager"""
        try:
            Display.section("🔧 Development Tools Setup")
            Display.progress("Detecting project type and installing required tools...")

            # Initialize tools manager
            tools_manager = ToolsManager(self.orchestrator.project_root)

            # Check current tool status
            Display.info("Checking existing tool installation...")
            status = tools_manager.get_installation_status()

            project_type = status.get("project_type", "unknown")
            Display.info(f"Detected project type: {project_type}")

            if status["missing_tools"]:
                Display.info(f"Installing {len(status['missing_tools'])} missing tools...")
                Display.progress(f"Tools to install: {', '.join(status['missing_tools'])}")

                # Install missing tools
                success = tools_manager.install_missing_tools(force=force)

                if success:
                    Display.success("✅ Development tools installed successfully!")

                    # Show final status
                    final_status = tools_manager.get_installation_status()
                    Display.info(f"Tools installed: {len(final_status['installed_tools'])}/{final_status['total_required']}")

                    if final_status['installed_tools']:
                        Display.info(f"Available tools: {', '.join(final_status['installed_tools'])}")

                    return True
                else:
                    Display.warning("⚠️ Some tools failed to install but basic configuration was created")
                    return True  # Don't fail initialization completely
            else:
                Display.success("✅ All required development tools are already installed!")

                # Still ensure configurations are up to date
                Display.progress("Verifying tool configurations...")
                tools_manager.install_missing_tools(force=False)  # This will update configs

                return True

        except Exception as e:
            self.logger.error(f"Failed to install development tools: {e}")
            Display.error(f"Tool installation failed: {str(e)}")
            Display.warning("⚠️ Continuing initialization without tool installation")
            return True  # Don't fail initialization completely

    def _build_context_from_args(self, args) -> dict:
        """Build execution context from command line arguments"""
        context = {}

        # Add verbose flag
        if hasattr(args, 'verbose') and args.verbose:
            context['verbose'] = True

        # Add dry run flag
        if hasattr(args, 'dry_run') and args.dry_run:
            context['dry_run'] = True

        return context