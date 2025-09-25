# CCOM + MCP Memory Keeper Integration Implementation

## Implementation Plan - Based on Analysis

Your MCP analysis confirms this integration will solve CCOM's context continuity perfectly. Here's the detailed implementation plan:

## Phase 1: MCP Bridge Implementation (Week 1)

### 1.1 Install and Configure MCP Memory Keeper

```bash
# Test installation locally
npm install -g mcp-memory-keeper

# Configure for Claude Code/Desktop
claude mcp add --scope user memory-keeper npx mcp-memory-keeper

# Verify installation
claude mcp list  # Should show memory-keeper as active

# Test basic functionality
# In Claude session:
# "Please save this note: Testing MCP Memory Keeper integration"
# "Retrieve my recent notes"
```

### 1.2 Create MCP Bridge Module

```python
# ccom/mcp_bridge.py
import subprocess
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

class MCPMemoryBridge:
    """Bridge between CCOM and MCP Memory Keeper"""
    
    def __init__(self, project_name: str = None):
        self.project_name = project_name or "ccom-default"
        self.channel = f"ccom-{self.project_name}"
        self.logger = logging.getLogger(__name__)
        
        # Test MCP availability
        self._test_mcp_connection()
    
    def _test_mcp_connection(self) -> bool:
        """Test if MCP Memory Keeper is available"""
        try:
            # Test by attempting to save a test item
            test_result = self._call_mcp_tool('mcp_context_status', {})
            return True
        except Exception as e:
            self.logger.warning(f"MCP Memory Keeper not available: {e}")
            return False
    
    def _call_mcp_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Call MCP Memory Keeper tools via Claude Code subprocess
        Note: This is a bridge approach - in production might use direct MCP client
        """
        try:
            # For now, use a simple JSON file approach as bridge
            # In full implementation, this would call MCP tools directly
            return self._bridge_implementation(tool_name, params)
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {tool_name}, {e}")
            return {}
    
    def _bridge_implementation(self, tool_name: str, params: Dict) -> Dict:
        """
        Temporary bridge implementation
        TODO: Replace with actual MCP tool calls
        """
        # For initial implementation, use file-based bridge
        bridge_file = f".ccom/mcp_bridge_{self.channel}.json"
        
        try:
            with open(bridge_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"items": [], "sessions": [], "channels": {}}
        
        if tool_name == 'mcp_context_save':
            item = {
                **params,
                'timestamp': datetime.now().isoformat(),
                'channel': self.channel
            }
            data['items'].append(item)
            
        elif tool_name == 'mcp_context_get':
            channel_filter = params.get('channel', self.channel)
            category_filter = params.get('category')
            
            filtered_items = [
                item for item in data['items']
                if item.get('channel') == channel_filter
                and (not category_filter or item.get('category') == category_filter)
            ]
            return {'items': filtered_items[-10:]}  # Return last 10 items
        
        # Save data back
        with open(bridge_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {'success': True}
    
    def save_context(self, 
                    feature: str, 
                    context_type: str, 
                    content: str, 
                    priority: str = "normal",
                    metadata: Dict = None) -> bool:
        """Save context to MCP Memory Keeper"""
        
        try:
            params = {
                'key': f'{feature}_{context_type}_{int(time.time())}',
                'value': content,
                'category': context_type,
                'priority': priority,
                'channel': self.channel,
                'metadata': metadata or {}
            }
            
            result = self._call_mcp_tool('mcp_context_save', params)
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"Failed to save context: {e}")
            return False
    
    def get_context(self, 
                   feature: str = None,
                   context_type: str = None,
                   limit: int = 10) -> List[Dict]:
        """Get relevant context from MCP Memory Keeper"""
        
        try:
            params = {
                'channel': self.channel,
                'limit': limit
            }
            
            if context_type:
                params['category'] = context_type
                
            result = self._call_mcp_tool('mcp_context_get', params)
            items = result.get('items', [])
            
            # Filter by feature if specified
            if feature:
                items = [
                    item for item in items
                    if feature.lower() in item.get('key', '').lower() or
                       feature.lower() in item.get('value', '').lower()
                ]
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to get context: {e}")
            return []
    
    def get_resume_context(self, feature: str) -> Dict:
        """Get comprehensive context for resuming work on a feature"""
        
        context = {
            'decisions': self.get_context(feature, 'decision', 5),
            'issues': self.get_context(feature, 'issue', 5),
            'progress': self.get_context(feature, 'progress', 5),
            'next_steps': self.get_context(feature, 'next_step', 3)
        }
        
        return context
    
    def create_checkpoint(self, name: str = None) -> str:
        """Create a checkpoint of current context state"""
        
        checkpoint_name = name or f"checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        try:
            params = {
                'name': checkpoint_name,
                'description': f'CCOM checkpoint for {self.project_name}',
                'includeFiles': False,  # Start simple
                'includeGitStatus': True
            }
            
            result = self._call_mcp_tool('mcp_context_checkpoint', params)
            return checkpoint_name
            
        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            return ""
    
    def search_context(self, query: str, limit: int = 5) -> List[Dict]:
        """Search context using semantic/text search"""
        
        try:
            params = {
                'query': query,
                'channel': self.channel,
                'limit': limit
            }
            
            result = self._call_mcp_tool('mcp_context_search', params)
            return result.get('items', [])
            
        except Exception as e:
            self.logger.error(f"Failed to search context: {e}")
            return []
    
    def format_context_for_display(self, context: Dict) -> str:
        """Format context for CLI display"""
        
        output = []
        
        if context.get('decisions'):
            output.append("## Recent Decisions:")
            for item in context['decisions'][-3:]:
                timestamp = item.get('timestamp', '')[:10]  # Date only
                output.append(f"- {timestamp}: {item.get('value', '')}")
        
        if context.get('issues'):
            active_issues = [
                item for item in context['issues']
                if 'RESOLVED' not in item.get('value', '').upper()
                and 'FIXED' not in item.get('value', '').upper()
            ]
            if active_issues:
                output.append("\n## Active Issues:")
                for item in active_issues[-3:]:
                    timestamp = item.get('timestamp', '')[:10]
                    output.append(f"- {timestamp}: {item.get('value', '')}")
        
        if context.get('progress'):
            output.append("\n## Recent Progress:")
            for item in context['progress'][-3:]:
                timestamp = item.get('timestamp', '')[:10]
                output.append(f"- {timestamp}: {item.get('value', '')}")
        
        if context.get('next_steps'):
            output.append("\n## Next Steps:")
            for item in context['next_steps'][-3:]:
                output.append(f"- {item.get('value', '')}")
        
        return "\n".join(output) if output else "No context found for this feature."
```

