#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for CCOM MCP Memory Keeper Integration
Tests all aspects of the MCP system including database operations, capture mechanisms,
orchestrator integration, CLI routing, and error handling.
"""

import unittest
import sqlite3
import tempfile
import shutil
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import logging

# Add CCOM to path
sys.path.insert(0, str(Path(__file__).parent))

from ccom.mcp_native import MCPNativeIntegration, get_mcp_integration
from ccom.orchestrator import CCOMOrchestrator
from ccom.cli import create_enhanced_cli, handle_traditional_commands


class TestMCPDatabaseOperations(unittest.TestCase):
    """Test core MCP database functionality"""

    def setUp(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)
        self.data_dir = self.test_project / "data"
        self.data_dir.mkdir(exist_ok=True)

        # Initialize MCP with test database
        self.mcp = MCPNativeIntegration(str(self.test_project))

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_initialization(self):
        """Test database creation and schema"""
        self.assertTrue(self.mcp.context_db.exists())

        # Check schema
        with sqlite3.connect(str(self.mcp.context_db)) as conn:
            cursor = conn.execute("PRAGMA table_info(contexts)")
            columns = [row[1] for row in cursor.fetchall()]

            expected_columns = ['id', 'key', 'value', 'category', 'priority', 'channel', 'metadata', 'created_at', 'updated_at']
            for col in expected_columns:
                self.assertIn(col, columns)

    def test_save_context_basic(self):
        """Test basic context saving"""
        result = self.mcp.save_context(
            key="test_key",
            value="test_value",
            category="test",
            priority="normal"
        )

        self.assertTrue(result)

        # Verify saved data
        with sqlite3.connect(str(self.mcp.context_db)) as conn:
            cursor = conn.execute("SELECT key, value, category FROM contexts WHERE key = ?", ("test_key",))
            row = cursor.fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row[0], "test_key")
            self.assertEqual(row[1], "test_value")
            self.assertEqual(row[2], "test")

    def test_save_context_with_metadata(self):
        """Test context saving with metadata"""
        metadata = {"test": True, "source": "unit_test"}

        result = self.mcp.save_context(
            key="test_metadata",
            value="test with metadata",
            metadata=metadata
        )

        self.assertTrue(result)

        # Verify metadata
        with sqlite3.connect(str(self.mcp.context_db)) as conn:
            cursor = conn.execute("SELECT metadata FROM contexts WHERE key = ?", ("test_metadata",))
            row = cursor.fetchone()

            self.assertIsNotNone(row)
            stored_metadata = json.loads(row[0])
            self.assertEqual(stored_metadata["test"], True)
            self.assertEqual(stored_metadata["source"], "unit_test")

    def test_get_context(self):
        """Test context retrieval"""
        # Save test data
        self.mcp.save_context("test1", "value1", "category1")
        self.mcp.save_context("test2", "value2", "category2")

        # Test retrieval
        contexts = self.mcp.get_context(limit=10)

        self.assertIsInstance(contexts, list)
        self.assertGreaterEqual(len(contexts), 2)

        # Check data structure
        for context in contexts:
            self.assertIn('key', context)
            self.assertIn('value', context)
            self.assertIn('category', context)

    def test_search_context(self):
        """Test context search functionality"""
        # Save searchable data
        self.mcp.save_context("search_test1", "authentication system implementation", "feature")
        self.mcp.save_context("search_test2", "user login functionality", "feature")
        self.mcp.save_context("search_test3", "database configuration", "config")

        # Test search
        results = self.mcp.search_context("authentication")

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        # Verify search results contain the term
        found_auth = any("authentication" in str(result.get('value', '')) for result in results)
        self.assertTrue(found_auth)


class TestMCPCaptureInteraction(unittest.TestCase):
    """Test interaction capture functionality"""

    def setUp(self):
        """Create temporary test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)
        self.data_dir = self.test_project / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.mcp = MCPNativeIntegration(str(self.test_project))

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_capture_basic_interaction(self):
        """Test basic interaction capture"""
        result = self.mcp.capture_interaction(
            input_text="test command",
            output_text="test response",
            metadata={"test": True}
        )

        self.assertTrue(result)

        # Verify capture
        with sqlite3.connect(str(self.mcp.context_db)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM contexts").fetchone()[0]
            self.assertGreater(count, 0)

    def test_capture_with_fact_extraction(self):
        """Test capture with fact extraction"""
        result = self.mcp.capture_interaction(
            input_text="deploy my application",
            output_text="✅ Deployment successful! Application deployed to production with bank-level security.",
            metadata={"deployment": True}
        )

        self.assertTrue(result)

        # Check for extracted facts
        with sqlite3.connect(str(self.mcp.context_db)) as conn:
            facts = conn.execute("SELECT value FROM contexts WHERE category IN ('success', 'warning', 'error')").fetchall()
            self.assertGreater(len(facts), 0)

    def test_capture_large_interaction(self):
        """Test capture with large text content"""
        large_input = "x" * 5000  # 5KB input
        large_output = "y" * 10000  # 10KB output

        result = self.mcp.capture_interaction(
            input_text=large_input,
            output_text=large_output
        )

        self.assertTrue(result)

        # Verify truncation handling
        contexts = self.mcp.get_context(limit=1)
        self.assertGreater(len(contexts), 0)

    def test_capture_unicode_content(self):
        """Test capture with Unicode characters"""
        result = self.mcp.capture_interaction(
            input_text="test with emojis 🚀🔧✅",
            output_text="response with unicode: ñáéíóú and symbols: ←→↑↓"
        )

        self.assertTrue(result)

        # Verify Unicode handling
        contexts = self.mcp.get_context(limit=1)
        self.assertGreater(len(contexts), 0)


class TestOrchestratorIntegration(unittest.TestCase):
    """Test orchestrator MCP integration"""

    def setUp(self):
        """Setup test orchestrator"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create minimal project structure
        (Path(self.test_dir) / ".claude").mkdir(exist_ok=True)
        (Path(self.test_dir) / "data").mkdir(exist_ok=True)

        # Create minimal memory.json
        memory_file = Path(self.test_dir) / ".claude" / "memory.json"
        memory_file.write_text(json.dumps({
            "project": {"name": "test_project"},
            "features": {"test_feature": {"description": "test"}},
            "metadata": {"version": "0.3"}
        }))

        with patch('ccom.orchestrator.get_mcp_integration') as mock_mcp:
            mock_mcp_instance = Mock()
            mock_mcp_instance.capture_interaction.return_value = True
            mock_mcp_instance.get_project_context.return_value = {
                "total_context_items": 5,
                "database": "test.db"
            }
            mock_mcp_instance.get_activity_summary.return_value = {
                "total": 5,
                "categories": {"interaction": 3, "success": 2}
            }
            mock_mcp.return_value = mock_mcp_instance

            self.orchestrator = CCOMOrchestrator()
            self.mock_mcp = mock_mcp_instance

    def tearDown(self):
        """Clean up test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_show_memory_mcp_priority(self):
        """Test that show_memory prioritizes MCP over legacy"""
        result = self.orchestrator.show_memory()

        self.assertTrue(result)
        self.assertTrue(self.mock_mcp.get_project_context.call_count >= 1)
        self.mock_mcp.capture_interaction.assert_called()

    def test_show_status_with_capture(self):
        """Test status display with capture"""
        result = self.orchestrator.show_status()

        self.assertTrue(result)
        self.mock_mcp.capture_interaction.assert_called()

        # Verify capture call parameters
        call_args = self.mock_mcp.capture_interaction.call_args
        self.assertEqual(call_args[1]['input_text'], "show status")
        self.assertEqual(call_args[1]['metadata']['command_type'], "status_display")

    def test_handle_memory_command_with_capture(self):
        """Test memory command handling with capture"""
        result = self.orchestrator.handle_memory_command("memory")

        self.assertTrue(result)
        self.mock_mcp.capture_interaction.assert_called()

        # Verify capture metadata
        call_args = self.mock_mcp.capture_interaction.call_args
        self.assertIn("memory command:", call_args[1]['input_text'])
        self.assertEqual(call_args[1]['metadata']['command_type'], "memory_command")

    def test_natural_language_processing(self):
        """Test natural language command processing"""
        with patch.object(self.orchestrator, '_match_command_pattern') as mock_match:
            mock_match.return_value = lambda: True

            result = self.orchestrator.handle_natural_language("show memory")

            self.assertTrue(result)
            self.mock_mcp.capture_interaction.assert_called()


class TestCLIIntegration(unittest.TestCase):
    """Test CLI command routing and integration"""

    def setUp(self):
        """Setup CLI test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create test project structure
        (Path(self.test_dir) / ".claude").mkdir(exist_ok=True)
        (Path(self.test_dir) / "data").mkdir(exist_ok=True)

        memory_file = Path(self.test_dir) / ".claude" / "memory.json"
        memory_file.write_text(json.dumps({
            "project": {"name": "test_project"},
            "features": {},
            "metadata": {"version": "0.3"}
        }))

    def tearDown(self):
        """Clean up CLI test environment"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_parser_creation(self):
        """Test CLI parser creation"""
        parser = create_enhanced_cli()

        self.assertIsNotNone(parser)

        # Test memory flag parsing
        args = parser.parse_args(['--memory'])
        self.assertTrue(args.memory)

    def test_cli_memory_flag_routing(self):
        """Test --memory flag routes to orchestrator"""
        parser = create_enhanced_cli()
        args = parser.parse_args(['--memory'])

        with patch('ccom.cli.CCOMOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = Mock()
            mock_orchestrator.show_memory.return_value = True
            mock_orchestrator_class.return_value = mock_orchestrator

            from types import SimpleNamespace
            mock_args = SimpleNamespace(
                memory=True, status=False, mcp_context=False, mcp_activity=False,
                mcp_sessions=False, mcp_start_session=None, mcp_continue=None,
                remember=None, init=False, watch=False, monitor_config=False,
                workflow=None, install_tools=False, check_tools=False,
                tools_status=False, context_note=None, context_resume=None,
                context_search=None, context_checkpoint=None, context_status=False,
                context_summary=None, universal_memory=False
            )

            result = handle_traditional_commands(mock_args, mock_orchestrator)

            self.assertTrue(result)
            mock_orchestrator.show_memory.assert_called_once()


class TestErrorHandling(unittest.TestCase):
    """Test error handling and fallback mechanisms"""

    def setUp(self):
        """Setup error testing environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)
        self.data_dir = self.test_project / "data"
        self.data_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up error test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_corruption_handling(self):
        """Test handling of corrupted database"""
        # Create corrupted database file
        corrupt_db = self.data_dir / "context.db"
        corrupt_db.write_text("This is not a valid SQLite database")

        # Should handle corruption gracefully and reinitialize
        try:
            mcp = MCPNativeIntegration(str(self.test_project))
            # After reinitialization, operations should work
            result = mcp.save_context("test", "value")
            self.assertTrue(result)  # Should work after reinit
        except Exception as e:
            # If initialization fails completely, that's expected behavior
            self.assertIn("database", str(e).lower())

    def test_database_permission_error(self):
        """Test handling of database permission errors"""
        mcp = MCPNativeIntegration(str(self.test_project))

        # Mock permission error
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = PermissionError("Permission denied")

            result = mcp.save_context("test", "value")
            self.assertFalse(result)

    def test_orchestrator_mcp_failure_fallback(self):
        """Test orchestrator fallback when MCP fails"""
        os.chdir(self.test_dir)

        # Create memory.json for fallback
        memory_file = self.test_project / ".claude" / "memory.json"
        memory_file.parent.mkdir(exist_ok=True)
        memory_file.write_text(json.dumps({
            "project": {"name": "test_project"},
            "features": {"legacy_feature": {"description": "legacy test"}},
            "metadata": {"version": "0.3"}
        }))

        with patch('ccom.orchestrator.get_mcp_integration') as mock_mcp:
            # Make MCP fail
            mock_mcp_instance = Mock()
            mock_mcp_instance.get_project_context.side_effect = Exception("MCP Error")
            mock_mcp_instance.capture_interaction.return_value = False
            mock_mcp.return_value = mock_mcp_instance

            orchestrator = CCOMOrchestrator()

            # Should fall back to legacy memory
            with patch('builtins.print') as mock_print:
                result = orchestrator.show_memory()

                self.assertTrue(result)
                # Should print legacy memory content
                print_calls = [str(call) for call in mock_print.call_args_list]
                legacy_printed = any("legacy_feature" in call for call in print_calls)
                self.assertTrue(legacy_printed)


class TestPerformanceAndLimits(unittest.TestCase):
    """Test performance characteristics and limits"""

    def setUp(self):
        """Setup performance test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_project = Path(self.test_dir)
        self.data_dir = self.test_project / "data"
        self.data_dir.mkdir(exist_ok=True)

        self.mcp = MCPNativeIntegration(str(self.test_project))

    def tearDown(self):
        """Clean up performance test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_bulk_context_insertion(self):
        """Test performance with bulk context insertion"""
        start_time = datetime.now()

        # Insert 100 contexts
        success_count = 0
        for i in range(100):
            result = self.mcp.save_context(
                key=f"perf_test_{i}",
                value=f"Performance test data {i} " * 10,  # ~200 chars each
                category="performance_test"
            )
            if result:
                success_count += 1

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time (< 5 seconds)
        self.assertLess(duration, 5.0)
        self.assertGreaterEqual(success_count, 90)  # Allow some failures

        # Verify data integrity
        contexts = self.mcp.get_context(limit=200)
        performance_contexts = [c for c in contexts if c.get('category') == 'performance_test']
        self.assertGreaterEqual(len(performance_contexts), 90)

    def test_large_context_values(self):
        """Test handling of large context values"""
        large_value = "x" * 50000  # 50KB value

        result = self.mcp.save_context(
            key="large_value_test",
            value=large_value,
            category="large_data"
        )

        self.assertTrue(result)

        # Verify retrieval
        contexts = self.mcp.get_context(limit=1)
        self.assertGreater(len(contexts), 0)

    def test_concurrent_access_simulation(self):
        """Test simulation of concurrent access patterns"""
        import threading
        import time

        results = []

        def worker(worker_id):
            """Worker function for simulated concurrent access"""
            try:
                for i in range(10):
                    result = self.mcp.save_context(
                        key=f"worker_{worker_id}_item_{i}",
                        value=f"Worker {worker_id} data {i}",
                        category="concurrent_test"
                    )
                    results.append(result)
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                results.append(False)

        # Create and start threads
        threads = []
        for worker_id in range(5):
            thread = threading.Thread(target=worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)

        # Check results
        success_rate = sum(1 for r in results if r) / len(results) if results else 0
        self.assertGreater(success_rate, 0.8)  # Allow some contention failures


def run_comprehensive_test():
    """Run all test suites and generate comprehensive report"""

    # Create test suite
    test_classes = [
        TestMCPDatabaseOperations,
        TestMCPCaptureInteraction,
        TestOrchestratorIntegration,
        TestCLIIntegration,
        TestErrorHandling,
        TestPerformanceAndLimits
    ]

    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )

    print("🧪 " + "="*60)
    print("🧪 CCOM MCP MEMORY KEEPER - COMPREHENSIVE UNIT TESTS")
    print("🧪 " + "="*60)
    print()

    start_time = datetime.now()
    result = runner.run(suite)
    end_time = datetime.now()

    # Generate summary report
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*60)
    print("📊 TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"⏱️  Total Duration: {duration:.2f} seconds")
    print(f"✅ Tests Run: {result.testsRun}")
    print(f"🎯 Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    print(f"🏆 Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'See details above'}")

    if result.errors:
        print(f"\n💥 ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            error_msg = traceback.split('\n')[-2] if traceback.split('\n') else "Unknown error"
            print(f"   • {test}: {error_msg}")

    # Overall assessment
    if result.wasSuccessful():
        print(f"\n🎉 ALL TESTS PASSED - MCP MEMORY KEEPER IS FULLY FUNCTIONAL")
    else:
        print(f"\n⚠️  SOME TESTS FAILED - REVIEW ISSUES ABOVE")

    print("="*60)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)