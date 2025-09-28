"""
MCP Keeper Bridge for CCOM
Non-disruptive integration with Claude Code's MCP Keeper memory system
Falls back gracefully to existing auto-capture if MCP unavailable
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime, timedelta


class MCPKeeperBridge:
    """Bridge to Claude Code's MCP Keeper memory system"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.enabled = True
        self.fallback_to_legacy = True
        self.logger = logging.getLogger(__name__)

        # MCP Keeper detection
        self._mcp_available = None
        self._last_check = None

    def capture_if_mcp_available(self, output: str, context: Optional[Dict] = None) -> bool:
        """
        Attempt MCP Keeper capture, always fall back to auto-capture
        This ensures zero disruption to existing functionality
        """
        mcp_success = False

        # Try MCP Keeper first (if available)
        try:
            if self._is_mcp_keeper_available():
                mcp_success = self._capture_to_mcp_keeper(output, context)
                if mcp_success:
                    self.logger.info("✅ MCP Keeper capture successful")
        except Exception as e:
            self.logger.debug(f"MCP Keeper capture failed (graceful): {e}")

        # ALWAYS run existing auto-capture as backup/primary
        try:
            from .auto_capture import capture_if_evaluation
            auto_success = capture_if_evaluation(output, project=None)
            if auto_success:
                self.logger.debug("✅ Auto-capture backup successful")
            return mcp_success or auto_success
        except Exception as e:
            self.logger.error(f"Auto-capture fallback failed: {e}")
            return mcp_success

    def _is_mcp_keeper_available(self) -> bool:
        """Check if MCP Keeper is available and responsive"""
        # Cache check for 30 seconds to avoid repeated calls
        now = datetime.now()
        if (self._last_check and
            (now - self._last_check).seconds < 30 and
            self._mcp_available is not None):
            return self._mcp_available

        # Simplified check: Just use the connection test
        self._mcp_available = self._test_mcp_keeper_connection()

        self._last_check = now
        return self._mcp_available

    def _test_mcp_keeper_connection(self) -> bool:
        """Test actual MCP Keeper connectivity"""
        try:
            # Check for MCP Keeper markers
            # MCP Keeper would typically have:
            # 1. A memory service endpoint
            # 2. A specific MCP protocol version
            # 3. Write/read capabilities

            # Test 1: Check for MCP memory files or database
            mcp_memory_db = self.project_root / ".mcp" / "memory.db"
            mcp_memory_json = self.project_root / ".mcp" / "memory.json"
            mcp_config_path = self.project_root / ".mcp" / "config.json"

            if mcp_memory_db.exists() or mcp_memory_json.exists() or mcp_config_path.exists():
                self.logger.debug("MCP Keeper files detected")
                return True

            # Test 2: Try environment variable check
            import os
            if os.environ.get("MCP_KEEPER_ENABLED") == "true":
                self.logger.debug("MCP Keeper enabled via environment")
                return True

            # Test 3: Check for MCP server process
            try:
                # Try to connect to MCP server if running
                result = subprocess.run(
                    ["mcp", "status"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0 and "memory" in result.stdout.lower():
                    self.logger.debug("MCP Keeper server detected")
                    return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            # MCP Keeper not currently available
            return False

        except Exception as e:
            self.logger.debug(f"MCP Keeper connection test failed: {e}")
            return False

    def _capture_to_mcp_keeper(self, output: str, context: Optional[Dict] = None) -> bool:
        """Capture any CCOM output to MCP Keeper memory system"""
        try:
            # Extract output metadata
            output_data = self._extract_evaluation_metadata(output)

            if not output_data:
                return False

            # Prepare MCP Keeper payload
            mcp_payload = {
                "type": "ccom_output_capture",
                "timestamp": datetime.now().isoformat(),
                "project": str(self.project_root.name),
                "output": output_data,
                "context": context or {},
                "source": "ccom_auto_capture"
            }

            # Send to MCP Keeper (when available)
            # This would use actual MCP protocol
            success = self._send_to_mcp_keeper(mcp_payload)

            if success:
                self.logger.info(f"📊 MCP Keeper captured: {output_data.get('type', 'ccom_output')}")
                return True

        except Exception as e:
            self.logger.debug(f"MCP Keeper capture error: {e}")

        return False

    def _extract_evaluation_metadata(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract structured metadata from any CCOM output - captures everything"""
        # UNIVERSAL CAPTURE: Always capture all content (user requirement)
        metadata = {
            "raw_output": output,
            "length": len(output),
            "type": "ccom_output"
        }

        # Extract evaluation type
        if "google play" in output.lower():
            metadata["type"] = "google_play_evaluation"
        elif "apple store" in output.lower():
            metadata["type"] = "apple_store_evaluation"
        elif "security" in output.lower():
            metadata["type"] = "security_evaluation"
        elif "quality" in output.lower():
            metadata["type"] = "quality_evaluation"
        elif "monetization" in output.lower():
            metadata["type"] = "monetization_evaluation"
        elif "ccom" in output.lower() and "evaluation" in output.lower():
            # Extract CCOM evaluation type from title
            lines = output.split('\n')
            for line in lines:
                if "CCOM" in line and "EVALUATION" in line:
                    metadata["title"] = line.strip()
                    break

        # Extract key indicators
        if "tier 1" in output.lower() or "recommended" in output.lower():
            metadata["recommendation"] = "recommended"
        elif "tier 2" in output.lower() or "not recommended" in output.lower():
            metadata["recommendation"] = "not_recommended"

        # Extract revenue information
        import re
        revenue_pattern = r'\$[\d,]+(?:K|M|k|m)?(?:/month|/year)?'
        revenue_matches = re.findall(revenue_pattern, output)
        if revenue_matches:
            metadata["revenue_potential"] = revenue_matches[0]

        # Extract complexity/timeline
        timeline_patterns = [
            r'(\d+-\d+\s+weeks?)',
            r'(phase\s+\d+:\s+[^(]+\([^)]+\))',
            r'(implementation[:\s]+[^.]+)'
        ]
        for pattern in timeline_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                metadata["timeline"] = matches[0]
                break

        return metadata

    def _send_to_mcp_keeper(self, payload: Dict[str, Any]) -> bool:
        """Send payload to MCP Keeper memory system"""
        try:
            # Option 1: Write to MCP memory file (if available)
            mcp_memory_dir = self.project_root / ".mcp"
            if mcp_memory_dir.exists():
                memory_file = mcp_memory_dir / "memory.json"

                # Load existing memory or create new
                memory_data = {"entries": [], "metadata": {}}
                if memory_file.exists():
                    with open(memory_file, 'r', encoding='utf-8') as f:
                        memory_data = json.load(f)

                # Add new entry
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "type": "ccom_capture",
                    "payload": payload
                }
                memory_data["entries"].append(entry)

                # Save updated memory
                with open(memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, indent=2, ensure_ascii=False)

                self.logger.info("MCP Keeper memory file updated")
                return True

            # Option 2: Send via MCP command (if server available)
            try:
                import os
                if os.environ.get("MCP_KEEPER_ENABLED") == "true":
                    # Format payload for MCP command
                    mcp_cmd = [
                        "mcp", "memory", "add",
                        "--type", payload.get("type", "evaluation"),
                        "--content", json.dumps(payload)
                    ]

                    result = subprocess.run(
                        mcp_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=str(self.project_root)
                    )

                    if result.returncode == 0:
                        self.logger.info("MCP Keeper server accepted data")
                        return True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass

            # Option 3: Use environment-based MCP bridge (future)
            # This would integrate with Claude Code's MCP tools directly
            # when they become available for memory operations

            # No MCP Keeper method succeeded
            return False

        except Exception as e:
            self.logger.debug(f"MCP Keeper send failed: {e}")
            return False

    def read_from_mcp_keeper(self) -> Optional[Dict[str, Any]]:
        """Read memory from MCP Keeper system"""
        try:
            # Option 1: Read from MCP memory file
            mcp_memory_file = self.project_root / ".mcp" / "memory.json"
            if mcp_memory_file.exists():
                with open(mcp_memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # Option 2: Query MCP server
            import os
            if os.environ.get("MCP_KEEPER_ENABLED") == "true":
                try:
                    result = subprocess.run(
                        ["mcp", "memory", "list", "--format", "json"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=str(self.project_root)
                    )
                    if result.returncode == 0:
                        return json.loads(result.stdout)
                except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
                    pass

            return None

        except Exception as e:
            self.logger.debug(f"MCP Keeper read failed: {e}")
            return None

    def sync_with_json_memory(self) -> bool:
        """Sync MCP Keeper memory with JSON memory system"""
        try:
            # Read from MCP
            mcp_data = self.read_from_mcp_keeper()
            if not mcp_data:
                return False

            # Read from JSON memory
            json_memory_file = self.project_root / ".claude" / "memory.json"
            if not json_memory_file.exists():
                return False

            with open(json_memory_file, 'r', encoding='utf-8') as f:
                json_memory = json.load(f)

            # Merge strategy: Add MCP entries not in JSON
            if "entries" in mcp_data:
                for mcp_entry in mcp_data["entries"]:
                    # Check if entry exists in JSON memory
                    if self._should_sync_entry(mcp_entry, json_memory):
                        # Add to JSON memory
                        feature_name = self._extract_feature_from_mcp(mcp_entry)
                        json_memory["features"][feature_name] = {
                            "created": mcp_entry.get("timestamp", datetime.now().isoformat()),
                            "description": self._extract_description_from_mcp(mcp_entry),
                            "files": [],
                            "userTerm": feature_name
                        }

            # Save updated JSON memory
            with open(json_memory_file, 'w', encoding='utf-8') as f:
                json.dump(json_memory, f, indent=2, ensure_ascii=False)

            self.logger.info("MCP-JSON sync completed")
            return True

        except Exception as e:
            self.logger.error(f"MCP-JSON sync failed: {e}")
            return False

    def _should_sync_entry(self, mcp_entry: Dict, json_memory: Dict) -> bool:
        """Check if MCP entry should be synced to JSON memory"""
        # Extract identifier from MCP entry
        feature_name = self._extract_feature_from_mcp(mcp_entry)
        return feature_name not in json_memory.get("features", {})

    def _extract_feature_from_mcp(self, mcp_entry: Dict) -> str:
        """Extract feature name from MCP entry"""
        payload = mcp_entry.get("payload", {})
        eval_type = payload.get("evaluation", {}).get("type", "general")
        timestamp = mcp_entry.get("timestamp", "").split("T")[0].replace("-", "")
        return f"{eval_type}_{timestamp}"

    def _extract_description_from_mcp(self, mcp_entry: Dict) -> str:
        """Extract description from MCP entry"""
        payload = mcp_entry.get("payload", {})
        return payload.get("evaluation", {}).get("raw_output", "MCP Keeper memory entry")[:500]

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP Keeper status for diagnostics"""
        return {
            "available": self._is_mcp_keeper_available(),
            "enabled": self.enabled,
            "fallback_enabled": self.fallback_to_legacy,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "project_root": str(self.project_root)
        }


    def search_mcp_memory(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search MCP Keeper memory with advanced querying"""
        try:
            results = []
            mcp_data = self.read_from_mcp_keeper()

            if not mcp_data or "entries" not in mcp_data:
                return results

            query_lower = query.lower()

            for entry in mcp_data["entries"]:
                # Check if entry matches query
                if self._entry_matches_query(entry, query_lower, filters):
                    results.append(entry)

            # Sort by relevance/timestamp
            results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return results

        except Exception as e:
            self.logger.error(f"MCP search failed: {e}")
            return []

    def _entry_matches_query(self, entry: Dict, query: str, filters: Optional[Dict]) -> bool:
        """Check if MCP entry matches search query and filters"""
        # Text search in payload
        payload_str = json.dumps(entry.get("payload", {})).lower()
        if query not in payload_str:
            return False

        # Apply filters if provided
        if filters:
            # Filter by type
            if "type" in filters:
                entry_type = entry.get("payload", {}).get("type", "")
                if entry_type != filters["type"]:
                    return False

            # Filter by date range
            if "start_date" in filters or "end_date" in filters:
                entry_timestamp = entry.get("timestamp", "")
                if "start_date" in filters and entry_timestamp < filters["start_date"]:
                    return False
                if "end_date" in filters and entry_timestamp > filters["end_date"]:
                    return False

            # Filter by project
            if "project" in filters:
                entry_project = entry.get("payload", {}).get("project", "")
                if entry_project != filters["project"]:
                    return False

        return True

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about MCP Keeper memory"""
        try:
            stats = {
                "total_entries": 0,
                "types": {},
                "projects": {},
                "date_range": {"earliest": None, "latest": None},
                "memory_size_kb": 0
            }

            mcp_data = self.read_from_mcp_keeper()
            if not mcp_data or "entries" not in mcp_data:
                return stats

            entries = mcp_data["entries"]
            stats["total_entries"] = len(entries)

            for entry in entries:
                # Count by type
                entry_type = entry.get("payload", {}).get("type", "unknown")
                stats["types"][entry_type] = stats["types"].get(entry_type, 0) + 1

                # Count by project
                project = entry.get("payload", {}).get("project", "unknown")
                stats["projects"][project] = stats["projects"].get(project, 0) + 1

                # Track date range
                timestamp = entry.get("timestamp", "")
                if timestamp:
                    if not stats["date_range"]["earliest"] or timestamp < stats["date_range"]["earliest"]:
                        stats["date_range"]["earliest"] = timestamp
                    if not stats["date_range"]["latest"] or timestamp > stats["date_range"]["latest"]:
                        stats["date_range"]["latest"] = timestamp

            # Calculate memory size
            mcp_memory_file = self.project_root / ".mcp" / "memory.json"
            if mcp_memory_file.exists():
                stats["memory_size_kb"] = mcp_memory_file.stat().st_size / 1024

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get MCP stats: {e}")
            return {"error": str(e)}

    def cleanup_old_entries(self, days_to_keep: int = 30) -> int:
        """Clean up old MCP Keeper entries"""
        try:
            mcp_data = self.read_from_mcp_keeper()
            if not mcp_data or "entries" not in mcp_data:
                return 0

            cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
            original_count = len(mcp_data["entries"])

            # Filter entries
            mcp_data["entries"] = [
                entry for entry in mcp_data["entries"]
                if entry.get("timestamp", "") >= cutoff_date
            ]

            removed_count = original_count - len(mcp_data["entries"])

            if removed_count > 0:
                # Save cleaned data
                mcp_memory_file = self.project_root / ".mcp" / "memory.json"
                if mcp_memory_file.exists():
                    with open(mcp_memory_file, 'w', encoding='utf-8') as f:
                        json.dump(mcp_data, f, indent=2, ensure_ascii=False)

                self.logger.info(f"Cleaned up {removed_count} old MCP entries")

            return removed_count

        except Exception as e:
            self.logger.error(f"MCP cleanup failed: {e}")
            return 0


def get_mcp_keeper_bridge(project_root: str) -> Optional[MCPKeeperBridge]:
    """Factory function to create MCP Keeper bridge"""
    try:
        bridge = MCPKeeperBridge(project_root)
        return bridge
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to create MCP Keeper bridge: {e}")
        return None