### 1.3 Enhance CCOM CLI

```python
# Add to ccom/cli.py
import click
from .mcp_bridge import MCPMemoryBridge

# Add new context commands group
@cli.group()
def context():
    """Memory and context management commands"""
    pass

@context.command()
@click.argument('feature')
@click.argument('note', nargs=-1, required=True)
@click.option('--type', default='note', help='Context type (note, decision, issue, progress, next_step)')
@click.option('--priority', default='normal', help='Priority level (low, normal, high, critical)')
def note(feature, note, type, priority):
    """Save a note about a feature"""
    
    project_name = get_current_project_name()  # Implement this helper
    bridge = MCPMemoryBridge(project_name)
    
    note_text = ' '.join(note)
    success = bridge.save_context(feature, type, note_text, priority)
    
    if success:
        click.echo(f"✅ Saved {type} for {feature}: {note_text}")
    else:
        click.echo(f"❌ Failed to save {type} for {feature}")

@context.command()
@click.argument('feature')
def resume(feature):
    """Resume work on a feature with full context"""
    
    project_name = get_current_project_name()
    bridge = MCPMemoryBridge(project_name)
    
    click.echo(f"🧠 Resuming work on: {feature}\n")
    
    context = bridge.get_resume_context(feature)
    formatted_context = bridge.format_context_for_display(context)
    
    if formatted_context.strip():
        click.echo(formatted_context)
    else:
        click.echo(f"No previous context found for {feature}")
        click.echo("Use 'ccom context note' to start tracking context for this feature.")

@context.command()
@click.argument('query', nargs=-1, required=True)
def search(query):
    """Search context across all features"""
    
    project_name = get_current_project_name()
    bridge = MCPMemoryBridge(project_name)
    
    query_text = ' '.join(query)
    results = bridge.search_context(query_text)
    
    if results:
        click.echo(f"🔍 Search results for: {query_text}\n")
        for item in results:
            timestamp = item.get('timestamp', '')[:16].replace('T', ' ')
            category = item.get('category', 'note').upper()
            content = item.get('value', '')[:100] + ('...' if len(item.get('value', '')) > 100 else '')
            click.echo(f"[{timestamp}] {category}: {content}")
    else:
        click.echo(f"No results found for: {query_text}")

@context.command()
@click.option('--name', help='Checkpoint name')
def checkpoint(name):
    """Create a checkpoint of current context"""
    
    project_name = get_current_project_name()
    bridge = MCPMemoryBridge(project_name)
    
    checkpoint_name = bridge.create_checkpoint(name)
    
    if checkpoint_name:
        click.echo(f"✅ Checkpoint created: {checkpoint_name}")
    else:
        click.echo("❌ Failed to create checkpoint")

# Helper function
def get_current_project_name() -> str:
    """Get current project name from directory or config"""
    import os
    return os.path.basename(os.getcwd())
```

