#!/usr/bin/env python3
"""
Enhanced CCOM CLI v0.3 - Vibe Coder Interface
Advanced natural language processing and enterprise automation
"""

import sys
import argparse
from pathlib import Path
from orchestrator import CCOMOrchestrator

def create_enhanced_cli():
    """Create enhanced CLI with natural language support"""
    parser = argparse.ArgumentParser(
        description="CCOM v0.3 - Claude Code Orchestrator and Memory",
        epilog="Natural language examples: 'deploy my app', 'check security', 'quality audit'",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add natural language support
    parser.add_argument('command', nargs='*',
                       help='Natural language command or traditional command')

    # Traditional commands
    parser.add_argument('--status', action='store_true',
                       help='Show CCOM and project status')
    parser.add_argument('--memory', action='store_true',
                       help='Show memory contents')
    parser.add_argument('--stats', action='store_true',
                       help='Show memory statistics')
    parser.add_argument('--remember', type=str,
                       help='Remember a feature: --remember "auth system"')
    parser.add_argument('--init', action='store_true',
                       help='Initialize CCOM in current directory')
    parser.add_argument('--force', action='store_true',
                       help='Force refresh CCOM configuration even if v0.3 exists')

    # Advanced options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output for debugging')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without executing')

    return parser

def handle_traditional_commands(args, orchestrator):
    """Handle traditional flag-based commands"""
    if args.status:
        orchestrator.show_status()
        return True
    elif args.memory:
        orchestrator.show_memory()
        return True
    elif args.remember:
        orchestrator.handle_memory_command(f"remember {args.remember}")
        return True
    elif args.init:
        init_ccom_project(force=args.force)
        return True

    return False

def init_ccom_project(force=False):
    """Initialize CCOM v0.3 in current project"""
    print("🚀 Initializing CCOM v0.3 in current project...")

    current_dir = Path.cwd()
    claude_dir = current_dir / ".claude"

    # Create directories
    claude_dir.mkdir(exist_ok=True)
    agents_dir = claude_dir / "agents"
    agents_dir.mkdir(exist_ok=True)

    # Copy agents from CCOM installation
    ccom_dir = Path(__file__).parent.parent
    source_agents = ccom_dir / ".claude" / "agents"

    if source_agents.exists():
        import shutil
        for agent_file in source_agents.glob("*.md"):
            dest_file = agents_dir / agent_file.name
            shutil.copy2(agent_file, dest_file)
            print(f"✅ Installed agent: {agent_file.name}")

    # Handle CLAUDE.md - backup existing and create v0.3
    claude_md = current_dir / "CLAUDE.md"
    if claude_md.exists():
        # Check if it's already v0.3
        try:
            with open(claude_md, 'r', encoding='utf-8') as f:
                content = f.read()

            if "CCOM Integration for Claude Code v0.3" in content and not force:
                print("✅ CLAUDE.md already v0.3 configuration (use --force to refresh)")
            else:
                # Backup existing file
                backup_path = current_dir / "CLAUDE.md.bak"
                import shutil
                shutil.copy2(claude_md, backup_path)
                print(f"⚠️  Backed up existing CLAUDE.md to CLAUDE.md.bak")

                # Create v0.3 configuration
                create_enhanced_claude_md(claude_md)
                print("✅ Updated CLAUDE.md to v0.3 configuration")
        except Exception as e:
            print(f"⚠️  Error reading CLAUDE.md: {e}")
            # Backup existing file before creating new one
            backup_path = current_dir / "CLAUDE.md.bak"
            import shutil
            shutil.copy2(claude_md, backup_path)
            print(f"⚠️  Backed up existing CLAUDE.md to CLAUDE.md.bak")

            create_enhanced_claude_md(claude_md)
            print("✅ Created new CLAUDE.md v0.3 configuration")
    else:
        create_enhanced_claude_md(claude_md)
        print("✅ Created CLAUDE.md v0.3 configuration")

    # Initialize memory
    orchestrator = CCOMOrchestrator()
    orchestrator.save_memory()
    print("✅ Initialized memory system")

    print("\n🎉 CCOM v0.3 initialized successfully!")
    print("\n📖 Try these CCOM commands:")
    print("  ccom 'deploy my app'")
    print("  ccom 'check security'")
    print("  ccom 'quality audit'")
    print("  ccom --status")
    print("\n💡 CCOM only activates with 'ccom' prefix - regular Claude Code otherwise!")

def create_enhanced_claude_md(claude_md_path):
    """Create enhanced CLAUDE.md with CCOM v0.3 integration configuration"""
    content = """# CCOM Integration for Claude Code v0.3

## CCOM Command Processing

**IMPORTANT**: Only activate CCOM functionality when user message starts with "ccom" (case-insensitive).

### How CCOM Commands Work:
- **Trigger**: Message starts with "ccom"
- **Examples**:
  - "ccom can you test this app for code quality?"
  - "ccom deploy this to production"
  - "ccom check security vulnerabilities"
  - "ccom remember this auth system"
  - "ccom show me the project status"

### CCOM Response Protocol:
1. **CCOM Engagement Acknowledgment** - Always start with clear CCOM activation message
2. **Recognize CCOM prefix** - Any message starting with "ccom"
3. **Parse intent** - Extract action (deploy, test, security, remember, status)
4. **Execute CCOM workflow** - Use tools to perform enterprise-grade actions
5. **Provide vibe-coder friendly responses** - Hide complexity, build confidence

### CCOM Activation Messages:
**REQUIRED**: Always start CCOM responses with one of these acknowledgments:
- "🤖 **CCOM ENGAGED** - Enterprise automation activated"
- "🚀 **CCOM ACTIVE** - Running enterprise-grade [action]..."
- "🔧 **CCOM ORCHESTRATING** - Quality gates and workflows activated"
- "🛡️ **CCOM ENTERPRISE MODE** - Security and deployment protocols engaged"

---

## CCOM Actions Available

### 🔧 Quality & Testing
**Triggers**: "test", "quality", "check code", "lint", "format"
**Actions**:
- Run ESLint via Bash: `npm run lint` or `npx eslint .`
- Run Prettier: `npm run format` or `npx prettier --write .`
- Check test coverage: `npm test`
- Analyze code for enterprise standards

**Response Style**: "✅ Code quality: Enterprise grade" or "🔧 Fixing quality issues..."

### 🔒 Security
**Triggers**: "security", "vulnerabilities", "secure", "safety", "protect"
**Actions**:
- Run security audit: `npm audit`
- Scan code for hardcoded secrets using Grep
- Check for XSS vulnerabilities, dangerous functions
- Review security configuration

**Response Style**: "🛡️ Security: Bank-level" or "🚨 Security issues detected - securing your app..."

### 🚀 Deployment
**Triggers**: "deploy", "ship", "go live", "launch", "production"
**Actions**:
- Quality gates: Run linting and tests
- Security check: Vulnerability scan
- Build verification: `npm run build`
- Deploy: `npm run deploy` or deployment scripts
- Health check: Verify deployment success

**Response Style**: "🚀 Deploying with enterprise standards..." → "🎉 Your app is live!"

### 🧠 Memory Management
**Triggers**: "remember", "memory", "status", "features", "what have we built"
**Actions**:
- **Remember**: `node .claude/ccom.js remember <name> [description]`
- **Show Memory**: `node .claude/ccom.js memory`
- **Status**: `node .claude/ccom.js start` (loads context)
- **Stats**: `node .claude/ccom.js stats`

**Response Style**: "📊 Project Status" with feature counts and memory usage

---

## CCOM Implementation Guide

### When Processing CCOM Commands:

1. **Quality Check Workflow**:
```bash
# Check if package.json exists
# Run: npm run lint (or npx eslint .)
# Run: npm run format (or npx prettier --write .)
# Report results in vibe-coder language
```

2. **Security Scan Workflow**:
```bash
# Run: npm audit
# Use Grep to scan for: password, api_key, secret patterns
# Check for eval(), innerHTML, document.write
# Suggest security improvements
```

3. **Deployment Workflow**:
```bash
# Step 1: Quality check (lint + format)
# Step 2: Security scan (npm audit)
# Step 3: Build (npm run build if exists)
# Step 4: Deploy (npm run deploy if exists)
# Step 5: Verify deployment success
```

4. **Memory Operations**:
```bash
# Load: node .claude/ccom.js start
# Remember: node .claude/ccom.js remember "feature_name" "description"
# Show: node .claude/ccom.js memory
# Stats: node .claude/ccom.js stats
```

### Response Guidelines:
- **CCOM Visual Identity**: Always use TodoWrite tool for task tracking when engaged
- **Clear Engagement**: Start every CCOM response with activation acknowledgment
- **Hide Technical Details**: Never show raw eslint errors to vibe coders
- **Build Confidence**: Use phrases like "Enterprise grade", "Bank-level security"
- **Show Progress**: Use emojis 🔧 🔒 🚀 ✅ to indicate progress
- **Celebrate Success**: Always end successful deployments with 🎉
- **Professional Workflow**: Use systematic approach with todo tracking and memory updates

### Error Handling:
- If tools fail, provide helpful guidance
- Suggest fixes for common issues
- Maintain confidence even when fixing problems

---

## Non-CCOM Behavior
**CRITICAL**: If message does NOT start with "ccom", respond normally without any CCOM functionality. Act as regular Claude Code assistant.

---

## Project Context
This project uses CCOM (Claude Code Orchestrator and Memory) for enterprise-grade development automation. CCOM provides:
- Quality gates and code standards enforcement
- Security vulnerability scanning and hardening
- Deployment pipelines with health monitoring
- Memory persistence across sessions
- Natural language interface for vibe coders

## Development Standards
- Follow ESLint rules if .eslintrc exists
- Use Prettier formatting if .prettierrc exists
- Include proper error handling and input validation
- Use TypeScript when available
- Maintain enterprise security standards
"""

    with open(claude_md_path, 'w', encoding='utf-8') as f:
        f.write(content)

def show_help():
    """Show enhanced help with examples"""
    print("""
🚀 CCOM v0.3 - Claude Code Orchestrator and Memory

🎯 PREFIX-BASED ACTIVATION:
  Only commands starting with "ccom" activate CCOM functionality
  All other commands use regular Claude Code behavior

NATURAL LANGUAGE COMMANDS (Recommended):
  ccom "deploy my app"              → Enterprise deployment pipeline
  ccom "check security"             → Comprehensive security audit
  ccom "quality audit"              → Code quality analysis
  ccom "make it secure"             → Security hardening
  ccom "ship it to production"      → Full deployment sequence

TRADITIONAL COMMANDS:
  ccom --status                     → Show project status
  ccom --memory                     → Show remembered features
  ccom --remember "feature name"    → Add feature to memory
  ccom --init                       → Initialize/refresh CCOM in project

EXAMPLES:
  ccom "deploy"                     → Quick deployment
  ccom "security scan"              → Security check
  ccom "fix quality issues"         → Auto-fix code quality
  ccom --status                     → Traditional status check

ENTERPRISE FEATURES:
  ✅ Claude Code native integration (prefix-based activation)
  ✅ Visual engagement indicators (clear CCOM vs regular CC)
  ✅ Multi-agent orchestration (quality, security, deployment)
  ✅ TodoWrite integration (systematic workflow tracking)
  ✅ Memory system (cross-session feature tracking)
  ✅ Enterprise security scanning (vulnerability detection)
  ✅ Production deployment pipeline (zero-downtime)

For more info: https://github.com/your-repo/ccom
""")

def main():
    """Enhanced main CLI entry point"""
    parser = create_enhanced_cli()

    # Handle no arguments
    if len(sys.argv) == 1:
        show_help()
        return

    args = parser.parse_args()

    try:
        orchestrator = CCOMOrchestrator()

        # Handle traditional commands first
        if handle_traditional_commands(args, orchestrator):
            return

        # Handle natural language commands
        if args.command:
            command_text = " ".join(args.command)

            if args.verbose:
                print(f"🔍 Processing: '{command_text}'")

            if args.dry_run:
                print(f"🧪 Dry run: Would execute '{command_text}'")
                return

            orchestrator.handle_natural_language(command_text)
        else:
            print("❓ No command provided. Use 'ccom --help' for usage.")

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()