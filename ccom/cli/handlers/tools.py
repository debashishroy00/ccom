#!/usr/bin/env python3
"""
Tools Commands Handler
Handles development tool management
"""

from .base import BaseHandler
from ...utils import Display
from ...legacy.tools_manager import ToolsManager


class ToolsHandler(BaseHandler):
    """
    Handles tool management commands

    Responsibilities:
    - Tool installation and checking
    - Development environment setup
    - Tool status reporting
    """

    def can_handle(self, args) -> bool:
        """Check if this handler can process the arguments"""
        return (
            args.install_tools or
            args.check_tools or
            args.tools_status
        )

    def handle(self, args) -> bool:
        """Handle tools commands"""
        try:
            if args.install_tools:
                return self._handle_install_tools()
            elif args.check_tools:
                return self._handle_check_tools()
            elif args.tools_status:
                return self._handle_tools_status()

            return False

        except Exception as e:
            self.logger.error(f"Tools command handling failed: {e}")
            Display.error(f"Tools operation failed: {str(e)}")
            return False

    def _handle_install_tools(self) -> bool:
        """Handle install tools command"""
        try:
            Display.progress("Installing development tools...")

            # Initialize tools manager
            tools_manager = ToolsManager(self.orchestrator.project_root)

            # Install tools
            success = tools_manager.install_missing_tools(force=True)

            if success:
                Display.success("Development tools installation completed")

                # Show status
                status = tools_manager.get_installation_status()
                Display.info(f"Tools installed: {len(status['installed_tools'])}/{status['total_required']}")

                return True
            else:
                Display.warning("Some tools failed to install")
                return False

        except Exception as e:
            self.logger.error(f"Tool installation failed: {e}")
            Display.error(f"Tool installation failed: {str(e)}")
            return False

    def _handle_check_tools(self) -> bool:
        """Handle check tools command"""
        try:
            Display.progress("Checking tool installation status...")

            # Initialize tools manager
            tools_manager = ToolsManager(self.orchestrator.project_root)

            # Check tools
            installed_tools = tools_manager.check_tool_availability()
            required_tools = tools_manager.get_tools_for_project()

            Display.section("🔧 Development Tools Status")

            for tool in required_tools:
                status = installed_tools.get(tool, {})
                if status.get("installed", False):
                    version = status.get("version", "unknown")
                    scope = status.get("scope", "")
                    scope_text = f" ({scope})" if scope else ""
                    Display.info(f"✅ {tool}: {version}{scope_text}")
                else:
                    Display.warning(f"❌ {tool}: Not installed")

            # Show project info
            project_type = tools_manager.tools_state.get("project_type", "unknown")
            Display.info(f"\nProject type: {project_type}")

            missing_count = len([t for t in required_tools if not installed_tools.get(t, {}).get("installed", False)])
            if missing_count == 0:
                Display.success("All required tools are installed")
            else:
                Display.warning(f"{missing_count} tools are missing - run 'ccom --install-tools' to install them")

            return True

        except Exception as e:
            self.logger.error(f"Tool check failed: {e}")
            Display.error(f"Tool check failed: {str(e)}")
            return False

    def _handle_tools_status(self) -> bool:
        """Handle tools status command"""
        try:
            Display.section("🔧 Development Tools Status")

            # Initialize tools manager
            tools_manager = ToolsManager(self.orchestrator.project_root)

            # Get comprehensive status
            status = tools_manager.get_installation_status()

            # Show project overview
            Display.subsection("Project Overview")
            Display.key_value_table({
                "Project Type": status.get("project_type", "unknown"),
                "Total Required Tools": status.get("total_required", 0),
                "Installed Tools": status.get("installed_count", 0),
                "Missing Tools": len(status.get("missing_tools", []))
            })

            # Show installed tools
            if status.get("installed_tools"):
                Display.subsection("✅ Installed Tools")
                for tool in status["installed_tools"]:
                    print(f"  ✅ {tool}")

            # Show missing tools
            if status.get("missing_tools"):
                Display.subsection("❌ Missing Tools")
                for tool in status["missing_tools"]:
                    print(f"  ❌ {tool}")
                Display.info("\nRun 'ccom --install-tools' to install missing tools")

            # Show configurations
            configs = status.get("configurations", {})
            if configs:
                Display.subsection("⚙️ Configuration Files")
                for config_type, exists in configs.items():
                    status_icon = "✅" if exists else "❌"
                    print(f"  {status_icon} {config_type}")

            return True

        except Exception as e:
            self.logger.error(f"Tools status failed: {e}")
            Display.error(f"Tools status failed: {str(e)}")
            return False