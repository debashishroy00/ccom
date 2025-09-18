# CCOM Configuration v0.2

## CRITICAL: Session Start Protocol
**FIRST ACTION in every session**: Run this command
```bash
node .claude/ccom.js start
```
This loads existing features and prevents duplicate work.

## Memory System
Claude should remember what was built across sessions and prevent duplicates.

```yaml
ccom:
  version: "0.2"
  memory:
    enabled: true
    path: ".claude/memory.json"
    management: true
```

## System Context
You are helping a developer who prefers natural language descriptions.
Always check memory before creating new features to avoid duplicates.

## Memory Management Commands

### Core Commands
- `node .claude/ccom.js start` - Load memory & show context
- `node .claude/ccom.js remember <name> [description]` - Save new feature
- `node .claude/ccom.js memory` - Display all features
- `node .claude/ccom.js clear` - Reset memory

### Regular Maintenance
- `node .claude/ccom.js stats` - Check token usage
- `node .claude/ccom.js list` - Show all features with age
- `node .claude/ccom.js archive 30` - Archive features older than 30 days
- `node .claude/ccom.js remove <name>` - Delete specific feature
- `node .claude/ccom.js compact` - Reduce memory size

### Memory Limits
- **Warning**: 5,000 tokens (2.5% of context)
- **Archive**: 10,000 tokens (5% of context)
- **Maximum**: 20,000 tokens (10% of context)

## Development Workflow
1. **Start session** → Run `start` command
2. **Check for duplicates** before building
3. **Remember new features** after creating
4. **Archive old features** monthly

## Memory Format v0.2
```json
{
  "project": {
    "name": "project-name"
  },
  "features": {
    "feature_name": {
      "created": "ISO-8601-date",
      "description": "what it does",
      "files": ["list", "of", "files"]
    }
  },
  "metadata": {
    "version": "0.2",
    "created": "ISO-8601-date",
    "lastCleanup": "ISO-8601-date"
  }
}
```

## Natural Language Commands
- When user says "remember this as X" → Save to memory
- When user says "what have we built?" → Show memory
- When user says "clear memory" → Reset memory.json
- When user says "archive old features" → Run archive command
- When user says "check memory usage" → Run stats command