### 1.4 Integrate with CCOM Orchestrator

```python
# Enhance ccom/orchestrator.py
from .mcp_bridge import MCPMemoryBridge

class CCOMOrchestrator:
    def __init__(self):
        # ... existing initialization
        self.project_name = self._get_project_name()
        self.memory_bridge = MCPMemoryBridge(self.project_name)
        
    def execute_command_with_context(self, command: str, args: List[str]) -> Dict:
        """Enhanced command execution with context capture"""
        
        # Execute existing command
        results = self.execute_command(command, args)
        
        # Auto-capture important results
        self._auto_capture_results(command, results)
        
        return results
    
    def _auto_capture_results(self, command: str, results: Dict):
        """Automatically capture command results to memory"""
        
        feature = self._extract_feature_from_command(command)
        
        if not feature:
            return
        
        # Capture validation errors
        if results.get('validation_errors'):
            for error in results['validation_errors']:
                self.memory_bridge.save_context(
                    feature, 
                    'issue', 
                    f"Validation error: {error}",
                    'high'
                )
        
        # Capture successful operations  
        if results.get('success') and results.get('operation'):
            self.memory_bridge.save_context(
                feature,
                'progress',
                f"Completed: {results['operation']}",
                'normal'
            )
        
        # Capture file modifications
        if results.get('files_modified'):
            file_list = ', '.join(results['files_modified'])
            self.memory_bridge.save_context(
                feature,
                'progress', 
                f"Modified files: {file_list}",
                'normal'
            )
    
    def _extract_feature_from_command(self, command: str) -> str:
        """Extract feature name from command for context tracking"""
        
        # Simple extraction logic - enhance as needed
        words = command.lower().split()
        
        # Look for common feature indicators
        feature_indicators = ['auth', 'user', 'login', 'api', 'database', 'ui']
        
        for word in words:
            if any(indicator in word for indicator in feature_indicators):
                return word
        
        # Fallback to command type
        if words:
            return words[0]
            
        return 'general'
```

## Phase 2: Enhanced Features (Week 2)

### 2.1 Advanced Context Commands

