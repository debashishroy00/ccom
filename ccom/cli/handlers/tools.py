#!/usr/bin/env python3
"""
Tools Commands Handler
Handles development tool management
"""

from .base import BaseHandler
from ...utils import Display
from ...legacy.tools_manager import ToolsManager
from ...memory.advanced_memory_keeper import AdvancedMemoryKeeper


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
        """Handle install tools command with intelligent memory checking"""
        try:
            Display.header("🧠 CCOM Intelligence: Checking Memory Before Installation")

            # Initialize memory keeper
            memory_keeper = AdvancedMemoryKeeper(self.orchestrator.project_root)

            # Query memory for recent tool installations
            memory_query = memory_keeper.query_command_memory("install tools", timeframe_hours=24)

            # Check if tools were recently installed successfully
            if memory_query["has_recent_execution"]:
                Display.section("🔍 Memory Intelligence Found Recent Activity")

                for cmd in memory_query["recent_commands"]:
                    if cmd["success_rate"] > 0.8:  # Recent successful installation
                        Display.warning(f"⚠️  Tools were successfully installed recently: {cmd['last_executed']}")
                        Display.info(f"📊 Success Rate: {cmd['success_rate']:.1%} ({cmd['count']} attempts)")

                        # Check current tool status first
                        Display.progress("Checking current tool status...")
                        tools_manager = ToolsManager(self.orchestrator.project_root)
                        installed_tools = tools_manager.check_tool_availability()
                        required_tools = tools_manager.get_tools_for_project()

                        missing_count = len([t for t in required_tools if not installed_tools.get(t, {}).get("installed", False)])

                        if missing_count == 0:
                            Display.success("✅ All required tools are already installed")
                            Display.info("💡 Memory Intelligence: No installation needed")

                            # Capture this decision in memory
                            memory_keeper.capture_command_execution(
                                "install tools",
                                {"memory_check": True, "tools_already_installed": True},
                                {"success": True, "action": "skipped_unnecessary_installation", "missing_tools": 0}
                            )

                            return True
                        else:
                            Display.info(f"📋 Found {missing_count} missing tools - proceeding with installation")
                            break

                # Show memory recommendations
                if memory_query["recommendations"]:
                    Display.subsection("🧠 Memory Recommendations")
                    for rec in memory_query["recommendations"]:
                        Display.info(f"  {rec}")

            Display.progress("Installing development tools...")

            # Initialize tools manager
            tools_manager = ToolsManager(self.orchestrator.project_root)

            # Install tools
            success = tools_manager.install_missing_tools(force=True)

            # Capture command execution in memory
            context = {
                "memory_check_performed": True,
                "had_recent_execution": memory_query["has_recent_execution"]
            }

            if success:
                Display.success("Development tools installation completed")

                # Show status
                status = tools_manager.get_installation_status()
                Display.info(f"Tools installed: {len(status['installed_tools'])}/{status['total_required']}")

                # Capture successful installation
                memory_keeper.capture_command_execution(
                    "install tools",
                    context,
                    {
                        "success": True,
                        "tools_installed": len(status['installed_tools']),
                        "total_required": status['total_required'],
                        "installation_status": status
                    }
                )

                return True
            else:
                Display.warning("Some tools failed to install")

                # Capture failed installation
                memory_keeper.capture_command_execution(
                    "install tools",
                    context,
                    {"success": False, "error": "some_tools_failed"}
                )

                return False

        except Exception as e:
            self.logger.error(f"Tool installation failed: {e}")
            Display.error(f"Tool installation failed: {str(e)}")

            # Capture exception in memory
            try:
                memory_keeper = AdvancedMemoryKeeper(self.orchestrator.project_root)
                memory_keeper.capture_command_execution(
                    "install tools",
                    {"error": str(e)},
                    {"success": False, "exception": str(e)}
                )
            except:
                pass  # Don't let memory issues crash the main operation

            return False

    def _handle_check_tools(self) -> bool:
        """Handle check tools command with memory intelligence"""
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

            # Capture tool check in memory
            try:
                memory_keeper = AdvancedMemoryKeeper(self.orchestrator.project_root)
                memory_keeper.capture_command_execution(
                    "check tools",
                    {"project_type": project_type},
                    {
                        "success": True,
                        "installed_tools": len([t for t in required_tools if installed_tools.get(t, {}).get("installed", False)]),
                        "missing_tools": missing_count,
                        "total_required": len(required_tools),
                        "tool_status": installed_tools
                    }
                )
            except Exception as mem_e:
                self.logger.warning(f"Failed to capture tool check in memory: {mem_e}")

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