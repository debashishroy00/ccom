# CCOM API Documentation

## JavaScript API (ccom.js)

### Class: CCOM

The main CCOM class provides memory persistence and management functionality.

#### Constructor

```javascript
const ccom = new CCOM();
```

Creates a new CCOM instance, automatically loading existing memory from `.claude/memory.json`.

#### Core Memory Methods

##### `loadMemory()`
```javascript
memory = ccom.loadMemory()
```
- **Returns**: Memory object or creates empty memory if file doesn't exist
- **Throws**: None (handles errors gracefully)

##### `saveMemory(memory?)`
```javascript
success = ccom.saveMemory(memory)
```
- **Parameters**:
  - `memory` (optional): Memory object to save. Defaults to `this.memory`
- **Returns**: `boolean` - Success status
- **Side Effects**: Writes to `.claude/memory.json`

##### `createEmptyMemory()`
```javascript
emptyMemory = ccom.createEmptyMemory()
```
- **Returns**: Fresh memory object with v0.2 structure
- **Format**:
```json
{
  "project": { "name": "project-name", "created": "2025-09-18" },
  "features": {},
  "metadata": { "version": "0.2", "created": "ISO-date", "lastCleanup": "ISO-date" }
}
```

#### Feature Management

##### `rememberFeature(name, data)`
```javascript
success = ccom.rememberFeature("auth_system", {
  description: "User authentication",
  files: ["auth.js", "login.html"]
})
```
- **Parameters**:
  - `name` (string): Feature name
  - `data` (object): Feature metadata
    - `description` (string): Feature description
    - `files` (array): Associated files
    - `userTerm` (string): User-friendly name
- **Returns**: `boolean` - Success (false if duplicate detected)
- **Side Effects**: Saves to memory, logs to console

##### `checkDuplicate(name)`
```javascript
existingName = ccom.checkDuplicate("auth system")
```
- **Parameters**: `name` (string): Feature name to check
- **Returns**: `string | false` - Existing feature name or false if no duplicate
- **Note**: Case-insensitive matching, checks both feature names and userTerms

##### `removeFeature(name)`
```javascript
success = ccom.removeFeature("auth_system")
```
- **Parameters**: `name` (string): Feature name to remove
- **Returns**: `boolean` - Success status
- **Side Effects**: Removes from memory, saves changes

#### Memory Management (v0.2)

##### `getMemoryStats()`
```javascript
stats = ccom.getMemoryStats()
```
- **Returns**: Object with memory statistics
```javascript
{
  featureCount: 5,
  bytes: 1024,
  tokens: 256,
  percentage: 0.128,
  oldest: "2025-09-17",
  newest: "2025-09-18",
  version: "0.2"
}
```

##### `archiveOldFeatures(days)`
```javascript
archivedCount = ccom.archiveOldFeatures(30)
```
- **Parameters**: `days` (number): Archive features older than N days
- **Returns**: `number` - Count of archived features
- **Side Effects**: Creates archive file, updates memory

##### `compactMemory()`
```javascript
compactedCount = ccom.compactMemory()
```
- **Returns**: `number` - Count of compacted descriptions
- **Side Effects**: Truncates descriptions >100 chars, saves memory

##### `listFeatures(sortBy)`
```javascript
ccom.listFeatures("name")  // Sort alphabetically
ccom.listFeatures("created")  // Sort by creation date (default)
```
- **Parameters**: `sortBy` (string): "name" or "created"
- **Side Effects**: Prints formatted feature list to console

#### Display Methods

##### `getContextSummary()`
```javascript
summary = ccom.getContextSummary()
```
- **Returns**: `string` - Formatted memory summary for Claude context
- **Format**: Project name, token usage, feature list, warnings

##### `showMemory()`
```javascript
ccom.showMemory()
```
- **Side Effects**: Prints detailed memory contents to console

##### `displayMemoryStats()`
```javascript
stats = ccom.displayMemoryStats()
```
- **Returns**: Stats object (same as `getMemoryStats()`)
- **Side Effects**: Prints formatted statistics with warnings

##### `clearMemory()`
```javascript
ccom.clearMemory()
```
- **Side Effects**: Resets memory to empty state, saves changes

## Python CLI API (cco.cli)

### Functions

#### `init_project()`
```python
success = init_project()
```
- **Returns**: `bool` - Success status
- **Side Effects**: Creates `.claude/` directory, copies templates
- **Files Created**:
  - `CLAUDE.md` (with backup if exists)
  - `.claude/ccom.js`
  - `.claude/archive/`

#### `show_status()`
```python
success = show_status()
```
- **Returns**: `bool` - Success status
- **Validates**: CCOM initialization, calls Node.js backend

#### `run_ccom_command(args)`
```python
success = run_ccom_command(["remember", "feature_name", "description"])
```
- **Parameters**: `args` (list): Command arguments for ccom.js
- **Returns**: `bool` - Success status
- **Error Handling**: Captures subprocess errors, checks Node.js availability

### CLI Commands

#### Basic Commands
```bash
ccom init                          # Initialize project
ccom status                        # Show memory status
ccom remember "name" ["description"]  # Add feature (with optional description)
ccom memory                        # Show detailed memory
ccom clear                         # Clear all memory
```

#### Memory Management
```bash
ccom stats                         # Memory statistics
ccom list [created|name]           # List features (sorted)
ccom archive [days]                # Archive old features (default: 30 days)
ccom remove "name"                 # Remove specific feature
ccom compact                       # Compress memory
```

## Memory Format Specification

### v0.2 Memory Structure
```typescript
interface Memory {
  project: {
    name: string;
    created: string;  // YYYY-MM-DD format
  };
  features: {
    [featureName: string]: {
      created: string;    // ISO 8601 datetime
      description: string;
      files: string[];
      userTerm: string;
    };
  };
  metadata: {
    version: string;      // "0.2"
    created: string;      // ISO 8601 datetime
    lastCleanup: string;  // ISO 8601 datetime
  };
}
```

### Archive File Format
```typescript
interface ArchiveFile {
  archivedDate: string;   // ISO 8601 datetime
  cutoffDays: number;
  features: {
    [featureName: string]: FeatureData;
  };
}
```

## Error Handling

### JavaScript Errors
- **File System**: Graceful fallback to empty memory
- **JSON Parsing**: Creates new memory structure
- **Duplicate Detection**: Returns false, logs warning

### Python CLI Errors
- **Node.js Missing**: Clear error message with installation prompt
- **CCOM Not Initialized**: Prompts user to run `ccom init`
- **Subprocess Errors**: Captures and displays stderr

## Token Calculation

CCOM approximates tokens using:
```javascript
const tokens = Math.ceil(bytes / 4);
```

### Memory Thresholds
- **Info**: 5,000 tokens (2.5% of 200k context)
- **Warning**: 10,000 tokens (5% of context)
- **Critical**: 20,000 tokens (10% of context)

## Hook System (Planned)

```javascript
// Future integration points
ccom.onSessionStart()    // Auto-display memory
ccom.onCommand(command)  // Detect duplicate attempts
```

Current implementation includes hook scaffolding but requires Claude Code integration.

## File Locations

- **Memory**: `.claude/memory.json`
- **Archive**: `.claude/archive/archive-YYYY-MM-DD.json`
- **Config**: `CLAUDE.md`
- **Backend**: `.claude/ccom.js`

## Version Migration

CCOM automatically migrates v0.1 → v0.2 memory format by adding metadata section while preserving existing features.