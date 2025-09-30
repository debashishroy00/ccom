#!/usr/bin/env python3
"""
Memory Commands Handler
Handles memory management and feature tracking
"""

from .base import BaseHandler
from ...utils import Display


class MemoryHandler(BaseHandler):
    """
    Handles memory-related commands

    Responsibilities:
    - Memory display and management
    - Feature remembering and forgetting
    - Memory statistics
    """

    def can_handle(self, args) -> bool:
        """Check if this handler can process the arguments"""
        return (
            args.memory or
            args.remember is not None or
            args.forget is not None
        )

    def handle(self, args) -> bool:
        """Handle memory commands"""
        try:
            # Show memory
            if args.memory:
                return self._handle_show_memory()

            # Remember feature
            if args.remember is not None:
                return self._handle_remember(args.remember)

            # Forget feature
            if args.forget is not None:
                return self._handle_forget(args.forget)

            return False

        except Exception as e:
            self.logger.error(f"Memory command handling failed: {e}")
            Display.error(f"Memory operation failed: {str(e)}")
            return False

    def _handle_show_memory(self) -> bool:
        """Handle show memory command"""
        try:
            self.orchestrator.memory_manager.display_memory_summary()
            return True

        except Exception as e:
            self.logger.error(f"Failed to show memory: {e}")
            Display.error("Failed to display memory")
            return False

    def _handle_remember(self, feature_name: str) -> bool:
        """Handle remember feature command"""
        try:
            # Check for duplicates
            if self.orchestrator.memory_manager.check_duplicate_feature(feature_name):
                Display.warning(f"Feature '{feature_name}' already exists in memory")
                Display.info("Use a different name or update the existing feature")
                return False

            # Prompt for description
            description = self._get_feature_description(feature_name)

            # Add to memory
            success = self.orchestrator.memory_manager.add_feature(feature_name, description)

            if success:
                Display.success(f"Remembered feature: {feature_name}")
                Display.info("Use 'ccom --memory' to view all remembered features")
                return True
            else:
                Display.error("Failed to save feature to memory")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remember feature: {e}")
            Display.error(f"Failed to remember feature: {str(e)}")
            return False

    def _handle_forget(self, feature_name: str) -> bool:
        """Handle forget feature command"""
        try:
            # Check if feature exists
            if not self.orchestrator.memory_manager.check_duplicate_feature(feature_name):
                Display.warning(f"Feature '{feature_name}' not found in memory")
                return False

            # Confirm deletion
            if not self._confirm_deletion(feature_name):
                Display.info("Feature deletion cancelled")
                return True

            # Remove from memory
            success = self.orchestrator.memory_manager.remove_feature(feature_name)

            if success:
                Display.success(f"Forgotten feature: {feature_name}")
                return True
            else:
                Display.error("Failed to remove feature from memory")
                return False

        except Exception as e:
            self.logger.error(f"Failed to forget feature: {e}")
            Display.error(f"Failed to forget feature: {str(e)}")
            return False

    def _get_feature_description(self, feature_name: str) -> str:
        """Get feature description from user input"""
        try:
            # For CLI usage, provide a simple default description
            # In a real implementation, this might prompt for input
            return f"Feature: {feature_name} - Added via CLI"

        except Exception:
            return f"Feature: {feature_name}"

    def _confirm_deletion(self, feature_name: str) -> bool:
        """Confirm feature deletion"""
        try:
            # For CLI usage, assume confirmation
            # In an interactive implementation, this would prompt the user
            return True

        except Exception:
            return False