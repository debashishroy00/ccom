#!/usr/bin/env python3
"""
SDK Commands Handler
Handles SDK integration and migration commands
"""

import asyncio
from .base import BaseHandler
from ...utils import Display


class SDKHandler(BaseHandler):
    """
    Handles SDK integration commands

    Responsibilities:
    - SDK status and metrics
    - Migration recommendations
    - Agent mode management
    - SDK migration process
    """

    def can_handle(self, args) -> bool:
        """Check if this handler can process the arguments"""
        return (
            args.sdk_status or
            args.migration_recommendations or
            args.set_agent_mode is not None or
            args.migrate_to_sdk
        )

    def handle(self, args) -> bool:
        """Handle SDK commands"""
        try:
            if args.sdk_status:
                return self._handle_sdk_status()
            elif args.migration_recommendations:
                return self._handle_migration_recommendations()
            elif args.set_agent_mode is not None:
                return self._handle_set_agent_mode(args.set_agent_mode)
            elif args.migrate_to_sdk:
                return self._handle_migrate_to_sdk()

            return False

        except Exception as e:
            self.logger.error(f"SDK command handling failed: {e}")
            Display.error(f"SDK operation failed: {str(e)}")
            return False

    def _handle_sdk_status(self) -> bool:
        """Handle SDK status command"""
        return self.orchestrator.show_sdk_status()

    def _handle_migration_recommendations(self) -> bool:
        """Handle migration recommendations command"""
        try:
            Display.header("🤖 CCOM Migration Recommendations")

            recommendations = self.orchestrator.get_migration_recommendations()

            Display.section("📊 Current Configuration")
            Display.key_value_table({
                "Mode": recommendations['current_mode'].upper(),
                "SDK Agents Available": f"{recommendations['sdk_agents_available']}/{recommendations['total_agents']}"
            })

            if recommendations['recommendations']:
                Display.section("💡 Recommendations")
                for rec in recommendations['recommendations']:
                    priority_icon = "🔴" if rec["priority"] == "high" else "🟡" if rec["priority"] == "medium" else "🟢"
                    print(f"  {priority_icon} {rec['message']}")
            else:
                Display.success("No recommendations - System optimally configured")

            Display.section("📈 Performance Comparison")
            perf = recommendations['performance_comparison']
            Display.key_value_table({
                "SDK Success Rate": perf['sdk_success_rate'],
                "Legacy Success Rate": perf['legacy_success_rate'],
                "SDK Average Time": perf['sdk_avg_time'],
                "Legacy Average Time": perf['legacy_avg_time']
            })

            return True

        except Exception as e:
            self.logger.error(f"Failed to get migration recommendations: {e}")
            Display.error("Failed to get migration recommendations")
            return False

    def _handle_set_agent_mode(self, mode: str) -> bool:
        """Handle set agent mode command"""
        Display.progress(f"Setting agent mode to {mode.upper()}...")
        return self.orchestrator.set_agent_mode(mode)

    def _handle_migrate_to_sdk(self) -> bool:
        """Handle migrate to SDK command"""
        try:
            Display.header("🚀 CCOM SDK Migration")
            Display.progress("Checking migration readiness...")

            # Run migration asynchronously
            success = asyncio.run(self.orchestrator.migrate_to_sdk_mode())

            if success:
                Display.success("MIGRATION SUCCESSFUL!")
                Display.info("Your CCOM installation now uses modern SDK-based agents")
                Display.info("Run 'ccom --sdk-status' to see the new configuration")
            else:
                Display.warning("MIGRATION NOT READY")
                Display.info("Run 'ccom --migration-recommendations' for guidance")

            return success

        except Exception as e:
            self.logger.error(f"SDK migration failed: {e}")
            Display.error(f"Error during SDK migration: {str(e)}")
            Display.info("Try 'ccom --migration-recommendations' for troubleshooting")
            return False