#!/usr/bin/env python3
"""
Test script for memory integration and session continuity
"""

import sys
from pathlib import Path

# Add CCOM to path
sys.path.insert(0, str(Path(__file__).parent))

from ccom.memory.advanced_memory_keeper import AdvancedMemoryKeeper
from ccom.utils import Display

def test_memory_integration():
    """Test the memory integration functionality"""
    Display.header("🧠 Testing CCOM Memory Integration")

    project_root = Path.cwd()
    memory_keeper = AdvancedMemoryKeeper(project_root)

    # Test 1: Session Intelligence
    Display.section("Test 1: Session Intelligence")
    session_intel = memory_keeper.get_session_intelligence()
    Display.info(f"Session ID: {session_intel.get('session_id', 'N/A')}")
    Display.info(f"Recent Commands: {len(session_intel.get('recent_commands', []))}")

    # Test 2: Command Memory Query
    Display.section("Test 2: Command Memory Query")
    memory_query = memory_keeper.query_command_memory("install tools", timeframe_hours=24)
    Display.info(f"Has Recent Execution: {memory_query['has_recent_execution']}")
    Display.info(f"Recent Commands: {len(memory_query['recent_commands'])}")

    for cmd in memory_query['recent_commands']:
        Display.info(f"  - {cmd['command']} (Success Rate: {cmd['success_rate']:.1%})")

    # Test 3: Simulate Tool Installation Command
    Display.section("Test 3: Simulate Tool Installation")
    memory_keeper.capture_command_execution(
        "install tools",
        {"test_run": True, "simulated": True},
        {"success": True, "tools_installed": 5, "test_simulation": True}
    )
    Display.success("Command captured in memory")

    # Test 4: Query Again
    Display.section("Test 4: Query After Simulation")
    memory_query_after = memory_keeper.query_command_memory("install tools", timeframe_hours=1)
    Display.info(f"Has Recent Execution (After): {memory_query_after['has_recent_execution']}")

    if memory_query_after['recommendations']:
        Display.section("🧠 Memory Recommendations")
        for rec in memory_query_after['recommendations']:
            Display.info(f"  {rec}")

    # Display the recent command that was captured
    for cmd in memory_query_after['recent_commands']:
        Display.info(f"  - {cmd['command']} (Success Rate: {cmd['success_rate']:.1%}, Count: {cmd['count']})")

    Display.success("✅ Memory integration test completed")

if __name__ == "__main__":
    test_memory_integration()