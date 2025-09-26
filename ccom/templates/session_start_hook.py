#!/usr/bin/env python3
"""
CCOM SessionStart Hook Template - MCP Context Loader
Automatically loads project context from MCP Memory Keeper at session start

This file is automatically created by CCOM init and provides seamless
session continuity across Claude Code sessions.
"""

import json
import sys
import os
import subprocess
from pathlib import Path

def get_mcp_context():
    """Get project context from CCOM MCP integration"""
    try:
        # Run CCOM to get project context
        result = subprocess.run(
            ["ccom", "--mcp-context"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"⚠️ Could not load MCP context: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return "⚠️ MCP context loading timed out"
    except Exception as e:
        return f"⚠️ MCP context error: {str(e)}"

def get_recent_activity():
    """Get recent activity summary from MCP"""
    try:
        result = subprocess.run(
            ["ccom", "--mcp-activity"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return None

    except Exception:
        return None

def main():
    """Generate SessionStart hook output with MCP context"""

    project_root = Path.cwd()
    project_name = project_root.name

    # Get MCP context
    mcp_context = get_mcp_context()
    recent_activity = get_recent_activity()

    # Build comprehensive session context
    context_parts = [
        f"🎯 **SESSION CONTINUITY LOADED** - {project_name}",
        "=" * 60,
        "",
        "📊 **MCP MEMORY CONTEXT**:",
        mcp_context,
        ""
    ]

    if recent_activity:
        context_parts.extend([
            "📈 **RECENT ACTIVITY**:",
            recent_activity,
            ""
        ])

    context_parts.extend([
        "💡 **Session Context**: Previous work and decisions automatically loaded from MCP Memory Keeper",
        "🔗 **Continuity**: This session has full awareness of past interactions and project evolution",
        "🚀 **Ready**: You can continue exactly where you left off",
        ""
    ])

    additional_context = "\n".join(context_parts)

    # Output hook response
    hook_output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional_context
        }
    }

    print(json.dumps(hook_output, indent=2))

if __name__ == "__main__":
    main()