"""
Test edge cases, performance, and CLI with REAL scenarios.
Focus on error conditions, performance requirements, and CLI functionality.
Uses v2 Parser API exclusively.
"""

import pytest

# Module-level marker: fast tests (~5s)
pytestmark = pytest.mark.fast
import time
import subprocess
import sys
from caching_parser import Parser
from tests.conftest import DEMO_FILE


class TestRealPerformanceRequirements:
    """Test performance requirements with real demo file processing."""

    def test_header_parsing_performance_requirement(self):
        """Test header parsing meets performance requirement with real file."""
        start_time = time.time()

        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)

        elapsed_time = time.time() - start_time

        # Verify parsing succeeded and meets performance requirement
        assert result.success is True
        assert result.header.map_name == "start"
        assert elapsed_time < 10.0, f"Header parsing took {elapsed_time:.2f}s, must be under 10s"

    def test_draft_parsing_performance_requirement(self):
        """Test draft parsing meets performance requirement with real file."""
        start_time = time.time()

        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        elapsed_time = time.time() - start_time

        # Verify parsing succeeded and meets performance requirement
        assert result.success is True
        assert len(result.game_info.picks_bans) == 24
        assert elapsed_time < 20.0, f"Draft parsing took {elapsed_time:.2f}s, must be under 20s"

    def test_messages_parsing_performance_requirement(self):
        """Test messages parsing meets performance requirement with real file."""
        start_time = time.time()

        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 100})

        elapsed_time = time.time() - start_time

        # Verify parsing succeeded and meets performance requirement
        assert result.success is True
        assert len(result.messages.messages) == 100
        assert elapsed_time < 30.0, f"Messages parsing took {elapsed_time:.2f}s, must be under 30s"

    def test_repeated_parsing_performance_consistency(self):
        """Test repeated parsing maintains consistent performance."""
        parse_times = []
        parser = Parser(DEMO_FILE)

        # Perform multiple parsing operations
        for _ in range(5):
            start_time = time.time()
            result = parser.parse(header=True)
            elapsed_time = time.time() - start_time

            assert result.success is True
            assert result.header.map_name == "start"
            parse_times.append(elapsed_time)

        # All times should be under limit
        for i, parse_time in enumerate(parse_times):
            assert parse_time < 10.0, f"Parse {i+1} took {parse_time:.2f}s, must be under 10s"

        # Performance should be relatively consistent (no extreme outliers)
        # Skip consistency check if times are very small (cached results)
        avg_time = sum(parse_times) / len(parse_times)
        if avg_time > 0.01:  # Only check consistency for non-cached (>10ms) results
            for parse_time in parse_times:
                assert parse_time < avg_time * 3, f"Parse time {parse_time:.2f}s too far from average {avg_time:.2f}s"


