"""
MCP Keeper Bridge for CCOM
Non-disruptive integration with Claude Code's MCP Keeper memory system
Falls back gracefully to existing auto-capture if MCP unavailable
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from datetime import datetime


class MCPKeeperBridge:
    """Bridge to Claude Code's MCP Keeper memory system"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.enabled = True
        self.fallback_to_legacy = True
        self.logger = logging.getLogger(__name__)

        # MCP Keeper detection
        self._mcp_available = None
        self._last_check = None

    def capture_if_mcp_available(self, output: str, context: Optional[Dict] = None) -> bool:
        """
        Attempt MCP Keeper capture, always fall back to auto-capture
        This ensures zero disruption to existing functionality
        """
        mcp_success = False

        # Try MCP Keeper first (if available)
        try:
            if self._is_mcp_keeper_available():
                mcp_success = self._capture_to_mcp_keeper(output, context)
                if mcp_success:
                    self.logger.info("✅ MCP Keeper capture successful")
        except Exception as e:
            self.logger.debug(f"MCP Keeper capture failed (graceful): {e}")

        # ALWAYS run existing auto-capture as backup/primary
        try:
            from .auto_capture import capture_if_evaluation
            auto_success = capture_if_evaluation(output, project=None)
            if auto_success:
                self.logger.debug("✅ Auto-capture backup successful")
            return mcp_success or auto_success
        except Exception as e:
            self.logger.error(f"Auto-capture fallback failed: {e}")
            return mcp_success

    def _is_mcp_keeper_available(self) -> bool:
        """Check if MCP Keeper is available and responsive"""
        # Cache check for 30 seconds to avoid repeated calls
        now = datetime.now()
        if (self._last_check and
            (now - self._last_check).seconds < 30 and
            self._mcp_available is not None):
            return self._mcp_available

        try:
            # Try to detect MCP Keeper via Claude Code MCP tools
            # Look for MCP server or memory keeper indicators
            result = subprocess.run([
                "claude", "--version"
            ], capture_output=True, text=True, timeout=5)

            # Check for MCP Keeper in Claude Code
            if result.returncode == 0:
                # Additional check for MCP Keeper specific functionality
                self._mcp_available = self._test_mcp_keeper_connection()
            else:
                self._mcp_available = False

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            self._mcp_available = False
        except Exception as e:
            self.logger.debug(f"MCP Keeper detection failed: {e}")
            self._mcp_available = False

        self._last_check = now
        return self._mcp_available

    def _test_mcp_keeper_connection(self) -> bool:
        """Test actual MCP Keeper connectivity"""
        try:
            # Try to ping MCP Keeper memory system
            # This would use actual MCP protocol when available

            # For now, detect via Claude Code environment
            # In future, this would be actual MCP Keeper API calls

            # Placeholder for MCP Keeper detection
            # When MCP Keeper is available, this would test:
            # - MCP server connection
            # - Memory keeper responsiveness
            # - Write permissions

            return False  # Currently unavailable, graceful fallback

        except Exception as e:
            self.logger.debug(f"MCP Keeper connection test failed: {e}")
            return False

    def _capture_to_mcp_keeper(self, output: str, context: Optional[Dict] = None) -> bool:
        """Capture evaluation to MCP Keeper memory system"""
        try:
            # Extract evaluation metadata
            evaluation_data = self._extract_evaluation_metadata(output)

            if not evaluation_data:
                return False

            # Prepare MCP Keeper payload
            mcp_payload = {
                "type": "evaluation_capture",
                "timestamp": datetime.now().isoformat(),
                "project": str(self.project_root.name),
                "evaluation": evaluation_data,
                "context": context or {},
                "source": "ccom_auto_capture"
            }

            # Send to MCP Keeper (when available)
            # This would use actual MCP protocol
            success = self._send_to_mcp_keeper(mcp_payload)

            if success:
                self.logger.info(f"📊 MCP Keeper captured: {evaluation_data.get('type', 'evaluation')}")
                return True

        except Exception as e:
            self.logger.debug(f"MCP Keeper capture error: {e}")

        return False

    def _extract_evaluation_metadata(self, output: str) -> Optional[Dict[str, Any]]:
        """Extract structured metadata from evaluation output"""
        # Check if this looks like an evaluation
        if not any(indicator in output.lower() for indicator in [
            "evaluation", "assessment", "analysis", "recommendation",
            "tier 1", "tier 2", "revenue potential", "ccom"
        ]):
            return None

        metadata = {
            "raw_output": output,
            "length": len(output),
            "type": "general_evaluation"
        }

        # Extract evaluation type
        if "google play" in output.lower():
            metadata["type"] = "google_play_evaluation"
        elif "apple store" in output.lower():
            metadata["type"] = "apple_store_evaluation"
        elif "security" in output.lower():
            metadata["type"] = "security_evaluation"
        elif "quality" in output.lower():
            metadata["type"] = "quality_evaluation"
        elif "monetization" in output.lower():
            metadata["type"] = "monetization_evaluation"
        elif "ccom" in output.lower() and "evaluation" in output.lower():
            # Extract CCOM evaluation type from title
            lines = output.split('\n')
            for line in lines:
                if "CCOM" in line and "EVALUATION" in line:
                    metadata["title"] = line.strip()
                    break

        # Extract key indicators
        if "tier 1" in output.lower() or "recommended" in output.lower():
            metadata["recommendation"] = "recommended"
        elif "tier 2" in output.lower() or "not recommended" in output.lower():
            metadata["recommendation"] = "not_recommended"

        # Extract revenue information
        import re
        revenue_pattern = r'\$[\d,]+(?:K|M|k|m)?(?:/month|/year)?'
        revenue_matches = re.findall(revenue_pattern, output)
        if revenue_matches:
            metadata["revenue_potential"] = revenue_matches[0]

        # Extract complexity/timeline
        timeline_patterns = [
            r'(\d+-\d+\s+weeks?)',
            r'(phase\s+\d+:\s+[^(]+\([^)]+\))',
            r'(implementation[:\s]+[^.]+)'
        ]
        for pattern in timeline_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            if matches:
                metadata["timeline"] = matches[0]
                break

        return metadata

    def _send_to_mcp_keeper(self, payload: Dict[str, Any]) -> bool:
        """Send payload to MCP Keeper (placeholder for actual implementation)"""
        try:
            # This would be the actual MCP Keeper API call
            # For now, it's a placeholder that gracefully fails

            # Future implementation would:
            # 1. Connect to MCP Keeper server
            # 2. Send structured evaluation data
            # 3. Receive confirmation
            # 4. Handle errors gracefully

            # Placeholder: Always fail gracefully for now
            return False

        except Exception as e:
            self.logger.debug(f"MCP Keeper send failed: {e}")
            return False

    def get_mcp_status(self) -> Dict[str, Any]:
        """Get current MCP Keeper status for diagnostics"""
        return {
            "available": self._is_mcp_keeper_available(),
            "enabled": self.enabled,
            "fallback_enabled": self.fallback_to_legacy,
            "last_check": self._last_check.isoformat() if self._last_check else None,
            "project_root": str(self.project_root)
        }


def get_mcp_keeper_bridge(project_root: str) -> Optional[MCPKeeperBridge]:
    """Factory function to create MCP Keeper bridge"""
    try:
        bridge = MCPKeeperBridge(project_root)
        return bridge
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to create MCP Keeper bridge: {e}")
        return None