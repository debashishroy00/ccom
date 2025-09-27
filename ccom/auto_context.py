"""
Automatic Context Capture for CCOM v2.0
Lightweight auto-capture using Node.js memory system
"""

import subprocess
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class AutoContextCapture:
    """Automatically captures context from CCOM operations using Node.js memory"""

    def __init__(self, project_name: str = None):
        self.project_name = project_name
        self.enabled = True

    def _call_node_memory(self, command: str, feature: str = "", description: str = "") -> bool:
        """Call Node.js memory system directly"""
        if not self.enabled:
            return False

        try:
            # Use the working Node.js memory system
            cmd = ["node", ".claude/ccom.js", command]
            if command == "remember" and feature and description:
                cmd.extend([feature, description])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=str(Path.cwd()),
                encoding='utf-8',
                errors='replace'
            )

            return result.returncode == 0
        except Exception:
            return False

    def capture_evaluation(self, evaluation_data: Dict):
        """Capture comprehensive evaluation results - KEY METHOD FOR APPLE STORE"""
        if not self.enabled:
            return

        feature_name = evaluation_data.get('feature_name', 'evaluation')

        # Build comprehensive description
        parts = []

        # Add evaluation type
        if evaluation_data.get('evaluation_type'):
            parts.append(f"{evaluation_data['evaluation_type']} evaluation")

        # Add grade/score
        if evaluation_data.get('grade'):
            parts.append(f"Grade: {evaluation_data['grade']}")

        # Add recommendation
        if evaluation_data.get('recommendation'):
            parts.append(f"Recommendation: {evaluation_data['recommendation']}")

        # Add key findings
        if evaluation_data.get('key_findings'):
            findings = evaluation_data['key_findings'][:3]  # Top 3
            parts.append(f"Key findings: {', '.join(findings)}")

        # Add market analysis
        if evaluation_data.get('market_analysis'):
            parts.append(f"Market analysis: {evaluation_data['market_analysis']}")

        # Add revenue potential
        if evaluation_data.get('revenue_potential'):
            parts.append(f"Revenue potential: {evaluation_data['revenue_potential']}")

        description = ". ".join(parts)

        # Save to Node.js memory
        self._call_node_memory("remember", feature_name, description)

    def capture_interaction(self, input_text: str, output_text: str):
        """Capture ALL significant Claude interactions automatically"""
        if not self.enabled:
            return

        # FIXED: Universal capture - capture EVERYTHING, not just filtered facts
        feature = self._detect_feature(input_text)

        # Always capture the basic interaction
        combined_content = f"{input_text}\n{output_text}"
        self._call_node_memory("remember", feature, combined_content)

        # OPTIONAL: Also extract specific facts for detailed analysis
        facts = self._extract_facts(input_text, output_text)
        for fact in facts:
            # Only save additional facts if they're different from main content
            if fact['content'] not in combined_content:
                self._call_node_memory("remember", fact['feature'], fact['content'])

        # Additional universal patterns
        self._capture_universal_patterns(input_text, output_text, feature)

    def capture_command(self, command: str, args: List[str] = None, result: str = ""):
        """Capture command execution"""
        if not self.enabled:
            return

        feature = self._extract_feature_from_command(command, args)
        description = f"Executed: {command}"

        if args:
            description += f" {' '.join(args)}"

        if result:
            # Extract success/failure
            if any(word in result.lower() for word in ['success', 'complete', 'passed']):
                description += " - SUCCESS"
            elif any(word in result.lower() for word in ['fail', 'error', 'issue']):
                description += " - FAILED"

        self._call_node_memory("remember", feature, description)

    def capture_workflow(self, workflow_name: str, status: str, details: Dict = None):
        """Capture workflow execution"""
        if not self.enabled:
            return

        feature = f"workflow_{workflow_name}"

        if status == "completed":
            description = f"{workflow_name} workflow completed successfully"
            if details and details.get('metrics'):
                description += f". Metrics: {details['metrics']}"
        elif status == "failed":
            description = f"{workflow_name} workflow failed"
            if details and details.get('error'):
                description += f". Error: {details['error']}"
        else:
            description = f"{workflow_name} workflow {status}"

        self._call_node_memory("remember", feature, description)

    def capture_quality_results(self, results: Dict):
        """Capture code quality results"""
        if not self.enabled:
            return

        feature = "code_quality"

        if results.get('grade'):
            description = f"Code quality: {results['grade']}"
        else:
            description = "Code quality check completed"

        if results.get('issues_count'):
            description += f". Issues found: {results['issues_count']}"

        if results.get('improvements'):
            improvements = results['improvements'][:3]  # Top 3
            description += f". Improvements: {', '.join(improvements)}"

        self._call_node_memory("remember", feature, description)

    def capture_security_results(self, results: Dict):
        """Capture security scan results"""
        if not self.enabled:
            return

        feature = "security"

        vuln_count = len(results.get('vulnerabilities', []))
        if vuln_count == 0:
            description = "Security scan: PASSED - No vulnerabilities found"
        else:
            description = f"Security scan: {vuln_count} vulnerabilities found"

            # Add high-severity issues
            high_vulns = [v for v in results.get('vulnerabilities', [])
                         if v.get('severity') in ['high', 'critical']]
            if high_vulns:
                description += f". Critical issues: {len(high_vulns)}"

        self._call_node_memory("remember", feature, description)

    def capture_deployment(self, status: str, details: Dict = None):
        """Capture deployment status"""
        if not self.enabled:
            return

        feature = "deployment"

        if status == "success":
            description = "Deployment successful"
            if details and details.get('url'):
                description += f". URL: {details['url']}"
        elif status == "failed":
            description = "Deployment failed"
            if details and details.get('error'):
                description += f". Error: {details['error']}"
        else:
            description = f"Deployment {status}"

        self._call_node_memory("remember", feature, description)

    def _capture_universal_patterns(self, input_text: str, output_text: str, feature: str):
        """Capture universal patterns from any Claude interaction"""

        # Capture long detailed responses (likely important analysis)
        if len(output_text) > 1000:
            # Extract first meaningful paragraph
            paragraphs = [p.strip() for p in output_text.split('\n\n') if len(p.strip()) > 100]
            if paragraphs:
                summary = paragraphs[0][:300] + "..." if len(paragraphs[0]) > 300 else paragraphs[0]
                self._call_node_memory("remember", f"{feature}_analysis", f"Detailed analysis: {summary}")

        # Capture implementation discussions
        if any(word in output_text.lower() for word in ['implement', 'build', 'create', 'develop']):
            impl_sentences = self._extract_implementation_details(output_text)
            if impl_sentences:
                self._call_node_memory("remember", f"{feature}_implementation", impl_sentences)

        # Capture architectural decisions
        if any(word in output_text.lower() for word in ['architecture', 'design', 'pattern', 'approach']):
            arch_details = self._extract_architectural_decisions(output_text)
            if arch_details:
                self._call_node_memory("remember", f"{feature}_architecture", arch_details)

        # Capture problem-solving
        if any(word in input_text.lower() for word in ['problem', 'issue', 'error', 'bug', 'fix']):
            solution = self._extract_solution_details(output_text)
            if solution:
                self._call_node_memory("remember", f"{feature}_solution", solution)

        # Capture research/investigation
        if any(word in input_text.lower() for word in ['how', 'what', 'why', 'explain', 'understand']):
            research = self._extract_research_findings(output_text)
            if research:
                self._call_node_memory("remember", f"{feature}_research", research)

        # Capture code discussions
        if '```' in output_text or 'function' in output_text.lower() or 'class' in output_text.lower():
            code_summary = self._extract_code_discussion(output_text)
            if code_summary:
                self._call_node_memory("remember", f"{feature}_code", code_summary)

    def _extract_implementation_details(self, text: str) -> str:
        """Extract implementation-related content"""
        sentences = text.split('.')
        impl_sentences = []

        for sentence in sentences:
            if any(word in sentence.lower() for word in ['implement', 'build', 'create', 'develop', 'add']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    impl_sentences.append(clean_sentence)

        return '. '.join(impl_sentences[:3]) if impl_sentences else ""

    def _extract_architectural_decisions(self, text: str) -> str:
        """Extract architectural decision content"""
        sentences = text.split('.')
        arch_sentences = []

        for sentence in sentences:
            if any(word in sentence.lower() for word in ['architecture', 'design', 'pattern', 'structure', 'approach']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    arch_sentences.append(clean_sentence)

        return '. '.join(arch_sentences[:3]) if arch_sentences else ""

    def _extract_solution_details(self, text: str) -> str:
        """Extract solution/fix details"""
        sentences = text.split('.')
        solution_sentences = []

        for sentence in sentences:
            if any(word in sentence.lower() for word in ['solution', 'fix', 'resolve', 'solve', 'answer']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    solution_sentences.append(clean_sentence)

        return '. '.join(solution_sentences[:3]) if solution_sentences else ""

    def _extract_research_findings(self, text: str) -> str:
        """Extract research/explanation content"""
        # Look for explanatory content
        if len(text) > 500:  # Substantial response
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
            if paragraphs:
                return paragraphs[0][:400] + "..." if len(paragraphs[0]) > 400 else paragraphs[0]
        return ""

    def _extract_code_discussion(self, text: str) -> str:
        """Extract code-related discussion"""
        # Look for code blocks or function/class mentions
        if '```' in text:
            # Count code blocks
            code_blocks = text.count('```') // 2
            return f"Code discussion with {code_blocks} code block(s)"
        elif any(word in text.lower() for word in ['function', 'class', 'method', 'variable']):
            sentences = text.split('.')
            code_sentences = []

            for sentence in sentences:
                if any(word in sentence.lower() for word in ['function', 'class', 'method', 'code']):
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 20:
                        code_sentences.append(clean_sentence)

            return '. '.join(code_sentences[:2]) if code_sentences else ""
        return ""

    def _detect_feature(self, input_text: str) -> str:
        """Detect feature from input text"""
        input_lower = input_text.lower()

        # Enhanced feature detection for evaluations
        if any(word in input_lower for word in ['apple store', 'app store', 'ios']):
            return 'apple_store_evaluation'
        elif any(word in input_lower for word in ['google play', 'android', 'play store']):
            return 'google_play_evaluation'
        elif any(word in input_lower for word in ['monetization', 'revenue', 'pricing']):
            return 'monetization_evaluation'
        elif any(word in input_lower for word in ['slack', 'integration']):
            return 'slack_integration_evaluation'
        elif any(word in input_lower for word in ['evaluate', 'assess', 'analysis', 'review']):
            return 'evaluation'
        elif any(word in input_lower for word in ['deploy', 'ship', 'production']):
            return 'deployment'
        elif any(word in input_lower for word in ['quality', 'lint', 'test']):
            return 'quality'
        elif any(word in input_lower for word in ['security', 'audit', 'vulnerab']):
            return 'security'
        elif any(word in input_lower for word in ['build', 'compile']):
            return 'build'
        elif any(word in input_lower for word in ['auth', 'login', 'password']):
            return 'authentication'
        else:
            return 'general'

    def _extract_facts(self, input_text: str, output_text: str) -> List[Dict]:
        """Extract ALL meaningful facts from interaction"""
        facts = []
        feature = self._detect_feature(input_text)

        # Check for evaluations with grades/scores
        grade_match = re.search(r'(?:grade|score)[:\s]+([A-F][+-]?|\d+(?:/\d+)?(?:%)?)', output_text, re.IGNORECASE)
        if grade_match:
            facts.append({
                'feature': feature,
                'content': f"Evaluation grade: {grade_match.group(1)}",
                'priority': 'high'
            })

        # Check for recommendations (more comprehensive)
        if 'recommend' in output_text.lower():
            sentences = output_text.split('.')
            for sentence in sentences:
                if 'recommend' in sentence.lower():
                    facts.append({
                        'feature': feature,
                        'content': f"Recommendation: {sentence.strip()[:250]}",
                        'priority': 'high'
                    })
                    break

        # Check for revenue/market analysis
        if any(word in output_text.lower() for word in ['revenue', 'market', 'monetization', '$']):
            money_match = re.search(r'\$[\d,]+(?:K|M|k|m)?(?:/month|/year)?', output_text)
            if money_match:
                facts.append({
                    'feature': feature,
                    'content': f"Revenue potential: {money_match.group(0)}",
                    'priority': 'high'
                })

        # Extract key decisions and conclusions
        if any(word in output_text.lower() for word in ['conclusion', 'decision', 'result', 'outcome']):
            conclusions = self._extract_conclusions(output_text)
            if conclusions:
                facts.append({
                    'feature': feature,
                    'content': f"Conclusion: {conclusions}",
                    'priority': 'normal'
                })

        # Extract technical specifications
        if any(word in output_text.lower() for word in ['specification', 'requirement', 'feature', 'functionality']):
            specs = self._extract_specifications(output_text)
            if specs:
                facts.append({
                    'feature': feature,
                    'content': f"Specifications: {specs}",
                    'priority': 'normal'
                })

        # Extract warnings and important notes
        if any(word in output_text.lower() for word in ['warning', 'important', 'note', 'caution']):
            warnings = self._extract_warnings(output_text)
            if warnings:
                facts.append({
                    'feature': feature,
                    'content': f"Important note: {warnings}",
                    'priority': 'normal'
                })

        # Extract URLs and references
        url_matches = re.findall(r'https?://[^\s<>"{}\\^`\[\]]+', output_text)
        if url_matches:
            facts.append({
                'feature': feature,
                'content': f"References: {', '.join(url_matches[:3])}",
                'priority': 'normal'
            })

        # Extract tool/technology mentions
        tech_words = ['api', 'database', 'framework', 'library', 'tool', 'service', 'platform']
        if any(word in output_text.lower() for word in tech_words):
            tech_mentions = self._extract_technology_mentions(output_text)
            if tech_mentions:
                facts.append({
                    'feature': feature,
                    'content': f"Technologies discussed: {tech_mentions}",
                    'priority': 'normal'
                })

        return facts

    def _extract_conclusions(self, text: str) -> str:
        """Extract conclusion-type content"""
        sentences = text.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['conclusion', 'result', 'outcome', 'summary']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    return clean_sentence[:200]
        return ""

    def _extract_specifications(self, text: str) -> str:
        """Extract specification content"""
        sentences = text.split('.')
        spec_sentences = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['spec', 'requirement', 'feature', 'must', 'should']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    spec_sentences.append(clean_sentence)
        return '. '.join(spec_sentences[:2]) if spec_sentences else ""

    def _extract_warnings(self, text: str) -> str:
        """Extract warning/important content"""
        sentences = text.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['warning', 'important', 'note', 'caution', 'critical']):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20:
                    return clean_sentence[:200]
        return ""

    def _extract_technology_mentions(self, text: str) -> str:
        """Extract technology/tool mentions"""
        # Common technologies to look for
        technologies = []
        tech_patterns = [
            r'\b(React|Vue|Angular|Node\.js|Python|JavaScript|TypeScript|Java|C\+\+|C#)\b',
            r'\b(MySQL|PostgreSQL|MongoDB|Redis|SQLite)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes)\b',
            r'\b(REST|GraphQL|API|OAuth|JWT)\b'
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            technologies.extend(matches)

        return ', '.join(list(set(technologies))[:5]) if technologies else ""

    def _extract_feature_from_command(self, command: str, args: List[str] = None) -> str:
        """Extract feature from command"""
        command_lower = command.lower()

        if 'deploy' in command_lower:
            return 'deployment'
        elif 'test' in command_lower or 'quality' in command_lower:
            return 'quality'
        elif 'security' in command_lower or 'audit' in command_lower:
            return 'security'
        elif 'build' in command_lower:
            return 'build'
        else:
            return 'general'


# Global instance for easy access
_auto_context = None

def get_auto_context(project_name: str = None) -> AutoContextCapture:
    """Get or create the global auto-context instance"""
    global _auto_context
    if _auto_context is None:
        _auto_context = AutoContextCapture(project_name)
    return _auto_context

def capture_evaluation(evaluation_data: Dict):
    """Quick helper for evaluation capture"""
    auto = get_auto_context()
    auto.capture_evaluation(evaluation_data)

def capture_interaction(input_text: str, output_text: str):
    """Quick helper for interaction capture"""
    auto = get_auto_context()
    auto.capture_interaction(input_text, output_text)

def capture_claude_code_ccom(input_text: str, output_text: str, project_path: str = None):
    """
    Hook for Claude Code CCOM commands to trigger auto-capture
    This bridges Claude Code CCOM commands to the CCOM auto-capture system
    """
    try:
        import os
        from pathlib import Path

        # Set working directory if specified
        original_cwd = None
        if project_path:
            original_cwd = os.getcwd()
            project_path = Path(project_path).resolve()
            if project_path.exists():
                os.chdir(str(project_path))

        # Use existing auto_context system
        auto = get_auto_context()
        auto.capture_interaction(input_text, output_text)

        # Restore original directory
        if original_cwd:
            os.chdir(original_cwd)

        return True
    except Exception as e:
        # Silent fail - don't break Claude Code if auto-capture fails
        import logging
        logging.getLogger(__name__).debug(f"Claude Code CCOM auto-capture failed: {e}")
        return False