#!/usr/bin/env python3
"""
CCOM Capture Hook for Claude Code
Simple command-line interface for Claude Code to trigger auto-capture
"""

import sys
import os
from pathlib import Path

def main():
    """
    Command-line hook for Claude Code CCOM auto-capture
    Usage: python ccom_capture_hook.py "input_text" "output_text" [project_path]
    """
    if len(sys.argv) < 3:
        print("Usage: python ccom_capture_hook.py \"input_text\" \"output_text\" [project_path]", file=sys.stderr)
        sys.exit(1)

    input_text = sys.argv[1]
    output_text = sys.argv[2]
    project_path = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        # Add CCOM to Python path
        script_dir = Path(__file__).parent
        sys.path.insert(0, str(script_dir))

        # Import and call the hook
        from ccom.auto_context import capture_claude_code_ccom

        success = capture_claude_code_ccom(input_text, output_text, project_path)

        if success:
            print("✅ Auto-capture successful")
            sys.exit(0)
        else:
            print("⚠️ Auto-capture failed (non-critical)", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"❌ Auto-capture error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()