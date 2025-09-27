"""
Auto-capture for CCOM evaluations
Restores the smart extraction that was in mcp_bridge.py
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict
import re
from datetime import datetime

class AutoCapture:
    def __init__(self):
        self.enabled = True

    def capture_evaluation(self, output: str, project: str = None) -> bool:
        """
        Auto-capture evaluation outputs and save to memory.json
        This restores the functionality that was in mcp_bridge.py
        """
        if not self.enabled:
            return False

        # Check if this is an evaluation output (look for evaluation patterns)
        if not self._is_evaluation_output(output):
            return False

        try:
            # Extract evaluation type from output
            eval_type = self._detect_evaluation_type(output)

            # Build feature name (matching the memory.json pattern)
            feature_name = f"{eval_type}_evaluation_2025"

            # Extract comprehensive evaluation content
            evaluation_content = self._extract_evaluation_content(output)

            if evaluation_content:
                # Call Node.js memory system (like mcp_bridge did)
                return self._save_to_memory(feature_name, evaluation_content)

        except Exception as e:
            # Silent fail - don't break evaluation
            pass

        return False

    def _is_evaluation_output(self, output: str) -> bool:
        """Check if output is an evaluation that should be captured"""
        evaluation_indicators = [
            "evaluation",
            "assessment",
            "analysis",
            "recommendation",
            "TIER 1",
            "TIER 2",
            "revenue potential",
            "implementation complexity",
            "market analysis",
            "competitive analysis",
            "integration potential",
            "technical complexity",
            "business value",
            "ROI",
            "NOT RECOMMENDED",
            "RECOMMENDED"
        ]

        output_lower = output.lower()
        return any(indicator in output_lower for indicator in evaluation_indicators)

    def _detect_evaluation_type(self, output: str) -> str:
        """Extract evaluation type from output"""
        output_lower = output.lower()

        # Check for specific integration types
        if "salesforce" in output_lower:
            return "salesforce_integration"
        elif "slack" in output_lower:
            return "slack_integration"
        elif "calendar" in output_lower:
            return "calendar_integration"
        elif "google play" in output_lower:
            return "google_play"
        elif "apple store" in output_lower or "app store" in output_lower:
            return "apple_store"
        elif "stripe" in output_lower or "payment" in output_lower:
            return "payment_integration"
        elif "yahoo mail" in output_lower:
            return "yahoo_mail_integration"
        elif "react migration" in output_lower or "react" in output_lower:
            return "react_migration"
        elif "angular migration" in output_lower or "angular" in output_lower:
            return "angular_migration"
        elif "typescript" in output_lower or "tsx" in output_lower:
            return "typescript_tsx"
        elif "monetization" in output_lower:
            return "monetization"
        elif "ai assistant" in output_lower:
            return "ai_assistant_monetization"
        elif "white label" in output_lower:
            return "white_label_enterprise_monetization"
        elif "penetration test" in output_lower or "security test" in output_lower:
            return "penetration_test"
        elif "frontend architecture" in output_lower:
            return "frontend_architecture_assessment"
        elif "quality audit" in output_lower:
            return "quality_audit_post_cleanup"
        else:
            return "general"

    def _extract_evaluation_content(self, output: str) -> str:
        """Extract and format comprehensive evaluation content"""
        # For CCOM evaluations, capture comprehensive summaries

        # Check if this is a CCOM evaluation report
        if "CCOM" in output and "EVALUATION" in output:
            return self._extract_ccom_evaluation_summary(output)

        # Legacy extraction for other formats
        content_parts = []

        # Extract recommendation if present
        recommendation = self._extract_recommendation(output)
        if recommendation:
            content_parts.append(f"Recommendation: {recommendation}")

        # Extract revenue/ROI information
        revenue = self._extract_revenue_info(output)
        if revenue:
            content_parts.append(f"Revenue potential: {revenue}")

        # Extract complexity/timeline
        complexity = self._extract_complexity(output)
        if complexity:
            content_parts.append(f"Implementation complexity: {complexity}")

        # Extract market analysis
        market = self._extract_market_analysis(output)
        if market:
            content_parts.append(f"Market analysis: {market}")

        # If we found specific content, format it
        if content_parts:
            formatted_content = ". ".join(content_parts)
            if len(formatted_content) > 800:
                formatted_content = formatted_content[:797] + "..."
            return formatted_content

        # Fallback: extract first substantial paragraph
        paragraphs = [p.strip() for p in output.split('\n\n') if len(p.strip()) > 100]
        if paragraphs:
            content = paragraphs[0]
            if len(content) > 800:
                content = content[:797] + "..."
            return content

        return "Comprehensive evaluation completed"

    def _extract_ccom_evaluation_summary(self, output: str) -> str:
        """Extract comprehensive summary from CCOM evaluation reports"""
        lines = output.strip().split('\n')

        # Extract key components
        summary_parts = []

        # Get evaluation title/type
        title_line = None
        for line in lines:
            if "CCOM" in line and "EVALUATION" in line:
                title_line = line.strip()
                break

        # Extract project type
        project_type = None
        for line in lines:
            if "Project Type:" in line:
                project_type = line.split("Project Type:")[-1].strip()
                break

        # Extract tier/recommendation
        tier = None
        for line in lines:
            if "TIER" in line and ("RECOMMENDED" in line or "NOT RECOMMENDED" in line):
                tier = line.strip()
                break

        # Extract revenue potential
        revenue = None
        for line in lines:
            if "$" in line and ("revenue" in line.lower() or "month" in line):
                revenue = line.strip()
                break

        # Extract complexity/timeline
        complexity = None
        for line in lines:
            if "weeks" in line.lower() or "complexity" in line.lower():
                if "Implementation" in line or "Phase" in line:
                    complexity = line.strip()
                    break

        # Build summary
        if title_line:
            summary_parts.append(title_line.replace("🔍 ", "").replace(" - ", ": "))

        if project_type:
            summary_parts.append(f"Project: {project_type}")

        if tier:
            summary_parts.append(tier)

        if revenue:
            summary_parts.append(revenue)

        if complexity:
            summary_parts.append(complexity)

        # Join and format
        if summary_parts:
            summary = ". ".join(summary_parts)
            if len(summary) > 800:
                summary = summary[:797] + "..."
            return summary

        return "CCOM comprehensive evaluation completed"

    def _extract_recommendation(self, output: str) -> str:
        """Extract recommendation from output"""
        patterns = [
            r"recommendation[:\s]+([^.\n]+)",
            r"recommend[:\s]+([^.\n]+)",
            r"(not recommended|recommended|avoid|implement immediately)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1 if match.lastindex else 0).strip()

        return ""

    def _extract_revenue_info(self, output: str) -> str:
        """Extract revenue/ROI information"""
        patterns = [
            r"revenue potential[:\s]+([^.\n]+)",
            r"\$[\d,]+(?:K|M|k|m)?(?:/month|/year)?",
            r"roi[:\s]+([^.\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return ""

    def _extract_complexity(self, output: str) -> str:
        """Extract implementation complexity"""
        patterns = [
            r"implementation complexity[:\s]+([^.\n]+)",
            r"technical complexity[:\s]+([^.\n]+)",
            r"complexity[:\s]+([^.\n]+)",
            r"timeline[:\s]+([^.\n]+)",
            r"\d+-\d+ weeks?",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1 if match.lastindex else 0).strip()

        return ""

    def _extract_market_analysis(self, output: str) -> str:
        """Extract market analysis"""
        patterns = [
            r"market analysis[:\s]+([^.\n]+)",
            r"market timing[:\s]+([^.\n]+)",
            r"competitive[:\s]+([^.\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_technical_details(self, output: str) -> str:
        """Extract key technical details"""
        # Look for technical specifications, APIs, frameworks mentioned
        tech_indicators = [
            r"api[:\s]+([^.\n]+)",
            r"framework[:\s]+([^.\n]+)",
            r"integration[:\s]+([^.\n]+)",
            r"oauth2?",
            r"rest api",
            r"graphql",
        ]

        for pattern in tech_indicators:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(0).strip()

        return ""

    def _save_to_memory(self, feature_name: str, content: str) -> bool:
        """Save to Node.js memory system"""
        try:
            # Get the current working directory to find .claude/ccom.js
            cwd = Path.cwd()
            ccom_js = cwd / ".claude" / "ccom.js"

            # If not in current dir, try parent dirs (for cross-project usage)
            if not ccom_js.exists():
                for parent in cwd.parents:
                    ccom_js = parent / ".claude" / "ccom.js"
                    if ccom_js.exists():
                        cwd = parent
                        break

            if not ccom_js.exists():
                return False

            # Call Node.js memory system
            cmd = [
                "node",
                str(ccom_js),
                "remember",
                feature_name,
                content
            ]

            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                print(f"✅ Auto-captured comprehensive evaluation: {feature_name}")
                return True
            else:
                print(f"⚠️ Failed to auto-capture: {result.stderr}")
                return False

        except Exception as e:
            print(f"⚠️ Auto-capture error: {e}")
            return False

# Global instance
_auto_capture = AutoCapture()

def capture_if_evaluation(output: str, project: str = None) -> bool:
    """Public API for auto-capture"""
    return _auto_capture.capture_evaluation(output, project)

def enable_auto_capture():
    """Enable auto-capture"""
    _auto_capture.enabled = True

def disable_auto_capture():
    """Disable auto-capture"""
    _auto_capture.enabled = False