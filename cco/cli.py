#!/usr/bin/env python3
"""CCOM CLI - Claude Code Orchestrator and Memory"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

def get_template_path():
    """Get path to template files"""
    return Path(__file__).parent / "templates"

def run_ccom_command(args):
    """Run Node.js ccom.js command with proper error handling"""
    try:
        cmd = ["node", ".claude/ccom.js"] + args
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', check=False)

        # Print stdout if available
        if result.stdout:
            # Handle emoji output on Windows
            try:
                print(result.stdout, end='')
            except UnicodeEncodeError:
                # Fallback for Windows console without UTF-8 support
                print(result.stdout.encode('ascii', 'replace').decode('ascii'), end='')

        # Print stderr if available
        if result.stderr:
            try:
                print(result.stderr, file=sys.stderr, end='')
            except UnicodeEncodeError:
                print(result.stderr.encode('ascii', 'replace').decode('ascii'), file=sys.stderr, end='')

        return result.returncode == 0
    except FileNotFoundError:
        print("ERROR: Node.js not found. Please install Node.js to use CCOM.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"ERROR: Failed to run ccom command: {e}", file=sys.stderr)
        return False

def init_project():
    """Initialize CCO in current directory"""
    current_dir = Path.cwd()
    template_dir = get_template_path()

    print("Initializing CCOM v0.2...")

    # Create .claude directory
    claude_dir = current_dir / ".claude"
    claude_dir.mkdir(exist_ok=True)

    # Create archive directory
    archive_dir = claude_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    # Copy CLAUDE.md
    claude_md_src = template_dir / "CLAUDE.md"
    claude_md_dst = current_dir / "CLAUDE.md"

    if claude_md_dst.exists():
        print(f"WARNING: CLAUDE.md already exists, backing up to CLAUDE.md.bak")
        shutil.copy2(claude_md_dst, current_dir / "CLAUDE.md.bak")

    shutil.copy2(claude_md_src, claude_md_dst)
    print(f"Created CLAUDE.md")

    # Copy ccom.js
    ccom_js_src = template_dir / "ccom.js"
    ccom_js_dst = claude_dir / "ccom.js"
    shutil.copy2(ccom_js_src, ccom_js_dst)
    print(f"Created .claude/ccom.js")
    print(f"Created .claude/archive/")

    print("\nCCOM v0.2 initialized!")
    print("\nTest it:")
    print("  ccom status")
    print("  ccom remember 'my feature'")
    print("  ccom memory")
    print("\nMemory management:")
    print("  ccom stats")
    print("  ccom list")
    print("  ccom archive 30")

    return True

def show_status():
    """Show CCOM status in current directory"""
    claude_dir = Path.cwd() / ".claude"
    memory_file = claude_dir / "memory.json"

    if not claude_dir.exists():
        print("ERROR: CCOM not initialized. Run 'ccom init' first.")
        return False

    if not memory_file.exists():
        print("CCOM initialized but no memory yet.")
        return True

    # Run the node command to show status
    return run_ccom_command(["start"])

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CCOM - Claude Code Orchestrator and Memory",
        epilog="For more info: https://github.com/debashishroy00/ccom"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize CCOM in current directory")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show CCOM status")

    # Memory command
    memory_parser = subparsers.add_parser("memory", help="Show memory contents")

    # Remember command
    remember_parser = subparsers.add_parser("remember", help="Remember a feature")
    remember_parser.add_argument("name", help="Feature name to remember")
    remember_parser.add_argument("description", nargs="?", help="Optional feature description")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear memory")

    # v0.2 Memory Management Commands
    stats_parser = subparsers.add_parser("stats", help="Show memory usage statistics")

    list_parser = subparsers.add_parser("list", help="List features with age")
    list_parser.add_argument("sort", nargs="?", default="created", help="Sort by: created or name")

    archive_parser = subparsers.add_parser("archive", help="Archive old features")
    archive_parser.add_argument("days", nargs="?", type=int, default=30, help="Archive features older than N days (default: 30)")

    remove_parser = subparsers.add_parser("remove", help="Remove specific feature")
    remove_parser.add_argument("name", help="Feature name to remove")

    compact_parser = subparsers.add_parser("compact", help="Compact memory by truncating long descriptions")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "init":
        success = init_project()
        sys.exit(0 if success else 1)
    elif args.command == "status":
        success = show_status()
        sys.exit(0 if success else 1)
    elif args.command == "memory":
        success = run_ccom_command(["memory"])
        sys.exit(0 if success else 1)
    elif args.command == "remember":
        if args.description:
            success = run_ccom_command(["remember", args.name, args.description])
        else:
            success = run_ccom_command(["remember", args.name])
        sys.exit(0 if success else 1)
    elif args.command == "clear":
        success = run_ccom_command(["clear"])
        sys.exit(0 if success else 1)
    elif args.command == "stats":
        success = run_ccom_command(["stats"])
        sys.exit(0 if success else 1)
    elif args.command == "list":
        success = run_ccom_command(["list", args.sort])
        sys.exit(0 if success else 1)
    elif args.command == "archive":
        success = run_ccom_command(["archive", str(args.days)])
        sys.exit(0 if success else 1)
    elif args.command == "remove":
        success = run_ccom_command(["remove", args.name])
        sys.exit(0 if success else 1)
    elif args.command == "compact":
        success = run_ccom_command(["compact"])
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()