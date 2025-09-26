"""
Universal Context Capture for CCOM - Like mem0/MCP
Captures ALL interactions automatically without pattern matching
"""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from .mcp_bridge import MCPMemoryBridge


class UniversalCapture:
    """
    Captures EVERYTHING - no pattern matching needed.
    Works like mem0: capture all, extract meaning later.
    """

    def __init__(self, project_name: str = None):
        self.bridge = MCPMemoryBridge(project_name)
        self.enabled = True

        # Store raw interactions for processing
        self.interactions_buffer = []
        self.max_buffer_size = 10

    def capture_interaction(self, input_text: str, output_text: str, metadata: Dict = None):
        """
        Core method - captures EVERY interaction automatically.
        No pattern matching, no special handling - just save everything.

        This is how mem0 works - capture all, extract meaning later.
        """
        if not self.enabled:
            return

        # Create interaction record
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'input': input_text,
            'output': output_text,
            'metadata': metadata or {}
        }

        # Add to buffer
        self.interactions_buffer.append(interaction)

        # Process and save
        self._process_interaction(interaction)

        # Flush buffer if needed
        if len(self.interactions_buffer) >= self.max_buffer_size:
            self._flush_buffer()

    def _process_interaction(self, interaction: Dict):
        """
        Process a single interaction - extract key information.
        This is where the 'intelligence' happens, similar to mem0's LLM extraction.
        """

        input_text = interaction['input'].lower()
        output_text = interaction['output']

        # Extract key facts from the interaction (simplified version of what mem0 does with LLM)
        facts = self._extract_facts(input_text, output_text)

        # Save each fact as a separate context item
        for fact in facts:
            self.bridge.save_context(
                feature=fact['feature'],
                context_type=fact['type'],
                content=fact['content'],
                priority=fact['priority'],
                metadata={
                    'input': input_text[:100],  # Store truncated input for reference
                    'timestamp': interaction['timestamp']
                }
            )

    def _extract_facts(self, input_text: str, output_text: str) -> list:
        """
        Extract important facts from interaction.
        In mem0, this is done by LLM. Here we use simple heuristics.
        """
        facts = []

        # Always save the command execution
        facts.append({
            'feature': self._detect_feature(input_text),
            'type': 'progress',
            'content': f"Command: {input_text[:200]}",
            'priority': 'normal'
        })

        # Extract facts from output
        output_lower = output_text.lower()

        # Success/failure detection
        if any(word in output_lower for word in ['success', 'complete', 'passed', '✅']):
            facts.append({
                'feature': self._detect_feature(input_text),
                'type': 'progress',
                'content': self._extract_success_message(output_text),
                'priority': 'normal'
            })
        elif any(word in output_lower for word in ['fail', 'error', '❌', 'issue']):
            facts.append({
                'feature': self._detect_feature(input_text),
                'type': 'issue',
                'content': self._extract_error_message(output_text),
                'priority': 'high'
            })

        # Grade/score detection
        if 'grade' in output_lower or 'score' in output_lower:
            score = self._extract_score(output_text)
            if score:
                facts.append({
                    'feature': 'evaluation',
                    'type': 'note',
                    'content': score,
                    'priority': 'high'
                })

        # URL detection
        if 'http' in output_text or 'www.' in output_text:
            urls = self._extract_urls(output_text)
            for url in urls[:2]:  # Max 2 URLs
                facts.append({
                    'feature': self._detect_feature(input_text),
                    'type': 'note',
                    'content': f"URL: {url}",
                    'priority': 'low'
                })

        # Warning detection
        if 'warning' in output_lower or '⚠️' in output_text:
            facts.append({
                'feature': self._detect_feature(input_text),
                'type': 'warning',
                'content': self._extract_warning(output_text),
                'priority': 'normal'
            })

        # Recommendation detection
        if 'recommend' in output_lower or 'suggestion' in output_lower:
            facts.append({
                'feature': self._detect_feature(input_text),
                'type': 'decision',
                'content': self._extract_recommendation(output_text),
                'priority': 'high'
            })

        return facts

    def _detect_feature(self, input_text: str) -> str:
        """
        Simple feature detection from input.
        This is much simpler than before - just basic categorization.
        """
        input_lower = input_text.lower()

        # Basic feature detection
        feature_keywords = {
            'auth': ['auth', 'login', 'password', 'jwt', 'token'],
            'deploy': ['deploy', 'ship', 'production', 'release'],
            'quality': ['quality', 'lint', 'format', 'test', 'check'],
            'security': ['security', 'vulnerab', 'audit', 'scan'],
            'build': ['build', 'compile', 'bundle', 'webpack'],
            'evaluate': ['evaluate', 'improve', 'assess', 'review'],
            'api': ['api', 'endpoint', 'route', 'rest'],
            'database': ['database', 'db', 'sql', 'mongo', 'redis']
        }

        for feature, keywords in feature_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return feature

        return 'general'

    def _extract_success_message(self, output: str) -> str:
        """Extract success message from output"""
        lines = output.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['success', 'complete', 'passed']):
                return line.strip()[:200]
        return "Operation completed successfully"

    def _extract_error_message(self, output: str) -> str:
        """Extract error message from output"""
        lines = output.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['error', 'fail', 'issue']):
                return line.strip()[:200]
        return "Operation encountered issues"

    def _extract_score(self, output: str) -> Optional[str]:
        """Extract score or grade from output"""
        import re

        # Look for patterns like "Grade: A+", "Score: 95/100", etc.
        grade_pattern = r'(?:grade|score)[:\s]+([A-F][+-]?|\d+(?:/\d+)?(?:%)?)'
        match = re.search(grade_pattern, output, re.IGNORECASE)
        if match:
            return f"Score: {match.group(1)}"

        return None

    def _extract_urls(self, output: str) -> list:
        """Extract URLs from output"""
        import re
        url_pattern = r'https?://[^\s<>"{}\\^`\[\]]+|www\.[^\s<>"{}\\^`\[\]]+'
        return re.findall(url_pattern, output)[:5]  # Max 5 URLs

    def _extract_warning(self, output: str) -> str:
        """Extract warning message from output"""
        lines = output.split('\n')
        for line in lines:
            if 'warning' in line.lower() or '⚠️' in line:
                return line.strip()[:200]
        return "Warning detected in output"

    def _extract_recommendation(self, output: str) -> str:
        """Extract recommendation from output"""
        lines = output.split('\n')
        for line in lines:
            if 'recommend' in line.lower() or 'suggestion' in line.lower():
                return line.strip()[:200]
        return "Recommendation provided in output"

    def _flush_buffer(self):
        """Flush interaction buffer - for batch processing if needed"""
        self.interactions_buffer = []

    def get_recent_context(self, hours: int = 24) -> Dict:
        """
        Retrieve recent context - like mem0's retrieval.
        Returns relevant memories based on recency and importance.
        """
        # Get all recent items
        all_items = self.bridge.get_context(limit=100)

        # Filter by time
        cutoff = datetime.now().timestamp() - (hours * 3600)
        recent_items = []

        for item in all_items:
            try:
                item_time = datetime.fromisoformat(item.get('timestamp', ''))
                if item_time.timestamp() > cutoff:
                    recent_items.append(item)
            except:
                continue

        # Group by feature and type
        context_summary = {
            'total_interactions': len(recent_items),
            'features': {},
            'issues': [],
            'successes': [],
            'key_facts': []
        }

        for item in recent_items:
            feature = item.get('key', '').split('_')[0] if '_' in item.get('key', '') else 'general'

            if feature not in context_summary['features']:
                context_summary['features'][feature] = 0
            context_summary['features'][feature] += 1

            # Collect issues
            if item.get('category') == 'issue':
                context_summary['issues'].append(item.get('value', '')[:100])

            # Collect successes
            if item.get('category') == 'progress':
                context_summary['successes'].append(item.get('value', '')[:100])

            # High priority items are key facts
            if item.get('priority') == 'high':
                context_summary['key_facts'].append(item.get('value', '')[:100])

        return context_summary

    def search(self, query: str) -> list:
        """
        Search through captured context - like mem0's semantic search.
        Simple text search for now, could be enhanced with embeddings.
        """
        return self.bridge.search_context(query, limit=10)


# Global instance for easy access
_universal_capture = None


def get_universal_capture(project_name: str = None) -> UniversalCapture:
    """Get or create the global universal capture instance"""
    global _universal_capture
    if _universal_capture is None:
        _universal_capture = UniversalCapture(project_name)
    return _universal_capture


def capture(input_text: str, output_text: str, metadata: Dict = None):
    """
    Simple interface to capture interactions.
    This is all you need - no complex pattern matching!
    """
    universal = get_universal_capture()
    universal.capture_interaction(input_text, output_text, metadata)