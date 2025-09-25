"""MCP Memory Keeper Bridge for CCOM - Enhanced Seamless Implementation"""

import subprocess
import json
import time
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

class MCPMemoryBridge:
    """Bridge between CCOM and MCP Memory Keeper"""

    def __init__(self, project_name: str = None):
        self.project_name = project_name or self._get_project_name()
        self.channel = f"ccom-{self.project_name}"
        self.logger = logging.getLogger(__name__)

        # Bridge storage directory
        self.bridge_dir = Path(".ccom")
        self.bridge_dir.mkdir(exist_ok=True)

        # Test MCP availability
        self.mcp_available = self._test_mcp_connection()
        if not self.mcp_available:
            self.logger.info("MCP Memory Keeper not available - using file-based bridge")

    def _get_project_name(self) -> str:
        """Get project name from directory"""
        return os.path.basename(os.getcwd())

    def _test_mcp_connection(self) -> bool:
        """Test if MCP Memory Keeper is available"""
        try:
            # Check if mcp-memory-keeper is installed
            result = subprocess.run(
                ["which", "mcp-memory-keeper"] if os.name != 'nt' else ["where", "mcp-memory-keeper"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"MCP Memory Keeper check failed: {e}")
            return False

    def _call_mcp_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Call MCP Memory Keeper tools via bridge
        Phase 1: File-based bridge implementation
        """
        try:
            # For Phase 1, use file-based bridge
            return self._file_bridge_implementation(tool_name, params)
        except Exception as e:
            self.logger.error(f"MCP tool call failed: {tool_name}, {e}")
            return {"success": False, "error": str(e)}

    def _file_bridge_implementation(self, tool_name: str, params: Dict) -> Dict:
        """
        File-based bridge implementation for Phase 1
        This simulates MCP Memory Keeper functionality locally
        """
        bridge_file = self.bridge_dir / f"mcp_bridge_{self.channel}.json"

        # Load existing data
        try:
            if bridge_file.exists():
                with open(bridge_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"items": [], "sessions": [], "channels": {}, "checkpoints": {}}
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"items": [], "sessions": [], "channels": {}, "checkpoints": {}}

        # Handle different tool operations
        if tool_name == 'context_save':
            item = {
                **params,
                'id': f"{params.get('key')}_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'channel': params.get('channel', self.channel),
                'session_id': data.get('current_session', 'default')
            }
            data['items'].append(item)

            # Update channel info
            channel_name = item['channel']
            if channel_name not in data['channels']:
                data['channels'][channel_name] = {
                    'created': datetime.now().isoformat(),
                    'item_count': 0
                }
            data['channels'][channel_name]['item_count'] += 1
            data['channels'][channel_name]['last_activity'] = datetime.now().isoformat()

            result = {'success': True, 'id': item['id']}

        elif tool_name == 'context_get':
            channel_filter = params.get('channel', self.channel)
            category_filter = params.get('category')
            limit = params.get('limit', 10)

            # Filter items
            filtered_items = []
            for item in data['items']:
                if item.get('channel') == channel_filter:
                    if not category_filter or item.get('category') == category_filter:
                        filtered_items.append(item)

            # Sort by timestamp (newest first) and limit
            filtered_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            filtered_items = filtered_items[:limit]

            result = {'items': filtered_items, 'total': len(filtered_items)}

        elif tool_name == 'context_checkpoint':
            checkpoint_name = params.get('name', f"checkpoint-{int(time.time())}")
            checkpoint = {
                'name': checkpoint_name,
                'description': params.get('description', ''),
                'created': datetime.now().isoformat(),
                'items_count': len(data['items']),
                'channels': list(data['channels'].keys()),
                'snapshot': {
                    'items': data['items'].copy(),
                    'channels': data['channels'].copy()
                }
            }
            data['checkpoints'][checkpoint_name] = checkpoint
            result = {'success': True, 'checkpoint_id': checkpoint_name}

        elif tool_name == 'context_search':
            query = params.get('query', '').lower()
            limit = params.get('limit', 5)

            # Simple text search
            matching_items = []
            for item in data['items']:
                if query in item.get('value', '').lower() or query in item.get('key', '').lower():
                    matching_items.append(item)
                    if len(matching_items) >= limit:
                        break

            result = {'items': matching_items}

        else:
            result = {'success': False, 'error': f'Unknown tool: {tool_name}'}

        # Save data back
        with open(bridge_file, 'w') as f:
            json.dump(data, f, indent=2)

        return result

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

            result = self._call_mcp_tool('context_save', params)

            if result.get('success'):
                self.logger.info(f"Saved {context_type} for {feature}")
                return True
            return False

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

            result = self._call_mcp_tool('context_get', params)
            items = result.get('items', [])

            # Filter by feature if specified
            if feature:
                feature_lower = feature.lower()
                items = [
                    item for item in items
                    if feature_lower in item.get('key', '').lower() or
                       feature_lower in item.get('value', '').lower()
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
            'next_steps': self.get_context(feature, 'next_step', 3),
            'notes': self.get_context(feature, 'note', 3)
        }

        return context

    def create_checkpoint(self, name: str = None) -> str:
        """Create a checkpoint of current context state"""

        checkpoint_name = name or f"{self.project_name}-checkpoint-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        try:
            params = {
                'name': checkpoint_name,
                'description': f'CCOM checkpoint for {self.project_name}',
                'includeFiles': False,  # Start simple
                'includeGitStatus': True
            }

            result = self._call_mcp_tool('context_checkpoint', params)

            if result.get('success'):
                self.logger.info(f"Created checkpoint: {checkpoint_name}")
                return checkpoint_name
            return ""

        except Exception as e:
            self.logger.error(f"Failed to create checkpoint: {e}")
            return ""

    def search_context(self, query: str, limit: int = 5) -> List[Dict]:
        """Search context using text search"""

        try:
            params = {
                'query': query,
                'channel': self.channel,
                'limit': limit
            }

            result = self._call_mcp_tool('context_search', params)
            return result.get('items', [])

        except Exception as e:
            self.logger.error(f"Failed to search context: {e}")
            return []

    def format_context_for_display(self, context: Dict) -> str:
        """Format context for CLI display"""

        output = []

        # Decisions
        if context.get('decisions'):
            output.append("📋 **Recent Decisions:**")
            for item in context['decisions'][-3:]:
                timestamp = item.get('timestamp', '')[:10]
                output.append(f"  • {timestamp}: {item.get('value', '')}")

        # Active Issues
        if context.get('issues'):
            active_issues = [
                item for item in context['issues']
                if not any(word in item.get('value', '').upper()
                          for word in ['RESOLVED', 'FIXED', 'COMPLETED'])
            ]
            if active_issues:
                output.append("\n⚠️  **Active Issues:**")
                for item in active_issues[-3:]:
                    timestamp = item.get('timestamp', '')[:10]
                    output.append(f"  • {timestamp}: {item.get('value', '')}")

        # Recent Progress
        if context.get('progress'):
            output.append("\n✅ **Recent Progress:**")
            for item in context['progress'][-3:]:
                timestamp = item.get('timestamp', '')[:10]
                output.append(f"  • {timestamp}: {item.get('value', '')}")

        # Next Steps
        if context.get('next_steps'):
            output.append("\n🎯 **Next Steps:**")
            for item in context['next_steps'][-3:]:
                output.append(f"  • {item.get('value', '')}")

        # Notes
        if context.get('notes'):
            output.append("\n📝 **Notes:**")
            for item in context['notes'][-3:]:
                output.append(f"  • {item.get('value', '')}")

        return "\n".join(output) if output else "No context found for this feature."

    def get_statistics(self) -> Dict:
        """Get memory statistics"""

        bridge_file = self.bridge_dir / f"mcp_bridge_{self.channel}.json"

        try:
            if bridge_file.exists():
                with open(bridge_file, 'r') as f:
                    data = json.load(f)

                # Calculate statistics
                total_items = len(data.get('items', []))
                categories = {}
                priorities = {}

                for item in data.get('items', []):
                    cat = item.get('category', 'unknown')
                    pri = item.get('priority', 'normal')
                    categories[cat] = categories.get(cat, 0) + 1
                    priorities[pri] = priorities.get(pri, 0) + 1

                return {
                    'total_items': total_items,
                    'categories': categories,
                    'priorities': priorities,
                    'channels': list(data.get('channels', {}).keys()),
                    'checkpoints': len(data.get('checkpoints', {}))
                }
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")

        return {
            'total_items': 0,
            'categories': {},
            'priorities': {},
            'channels': [],
            'checkpoints': 0
        }

    def extract_and_save_from_output(self, command: str, output: str) -> bool:
        """Intelligently extract context from command output and save automatically"""

        insights = self._extract_insights_from_output(command, output)

        for insight in insights:
            self.save_context(
                insight['feature'],
                insight['type'],
                insight['content'],
                insight['priority']
            )

        return len(insights) > 0

    def _extract_insights_from_output(self, command: str, output: str) -> List[Dict]:
        """Extract meaningful insights from command output"""
        insights = []

        # Extract from different types of outputs
        if 'lint' in command or 'eslint' in command:
            insights.extend(self._extract_lint_insights(output))
        elif 'test' in command:
            insights.extend(self._extract_test_insights(output))
        elif 'security' in command or 'audit' in command:
            insights.extend(self._extract_security_insights(output))
        elif 'deploy' in command:
            insights.extend(self._extract_deployment_insights(output))
        elif 'build' in command:
            insights.extend(self._extract_build_insights(output))

        # Always extract general insights
        insights.extend(self._extract_general_insights(command, output))

        return insights

    def _extract_lint_insights(self, output: str) -> List[Dict]:
        """Extract insights from linting output"""
        insights = []

        # Look for error patterns
        error_patterns = [
            r'(\d+) error[s]?',
            r'(\d+) warning[s]?',
            r'Error: (.+?) at',
            r'Warning: (.+?) at'
        ]

        for pattern in error_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches[:3]:  # Top 3 issues
                if isinstance(match, tuple):
                    content = f"Linting: {match[1] if len(match) > 1 else match[0]}"
                else:
                    content = f"Linting: {match} issues found"

                insights.append({
                    'feature': 'quality',
                    'type': 'issue',
                    'content': content,
                    'priority': 'normal'
                })

        # Success case
        if 'no errors' in output.lower() or 'passed' in output.lower():
            insights.append({
                'feature': 'quality',
                'type': 'progress',
                'content': 'Linting passed - no errors found',
                'priority': 'normal'
            })

        return insights

    def _extract_test_insights(self, output: str) -> List[Dict]:
        """Extract insights from test output"""
        insights = []

        # Test result patterns
        test_patterns = [
            r'(\d+) passing',
            r'(\d+) failing',
            r'Tests: (\d+) failed, (\d+) passed',
            r'✓ (.+?) \(\d+ms\)',  # Passing tests
            r'✗ (.+?)$'  # Failing tests
        ]

        for pattern in test_patterns:
            matches = re.findall(pattern, output, re.MULTILINE)
            for match in matches[:5]:  # Top 5 results
                if 'passing' in str(match) or '✓' in str(match):
                    insights.append({
                        'feature': 'testing',
                        'type': 'progress',
                        'content': f"Test passed: {match}",
                        'priority': 'normal'
                    })
                elif 'failing' in str(match) or '✗' in str(match):
                    insights.append({
                        'feature': 'testing',
                        'type': 'issue',
                        'content': f"Test failed: {match}",
                        'priority': 'high'
                    })

        return insights

    def _extract_security_insights(self, output: str) -> List[Dict]:
        """Extract insights from security output"""
        insights = []

        # Security patterns
        vuln_patterns = [
            r'(\d+) vulnerabilit(?:y|ies) found',
            r'High severity: (.+?)$',
            r'Critical: (.+?)$',
            r'Found (\d+) issues'
        ]

        for pattern in vuln_patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)
            for match in matches[:3]:
                insights.append({
                    'feature': 'security',
                    'type': 'issue',
                    'content': f"Security: {match}",
                    'priority': 'high'
                })

        # Success case
        if 'no vulnerabilities' in output.lower() or 'no issues found' in output.lower():
            insights.append({
                'feature': 'security',
                'type': 'progress',
                'content': 'Security scan passed - no vulnerabilities found',
                'priority': 'normal'
            })

        return insights

    def _extract_deployment_insights(self, output: str) -> List[Dict]:
        """Extract insights from deployment output"""
        insights = []

        # Deployment patterns
        deploy_patterns = [
            r'deployed to (.+?)$',
            r'URL: (https?://[^\s]+)',
            r'Build time: (.+?)$',
            r'Error: (.+?)$'
        ]

        for pattern in deploy_patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)
            for match in matches[:3]:
                if 'error' in pattern.lower():
                    insights.append({
                        'feature': 'deployment',
                        'type': 'issue',
                        'content': f"Deployment error: {match}",
                        'priority': 'critical'
                    })
                else:
                    insights.append({
                        'feature': 'deployment',
                        'type': 'progress',
                        'content': f"Deployment: {match}",
                        'priority': 'normal'
                    })

        return insights

    def _extract_build_insights(self, output: str) -> List[Dict]:
        """Extract insights from build output"""
        insights = []

        # Build patterns
        if 'built successfully' in output.lower():
            insights.append({
                'feature': 'build',
                'type': 'progress',
                'content': 'Build completed successfully',
                'priority': 'normal'
            })

        # Extract bundle sizes
        size_matches = re.findall(r'(\w+\.js)\s+(\d+(?:\.\d+)?)\s*([KMG]B)', output)
        for match in size_matches[:3]:
            file, size, unit = match
            insights.append({
                'feature': 'build',
                'type': 'note',
                'content': f"Bundle size: {file} = {size}{unit}",
                'priority': 'low'
            })

        # Build errors
        if 'build failed' in output.lower() or 'error' in output.lower():
            insights.append({
                'feature': 'build',
                'type': 'issue',
                'content': 'Build failed - check output for details',
                'priority': 'high'
            })

        return insights

    def _extract_general_insights(self, command: str, output: str) -> List[Dict]:
        """Extract general insights from any output"""
        insights = []

        # Extract URLs
        url_matches = re.findall(r'https?://[^\s<>"]+', output)
        for url in url_matches[:2]:  # Max 2 URLs
            insights.append({
                'feature': self._extract_feature_from_command(command),
                'type': 'note',
                'content': f"URL: {url}",
                'priority': 'low'
            })

        # Extract file paths being modified
        file_matches = re.findall(r'([^\s]+\.(js|ts|py|html|css|json|md))', output)
        if len(file_matches) > 0 and len(file_matches) <= 5:
            file_list = [match[0] for match in file_matches]
            insights.append({
                'feature': self._extract_feature_from_command(command),
                'type': 'progress',
                'content': f"Modified files: {', '.join(file_list)}",
                'priority': 'low'
            })

        return insights

    def _extract_feature_from_command(self, command: str) -> str:
        """Extract feature name from command"""
        feature_keywords = {
            'auth': ['auth', 'login', 'jwt', 'token'],
            'api': ['api', 'endpoint', 'route'],
            'ui': ['ui', 'component', 'view', 'page'],
            'database': ['db', 'database', 'model', 'schema'],
            'test': ['test', 'spec', 'jest'],
            'build': ['build', 'webpack', 'bundle'],
            'deploy': ['deploy', 'deployment', 'production'],
            'security': ['security', 'audit', 'vulnerability']
        }

        command_lower = command.lower()

        for feature, keywords in feature_keywords.items():
            if any(keyword in command_lower for keyword in keywords):
                return feature

        return 'general'

    def get_intelligent_summary(self, hours: int = 24) -> str:
        """Get an intelligent summary of recent work"""

        try:
            bridge_file = self.bridge_dir / f"mcp_bridge_{self.channel}.json"
            if not bridge_file.exists():
                return "No activity recorded yet."

            with open(bridge_file, 'r') as f:
                data = json.load(f)

            # Get recent items
            items = data.get('items', [])
            cutoff = datetime.now().timestamp() - (hours * 3600)

            recent_items = []
            for item in items:
                try:
                    item_time = datetime.fromisoformat(item.get('timestamp', ''))
                    if item_time.timestamp() > cutoff:
                        recent_items.append(item)
                except:
                    continue

            if not recent_items:
                return f"No activity in the last {hours} hours."

            # Analyze patterns
            features = {}
            categories = {}

            for item in recent_items:
                # Extract feature from key or content
                feature = self._extract_feature_from_item(item)
                features[feature] = features.get(feature, 0) + 1

                cat = item.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1

            # Build summary
            summary = []
            summary.append(f"📊 **Recent Activity Summary ({hours}h)**\n")

            # Top features
            if features:
                summary.append("🎯 **Active Features:**")
                for feature, count in sorted(features.items(), key=lambda x: x[1], reverse=True)[:3]:
                    summary.append(f"  • {feature}: {count} updates")
                summary.append("")

            # Activity breakdown
            if categories:
                summary.append("📋 **Activity Breakdown:**")
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                    icon = {'progress': '✅', 'issue': '⚠️', 'decision': '🎯', 'note': '📝'}.get(cat, '•')
                    summary.append(f"  {icon} {cat}: {count}")
                summary.append("")

            # Recent highlights
            summary.append("🔍 **Recent Highlights:**")
            recent_sorted = sorted(recent_items, key=lambda x: x.get('timestamp', ''), reverse=True)

            for item in recent_sorted[:3]:
                timestamp = item.get('timestamp', '')[:16].replace('T', ' ')
                content = item.get('value', '')[:60] + ('...' if len(item.get('value', '')) > 60 else '')
                summary.append(f"  • {timestamp}: {content}")

            return "\n".join(summary)

        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return "Unable to generate summary at this time."

    def _extract_feature_from_item(self, item: Dict) -> str:
        """Extract feature name from context item"""

        # Try key first
        key = item.get('key', '')
        if '_' in key:
            potential_feature = key.split('_')[0]
            if len(potential_feature) > 2:
                return potential_feature

        # Try content
        content = item.get('value', '').lower()

        # Feature keywords
        feature_patterns = {
            'auth': ['authentication', 'login', 'jwt', 'token', 'password'],
            'api': ['api', 'endpoint', 'route', 'rest', 'graphql'],
            'ui': ['component', 'view', 'page', 'interface', 'frontend'],
            'database': ['database', 'model', 'schema', 'query', 'sql'],
            'testing': ['test', 'spec', 'unit', 'integration'],
            'deployment': ['deploy', 'production', 'staging', 'release'],
            'security': ['security', 'vulnerability', 'audit', 'cors'],
            'performance': ['performance', 'optimization', 'speed', 'cache']
        }

        for feature, keywords in feature_patterns.items():
            if any(keyword in content for keyword in keywords):
                return feature

        return 'general'