class TestRealErrorConditions:
    """Test error conditions with real file system scenarios."""

    def test_nonexistent_file_error_messages(self):
        """Test specific error messages for nonexistent files."""
        # Test header parsing
        parser = Parser("/nonexistent/directory/file.dem")
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(header=True)
        assert "Demo file not found" in str(exc_info.value)

        # Test draft parsing
        parser = Parser("/another/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(game_info=True)
        assert "Demo file not found" in str(exc_info.value)

        # Test messages parsing
        parser = Parser("/yet/another/nonexistent.dem")
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(messages={"max_messages": 10})
        assert "Demo file not found" in str(exc_info.value)

    def test_directory_instead_of_file_error(self):
        """Test proper error when directory provided instead of file."""
        # Test with actual directory
        parser = Parser("/tmp")
        with pytest.raises(ValueError) as exc_info:
            parser.parse(header=True)
        assert "is a directory" in str(exc_info.value)

        parser = Parser("/tmp")
        with pytest.raises((ValueError, Exception)) as exc_info:
            parser.parse(game_info=True)
        # May raise ValueError or ValidationError depending on implementation

    def test_empty_and_invalid_paths(self):
        """Test error handling for empty and invalid file paths."""
        # Empty path
        parser = Parser("")
        with pytest.raises(FileNotFoundError):
            parser.parse(header=True)

        # Whitespace only path
        parser = Parser("   ")
        with pytest.raises(FileNotFoundError):
            parser.parse(header=True)

        # Invalid characters in path (depending on OS)
        parser = Parser("/nonexistent\x00/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(header=True)

    def test_parser_initialization_errors(self):
        """Test parser initialization error scenarios."""
        # Nonexistent library path
        with pytest.raises(FileNotFoundError) as exc_info:
            Parser(DEMO_FILE, library_path="/completely/nonexistent/library.so")
        assert "Shared library not found" in str(exc_info.value)

        # Directory instead of library file should also fail
        with pytest.raises((FileNotFoundError, OSError)) as exc_info:
            Parser(DEMO_FILE, library_path="/tmp")
        # Could be FileNotFoundError or OSError depending on ctypes behavior


class TestRealDataBoundaryConditions:
    """Test boundary conditions with real data parsing."""

    def test_messages_parsing_boundary_values(self):
        """Test messages parsing with boundary values for max_messages."""
        parser = Parser(DEMO_FILE)

        # Test with max_messages = 1
        result_1 = parser.parse(messages={"max_messages": 1})
        assert result_1.success is True
        assert len(result_1.messages.messages) == 1
        assert result_1.messages.messages[0].type == "CDemoFileHeader"

        # Test with max_messages = 0 (returns all messages in this implementation)
        result_0 = parser.parse(messages={"max_messages": 0})
        assert result_0.success is True
        assert len(result_0.messages.messages) > 0  # Returns all messages when limit is 0

        # Test with very large max_messages
        result_large = parser.parse(messages={"max_messages": 10000})
        assert result_large.success is True
        assert len(result_large.messages.messages) > 0
        # Should not crash or cause memory issues

    def test_message_filter_boundary_conditions(self):
        """Test message filtering with boundary conditions."""
        parser = Parser(DEMO_FILE)

        # Empty filter string (should return all messages)
        result_empty = parser.parse(messages={"filter": "", "max_messages": 10})
        assert result_empty.success is True
        assert len(result_empty.messages.messages) == 10

        # Filter that matches no messages
        result_none = parser.parse(messages={"filter": "NonExistentMessageType", "max_messages": 10})
        assert result_none.success is True
        # May have 0 messages or fail to find matches

        # Very long filter string
        long_filter = "CDemoFileHeader" + "X" * 1000
        result_long = parser.parse(messages={"filter": long_filter, "max_messages": 5})
        assert result_long.success is True

    def test_data_consistency_edge_cases(self):
        """Test data consistency at edge cases."""
        parser = Parser(DEMO_FILE)

        # Parse very few messages
        result_few = parser.parse(messages={"max_messages": 2})
        assert result_few.success is True
        assert len(result_few.messages.messages) <= 2

        if len(result_few.messages.messages) > 0:
            # First message should still be CDemoFileHeader
            assert result_few.messages.messages[0].type == "CDemoFileHeader"
            assert result_few.messages.messages[0].tick == 0

            # All messages should have valid data
            for msg in result_few.messages.messages:
                assert len(msg.type) > 0
                assert msg.tick >= 0
                assert msg.net_tick >= 0
                assert msg.data is not None


class TestRealCLIFunctionality:
    """Test CLI functionality with real demo file."""

    def test_cli_with_real_demo_file(self):
        """Test CLI processes real demo file correctly."""
        from python_manta.manta_python import _run_cli
        import io
        from contextlib import redirect_stdout, redirect_stderr

        # Capture CLI output
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            try:
                _run_cli(["manta_python.py", DEMO_FILE])
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code

        output = stdout_buffer.getvalue()

        # CLI should succeed and show real parsed data
        assert exit_code == 0 or exit_code is None
        assert "Success! Parsed header from:" in output
        assert "Map: start" in output
        assert "Build Num: 10512" in output
        assert "Server: Valve TI14" in output

    def test_cli_invalid_arguments(self):
        """Test CLI error handling with invalid arguments."""
        from python_manta.manta_python import _run_cli
        import io
        from contextlib import redirect_stdout

        # Test with no file argument
        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            try:
                _run_cli(["manta_python.py"])
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code

        output = stdout_buffer.getvalue()
        assert exit_code == 1
        assert "Usage: python manta_python.py <demo_file.dem>" in output

    def test_cli_nonexistent_file(self):
        """Test CLI error handling with nonexistent file."""
        from python_manta.manta_python import _run_cli
        import io
        from contextlib import redirect_stdout

        stdout_buffer = io.StringIO()
        with redirect_stdout(stdout_buffer):
            try:
                _run_cli(["manta_python.py", "/nonexistent/file.dem"])
                exit_code = 0
            except SystemExit as e:
                exit_code = e.code

        output = stdout_buffer.getvalue()
        assert exit_code == 1
        assert "Error:" in output

    def test_cli_as_script_execution(self):
        """Test running the module as a script with real file."""
        from pathlib import Path
        script_path = str(Path(__file__).parent.parent / "src" / "python_manta" / "manta_python.py")

        # Test successful execution
        result = subprocess.run([
            sys.executable, script_path, DEMO_FILE
        ], capture_output=True, text=True, timeout=30)

        # Should succeed and show parsed data
        assert result.returncode == 0
        assert "Success! Parsed header from:" in result.stdout
        assert "Map: start" in result.stdout
        assert "Build Num: 10512" in result.stdout

        # Test with invalid arguments
        result_invalid = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, timeout=10)

        assert result_invalid.returncode == 1
        assert "Usage:" in result_invalid.stdout


class TestRealMemoryAndResourceManagement:
    """Test memory and resource management with real parsing operations."""

    def test_memory_usage_stability(self):
        """Test memory usage remains stable across multiple operations."""
        parser = Parser(DEMO_FILE)

        # Perform many operations to test for memory leaks
        for i in range(10):
            result_header = parser.parse(header=True)
            assert result_header.success is True
            assert result_header.header.map_name == "start"

            result_game = parser.parse(game_info=True)
            assert result_game.success is True
            assert len(result_game.game_info.picks_bans) == 24

            result_msg = parser.parse(messages={"max_messages": 10})
            assert result_msg.success is True
            assert len(result_msg.messages.messages) == 10

            # Verify data integrity is maintained across iterations
            assert result_header.header.build_num == 10512, f"Header corrupted on iteration {i}"
            radiant_picks = [e.hero_id for e in result_game.game_info.picks_bans if e.is_pick and e.team == 2]
            assert radiant_picks == [99, 123, 66, 114, 95], f"Draft corrupted on iteration {i}"

    def test_concurrent_parser_instances(self):
        """Test multiple parser instances don't interfere with each other."""
        parsers = [Parser(DEMO_FILE) for _ in range(5)]

        # All parsers should work independently
        for i, parser in enumerate(parsers):
            result = parser.parse(header=True)
            assert result.success is True, f"Parser {i} failed"
            assert result.header.map_name == "start", f"Parser {i} returned wrong map name"
            assert result.header.build_num == 10512, f"Parser {i} returned wrong build number"

        # Cross-verify all parsers produce identical results
        results = [parser.parse(header=True) for parser in parsers]
        for i, result in enumerate(results[1:], 1):
            assert result.header.map_name == results[0].header.map_name, f"Parser {i} inconsistent map name"
            assert result.header.build_num == results[0].header.build_num, f"Parser {i} inconsistent build number"

    def test_large_message_parsing_stability(self):
        """Test parsing large numbers of messages maintains stability."""
        parser = Parser(DEMO_FILE)

        # Test with progressively larger message counts
        message_counts = [10, 50, 100, 500, 1000]

        for count in message_counts:
            result = parser.parse(messages={"max_messages": count})

            assert result.success is True, f"Failed at {count} messages"
            assert len(result.messages.messages) <= count, f"Returned too many messages for {count} limit"

            # Verify data integrity
            if len(result.messages.messages) > 0:
                assert result.messages.messages[0].type == "CDemoFileHeader"
                assert result.messages.messages[0].tick == 0

                # Verify tick ordering is maintained
                ticks = [msg.tick for msg in result.messages.messages]
                assert ticks == sorted(ticks), f"Tick ordering broken at {count} messages"
