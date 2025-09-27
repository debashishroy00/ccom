"""MCP Direct Integration for CCOM - Phase 1 Implementation

Replaces problematic dual memory system with direct MCP Memory Keeper requests through Claude.
Eliminates coordination issues between Node.js legacy system and Python MCP bridge.
"""

from typing import Dict, List, Optional
import json
import os
from datetime import datetime


class MCPDirectIntegration:
    """Direct integration with MCP Memory Keeper via Claude"""

    def __init__(self, project_name: str = None):
        self.project_name = project_name or self._get_project_name()

    def _get_project_name(self) -> str:
        """Get project name from directory"""
        return os.path.basename(os.getcwd())

    def save_feature(self, feature_name: str, description: str, status: str = "active") -> bool:
        """Save feature directly to MCP Memory Keeper via Claude"""

        print(f"\n🧠 CCOM requesting MCP save for feature: {feature_name}")
        print("=" * 60)
        print("Claude: Please execute this MCP Memory Keeper operation:")
        print(f"""
mcp_context_save({{
    key: '{feature_name}',
    value: '{description}',
    category: 'feature',
    priority: 'high',
    channel: '{self.project_name}',
    metadata: {{
        status: '{status}',
        created_by: 'ccom',
        timestamp: '{datetime.now().isoformat()}'
    }}
}})
        """)
        print("=" * 60)

        # Claude will execute the MCP operation
        # For now, return True to indicate request was made
        return True

    def check_feature_exists(self, feature_name: str) -> List[Dict]:
        """Check for existing features via MCP Memory Keeper"""

        print(f"\n🔍 CCOM requesting MCP search for: {feature_name}")
        print("=" * 60)
        print("Claude: Please execute this MCP Memory Keeper search:")
        print(f"""
mcp_context_search({{
    query: '{feature_name}',
    category: 'feature',
    channel: '{self.project_name}'
}})

Return the results so CCOM can check for duplicates.
If any features are found, display them in this format:
- Feature: <name> | Description: <description> | Status: <status>
        """)
        print("=" * 60)

        # Claude will execute and return results
        # For now, return empty list (no duplicates found)
        return []

    def get_feature_context(self, feature_name: str) -> Dict:
        """Get comprehensive context for a feature"""

        print(f"\n📖 CCOM requesting context for: {feature_name}")
        print("=" * 60)
        print("Claude: Please retrieve context from MCP Memory Keeper:")
        print(f"""
mcp_context_get({{
    channel: '{self.project_name}',
    keyPattern: '{feature_name}.*'
}})

Show organized context:
📋 **Decisions**: Recent architectural decisions
⚠️  **Issues**: Open issues and blockers
✅ **Progress**: Completed milestones
🎯 **Next Steps**: Planned actions
📝 **Notes**: Additional context

Format each section clearly for easy reading.
        """)
        print("=" * 60)

        return {}

    def list_all_features(self, status_filter: str = None) -> List[Dict]:
        """List all features in the project"""

        print(f"\n📋 CCOM requesting all features list")
        print("=" * 60)
        print("Claude: Please retrieve all features from MCP Memory Keeper:")

        filter_clause = ""
        if status_filter:
            filter_clause = f"Filter by status: '{status_filter}'"

        print(f"""
mcp_context_get({{
    channel: '{self.project_name}',
    category: 'feature'
}})

{filter_clause}

Display features in this format:
• <feature_name>: <description> [<status>] (<timestamp>)
        """)
        print("=" * 60)

        return []

    def save_context_note(self, feature_name: str, note: str, context_type: str = "note") -> bool:
        """Save contextual note for a feature"""

        print(f"\n📝 CCOM saving {context_type} for: {feature_name}")
        print("=" * 60)
        print("Claude: Please save this context to MCP Memory Keeper:")
        print(f"""
mcp_context_save({{
    key: '{feature_name}_{context_type}_{int(datetime.now().timestamp())}',
    value: '{note}',
    category: '{context_type}',
    priority: 'normal',
    channel: '{self.project_name}',
    metadata: {{
        feature: '{feature_name}',
        created_by: 'ccom',
        timestamp: '{datetime.now().isoformat()}'
    }}
}})
        """)
        print("=" * 60)

        return True

    def create_checkpoint(self, name: str = None, description: str = None) -> str:
        """Create a checkpoint of current project state"""

        checkpoint_name = name or f"{self.project_name}-checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        checkpoint_desc = description or f"CCOM checkpoint for {self.project_name}"

        print(f"\n💾 CCOM creating checkpoint: {checkpoint_name}")
        print("=" * 60)
        print("Claude: Please create MCP Memory Keeper checkpoint:")
        print(f"""
mcp_context_checkpoint({{
    name: '{checkpoint_name}',
    description: '{checkpoint_desc}',
    includeGitStatus: true,
    metadata: {{
        project: '{self.project_name}',
        created_by: 'ccom',
        timestamp: '{datetime.now().isoformat()}'
    }}
}})

After creating checkpoint, display:
✅ Checkpoint created: {checkpoint_name}
📍 Restore key: {checkpoint_name}
        """)
        print("=" * 60)

        return checkpoint_name

    def search_context(self, query: str, limit: int = 5) -> List[Dict]:
        """Search all context for query"""

        print(f"\n🔍 CCOM searching context for: '{query}'")
        print("=" * 60)
        print("Claude: Please search MCP Memory Keeper:")
        print(f"""
mcp_context_search({{
    query: '{query}',
    channel: '{self.project_name}',
    limit: {limit}
}})

Display results with:
- Relevance ranking
- Context type (feature, note, decision, etc.)
- Timestamp
- Key excerpts
        """)
        print("=" * 60)

        return []

    def get_project_summary(self) -> Dict:
        """Get intelligent project summary"""

        print(f"\n📊 CCOM requesting project summary")
        print("=" * 60)
        print("Claude: Please generate project summary from MCP Memory Keeper:")
        print(f"""
mcp_context_get({{
    channel: '{self.project_name}',
    limit: 50
}})

Analyze and display:
🎯 **Active Features**: Current development focus
📈 **Recent Progress**: Last 7 days activity
⚠️  **Open Issues**: Blockers and problems
🔍 **Next Actions**: Recommended priorities
📊 **Statistics**: Feature count, activity level
        """)
        print("=" * 60)

        return {}


class MCPLegacyBridge:
    """Bridge to maintain compatibility with existing CCOM workflows"""

    def __init__(self, project_name: str = None):
        self.mcp = MCPDirectIntegration(project_name)

    def rememberFeature(self, feature_name: str, description: str = "") -> bool:
        """Legacy compatibility method for existing CCOM code"""
        return self.mcp.save_feature(feature_name, description)

    def checkDuplicate(self, feature_name: str) -> List[Dict]:
        """Legacy compatibility method for duplicate checking"""
        return self.mcp.check_feature_exists(feature_name)

    def getFeatureContext(self, feature_name: str) -> Dict:
        """Legacy compatibility method for context retrieval"""
        return self.mcp.get_feature_context(feature_name)


# Compatibility export for existing imports
MCPMemoryBridge = MCPLegacyBridge