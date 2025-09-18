# CCOM v0.2 - Claude Code Orchestrator and Memory

**Production-ready memory persistence for Claude Code with management features. Zero dependencies, 743 lines total.**

## 🚀 One-Command Install

```bash
# Install once
pip install ccom

# Use in any project
cd my-project
ccom init

# Test it immediately
ccom status
ccom remember "auth system"
ccom remember "auth system"  # ⚠️ Duplicate detected!

# Memory management (v0.2 features)
ccom stats                   # Check memory usage
ccom list name              # List features alphabetically
ccom compact                # Compress memory
ccom archive 30             # Archive old features

# Or install from GitHub (latest)
pip install git+https://github.com/debashishroy00/ccom.git
```

## 📋 What CCOM Solves

Claude Code forgets everything between sessions, causing developers to:
- ❌ Rebuild existing features repeatedly
- ❌ Re-explain project context every session
- ❌ Waste time on duplicate work
- ❌ Lose track of what's been built

CCOM provides **persistent memory** that survives session restarts and prevents duplicate work.

## 🏗️ Architecture

CCOM uses a hybrid Python + Node.js architecture:
- **Python CLI** (`ccom` command) - Cross-platform installation and project setup
- **Node.js Backend** (`ccom.js`) - Memory persistence and management logic
- **Zero Dependencies** - Pure stdlib implementations

```
ccom init → Deploys ccom.js + CLAUDE.md → Ready for Claude Code
```

## 📚 Command Reference

### Core Commands
```bash
ccom init                    # Initialize CCOM in current directory
ccom status                  # Show memory summary with context usage
ccom remember "feature"      # Add feature to memory
ccom memory                  # Show detailed memory contents
ccom clear                   # Clear all memory (start fresh)
```

### Memory Management (v0.2)
```bash
ccom stats                   # Memory statistics and token usage
ccom list [created|name]     # List features with age (sort by date/name)
ccom compact                 # Truncate long descriptions to save tokens
ccom archive [days]          # Archive features older than N days (default: 30)
ccom remove "feature"        # Delete specific feature
```

### Direct Node.js Usage (with descriptions)
```bash
node .claude/ccom.js start
node .claude/ccom.js remember "feature" "detailed description"
node .claude/ccom.js stats
node .claude/ccom.js list name
```

## 💾 Memory Format v0.2

CCOM stores memory in `.claude/memory.json`:

```json
{
  "project": {
    "name": "my-project",
    "created": "2025-09-18"
  },
  "features": {
    "auth_system": {
      "created": "2025-09-18T10:30:00.000Z",
      "description": "User authentication with JWT tokens",
      "files": ["auth.js", "login.html"],
      "userTerm": "auth system"
    }
  },
  "metadata": {
    "version": "0.2",
    "created": "2025-09-18T10:00:00.000Z",
    "lastCleanup": "2025-09-18T15:00:00.000Z"
  }
}
```

## 🎯 Memory Limits

CCOM monitors token usage to prevent context bloat:
- **💡 Info**: 5,000 tokens (2.5% of context) - Monitor growth
- **⚠️ Warning**: 10,000 tokens (5% of context) - Consider archiving
- **🚨 Critical**: 20,000 tokens (10% of context) - Archive immediately

## 🔄 Workflow

1. **Session Start**: `ccom status` → Loads existing features
2. **Before Building**: Check displayed features for duplicates
3. **After Building**: `ccom remember "new_feature"`
4. **Monthly Cleanup**: `ccom archive 30` → Archive old features

## 📁 File Structure

After `ccom init`, your project has:

```
my-project/
├── CLAUDE.md              # CCOM configuration for Claude
├── .claude/
│   ├── ccom.js           # Memory management system (504 lines)
│   ├── memory.json       # Persistent memory storage
│   └── archive/          # Archived features directory
```

## 🚀 Features

### ✅ Implemented
- **Persistent Memory** - Survives Claude Code restarts
- **Duplicate Detection** - Warns before rebuilding features
- **Memory Management** - Archive, compact, remove features
- **Token Monitoring** - Context usage tracking with warnings
- **Cross-Platform** - Windows, macOS, Linux support
- **Zero Dependencies** - No npm packages or external deps
- **Rich Output** - Emoji-enhanced terminal interface

### 🔄 Auto-Migration
CCOM automatically upgrades v0.1 memory files to v0.2 format.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test: `ccom init && ccom status`
4. Commit: `git commit -m "Add feature"`
5. Push: `git push origin feature-name`
6. Create Pull Request

## 📄 License

MIT License - see LICENSE file for details.

## 🐛 Issues & Support

Report issues: https://github.com/debashishroy00/ccom/issues