```python
# Add to CLI
@context.command()
@click.argument('feature')
@click.option('--days', default=7, help='Look back days')
def timeline(feature, days):
    """Show timeline of work on a feature"""
    
    project_name = get_current_project_name()
    bridge = MCPMemoryBridge(project_name)
    
    # Get context from last N days
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    
    context = bridge.get_context(feature, limit=50)
    
    # Filter and sort by timestamp
    recent_context = [
        item for item in context
        if datetime.fromisoformat(item.get('timestamp', '').replace('Z', '+00:00')) > cutoff
    ]
    
    recent_context.sort(key=lambda x: x.get('timestamp', ''))
    
    click.echo(f"📅 Timeline for {feature} (last {days} days):\n")
    
    for item in recent_context:
        timestamp = item.get('timestamp', '')[:16].replace('T', ' ')
        category = item.get('category', 'note').upper()
        content = item.get('value', '')
        click.echo(f"{timestamp} [{category}] {content}")

@context.command()
def status():
    """Show memory status and statistics"""
    
    project_name = get_current_project_name()
    bridge = MCPMemoryBridge(project_name)
    
    # Get all context for statistics
    all_context = bridge.get_context(limit=1000)
    
    # Calculate statistics
    total_items = len(all_context)
    categories = {}
    priorities = {}
    
    for item in all_context:
        cat = item.get('category', 'unknown')
        pri = item.get('priority', 'normal')
        categories[cat] = categories.get(cat, 0) + 1
        priorities[pri] = priorities.get(pri, 0) + 1
    
    click.echo(f"💾 Memory Status for {project_name}:")
    click.echo(f"Total Items: {total_items}")
    click.echo(f"\nBy Category:")
    for cat, count in sorted(categories.items()):
        click.echo(f"  {cat}: {count}")
    click.echo(f"\nBy Priority:")
    for pri, count in sorted(priorities.items()):
        click.echo(f"  {pri}: {count}")
```

## Phase 3: Auto-Capture Integration (Week 3)

### 3.1 Quality Check Auto-Capture

```python
# Enhance existing quality check methods
def run_eslint_validation(self, file_paths: List[str]) -> Dict:
    """Run ESLint with auto-capture"""
    
    results = self._execute_eslint(file_paths)
    
    # Auto-capture results
    if results.get('errors'):
        for error in results['errors'][:5]:  # Limit to top 5 errors
            self.memory_bridge.save_context(
                'quality',
                'issue',
                f"ESLint error: {error['message']} in {error['file']}",
                'normal'
            )
    
    if results.get('warnings'):
        warning_summary = f"ESLint: {len(results['warnings'])} warnings found"
        self.memory_bridge.save_context(
            'quality',
            'progress',
            warning_summary,
            'low'
        )
    
    return results

def run_security_scan(self, project_path: str) -> Dict:
    """Run security scan with auto-capture"""
    
    results = self._execute_security_scan(project_path)
    
    # Auto-capture security findings
    if results.get('vulnerabilities'):
        for vuln in results['vulnerabilities']:
            severity = vuln.get('severity', 'medium')
            priority = 'critical' if severity == 'critical' else 'high'
            
            self.memory_bridge.save_context(
                'security',
                'issue',
                f"Security vulnerability: {vuln['title']} ({severity})",
                priority
            )
    
    return results
```

## Testing Strategy

### Basic Integration Test

```bash
# Test installation
npm install -g mcp-memory-keeper
claude mcp add --scope user memory-keeper npx mcp-memory-keeper

# Test CCOM integration
cd your-test-project

# Test context commands
ccom context note auth "Testing MCP integration with JWT authentication"
ccom context note auth "Decided on 15-minute access tokens" --type decision --priority high
ccom context note auth "Need to add rate limiting" --type issue --priority normal

# Test context retrieval
ccom context resume auth  # Should show all saved context

# Test search
ccom context search "JWT"  # Should find authentication notes

# Test checkpoint
ccom context checkpoint --name "auth-feature-complete"
```

### Integration Validation

```python
# tests/test_mcp_integration.py
import pytest
from ccom.mcp_bridge import MCPMemoryBridge

def test_mcp_bridge_basic_operations():
    bridge = MCPMemoryBridge("test-project")
    
    # Test save
    success = bridge.save_context("auth", "decision", "Test decision", "high")
    assert success
    
    # Test retrieve
    context = bridge.get_context("auth", "decision")
    assert len(context) > 0
    assert "Test decision" in context[0]['value']
    
    # Test search
    results = bridge.search_context("Test decision")
    assert len(results) > 0

def test_context_cli_commands():
    # Test CLI commands integration
    from click.testing import CliRunner
    from ccom.cli import cli
    
    runner = CliRunner()
    
    # Test note command
    result = runner.invoke(cli, ['context', 'note', 'auth', 'Test note'])
    assert result.exit_code == 0
    assert "Saved" in result.output
    
    # Test resume command  
    result = runner.invoke(cli, ['context', 'resume', 'auth'])
    assert result.exit_code == 0
    assert "Test note" in result.output
```

