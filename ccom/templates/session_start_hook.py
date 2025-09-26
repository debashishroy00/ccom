#!/usr/bin/env python3
"""
CCOM SessionStart Hook Template - MCP Context Loader
Automatically loads project context from MCP Memory Keeper at session start

This file is automatically created by CCOM init and provides seamless
session continuity across Claude Code sessions.
"""

import json
from pathlib import Path

def main():
    """Generate SessionStart hook output - no operations, just static notification"""

    project_name = Path.cwd().name

    # Static notification - no file checks, no subprocess calls
    context_parts = [
        f"🎯 **{project_name}** - CCOM session continuity available",
        "💡 **Tip**: Use 'ccom what did we discuss' to load previous context"
    ]

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