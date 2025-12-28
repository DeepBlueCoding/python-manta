"""
Test CLI functionality with real demo file.
Uses v2 Parser API exclusively.
"""

import pytest
import subprocess
import sys
from pathlib import Path

pytestmark = pytest.mark.fast
from tests.conftest import DEMO_FILE


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
        assert "Server: Valve TI" in output

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
        script_path = str(Path(__file__).parent.parent.parent / "src" / "python_manta" / "manta_python.py")

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
