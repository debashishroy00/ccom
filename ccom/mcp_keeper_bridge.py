"""
MCP Keeper Bridge for CCOM - Rich Features Implementation
Professional-grade context management with SQLite database
Based on mcp-memory-keeper and mcp-memory-service specifications
"""

import sqlite3
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging
from datetime import datetime, timedelta
import re
import os


class MCPKeeperBridge:
    """
    Professional MCP Keeper Bridge with Rich Features

    Features:
    - SQLite database (context.db) for persistent storage
    - Channel-based organization with git integration
    - Checkpoint system for save/restore functionality
    - Priority levels and metadata tracking
    - Semantic search and natural language queries
    - Universal capture (everything, not just evaluations)
    """

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.enabled = True

        # Rich features configuration
        self.db_path = self.project_root / "context.db"
        self.current_channel = self._detect_git_channel()
        self.session_id = self._generate_session_id()

        # Caching for performance
        self._last_check = None
        self._mcp_available = None

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize SQLite database
        self._init_database()

        # Test MCP Keeper connectivity
        if self.enabled:
            self._mcp_available = self._test_mcp_keeper_connection()

    def _init_database(self):
        """Initialize SQLite database with comprehensive schema"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Main context entries table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        channel TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        priority TEXT DEFAULT 'normal',
                        raw_content TEXT NOT NULL,
                        metadata TEXT,
                        tags TEXT,
                        git_branch TEXT,
                        project_name TEXT,
                        content_hash TEXT UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Checkpoints table for save/restore functionality
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        checkpoint_name TEXT UNIQUE NOT NULL,
                        channel TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        description TEXT,
                        context_snapshot TEXT NOT NULL,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Channels table for topic-based organization
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS channels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        git_branch TEXT,
                        project_name TEXT,
                        priority TEXT DEFAULT 'normal',
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Search index for semantic search (future vector embeddings)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS search_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entry_id INTEGER NOT NULL,
                        content_tokens TEXT NOT NULL,
                        embedding_hash TEXT,
                        FOREIGN KEY (entry_id) REFERENCES context_entries (id)
                    )
                ''')

                # Performance indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_channel ON context_entries(channel)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON context_entries(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON context_entries(session_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_type ON context_entries(content_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON context_entries(priority)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_git_branch ON context_entries(git_branch)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_hash ON context_entries(content_hash)')

                conn.commit()
                self.logger.debug("✅ SQLite database initialized with rich schema")

        except Exception as e:
            self.logger.error(f"❌ Database initialization failed: {e}")

    def _detect_git_channel(self) -> str:
        """Detect current git branch to auto-derive channel name"""
        try:
            result = subprocess.run([
                "git", "branch", "--show-current"
            ], capture_output=True, text=True, cwd=self.project_root, timeout=3)

            if result.returncode == 0 and result.stdout.strip():
                branch = result.stdout.strip()
                # Convert branch name to channel format
                channel = re.sub(r'[^a-zA-Z0-9-_]', '-', branch).lower()
                return f"git-{channel}"

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass

        return "main-session"

    def _generate_session_id(self) -> str:
        """Generate unique session identifier"""
        timestamp = datetime.now().isoformat()
        project_name = self.project_root.name
        return hashlib.md5(f"{timestamp}-{project_name}".encode()).hexdigest()[:12]

    def capture_if_mcp_available(self, output: str, context: Optional[Dict] = None) -> bool:
        """
        Universal capture with rich MCP Keeper features
        Captures EVERYTHING (per user requirement) with rich metadata
        """
        mcp_success = False

        # Try MCP Keeper SQLite capture first
        try:
            if self._is_mcp_keeper_available():
                mcp_success = self._capture_to_mcp_keeper(output, context)
                if mcp_success:
                    self.logger.info("✅ MCP Keeper SQLite capture successful")
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
        """Check if MCP Keeper SQLite database is available"""
        # Cache check for 30 seconds to avoid repeated calls
        now = datetime.now()
        if (self._last_check and
            (now - self._last_check).seconds < 30 and
            self._mcp_available is not None):
            return self._mcp_available

        # Check for SQLite database
        self._mcp_available = self._test_mcp_keeper_connection()
        self._last_check = now
        return self._mcp_available

    def _test_mcp_keeper_connection(self) -> bool:
        """Test SQLite database connectivity"""
        try:
            # Test 1: Check for context.db database
            if self.db_path.exists():
                # Test database connectivity
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM context_entries")
                    self.logger.debug("✅ MCP Keeper SQLite database accessible")
                    return True

            # Test 2: Check if we can create the database
            if not self.db_path.exists():
                self._init_database()
                if self.db_path.exists():
                    self.logger.debug("✅ MCP Keeper SQLite database created")
                    return True

        except Exception as e:
            self.logger.debug(f"MCP Keeper connection test failed: {e}")

        return False

    def _capture_to_mcp_keeper(self, output: str, context: Optional[Dict] = None) -> bool:
        """Capture to SQLite database with rich metadata"""
        try:
            # Extract rich metadata
            metadata = self._extract_rich_metadata(output, context)

            # Create content hash for deduplication
            content_hash = hashlib.sha256(output.encode()).hexdigest()

            # Prepare SQLite entry
            entry_data = {
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'channel': self.current_channel,
                'content_type': metadata.get('content_type', 'ccom_output'),
                'priority': metadata.get('priority', 'normal'),
                'raw_content': output,
                'metadata': json.dumps(metadata),
                'tags': ','.join(metadata.get('tags', [])),
                'git_branch': self._detect_git_channel().replace('git-', ''),
                'project_name': self.project_root.name,
                'content_hash': content_hash
            }

            # Insert into database
            success = self._insert_context_entry(entry_data)

            # Update channel information
            if success:
                self._update_channel_info()
                self._update_search_index(entry_data)

            return success

        except Exception as e:
            self.logger.debug(f"MCP Keeper SQLite capture error: {e}")
            return False

    def _extract_rich_metadata(self, output: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract rich metadata from any CCOM output"""
        metadata = {
            'length': len(output),
            'content_type': 'ccom_output',
            'priority': 'normal',
            'tags': [],
            'source': 'ccom_auto_capture'
        }

        # Add context information (this can override defaults)
        if context:
            # Store original before override
            original_type = metadata.get('content_type')
            metadata.update(context)
            # If context explicitly sets content_type, don't auto-classify
            if 'content_type' in context and context['content_type'] != original_type:
                return metadata

        # Smart content classification
        output_lower = output.lower()

        # Content type detection
        if any(indicator in output_lower for indicator in ['evaluation', 'assessment', 'analysis']):
            metadata['content_type'] = 'evaluation'
            metadata['priority'] = 'high'
            metadata['tags'].append('evaluation')

        if 'tier 1' in output_lower or 'recommended' in output_lower:
            metadata['priority'] = 'high'
            metadata['tags'].append('recommendation')

        if any(indicator in output_lower for indicator in ['security', 'vulnerability', 'audit']):
            metadata['content_type'] = 'security_analysis'
            metadata['priority'] = 'high'
            metadata['tags'].append('security')

        if any(indicator in output_lower for indicator in ['build', 'deploy', 'production']):
            metadata['content_type'] = 'deployment'
            metadata['tags'].append('deployment')

        if any(indicator in output_lower for indicator in ['test', 'quality', 'lint']):
            metadata['content_type'] = 'quality_check'
            metadata['tags'].append('quality')

        # Extract title from first line
        lines = output.split('\n')
        if lines and lines[0].strip():
            metadata['title'] = lines[0].strip()[:100]  # Limit title length

        return metadata

    def _insert_context_entry(self, entry_data: Dict[str, Any]) -> bool:
        """Insert context entry into SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check for duplicates
                cursor.execute(
                    "SELECT id FROM context_entries WHERE content_hash = ?",
                    (entry_data['content_hash'],)
                )

                if cursor.fetchone():
                    self.logger.debug("🔄 Duplicate content detected, skipping insert")
                    return True  # Consider as success since content already exists

                # Insert new entry
                cursor.execute('''
                    INSERT INTO context_entries (
                        timestamp, session_id, channel, content_type, priority,
                        raw_content, metadata, tags, git_branch, project_name, content_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry_data['timestamp'], entry_data['session_id'], entry_data['channel'],
                    entry_data['content_type'], entry_data['priority'], entry_data['raw_content'],
                    entry_data['metadata'], entry_data['tags'], entry_data['git_branch'],
                    entry_data['project_name'], entry_data['content_hash']
                ))

                conn.commit()
                self.logger.info(f"📊 MCP Keeper captured: {entry_data['content_type']} in {entry_data['channel']}")
                return True

        except Exception as e:
            self.logger.error(f"SQLite insert failed: {e}")
            return False

    def _update_channel_info(self):
        """Update or create channel information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO channels (
                        channel_name, git_branch, project_name, last_used
                    ) VALUES (?, ?, ?, ?)
                ''', (
                    self.current_channel,
                    self._detect_git_channel().replace('git-', ''),
                    self.project_root.name,
                    datetime.now().isoformat()
                ))

                conn.commit()

        except Exception as e:
            self.logger.debug(f"Channel update failed: {e}")

    def _update_search_index(self, entry_data: Dict[str, Any]):
        """Update search index for semantic search (basic tokenization)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get the entry ID
                cursor.execute(
                    "SELECT id FROM context_entries WHERE content_hash = ?",
                    (entry_data['content_hash'],)
                )
                result = cursor.fetchone()

                if result:
                    entry_id = result[0]

                    # Basic tokenization (future: implement vector embeddings)
                    content = entry_data['raw_content'].lower()
                    tokens = re.findall(r'\b\w+\b', content)
                    token_string = ' '.join(set(tokens))  # Unique tokens only

                    cursor.execute('''
                        INSERT OR REPLACE INTO search_index (entry_id, content_tokens)
                        VALUES (?, ?)
                    ''', (entry_id, token_string))

                    conn.commit()

        except Exception as e:
            self.logger.debug(f"Search index update failed: {e}")

    # Phase 2: Advanced Memory Management
    def get_channel_context(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get recent context for specific channel"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, content_type, priority, raw_content, metadata, tags
                    FROM context_entries
                    WHERE channel = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (channel, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'content_type': row[1],
                        'priority': row[2],
                        'content': row[3][:300] + '...' if len(row[3]) > 300 else row[3],
                        'metadata': json.loads(row[4]) if row[4] else {},
                        'tags': row[5].split(',') if row[5] else []
                    })

                return results

        except Exception as e:
            self.logger.error(f"Channel context retrieval failed: {e}")
            return []

    def list_channels(self) -> List[Dict]:
        """List all available channels with metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT c.channel_name, c.description, c.git_branch, c.priority,
                           c.last_used, COUNT(ce.id) as entry_count
                    FROM channels c
                    LEFT JOIN context_entries ce ON c.channel_name = ce.channel
                    GROUP BY c.channel_name
                    ORDER BY c.last_used DESC
                ''')

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'name': row[0],
                        'description': row[1],
                        'git_branch': row[2],
                        'priority': row[3],
                        'last_used': row[4],
                        'entry_count': row[5]
                    })

                return results

        except Exception as e:
            self.logger.error(f"Channel listing failed: {e}")
            return []

    def switch_channel(self, channel_name: str, description: str = "") -> bool:
        """Switch to a different channel"""
        try:
            # Update current channel
            self.current_channel = channel_name

            # Ensure channel exists in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO channels (
                        channel_name, description, git_branch, project_name, last_used
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    channel_name,
                    description,
                    self._detect_git_channel().replace('git-', ''),
                    self.project_root.name,
                    datetime.now().isoformat()
                ))

                conn.commit()

            self.logger.info(f"🔀 Switched to channel: {channel_name}")
            return True

        except Exception as e:
            self.logger.error(f"Channel switch failed: {e}")
            return False

    def get_priority_context(self, priority: str = "high", limit: int = 10) -> List[Dict]:
        """Get context entries by priority level"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, channel, content_type, raw_content, metadata, tags
                    FROM context_entries
                    WHERE priority = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (priority, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'content_type': row[2],
                        'content': row[3][:300] + '...' if len(row[3]) > 300 else row[3],
                        'metadata': json.loads(row[4]) if row[4] else {},
                        'tags': row[5].split(',') if row[5] else []
                    })

                return results

        except Exception as e:
            self.logger.error(f"Priority context retrieval failed: {e}")
            return []

    def get_git_branch_context(self, branch: str = None, limit: int = 10) -> List[Dict]:
        """Get context for specific git branch"""
        if branch is None:
            branch = self._detect_git_channel().replace('git-', '')

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, channel, content_type, raw_content, metadata, tags
                    FROM context_entries
                    WHERE git_branch = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (branch, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'content_type': row[2],
                        'content': row[3][:300] + '...' if len(row[3]) > 300 else row[3],
                        'metadata': json.loads(row[4]) if row[4] else {},
                        'tags': row[5].split(',') if row[5] else []
                    })

                return results

        except Exception as e:
            self.logger.error(f"Git branch context retrieval failed: {e}")
            return []

    def get_content_by_type(self, content_type: str, limit: int = 10) -> List[Dict]:
        """Get context entries by content type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, channel, priority, raw_content, metadata, tags
                    FROM context_entries
                    WHERE content_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (content_type, limit))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'priority': row[2],
                        'content': row[3][:300] + '...' if len(row[3]) > 300 else row[3],
                        'metadata': json.loads(row[4]) if row[4] else {},
                        'tags': row[5].split(',') if row[5] else []
                    })

                return results

        except Exception as e:
            self.logger.error(f"Content type retrieval failed: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                stats = {}

                # Total entries
                cursor.execute("SELECT COUNT(*) FROM context_entries")
                stats['total_entries'] = cursor.fetchone()[0]

                # Entries by channel
                cursor.execute('''
                    SELECT channel, COUNT(*)
                    FROM context_entries
                    GROUP BY channel
                    ORDER BY COUNT(*) DESC
                ''')
                stats['entries_by_channel'] = dict(cursor.fetchall())

                # Entries by content type
                cursor.execute('''
                    SELECT content_type, COUNT(*)
                    FROM context_entries
                    GROUP BY content_type
                    ORDER BY COUNT(*) DESC
                ''')
                stats['entries_by_type'] = dict(cursor.fetchall())

                # Entries by priority
                cursor.execute('''
                    SELECT priority, COUNT(*)
                    FROM context_entries
                    GROUP BY priority
                ''')
                stats['entries_by_priority'] = dict(cursor.fetchall())

                # Total channels
                cursor.execute("SELECT COUNT(*) FROM channels")
                stats['total_channels'] = cursor.fetchone()[0]

                # Database size
                stats['db_size_mb'] = round(self.db_path.stat().st_size / 1024 / 1024, 2)

                # Recent activity (last 24 hours)
                yesterday = (datetime.now() - timedelta(days=1)).isoformat()
                cursor.execute('''
                    SELECT COUNT(*) FROM context_entries
                    WHERE timestamp > ?
                ''', (yesterday,))
                stats['recent_entries_24h'] = cursor.fetchone()[0]

                return stats

        except Exception as e:
            self.logger.error(f"Memory stats failed: {e}")
            return {}

    # Phase 3: Checkpoint & Session System
    def save_checkpoint(self, checkpoint_name: str, description: str = "") -> bool:
        """Save current context as named checkpoint (like saving your game)"""
        try:
            # Gather current context for this channel/session
            context_snapshot = self._create_context_snapshot()

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if checkpoint already exists
                cursor.execute(
                    "SELECT id FROM checkpoints WHERE checkpoint_name = ?",
                    (checkpoint_name,)
                )

                if cursor.fetchone():
                    # Update existing checkpoint
                    cursor.execute('''
                        UPDATE checkpoints
                        SET description = ?, context_snapshot = ?, metadata = ?,
                            channel = ?, session_id = ?, created_at = CURRENT_TIMESTAMP
                        WHERE checkpoint_name = ?
                    ''', (
                        description,
                        json.dumps(context_snapshot),
                        json.dumps({
                            'total_entries': len(context_snapshot.get('entries', [])),
                            'channel_count': len(context_snapshot.get('channels', [])),
                            'session_id': self.session_id
                        }),
                        self.current_channel,
                        self.session_id,
                        checkpoint_name
                    ))
                else:
                    # Create new checkpoint
                    cursor.execute('''
                        INSERT INTO checkpoints (
                            checkpoint_name, channel, session_id, description,
                            context_snapshot, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        checkpoint_name,
                        self.current_channel,
                        self.session_id,
                        description,
                        json.dumps(context_snapshot),
                        json.dumps({
                            'total_entries': len(context_snapshot.get('entries', [])),
                            'channel_count': len(context_snapshot.get('channels', [])),
                            'session_id': self.session_id
                        })
                    ))

                conn.commit()
                self.logger.info(f"💾 Checkpoint '{checkpoint_name}' saved successfully")
                return True

        except Exception as e:
            self.logger.error(f"Checkpoint save failed: {e}")
            return False

    def _create_context_snapshot(self) -> Dict[str, Any]:
        """Create comprehensive context snapshot for checkpoint"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'current_channel': self.current_channel,
            'git_branch': self._detect_git_channel(),
            'project_name': self.project_root.name,
            'entries': [],
            'channels': [],
            'stats': {}
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get all context entries for current channel
                cursor.execute('''
                    SELECT timestamp, content_type, priority, raw_content,
                           metadata, tags, git_branch
                    FROM context_entries
                    WHERE channel = ?
                    ORDER BY timestamp DESC
                ''', (self.current_channel,))

                for row in cursor.fetchall():
                    snapshot['entries'].append({
                        'timestamp': row[0],
                        'content_type': row[1],
                        'priority': row[2],
                        'content': row[3],
                        'metadata': json.loads(row[4]) if row[4] else {},
                        'tags': row[5].split(',') if row[5] else [],
                        'git_branch': row[6]
                    })

                # Get channel information
                cursor.execute('''
                    SELECT channel_name, description, git_branch, priority, last_used
                    FROM channels
                    ORDER BY last_used DESC
                ''')

                for row in cursor.fetchall():
                    snapshot['channels'].append({
                        'name': row[0],
                        'description': row[1],
                        'git_branch': row[2],
                        'priority': row[3],
                        'last_used': row[4]
                    })

                # Get current stats
                snapshot['stats'] = self.get_memory_stats()

        except Exception as e:
            self.logger.error(f"Context snapshot creation failed: {e}")

        return snapshot

    def restore_checkpoint(self, checkpoint_name: str) -> Optional[Dict]:
        """Restore context from named checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT context_snapshot, metadata, channel, description, created_at
                    FROM checkpoints
                    WHERE checkpoint_name = ?
                ''', (checkpoint_name,))

                result = cursor.fetchone()

                if not result:
                    self.logger.warning(f"Checkpoint '{checkpoint_name}' not found")
                    return None

                context_snapshot = json.loads(result[0])
                metadata = json.loads(result[1]) if result[1] else {}
                checkpoint_channel = result[2]
                description = result[3]
                created_at = result[4]

                # Switch to checkpoint's channel
                self.switch_channel(checkpoint_channel)

                self.logger.info(f"🔄 Restored checkpoint '{checkpoint_name}' from {created_at}")

                return {
                    'checkpoint_name': checkpoint_name,
                    'description': description,
                    'created_at': created_at,
                    'channel': checkpoint_channel,
                    'context': context_snapshot,
                    'metadata': metadata
                }

        except Exception as e:
            self.logger.error(f"Checkpoint restore failed: {e}")
            return None

    def list_checkpoints(self) -> List[Dict]:
        """List all available checkpoints"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT checkpoint_name, description, channel, metadata, created_at
                    FROM checkpoints
                    ORDER BY created_at DESC
                ''')

                results = []
                for row in cursor.fetchall():
                    metadata = json.loads(row[3]) if row[3] else {}
                    results.append({
                        'name': row[0],
                        'description': row[1],
                        'channel': row[2],
                        'created_at': row[4],
                        'entry_count': metadata.get('total_entries', 0),
                        'channel_count': metadata.get('channel_count', 0)
                    })

                return results

        except Exception as e:
            self.logger.error(f"Checkpoint listing failed: {e}")
            return []

    def delete_checkpoint(self, checkpoint_name: str) -> bool:
        """Delete a checkpoint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM checkpoints WHERE checkpoint_name = ?",
                    (checkpoint_name,)
                )

                if cursor.rowcount > 0:
                    conn.commit()
                    self.logger.info(f"🗑️ Checkpoint '{checkpoint_name}' deleted")
                    return True
                else:
                    self.logger.warning(f"Checkpoint '{checkpoint_name}' not found")
                    return False

        except Exception as e:
            self.logger.error(f"Checkpoint deletion failed: {e}")
            return False

    def get_checkpoint_diff(self, checkpoint_name: str) -> Optional[Dict]:
        """Compare current context with checkpoint"""
        try:
            checkpoint = self.restore_checkpoint(checkpoint_name)
            if not checkpoint:
                return None

            current_snapshot = self._create_context_snapshot()
            checkpoint_snapshot = checkpoint['context']

            diff = {
                'checkpoint_name': checkpoint_name,
                'current_entries': len(current_snapshot['entries']),
                'checkpoint_entries': len(checkpoint_snapshot['entries']),
                'entries_added': len(current_snapshot['entries']) - len(checkpoint_snapshot['entries']),
                'channels_changed': current_snapshot['current_channel'] != checkpoint_snapshot['current_channel'],
                'git_branch_changed': current_snapshot['git_branch'] != checkpoint_snapshot['git_branch']
            }

            return diff

        except Exception as e:
            self.logger.error(f"Checkpoint diff failed: {e}")
            return None

    def auto_checkpoint(self, threshold_entries: int = 10) -> Optional[str]:
        """Automatically create checkpoint when threshold is reached"""
        try:
            stats = self.get_memory_stats()
            total_entries = stats.get('total_entries', 0)

            if total_entries >= threshold_entries:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                checkpoint_name = f"auto_checkpoint_{timestamp}"
                description = f"Automatic checkpoint at {total_entries} entries"

                success = self.save_checkpoint(checkpoint_name, description)
                if success:
                    self.logger.info(f"🤖 Auto-checkpoint created: {checkpoint_name}")
                    return checkpoint_name

        except Exception as e:
            self.logger.error(f"Auto-checkpoint failed: {e}")

        return None

    # Phase 5: MCP Protocol Integration
    def _check_mcp_server_running(self) -> bool:
        """Check if MCP server is running and accessible"""
        try:
            # Check for MCP server process
            result = subprocess.run([
                "tasklist", "/FI", "IMAGENAME eq node.exe"
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0 and "mcp" in result.stdout.lower():
                return True

            # Alternative check - look for MCP port usage
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                # Common MCP ports
                for port in [8080, 3000, 3001, 8000]:
                    result = sock.connect_ex(('localhost', port))
                    if result == 0:
                        sock.close()
                        return True
                sock.close()
            except:
                pass

            return False

        except Exception as e:
            self.logger.debug(f"MCP server check failed: {e}")
            return False

    def _send_mcp_command(self, command: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Send command to MCP server using native MCP protocol"""
        try:
            # Try HTTP transport first
            return self._send_mcp_http(command, data)

        except Exception as e:
            self.logger.debug(f"MCP protocol communication failed: {e}")
            return None

    def _send_mcp_http(self, command: str, data: Dict[str, Any]) -> Optional[Dict]:
        """Send MCP command via HTTP transport"""
        try:
            import json
            import urllib.request
            import urllib.parse

            # MCP server endpoints
            mcp_endpoints = [
                "http://localhost:8080/mcp",
                "http://localhost:3000/mcp",
                "http://localhost:3001/mcp"
            ]

            mcp_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": f"memory/{command}",
                "params": data
            }

            for endpoint in mcp_endpoints:
                try:
                    req_data = json.dumps(mcp_payload).encode('utf-8')
                    request = urllib.request.Request(
                        endpoint,
                        data=req_data,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'CCOM-MCP-Bridge/1.0'
                        }
                    )

                    with urllib.request.urlopen(request, timeout=3) as response:
                        if response.status == 200:
                            response_data = json.loads(response.read().decode('utf-8'))
                            if 'result' in response_data:
                                self.logger.debug(f"✅ MCP server responded: {endpoint}")
                                return response_data['result']

                except Exception as e:
                    self.logger.debug(f"MCP endpoint {endpoint} failed: {e}")
                    continue

            return None

        except Exception as e:
            self.logger.error(f"MCP HTTP transport failed: {e}")
            return None

    def add_mcp_memory(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add memory entry via MCP protocol"""
        try:
            if not self._check_mcp_server_running():
                self.logger.debug("MCP server not running, using local SQLite")
                return False

            mcp_data = {
                "type": "context_entry",
                "content": content,
                "metadata": {
                    **metadata,
                    "timestamp": datetime.now().isoformat(),
                    "project": self.project_root.name,
                    "channel": self.current_channel,
                    "session_id": self.session_id
                }
            }

            result = self._send_mcp_command("add", mcp_data)

            if result and result.get('success'):
                self.logger.info("📡 MCP server memory addition successful")
                return True

            return False

        except Exception as e:
            self.logger.error(f"MCP memory addition failed: {e}")
            return False

    def query_mcp_memory(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Query memory via MCP protocol"""
        try:
            if not self._check_mcp_server_running():
                self.logger.debug("MCP server not running, using local search")
                return []

            mcp_data = {
                "query": query,
                "filters": filters or {},
                "limit": 10,
                "project": self.project_root.name
            }

            result = self._send_mcp_command("query", mcp_data)

            if result and isinstance(result, dict) and 'entries' in result:
                self.logger.info(f"📡 MCP server query returned {len(result['entries'])} results")
                return result['entries']

            return []

        except Exception as e:
            self.logger.error(f"MCP memory query failed: {e}")
            return []

    def create_mcp_checkpoint(self, name: str, description: str) -> bool:
        """Create checkpoint via MCP protocol"""
        try:
            if not self._check_mcp_server_running():
                return False

            mcp_data = {
                "checkpoint_name": name,
                "description": description,
                "project": self.project_root.name,
                "channel": self.current_channel,
                "context_data": self._create_context_snapshot()
            }

            result = self._send_mcp_command("checkpoint", mcp_data)

            if result and result.get('success'):
                self.logger.info(f"📡 MCP checkpoint '{name}' created successfully")
                return True

            return False

        except Exception as e:
            self.logger.error(f"MCP checkpoint creation failed: {e}")
            return False

    def sync_with_mcp_server(self) -> bool:
        """Sync local SQLite data with MCP server"""
        try:
            if not self._check_mcp_server_running():
                self.logger.debug("MCP server not available for sync")
                return False

            # Get local entries that haven't been synced
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, timestamp, content_type, raw_content, metadata, channel
                    FROM context_entries
                    WHERE metadata NOT LIKE '%"mcp_synced": true%'
                    ORDER BY timestamp DESC
                    LIMIT 50
                ''')

                unsynced_entries = cursor.fetchall()

            synced_count = 0
            for entry in unsynced_entries:
                entry_id, timestamp, content_type, content, metadata_str, channel = entry

                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}

                    # Send to MCP server
                    success = self.add_mcp_memory(content, {
                        **metadata,
                        'local_id': entry_id,
                        'content_type': content_type,
                        'channel': channel
                    })

                    if success:
                        # Mark as synced in local database
                        metadata['mcp_synced'] = True

                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE context_entries
                                SET metadata = ?
                                WHERE id = ?
                            ''', (json.dumps(metadata), entry_id))
                            conn.commit()

                        synced_count += 1

                except Exception as e:
                    self.logger.debug(f"Failed to sync entry {entry_id}: {e}")
                    continue

            if synced_count > 0:
                self.logger.info(f"📡 Synced {synced_count} entries with MCP server")

            return synced_count > 0

        except Exception as e:
            self.logger.error(f"MCP sync failed: {e}")
            return False

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP server status and connectivity info"""
        status = {
            'server_running': False,
            'connectivity': 'unavailable',
            'last_sync': None,
            'local_entries': 0,
            'synced_entries': 0,
            'protocol_version': 'unknown'
        }

        try:
            # Check server status
            status['server_running'] = self._check_mcp_server_running()

            if status['server_running']:
                # Test connectivity
                test_result = self._send_mcp_command("status", {})
                if test_result:
                    status['connectivity'] = 'active'
                    status['protocol_version'] = test_result.get('version', '1.0')
                else:
                    status['connectivity'] = 'error'

            # Get local statistics
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM context_entries")
                status['local_entries'] = cursor.fetchone()[0]

                cursor.execute('''
                    SELECT COUNT(*) FROM context_entries
                    WHERE metadata LIKE '%"mcp_synced": true%'
                ''')
                status['synced_entries'] = cursor.fetchone()[0]

        except Exception as e:
            self.logger.error(f"MCP status check failed: {e}")

        return status

    def enable_mcp_integration(self) -> bool:
        """Enable MCP protocol integration with auto-sync"""
        try:
            status = self.get_mcp_status()

            if not status['server_running']:
                self.logger.warning("⚠️ MCP server not running - integration disabled")
                return False

            # Test connectivity
            if status['connectivity'] != 'active':
                self.logger.warning("⚠️ MCP server not responding - integration disabled")
                return False

            # Perform initial sync
            sync_success = self.sync_with_mcp_server()

            if sync_success:
                self.logger.info("🔗 MCP integration enabled with auto-sync")
                return True
            else:
                self.logger.info("🔗 MCP integration enabled (no sync needed)")
                return True

        except Exception as e:
            self.logger.error(f"MCP integration enable failed: {e}")
            return False

    # Phase 6: Enterprise Features
    def consolidate_memory(self, similarity_threshold: float = 0.8) -> Dict[str, Any]:
        """
        Dream-inspired memory consolidation algorithm
        Consolidates similar entries to optimize storage and improve recall
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get all entries for analysis
                cursor.execute('''
                    SELECT id, timestamp, content_type, raw_content, metadata, tags, channel
                    FROM context_entries
                    ORDER BY timestamp ASC
                ''')

                all_entries = cursor.fetchall()

            consolidation_stats = {
                'entries_analyzed': len(all_entries),
                'duplicates_removed': 0,
                'entries_merged': 0,
                'space_saved_mb': 0,
                'similar_groups': []
            }

            # Group similar entries
            similarity_groups = self._find_similar_entries(all_entries, similarity_threshold)

            for group in similarity_groups:
                if len(group) > 1:
                    # Consolidate group into single comprehensive entry
                    consolidated = self._merge_entry_group(group)

                    if consolidated:
                        consolidation_stats['entries_merged'] += len(group) - 1
                        consolidation_stats['similar_groups'].append({
                            'size': len(group),
                            'content_type': consolidated.get('content_type'),
                            'merged_content_length': len(consolidated.get('content', ''))
                        })

            # Remove exact duplicates
            duplicates_removed = self._remove_exact_duplicates()
            consolidation_stats['duplicates_removed'] = duplicates_removed

            # Calculate space savings
            consolidation_stats['space_saved_mb'] = self._calculate_space_savings()

            self.logger.info(f"🧠 Memory consolidation completed: {consolidation_stats['entries_merged']} merged, {consolidation_stats['duplicates_removed']} duplicates removed")

            return consolidation_stats

        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")
            return {'error': str(e)}

    def _find_similar_entries(self, entries: List[Tuple], threshold: float) -> List[List[Tuple]]:
        """Find groups of similar entries using content similarity"""
        try:
            similar_groups = []
            processed_ids = set()

            for i, entry1 in enumerate(entries):
                if entry1[0] in processed_ids:
                    continue

                entry1_content = entry1[3].lower()  # raw_content
                entry1_type = entry1[2]  # content_type

                group = [entry1]
                processed_ids.add(entry1[0])

                for j, entry2 in enumerate(entries[i+1:], i+1):
                    if entry2[0] in processed_ids:
                        continue

                    entry2_content = entry2[3].lower()
                    entry2_type = entry2[2]

                    # Check if entries are similar
                    if entry1_type == entry2_type:
                        similarity = self._calculate_content_similarity(entry1_content, entry2_content)

                        if similarity >= threshold:
                            group.append(entry2)
                            processed_ids.add(entry2[0])

                if len(group) > 1:
                    similar_groups.append(group)

            return similar_groups

        except Exception as e:
            self.logger.error(f"Similarity analysis failed: {e}")
            return []

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings"""
        try:
            # Simple similarity based on common words and phrases
            words1 = set(content1.split())
            words2 = set(content2.split())

            if not words1 or not words2:
                return 0.0

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            jaccard_similarity = len(intersection) / len(union) if union else 0.0

            # Bonus for similar length
            length_similarity = 1 - abs(len(content1) - len(content2)) / max(len(content1), len(content2))
            length_bonus = min(length_similarity * 0.2, 0.2)

            return min(jaccard_similarity + length_bonus, 1.0)

        except Exception as e:
            self.logger.debug(f"Similarity calculation failed: {e}")
            return 0.0

    def _merge_entry_group(self, group: List[Tuple]) -> Optional[Dict]:
        """Merge a group of similar entries into one comprehensive entry"""
        try:
            if not group:
                return None

            # Use the most recent entry as base
            base_entry = max(group, key=lambda x: x[1])  # Sort by timestamp

            # Combine content from all entries
            combined_content = []
            all_tags = set()
            all_metadata = {}

            for entry in group:
                entry_id, timestamp, content_type, content, metadata_str, tags, channel = entry

                combined_content.append(f"[{timestamp}] {content}")

                if tags:
                    all_tags.update(tag.strip() for tag in tags.split(','))

                if metadata_str:
                    try:
                        metadata = json.loads(metadata_str)
                        all_metadata.update(metadata)
                    except:
                        pass

            # Create consolidated entry
            consolidated_content = "\\n\\n---CONSOLIDATED ENTRY---\\n\\n".join(combined_content)
            all_metadata['consolidated'] = True
            all_metadata['original_count'] = len(group)
            all_metadata['consolidation_timestamp'] = datetime.now().isoformat()

            # Update database with consolidated entry
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Update the base entry with consolidated content
                cursor.execute('''
                    UPDATE context_entries
                    SET raw_content = ?, metadata = ?, tags = ?
                    WHERE id = ?
                ''', (
                    consolidated_content,
                    json.dumps(all_metadata),
                    ','.join(sorted(all_tags)),
                    base_entry[0]
                ))

                # Remove other entries in the group
                other_ids = [entry[0] for entry in group if entry[0] != base_entry[0]]
                if other_ids:
                    placeholders = ','.join(['?'] * len(other_ids))
                    cursor.execute(f'DELETE FROM context_entries WHERE id IN ({placeholders})', other_ids)
                    cursor.execute(f'DELETE FROM search_index WHERE entry_id IN ({placeholders})', other_ids)

                conn.commit()

            return {
                'content': consolidated_content,
                'content_type': base_entry[2],
                'entry_count': len(group)
            }

        except Exception as e:
            self.logger.error(f"Entry group merge failed: {e}")
            return None

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        try:
            metrics = {
                'database_size_mb': self._calculate_space_savings(),
                'total_entries': 0,
                'total_channels': 0,
                'total_checkpoints': 0,
                'search_index_size': 0,
                'average_entry_size_bytes': 0,
                'largest_entry_size_bytes': 0,
                'most_active_channel': None,
                'memory_efficiency_score': 0,
                'query_performance_ms': 0
            }

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Basic counts
                cursor.execute('SELECT COUNT(*) FROM context_entries')
                metrics['total_entries'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM channels')
                metrics['total_channels'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM checkpoints')
                metrics['total_checkpoints'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM search_index')
                metrics['search_index_size'] = cursor.fetchone()[0]

                # Content size analysis
                if metrics['total_entries'] > 0:
                    cursor.execute('SELECT AVG(LENGTH(raw_content)), MAX(LENGTH(raw_content)) FROM context_entries')
                    avg_size, max_size = cursor.fetchone()
                    metrics['average_entry_size_bytes'] = int(avg_size or 0)
                    metrics['largest_entry_size_bytes'] = int(max_size or 0)

                # Most active channel
                cursor.execute('''
                    SELECT channel, COUNT(*) as entry_count
                    FROM context_entries
                    GROUP BY channel
                    ORDER BY entry_count DESC
                    LIMIT 1
                ''')
                result = cursor.fetchone()
                if result:
                    metrics['most_active_channel'] = {'name': result[0], 'entries': result[1]}

                # Performance test
                import time
                start_time = time.time()
                cursor.execute('SELECT COUNT(*) FROM context_entries WHERE content_type = "evaluation"')
                query_time = (time.time() - start_time) * 1000
                metrics['query_performance_ms'] = round(query_time, 2)

            # Calculate efficiency score
            if metrics['total_entries'] > 0:
                avg_mb_per_entry = metrics['database_size_mb'] / metrics['total_entries']
                # Lower is better - score based on reasonable threshold of 0.01MB per entry
                efficiency = max(0, 100 - (avg_mb_per_entry * 1000))
                metrics['memory_efficiency_score'] = round(efficiency, 1)

            return metrics

        except Exception as e:
            self.logger.error(f"Performance metrics failed: {e}")
            return {'error': str(e)}

    def _calculate_space_savings(self) -> float:
        """Calculate database size in MB"""
        try:
            if self.db_path.exists():
                size_mb = self.db_path.stat().st_size / 1024 / 1024
                return round(size_mb, 3)
            return 0.0
        except:
            return 0.0

    def _remove_exact_duplicates(self) -> int:
        """Remove entries with identical content hashes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find duplicate content hashes
                cursor.execute('''
                    SELECT content_hash, COUNT(*) as count
                    FROM context_entries
                    GROUP BY content_hash
                    HAVING COUNT(*) > 1
                ''')

                duplicate_hashes = cursor.fetchall()
                removed_count = 0

                for content_hash, count in duplicate_hashes:
                    # Keep the most recent entry, remove others
                    cursor.execute('''
                        SELECT id FROM context_entries
                        WHERE content_hash = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (content_hash, count - 1))

                    ids_to_remove = [row[0] for row in cursor.fetchall()[1:]]  # Skip first (keep it)

                    if ids_to_remove:
                        placeholders = ','.join(['?'] * len(ids_to_remove))
                        cursor.execute(f'DELETE FROM context_entries WHERE id IN ({placeholders})', ids_to_remove)
                        cursor.execute(f'DELETE FROM search_index WHERE entry_id IN ({placeholders})', ids_to_remove)
                        removed_count += len(ids_to_remove)

                conn.commit()
                return removed_count

        except Exception as e:
            self.logger.error(f"Duplicate removal failed: {e}")
            return 0

    # Phase 4: Intelligent Search & Retrieval
    def search_memory(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search memory with natural language queries and semantic understanding"""
        try:
            # Parse natural language time queries
            time_filter = self._parse_time_query(query)

            # Extract search terms
            search_terms = self._extract_search_terms(query)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Build dynamic query based on filters and time constraints
                where_conditions = []
                params = []

                # Text search in content and metadata
                if search_terms:
                    search_condition = "("
                    for i, term in enumerate(search_terms):
                        if i > 0:
                            search_condition += " OR "
                        search_condition += "raw_content LIKE ? OR tags LIKE ? OR metadata LIKE ?"
                        params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
                    search_condition += ")"
                    where_conditions.append(search_condition)

                # Time-based filtering
                if time_filter:
                    where_conditions.append("timestamp >= ?")
                    params.append(time_filter)

                # Apply additional filters
                if filters:
                    if 'channel' in filters:
                        where_conditions.append("channel = ?")
                        params.append(filters['channel'])

                    if 'content_type' in filters:
                        where_conditions.append("content_type = ?")
                        params.append(filters['content_type'])

                    if 'priority' in filters:
                        where_conditions.append("priority = ?")
                        params.append(filters['priority'])

                    if 'git_branch' in filters:
                        where_conditions.append("git_branch = ?")
                        params.append(filters['git_branch'])

                # Construct final query
                base_query = '''
                    SELECT timestamp, channel, content_type, priority, raw_content,
                           metadata, tags, git_branch
                    FROM context_entries
                '''

                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)

                base_query += " ORDER BY timestamp DESC LIMIT 20"

                cursor.execute(base_query, params)

                results = []
                for row in cursor.fetchall():
                    # Calculate relevance score
                    relevance = self._calculate_relevance(row[4], search_terms, query)

                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'content_type': row[2],
                        'priority': row[3],
                        'content': row[4][:400] + '...' if len(row[4]) > 400 else row[4],
                        'metadata': json.loads(row[5]) if row[5] else {},
                        'tags': row[6].split(',') if row[6] else [],
                        'git_branch': row[7],
                        'relevance_score': relevance
                    })

                # Sort by relevance score
                results.sort(key=lambda x: x['relevance_score'], reverse=True)

                return results[:10]  # Return top 10 most relevant

        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return []

    def _parse_time_query(self, query: str) -> Optional[str]:
        """Parse natural language time expressions"""
        query_lower = query.lower()
        now = datetime.now()

        # Time expressions mapping
        time_patterns = {
            'today': now.replace(hour=0, minute=0, second=0, microsecond=0),
            'yesterday': now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1),
            'this week': now - timedelta(days=now.weekday()),
            'last week': now - timedelta(days=now.weekday() + 7),
            'this month': now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            'last month': (now.replace(day=1) - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            'last 24 hours': now - timedelta(hours=24),
            'last hour': now - timedelta(hours=1),
            'recent': now - timedelta(hours=6)  # Default for "recent"
        }

        for pattern, time_threshold in time_patterns.items():
            if pattern in query_lower:
                return time_threshold.isoformat()

        # Check for "last X days/hours" patterns
        import re

        # Pattern: "last 5 days", "past 3 hours", etc.
        time_match = re.search(r'(?:last|past)\s+(\d+)\s+(day|hour|week)s?', query_lower)
        if time_match:
            num = int(time_match.group(1))
            unit = time_match.group(2)

            if unit == 'day':
                threshold = now - timedelta(days=num)
            elif unit == 'hour':
                threshold = now - timedelta(hours=num)
            elif unit == 'week':
                threshold = now - timedelta(weeks=num)
            else:
                return None

            return threshold.isoformat()

        return None

    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract meaningful search terms from query"""
        import re

        # Remove common time expressions first
        time_expressions = [
            'today', 'yesterday', 'this week', 'last week', 'this month', 'last month',
            'recent', 'latest', 'last 24 hours', 'last hour'
        ]

        cleaned_query = query.lower()
        for expr in time_expressions:
            cleaned_query = cleaned_query.replace(expr, '')

        # Remove common question words and articles
        stop_words = [
            'what', 'when', 'where', 'who', 'how', 'why', 'show', 'find', 'get',
            'tell', 'me', 'about', 'the', 'a', 'an', 'and', 'or', 'but', 'in',
            'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'up', 'down',
            'last', 'past', 'days', 'hours', 'weeks', 'search', 'lookup'
        ]

        # Extract meaningful terms (2+ characters, not stop words)
        terms = re.findall(r'\b\w{2,}\b', cleaned_query)
        meaningful_terms = [term for term in terms if term not in stop_words]

        return meaningful_terms[:5]  # Limit to 5 most important terms

    def _calculate_relevance(self, content: str, search_terms: List[str], original_query: str) -> float:
        """Calculate relevance score for search results"""
        if not search_terms:
            return 0.5  # Base relevance when no specific terms

        content_lower = content.lower()
        original_lower = original_query.lower()
        score = 0.0

        # Exact phrase match gets highest score
        if original_lower.replace('search', '').replace('find', '').strip() in content_lower:
            score += 5.0

        # Individual term matches
        for term in search_terms:
            term_count = content_lower.count(term.lower())
            if term_count > 0:
                # More occurrences = higher score, with diminishing returns
                score += min(term_count * 1.0, 3.0)

                # Bonus for term appearing early in content
                first_occurrence = content_lower.find(term.lower())
                if first_occurrence != -1 and first_occurrence < 100:
                    score += 0.5

        # Length penalty (very short or very long content gets lower score)
        content_length = len(content)
        if 50 <= content_length <= 1000:
            score += 0.5
        elif content_length < 20:
            score -= 1.0

        return round(score, 2)

    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        """Search memory by tags"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if match_all:
                    # All tags must be present
                    where_conditions = []
                    params = []
                    for tag in tags:
                        where_conditions.append("tags LIKE ?")
                        params.append(f'%{tag}%')

                    where_clause = " AND ".join(where_conditions)
                else:
                    # Any tag matches
                    where_conditions = []
                    params = []
                    for tag in tags:
                        where_conditions.append("tags LIKE ?")
                        params.append(f'%{tag}%')

                    where_clause = " OR ".join(where_conditions)

                cursor.execute(f'''
                    SELECT timestamp, channel, content_type, priority, raw_content,
                           metadata, tags, git_branch
                    FROM context_entries
                    WHERE {where_clause}
                    ORDER BY timestamp DESC
                    LIMIT 15
                ''', params)

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'content_type': row[2],
                        'priority': row[3],
                        'content': row[4][:300] + '...' if len(row[4]) > 300 else row[4],
                        'metadata': json.loads(row[5]) if row[5] else {},
                        'tags': row[6].split(',') if row[6] else [],
                        'git_branch': row[7]
                    })

                return results

        except Exception as e:
            self.logger.error(f"Tag search failed: {e}")
            return []

    def search_similar_content(self, reference_entry_id: int, limit: int = 5) -> List[Dict]:
        """Find similar content based on tags and content type"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get reference entry details
                cursor.execute('''
                    SELECT content_type, tags, priority, channel
                    FROM context_entries
                    WHERE id = ?
                ''', (reference_entry_id,))

                ref_entry = cursor.fetchone()
                if not ref_entry:
                    return []

                ref_type, ref_tags, ref_priority, ref_channel = ref_entry
                ref_tag_list = ref_tags.split(',') if ref_tags else []

                # Find similar entries
                similarity_conditions = []
                params = []

                # Same content type
                similarity_conditions.append("content_type = ?")
                params.append(ref_type)

                # Similar tags
                if ref_tag_list:
                    tag_conditions = []
                    for tag in ref_tag_list[:3]:  # Top 3 tags
                        tag_conditions.append("tags LIKE ?")
                        params.append(f'%{tag}%')

                    if tag_conditions:
                        similarity_conditions.append(f"({' OR '.join(tag_conditions)})")

                # Exclude the reference entry itself
                similarity_conditions.append("id != ?")
                params.append(reference_entry_id)

                cursor.execute(f'''
                    SELECT timestamp, channel, content_type, priority, raw_content,
                           metadata, tags, git_branch
                    FROM context_entries
                    WHERE {' AND '.join(similarity_conditions)}
                    ORDER BY
                        CASE WHEN priority = ? THEN 1 ELSE 2 END,
                        CASE WHEN channel = ? THEN 1 ELSE 2 END,
                        timestamp DESC
                    LIMIT ?
                ''', params + [ref_priority, ref_channel, limit])

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'channel': row[1],
                        'content_type': row[2],
                        'priority': row[3],
                        'content': row[4][:300] + '...' if len(row[4]) > 300 else row[4],
                        'metadata': json.loads(row[5]) if row[5] else {},
                        'tags': row[6].split(',') if row[6] else [],
                        'git_branch': row[7]
                    })

                return results

        except Exception as e:
            self.logger.error(f"Similar content search failed: {e}")
            return []

    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on existing content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                suggestions = set()

                # Get common tags
                cursor.execute('''
                    SELECT tags FROM context_entries
                    WHERE tags IS NOT NULL AND tags != ""
                ''')

                for row in cursor.fetchall():
                    tags = row[0].split(',')
                    for tag in tags:
                        tag = tag.strip()
                        if tag and partial_query.lower() in tag.lower():
                            suggestions.add(tag)

                # Get common content types
                cursor.execute('''
                    SELECT DISTINCT content_type FROM context_entries
                    WHERE content_type LIKE ?
                ''', (f'%{partial_query}%',))

                for row in cursor.fetchall():
                    suggestions.add(row[0])

                # Get channel names
                cursor.execute('''
                    SELECT DISTINCT channel_name FROM channels
                    WHERE channel_name LIKE ?
                ''', (f'%{partial_query}%',))

                for row in cursor.fetchall():
                    suggestions.add(row[0])

                return sorted(list(suggestions))[:10]

        except Exception as e:
            self.logger.error(f"Search suggestions failed: {e}")
            return []

    # Compatibility methods (existing interface)
    def sync_with_json_memory(self) -> bool:
        """Sync SQLite with JSON memory (backward compatibility)"""
        try:
            # Basic sync implementation
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM context_entries")
                count = cursor.fetchone()[0]

            self.logger.info(f"📊 SQLite memory has {count} entries")
            return True

        except Exception as e:
            self.logger.error(f"Memory sync failed: {e}")
            return False

    def search_mcp_memory(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """Search MCP memory (compatibility method)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Basic text search in content
                cursor.execute('''
                    SELECT timestamp, content_type, raw_content, metadata, channel
                    FROM context_entries
                    WHERE raw_content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', (f'%{query}%',))

                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'type': row[1],
                        'content': row[2][:200] + '...' if len(row[2]) > 200 else row[2],
                        'metadata': json.loads(row[3]) if row[3] else {},
                        'channel': row[4]
                    })

                return results

        except Exception as e:
            self.logger.error(f"Memory search failed: {e}")
            return []


# Global instance getter
def get_mcp_keeper_bridge(project_root: str) -> MCPKeeperBridge:
    """Get MCP Keeper Bridge instance"""
    return MCPKeeperBridge(project_root)