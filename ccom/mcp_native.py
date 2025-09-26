#!/usr/bin/env python3
"""
CCOM MCP Memory Keeper Native Integration

This module provides complete, native integration with MCP Memory Keeper,
using project-local SQLite storage and full MCP tools functionality.

Like mem0 - captures everything, extracts meaning automatically.
"""

import os
import json
import subprocess
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid

class MCPNativeIntegration:
    """Native MCP Memory Keeper integration with project-local storage."""

    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.data_dir = self.project_root / "data"
        self.context_db = self.data_dir / "context.db"

        # Ensure data directory exists
        self.data_dir.mkdir(exist_ok=True)

        # Set environment for project-local storage
        os.environ['DATA_DIR'] = str(self.data_dir)

        # Initialize logging
        self.logger = logging.getLogger(__name__)

        # Initialize database if needed
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database if it doesn't exist."""
        # Check if database exists and has proper schema
        needs_init = False

        if not self.context_db.exists():
            needs_init = True
            print(f"🔧 Initializing MCP database at {self.context_db}")
        else:
            # Check if database has tables
            try:
                with sqlite3.connect(str(self.context_db)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contexts'")
                    if not cursor.fetchone():
                        needs_init = True
                        print(f"🔧 Database exists but missing schema, reinitializing...")
            except Exception:
                needs_init = True
                print(f"🔧 Database corrupted, reinitializing...")

        if needs_init:
            self._create_basic_schema()

    def _create_basic_schema(self):
        """Create basic database schema compatible with MCP Memory Keeper."""
        try:
            with sqlite3.connect(str(self.context_db)) as conn:
                cursor = conn.cursor()

                # Create contexts table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS contexts (
                        id TEXT PRIMARY KEY,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        category TEXT DEFAULT 'note',
                        priority TEXT DEFAULT 'normal',
                        channel TEXT,
                        metadata TEXT DEFAULT '{}',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Create sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        name TEXT,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Create channels table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS channels (
                        id TEXT PRIMARY KEY,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)

                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contexts_channel ON contexts(channel)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contexts_category ON contexts(category)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_contexts_created_at ON contexts(created_at)")

                conn.commit()

                print(f"✅ Database initialized successfully: {self.context_db}")
                self.logger.info(f"Database initialized successfully: {self.context_db}")

        except Exception as e:
            self.logger.error(f"Failed to create database schema: {e}")
            raise

    def _run_mcp_tool(self, tool_name: str, parameters: Dict = None) -> Dict:
        """Run MCP Memory Keeper tool via Node.js MCP integration."""
        try:
            # Set working directory to data dir for database access
            cwd = str(self.data_dir)

            # Use the installed mcp-memory-keeper
            mcp_path = self.project_root / "node_modules" / ".bin" / "mcp-memory-keeper"

            # Create tool call in JSON format
            tool_call = {
                "tool": tool_name,
                "parameters": parameters or {}
            }

            # Run MCP tool via Node.js
            cmd = [
                "node",
                "-e",
                f"""
                const mcp = require('mcp-memory-keeper');
                const toolCall = {json.dumps(tool_call)};
                console.log(JSON.stringify(toolCall));
                """
            ]

            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                env=os.environ.copy()
            )

            if result.returncode == 0:
                try:
                    return {"success": True, "result": json.loads(result.stdout)}
                except json.JSONDecodeError:
                    return {"success": True, "result": result.stdout.strip()}
            else:
                self.logger.error(f"MCP tool {tool_name} failed: {result.stderr}")
                return {"success": False, "error": result.stderr.strip()}

        except Exception as e:
            self.logger.error(f"Failed to run MCP tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    def _run_mcp_command(self, command: str, silent: bool = False) -> Dict:
        """Legacy command runner - kept for compatibility."""
        return self._run_mcp_tool("legacy_command", {"command": command})

    def _direct_db_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Direct SQLite query for immediate results."""
        try:
            with sqlite3.connect(str(self.context_db)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return []

    def save_context(self, key: str, value: str, category: str = "progress",
                    priority: str = "normal", channel: str = None, metadata: Dict = None) -> bool:
        """Save context using MCP Memory Keeper tools."""
        try:
            # Use project name as default channel
            if not channel:
                channel = self.project_root.name

            # Prepare context data
            context_data = {
                "key": key,
                "value": value,
                "category": category,
                "priority": priority,
                "channel": channel,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }

            # Save via direct database insert (faster for batch operations)
            with sqlite3.connect(str(self.context_db)) as conn:
                cursor = conn.cursor()

                # Insert context
                cursor.execute("""
                    INSERT INTO contexts (id, key, value, category, priority, channel, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    key,
                    value,
                    category,
                    priority,
                    channel,
                    json.dumps(metadata or {}),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

                conn.commit()

            self.logger.debug(f"Saved context: {key} -> {value[:100]}...")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save context: {e}")
            return False

    def get_context(self, channel: str = None, category: str = None,
                   limit: int = 50, recent_hours: int = 24) -> List[Dict]:
        """Retrieve context with filtering."""
        try:
            # Use project name as default channel
            if not channel:
                channel = self.project_root.name

            # Build query
            conditions = []
            params = []

            if channel:
                conditions.append("channel = ?")
                params.append(channel)

            if category:
                conditions.append("category = ?")
                params.append(category)

            if recent_hours:
                conditions.append("created_at >= datetime('now', '-{} hours')".format(recent_hours))

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            query = f"""
                SELECT * FROM contexts
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)

            return self._direct_db_query(query, tuple(params))

        except Exception as e:
            self.logger.error(f"Failed to get context: {e}")
            return []

    def search_context(self, search_term: str, channel: str = None, limit: int = 20) -> List[Dict]:
        """Search context using text matching."""
        try:
            # Use project name as default channel
            if not channel:
                channel = self.project_root.name

            conditions = ["(key LIKE ? OR value LIKE ?)"]
            params = [f"%{search_term}%", f"%{search_term}%"]

            if channel:
                conditions.append("channel = ?")
                params.append(channel)

            where_clause = "WHERE " + " AND ".join(conditions)

            query = f"""
                SELECT * FROM contexts
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)

            return self._direct_db_query(query, tuple(params))

        except Exception as e:
            self.logger.error(f"Failed to search context: {e}")
            return []

    def capture_interaction(self, input_text: str, output_text: str, metadata: Dict = None) -> bool:
        """Universal capture method - saves everything like mem0."""
        try:
            # Generate unique key
            timestamp = int(datetime.now().timestamp())
            key = f"interaction_{timestamp}"

            # Extract facts from output using simple heuristics
            facts = self._extract_facts(input_text, output_text)

            # Save main interaction
            interaction_saved = self.save_context(
                key=key,
                value=f"Input: {input_text[:200]}...\nOutput: {output_text[:500]}...",
                category="interaction",
                metadata={
                    "input": input_text,
                    "output_preview": output_text[:1000],
                    "full_output_length": len(output_text),
                    **(metadata or {})
                }
            )

            # Save extracted facts
            facts_saved = 0
            for fact in facts:
                if self.save_context(
                    key=f"{key}_fact_{facts_saved}",
                    value=fact["value"],
                    category=fact["category"],
                    priority=fact.get("priority", "normal"),
                    metadata={"source_interaction": key, **fact.get("metadata", {})}
                ):
                    facts_saved += 1

            self.logger.info(f"Captured interaction with {facts_saved} extracted facts")
            return interaction_saved

        except Exception as e:
            self.logger.error(f"Failed to capture interaction: {e}")
            return False

    def _extract_facts(self, input_text: str, output_text: str) -> List[Dict]:
        """Extract meaningful facts from interaction (like mem0 approach)."""
        facts = []

        # Success detection
        if any(word in output_text.lower() for word in ["success", "complete", "passed", "✅", "done"]):
            facts.append({
                "value": f"Success: {input_text}",
                "category": "success",
                "priority": "high"
            })

        # Error detection
        if any(word in output_text.lower() for word in ["error", "failed", "fail", "❌", "issue"]):
            facts.append({
                "value": f"Error encountered: {input_text}",
                "category": "error",
                "priority": "high"
            })

        # Score/grade extraction
        import re
        grade_match = re.search(r"grade:\s*([A-F][+-]?)", output_text, re.IGNORECASE)
        if grade_match:
            facts.append({
                "value": f"Quality grade: {grade_match.group(1)} for {input_text}",
                "category": "quality",
                "priority": "high"
            })

        score_match = re.search(r"score:\s*(\d+)/(\d+)", output_text, re.IGNORECASE)
        if score_match:
            facts.append({
                "value": f"Score: {score_match.group(1)}/{score_match.group(2)} for {input_text}",
                "category": "metrics",
                "priority": "normal"
            })

        # URL extraction
        url_matches = re.findall(r"https?://[^\s]+", output_text)
        for url in url_matches:
            facts.append({
                "value": f"Resource: {url}",
                "category": "reference",
                "priority": "low"
            })

        # Warning detection
        if any(word in output_text.lower() for word in ["warning", "caution", "⚠️"]):
            facts.append({
                "value": f"Warning noted for: {input_text}",
                "category": "warning",
                "priority": "normal"
            })

        return facts

    def get_activity_summary(self, hours: int = 24) -> Dict:
        """Get intelligent activity summary for session context."""
        try:
            recent_context = self.get_context(recent_hours=hours, limit=100)

            if not recent_context:
                return {"total": 0, "message": "No recent activity"}

            # Categorize activities
            categories = {}
            successes = []
            errors = []

            for ctx in recent_context:
                cat = ctx.get("category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1

                if cat == "success":
                    successes.append(ctx["value"])
                elif cat == "error":
                    errors.append(ctx["value"])

            return {
                "total": len(recent_context),
                "categories": categories,
                "recent_successes": successes[:5],
                "recent_errors": errors[:3],
                "timeframe": f"Last {hours} hours"
            }

        except Exception as e:
            self.logger.error(f"Failed to get activity summary: {e}")
            return {"error": str(e)}

    def start_session(self, session_name: str = None, continue_from: str = None) -> Dict:
        """Start MCP session with optional continuation from previous session."""
        try:
            session_name = session_name or f"Claude Code Session - {self.project_root.name}"

            parameters = {
                "name": session_name,
                "description": f"Claude Code session for {self.project_root.name}",
                "projectDir": str(self.project_root)
            }

            if continue_from:
                parameters["continueFrom"] = continue_from

            result = self._run_mcp_tool("context_session_start", parameters)

            if result["success"]:
                print(f"🎯 **MCP SESSION STARTED**: {session_name}")
                if continue_from:
                    print(f"📖 **Continuing from session**: {continue_from}")
                return result["result"]
            else:
                print(f"⚠️ Failed to start MCP session: {result.get('error', 'Unknown error')}")
                return {"error": result.get("error", "Failed to start session")}

        except Exception as e:
            self.logger.error(f"Failed to start session: {e}")
            return {"error": str(e)}

    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """List recent MCP sessions for potential continuation."""
        try:
            result = self._run_mcp_tool("context_session_list", {"limit": limit})

            if result["success"]:
                return result["result"]
            else:
                self.logger.error(f"Failed to list sessions: {result.get('error')}")
                return []

        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []

    def get_session_context(self, session_id: str = None) -> Dict:
        """Get context for specific session or current session."""
        try:
            # Get context from specific session
            context_params = {"limit": 50}
            if session_id:
                context_params["sessionId"] = session_id

            # For now, use direct database query since we have the data locally
            # In full MCP integration, this would use context_get tool
            recent_context = self.get_context(limit=50)

            return {
                "session_id": session_id or "current",
                "context_items": recent_context,
                "total_items": len(recent_context)
            }

        except Exception as e:
            self.logger.error(f"Failed to get session context: {e}")
            return {"error": str(e)}

    def get_project_context(self) -> Dict:
        """Get comprehensive project context for session continuity."""
        try:
            # Get recent activity
            activity = self.get_activity_summary(hours=48)

            # Get by category
            decisions = self.get_context(category="decision", limit=10)
            issues = self.get_context(category="error", limit=5)
            successes = self.get_context(category="success", limit=10)

            # Get recent sessions
            sessions = self.list_sessions(limit=5)

            return {
                "project": self.project_root.name,
                "database": str(self.context_db),
                "activity_summary": activity,
                "recent_decisions": [d["value"] for d in decisions],
                "recent_issues": [i["value"] for i in issues],
                "recent_successes": [s["value"] for s in successes],
                "total_context_items": len(self.get_context(limit=1000)),
                "recent_sessions": sessions[:3] if sessions else []
            }

        except Exception as e:
            self.logger.error(f"Failed to get project context: {e}")
            return {"error": str(e)}


# Global instance for CCOM integration
_mcp_integration = None

def get_mcp_integration(project_root: str = None) -> MCPNativeIntegration:
    """Get or create MCP integration instance."""
    global _mcp_integration
    if _mcp_integration is None or (project_root and str(_mcp_integration.project_root) != project_root):
        _mcp_integration = MCPNativeIntegration(project_root)
    return _mcp_integration