# CCOM - Claude Code Orchestrator and Memory

## CRITICAL: Auto-Load Memory
Run this IMMEDIATELY when session starts:
```bash
node .claude/ccom.js start
```

## Session Start Protocol
1. **FIRST ACTION**: Execute `node .claude/ccom.js start`
2. **READ OUTPUT**: This shows existing features and duplicate warnings
3. **BEFORE ANY CODE**: Check if requested feature already exists
4. **IF DUPLICATE**: Warn user and suggest enhancing existing feature

## System Instructions
- Auto-load memory displays existing features on session start
- ALWAYS check for duplicates before building new features
- Update memory when new features are created
- Memory persists between all Claude Code sessions

## Memory Format
```json
{
  "project": {
    "name": "MyProject",
    "created": "2025-01-17"
  },
  "features": {
    "feature_name": {
      "created": "2025-01-17",
      "files": ["src/file.js"],
      "description": "What it does"
    }
  }
}
```

## Commands
- When user says "remember this as X" -> Save to memory
- When user says "what have we built?" -> Show memory
- When user says "clear memory" -> Reset memory.json