## Migration Strategy

### Backward Compatibility

```python
# ccom/memory_manager.py - Unified memory interface
class UnifiedMemoryManager:
    """Manages both legacy JSON memory and new MCP memory"""
    
    def __init__(self, project_name: str):
        self.legacy_memory = LegacyJSONMemory()  # Existing system
        self.mcp_memory = MCPMemoryBridge(project_name)
        self.migration_enabled = True
    
    def get_feature_context(self, feature_name: str) -> Dict:
        """Get context from both systems"""
        
        # Get from legacy system
        legacy_context = self.legacy_memory.get_feature(feature_name)
        
        # Get from MCP system
        mcp_context = self.mcp_memory.get_resume_context(feature_name)
        
        # Combine intelligently
        return self._merge_context(legacy_context, mcp_context)
    
    def save_feature_context(self, feature_name: str, context: Dict):
        """Save to both systems during migration"""
        
        # Save to legacy (for backward compatibility)
        self.legacy_memory.save_feature(feature_name, context)
        
        # Save to MCP (for enhanced capabilities)
        if self.migration_enabled:
            self._migrate_to_mcp(feature_name, context)
    
    def _migrate_to_mcp(self, feature_name: str, context: Dict):
        """Migrate legacy context to MCP format"""
        
        # Convert legacy format to MCP context items
        if context.get('description'):
            self.mcp_memory.save_context(
                feature_name, 'note', context['description'], 'normal'
            )
        
        if context.get('issues'):
            for issue in context['issues']:
                self.mcp_memory.save_context(
                    feature_name, 'issue', issue, 'normal'
                )
```

## Success Metrics & Monitoring

### Context Quality Metrics

```python
# ccom/metrics.py
class ContextMetrics:
    def __init__(self, bridge: MCPMemoryBridge):
        self.bridge = bridge
    
    def calculate_context_health(self, feature: str) -> Dict:
        """Calculate context completeness and quality"""
        
        context = self.bridge.get_context(feature, limit=100)
        
        metrics = {
            'total_items': len(context),
            'decisions_count': len([c for c in context if c.get('category') == 'decision']),
            'issues_resolved': len([c for c in context 
                                  if c.get('category') == 'issue' 
                                  and any(word in c.get('value', '').upper() 
                                         for word in ['FIXED', 'RESOLVED', 'COMPLETED'])]),
            'recent_activity': len([c for c in context 
                                  if self._is_recent(c.get('timestamp'))]),
            'context_completeness': self._calculate_completeness_score(context)
        }
        
        return metrics
    
    def _calculate_completeness_score(self, context: List[Dict]) -> float:
        """Score context completeness (0-100)"""
        
        score = 0
        
        # Has decisions
        if any(c.get('category') == 'decision' for c in context):
            score += 25
        
        # Has progress tracking
        if any(c.get('category') == 'progress' for c in context):
            score += 25
        
        # Has issue tracking
        if any(c.get('category') == 'issue' for c in context):
            score += 25
        
        # Has next steps
        if any(c.get('category') == 'next_step' for c in context):
            score += 25
        
        return score
```

## Deployment & Rollout

### Gradual Rollout Plan

1. **Week 1**: Core team testing with basic save/retrieve
2. **Week 2**: Add enhanced commands and auto-capture
3. **Week 3**: Full feature rollout with migration tools
4. **Week 4**: Monitor, optimize, and document lessons learned

### Configuration Management

```yaml
# .ccom/config.yml - Add MCP configuration
memory:
  provider: "mcp"  # or "legacy" or "hybrid"
  mcp:
    channel_prefix: "ccom"
    auto_capture: true
    retention_days: 90
    max_items_per_feature: 500
  
integration:
  mcp_memory_keeper:
    enabled: true
    priority_mapping:
      critical: "critical"
      high: "high"  
      normal: "normal"
      low: "low"
```

This implementation provides a solid foundation for CCOM + MCP Memory Keeper integration while maintaining backward compatibility and enabling gradual migration.   