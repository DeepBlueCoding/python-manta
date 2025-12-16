"""
Test Parser error handling with real error scenarios.
Uses v2 Parser API exclusively.
"""

import pytest

pytestmark = pytest.mark.fast
from caching_parser import Parser
from tests.conftest import DEMO_FILE


class TestParserErrorHandling:
    """Test Parser error handling with real error scenarios."""

    def test_missing_library_file_error(self):
        """Test Parser raises proper error for missing library."""
        with pytest.raises(FileNotFoundError, match="Shared library not found"):
            Parser(DEMO_FILE, library_path="/nonexistent/path/libmanta_wrapper.so")

    def test_nonexistent_demo_file_error(self):
        """Test Parser raises proper error for nonexistent demo file."""
        parser = Parser("/nonexistent/file.dem")

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(header=True)

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(game_info=True)

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(messages=True)

    def test_invalid_file_type_error(self):
        """Test Parser handles invalid file types properly."""
        parser = Parser("/tmp")

        # Directory instead of file should fail with ValueError
        with pytest.raises(ValueError) as exc_info:
            parser.parse(header=True)
        assert "is a directory" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            parser.parse(game_info=True)
        assert "is a directory" in str(exc_info.value)

    def test_empty_parse_still_succeeds(self):
        """Test parsing with no collectors still succeeds."""
        parser = Parser(DEMO_FILE)
        result = parser.parse()

        assert result.success is True
        # All collectors should be None
        assert result.header is None
        assert result.game_info is None


class TestRealErrorConditions:
    """Test error conditions with real file system scenarios."""

    def test_nonexistent_file_error_messages(self):
        """Test specific error messages for nonexistent files."""
        # Test header parsing
        parser = Parser("/nonexistent/directory/file.dem")
        with pytest.raises(FileNotFoundError) as exc_info:
            parser.parse(header=True)
        assert "Demo file not found" in str(exc_info.value)

        # Test game_info parsing
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


class TestAdvancedFeaturesErrorHandling:
    """Test error handling for advanced features."""

    def test_game_events_nonexistent_file(self):
        """Test game events with nonexistent file."""
        parser = Parser("/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(game_events={"max_events": 10})

    def test_modifiers_nonexistent_file(self):
        """Test modifiers with nonexistent file."""
        parser = Parser("/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(modifiers={"max_modifiers": 10})

    def test_string_tables_nonexistent_file(self):
        """Test string tables with nonexistent file."""
        parser = Parser("/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(string_tables={"max_entries": 10})

    def test_combat_log_nonexistent_file(self):
        """Test combat log with nonexistent file."""
        parser = Parser("/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(combat_log={"max_entries": 10})

    def test_parser_info_nonexistent_file(self):
        """Test parser info with nonexistent file."""
        parser = Parser("/nonexistent/file.dem")
        with pytest.raises(FileNotFoundError):
            parser.parse(parser_info=True)
