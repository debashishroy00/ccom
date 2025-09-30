#!/usr/bin/env python3
"""
Memory Management Module
Extracted from orchestrator.py to follow Single Responsibility Principle

Handles:
- Memory loading and saving
- Feature tracking
- Duplicate detection
- Memory validation
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from ccom.utils import FileUtils, ErrorHandler, Display


class MemoryManager:
    """
    Manages CCOM memory operations with proper separation of concerns

    Replaces memory-related methods from CCOMOrchestrator (200+ lines)
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.ccom_dir = project_root / ".claude"
        self.memory_file = self.ccom_dir / "memory.json"

        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler(self.logger)
        self.file_utils = FileUtils()

        # Load memory on initialization
        self._memory = self._load_memory()

    def _load_memory(self) -> Dict[str, Any]:
        """Load existing CCOM memory with error handling"""
        return self.error_handler.safe_execute(
            self._do_load_memory,
            default_return=self._create_empty_memory(),
            error_message="Failed to load memory"
        )

    def _do_load_memory(self) -> Dict[str, Any]:
        """Actual memory loading implementation"""
        if self.memory_file.exists():
            memory_data = self.file_utils.safe_read_json(self.memory_file)
            if memory_data:
                # Validate and migrate memory structure if needed
                return self._validate_and_migrate_memory(memory_data)

        return self._create_empty_memory()

    def _validate_and_migrate_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate memory structure and migrate if necessary"""
        # Ensure required keys exist
        if "project" not in memory_data:
            memory_data["project"] = {
                "name": self.project_root.name,
                "created": datetime.now().strftime("%Y-%m-%d")
            }

        if "features" not in memory_data:
            memory_data["features"] = {}

        if "metadata" not in memory_data:
            memory_data["metadata"] = {
                "version": "5.0",
                "created": datetime.now().isoformat(),
                "lastCleanup": datetime.now().isoformat()
            }

        # Update version if needed
        metadata = memory_data.get("metadata", {})
        if metadata.get("version") != "5.0":
            metadata["version"] = "5.0"
            metadata["migrated"] = datetime.now().isoformat()

        return memory_data

    def _create_empty_memory(self) -> Dict[str, Any]:
        """Create empty memory structure"""
        return {
            "project": {
                "name": self.project_root.name,
                "created": datetime.now().strftime("%Y-%m-%d"),
            },
            "features": {},
            "metadata": {
                "version": "5.0",
                "created": datetime.now().isoformat(),
                "lastCleanup": datetime.now().isoformat(),
            },
        }

    def save_memory(self) -> bool:
        """Save memory to file with error handling"""
        return self.error_handler.safe_execute(
            self._do_save_memory,
            default_return=False,
            error_message="Failed to save memory"
        )

    def _do_save_memory(self) -> bool:
        """Actual memory saving implementation"""
        # Ensure directory exists
        self.file_utils.ensure_directory(self.ccom_dir)

        # Update metadata
        self._memory["metadata"]["lastUpdate"] = datetime.now().isoformat()

        # Save with backup
        if self.memory_file.exists():
            self.file_utils.backup_file(self.memory_file)

        return self.file_utils.safe_write_json(self.memory_file, self._memory)

    @property
    def memory(self) -> Dict[str, Any]:
        """Get current memory (read-only)"""
        return self._memory.copy()

    def get_feature(self, feature_name: str) -> Optional[Dict[str, Any]]:
        """Get specific feature from memory"""
        return self._memory.get("features", {}).get(feature_name)

    def add_feature(self, feature_name: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add new feature to memory"""
        try:
            if "features" not in self._memory:
                self._memory["features"] = {}

            self._memory["features"][feature_name] = {
                "description": description,
                "created": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            return self.save_memory()

        except Exception as e:
            self.logger.error(f"Failed to add feature {feature_name}: {e}")
            return False

    def update_feature(self, feature_name: str, updates: Dict[str, Any]) -> bool:
        """Update existing feature in memory"""
        try:
            if feature_name not in self._memory.get("features", {}):
                return False

            feature = self._memory["features"][feature_name]
            feature.update(updates)
            feature["lastModified"] = datetime.now().isoformat()

            return self.save_memory()

        except Exception as e:
            self.logger.error(f"Failed to update feature {feature_name}: {e}")
            return False

    def remove_feature(self, feature_name: str) -> bool:
        """Remove feature from memory"""
        try:
            if feature_name in self._memory.get("features", {}):
                del self._memory["features"][feature_name]
                return self.save_memory()
            return False

        except Exception as e:
            self.logger.error(f"Failed to remove feature {feature_name}: {e}")
            return False

    def check_duplicate_feature(self, feature_name: str) -> bool:
        """Check if feature already exists (with fuzzy matching)"""
        try:
            features = self._memory.get("features", {})
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

        except Exception as e:
            self.logger.error(f"Failed to check duplicate for {feature_name}: {e}")
            return False

    def get_feature_list(self) -> List[str]:
        """Get list of all feature names"""
        return list(self._memory.get("features", {}).keys())

    def get_recent_features(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recently added/modified features"""
        try:
            features = self._memory.get("features", {})
            feature_list = []

            for name, feature in features.items():
                feature_copy = feature.copy()
                feature_copy["name"] = name
                feature_list.append(feature_copy)

            # Sort by creation date or last modified
            feature_list.sort(
                key=lambda x: x.get("lastModified", x.get("created", "")),
                reverse=True
            )

            return feature_list[:limit]

        except Exception as e:
            self.logger.error(f"Failed to get recent features: {e}")
            return []

    def cleanup_memory(self, max_age_days: int = 90) -> int:
        """Clean up old features based on age"""
        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            features = self._memory.get("features", {})
            removed_count = 0

            features_to_remove = []
            for name, feature in features.items():
                # Parse creation date
                created_str = feature.get("created", "")
                try:
                    created_date = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    if created_date < cutoff_date:
                        features_to_remove.append(name)
                except ValueError:
                    continue

            # Remove old features
            for name in features_to_remove:
                del features[name]
                removed_count += 1

            if removed_count > 0:
                self._memory["metadata"]["lastCleanup"] = datetime.now().isoformat()
                self.save_memory()

            return removed_count

        except Exception as e:
            self.logger.error(f"Failed to cleanup memory: {e}")
            return 0

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        try:
            features = self._memory.get("features", {})
            metadata = self._memory.get("metadata", {})

            return {
                "total_features": len(features),
                "project_name": self._memory.get("project", {}).get("name", "Unknown"),
                "created": metadata.get("created", "Unknown"),
                "last_update": metadata.get("lastUpdate", "Never"),
                "last_cleanup": metadata.get("lastCleanup", "Never"),
                "version": metadata.get("version", "Unknown"),
                "memory_file_size": self.memory_file.stat().st_size if self.memory_file.exists() else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {e}")
            return {}

    def export_memory(self, export_path: Path) -> bool:
        """Export memory to specified path"""
        try:
            export_data = {
                "exported": datetime.now().isoformat(),
                "source_project": self._memory.get("project", {}).get("name", "Unknown"),
                "memory": self._memory
            }

            return self.file_utils.safe_write_json(export_path, export_data, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to export memory: {e}")
            return False

    def import_memory(self, import_path: Path, merge: bool = True) -> bool:
        """Import memory from specified path"""
        try:
            imported_data = self.file_utils.safe_read_json(import_path)
            if not imported_data or "memory" not in imported_data:
                return False

            imported_memory = imported_data["memory"]

            if merge:
                # Merge features
                current_features = self._memory.get("features", {})
                imported_features = imported_memory.get("features", {})
                current_features.update(imported_features)
                self._memory["features"] = current_features
            else:
                # Replace entirely
                self._memory = self._validate_and_migrate_memory(imported_memory)

            # Update metadata
            self._memory["metadata"]["imported"] = datetime.now().isoformat()
            self._memory["metadata"]["importSource"] = str(import_path)

            return self.save_memory()

        except Exception as e:
            self.logger.error(f"Failed to import memory: {e}")
            return False

    def display_memory_summary(self) -> None:
        """Display memory summary using centralized display utilities"""
        stats = self.get_memory_stats()
        recent_features = self.get_recent_features(5)

        Display.header("🧠 CCOM Memory Summary")

        Display.section("📊 Statistics")
        Display.key_value_table({
            "Project": stats.get("project_name", "Unknown"),
            "Total Features": stats.get("total_features", 0),
            "Created": stats.get("created", "Unknown"),
            "Last Update": stats.get("last_update", "Never"),
            "Version": stats.get("version", "Unknown")
        })

        if recent_features:
            Display.section("📝 Recent Features")
            for feature in recent_features:
                name = feature.get("name", "Unknown")
                desc = feature.get("description", "No description")[:60]
                print(f"  • {name}: {desc}{'...' if len(desc) == 60 else ''}")
        else:
            Display.info("No features in memory yet")

        print("=" * 60)