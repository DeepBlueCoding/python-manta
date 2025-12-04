"""
Test Parser class business logic with REAL VALUES.
Focus on parser behavior, business rules, and data consistency.
Uses v2 Parser API exclusively.
"""

import pytest

# Module-level marker: core functionality tests (~30s)
pytestmark = pytest.mark.core
from python_manta import Parser, HeaderInfo, GameInfo, ParseResult

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


class TestParserBusinessLogic:
    """Test Parser business logic with real demo file."""

    def test_parser_produces_consistent_header_values(self):
        """Test parser consistently produces same header values across calls."""
        parser = Parser(DEMO_FILE)

        # Parse multiple times - should be identical
        result1 = parser.parse(header=True)
        result2 = parser.parse(header=True)
        result3 = parser.parse(header=True)

        # All results must be identical
        assert result1.header.map_name == result2.header.map_name == result3.header.map_name == "start"
        assert result1.header.build_num == result2.header.build_num == result3.header.build_num == 10512
        assert result1.header.server_name == result2.header.server_name == result3.header.server_name
        assert result1.success == result2.success == result3.success == True

    def test_parser_draft_business_rules(self):
        """Test draft parsing follows Dota 2 business rules."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        # Business rule: Must have exactly 10 picks in 5v5 game
        picks = [e for e in result.game_info.picks_bans if e.is_pick]
        assert len(picks) == 10

        # Business rule: Each team gets exactly 5 picks
        radiant_picks = [e for e in picks if e.team == 2]
        dire_picks = [e for e in picks if e.team == 3]
        assert len(radiant_picks) == 5
        assert len(dire_picks) == 5

        # Business rule: All hero IDs must be positive
        for event in result.game_info.picks_bans:
            assert event.hero_id > 0

        # Business rule: Team IDs must be 2 (Radiant) or 3 (Dire)
        for event in result.game_info.picks_bans:
            assert event.team in [2, 3]

    def test_parser_messages_ordering(self):
        """Test message parsing maintains correct ordering."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 20})

        # Business rule: Messages must be ordered by tick
        ticks = [msg.tick for msg in result.messages.messages]
        assert ticks == sorted(ticks), "Messages must be in tick order"

        # Business rule: First message should always be CDemoFileHeader
        assert result.messages.messages[0].type == "CDemoFileHeader"
        assert result.messages.messages[0].tick == 0

        # Business rule: All net_ticks must be non-negative
        for msg in result.messages.messages:
            assert msg.net_tick >= 0

    def test_multiple_parser_instances_independence(self):
        """Test multiple parser instances work independently with same results."""
        parser1 = Parser(DEMO_FILE)
        parser2 = Parser(DEMO_FILE)
        parser3 = Parser(DEMO_FILE)

        # All parsers should produce identical results for same file
        result1 = parser1.parse(header=True)
        result2 = parser2.parse(header=True)
        result3 = parser3.parse(header=True)

        assert result1.header.map_name == result2.header.map_name == result3.header.map_name == "start"
        assert result1.header.build_num == result2.header.build_num == result3.header.build_num == 10512

        # Test with game_info parsing
        result1 = parser1.parse(game_info=True)
        result2 = parser2.parse(game_info=True)

        assert len(result1.game_info.picks_bans) == len(result2.game_info.picks_bans) == 24

        # Pick sequences must be identical
        picks1 = [e.hero_id for e in result1.game_info.picks_bans if e.is_pick and e.team == 2]
        picks2 = [e.hero_id for e in result2.game_info.picks_bans if e.is_pick and e.team == 2]
        assert picks1 == picks2 == [99, 123, 66, 114, 95]

    def test_parser_single_pass_all_collectors(self):
        """Test parser collects all data in single pass."""
        parser = Parser(DEMO_FILE)

        # Parse all types in single pass
        result = parser.parse(
            header=True,
            game_info=True,
            messages={"max_messages": 5},
        )

        # All collectors must succeed
        assert result.success is True
        assert result.header is not None
        assert result.game_info is not None
        assert result.messages is not None

        # Verify data from each collector
        assert result.header.map_name == "start"
        assert len(result.game_info.picks_bans) == 24
        assert len(result.messages.messages) == 5
        assert result.messages.messages[0].type == "CDemoFileHeader"


class TestParserDataIntegrity:
    """Test parser data integrity and validation rules."""

    def test_draft_data_relationships(self):
        """Test draft data maintains proper relationships."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        # Data integrity: Total events = picks + bans
        picks = [e for e in result.game_info.picks_bans if e.is_pick]
        bans = [e for e in result.game_info.picks_bans if not e.is_pick]
        assert len(picks) + len(bans) == len(result.game_info.picks_bans) == 24

        # Data integrity: No duplicate picks within same team
        radiant_picks = [e.hero_id for e in picks if e.team == 2]
        dire_picks = [e.hero_id for e in picks if e.team == 3]

        assert len(radiant_picks) == len(set(radiant_picks)), "No duplicate picks in radiant"
        assert len(dire_picks) == len(set(dire_picks)), "No duplicate picks in dire"

        # Data integrity: No hero picked by both teams
        assert len(set(radiant_picks) & set(dire_picks)) == 0, "No hero picked by both teams"

    def test_message_data_consistency(self):
        """Test message parsing maintains data consistency."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 15})

        # Data consistency: All messages have required fields
        for msg in result.messages.messages:
            assert len(msg.type) > 0, "Message type cannot be empty"
            assert msg.tick >= 0, "Tick must be non-negative"
            assert msg.net_tick >= 0, "Net tick must be non-negative"
            assert msg.data is not None, "Message data cannot be None"

        # Data consistency: Message count matches actual count
        assert len(result.messages.messages) <= 15  # Requested max

    def test_header_data_validation(self):
        """Test header data passes validation rules."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)

        # Data validation: Required fields must not be empty
        assert len(result.header.map_name) > 0, "Map name cannot be empty"
        assert len(result.header.server_name) > 0, "Server name cannot be empty"
        assert len(result.header.client_name) > 0, "Client name cannot be empty"

        # Data validation: Numeric fields must be reasonable
        assert result.header.network_protocol > 0, "Network protocol must be positive"
        assert result.header.build_num > 0, "Build number must be positive"
        assert result.header.server_start_tick >= 0, "Start tick must be non-negative"

        # Data validation: Demo file stamp must be valid
        assert len(result.header.demo_file_stamp) > 0, "Demo file stamp cannot be empty"


class TestParserLibraryIntegration:
    """Test parser integration with underlying library."""

    def test_custom_library_path_works(self):
        """Test parser works with custom library path."""
        # Use explicit library path
        lib_path = "/home/juanma/projects/equilibrium_coach/python_manta/src/python_manta/libmanta_wrapper.so"
        parser = Parser(DEMO_FILE, library_path=lib_path)

        # Should produce same results as default parser
        result = parser.parse(header=True)
        assert result.success is True
        assert result.header.map_name == "start"
        assert result.header.build_num == 10512

    def test_memory_consistency_multiple_calls(self):
        """Test parser handles memory consistently across multiple calls."""
        parser = Parser(DEMO_FILE)

        # Multiple operations should not cause memory issues
        for i in range(5):
            result = parser.parse(header=True)
            assert result.header.map_name == "start", f"Failed on iteration {i}"

            result = parser.parse(game_info=True)
            assert len(result.game_info.picks_bans) == 24, f"Failed on iteration {i}"

            result = parser.parse(messages={"max_messages": 3})
            assert len(result.messages.messages) == 3, f"Failed on iteration {i}"


class TestParserErrorHandling:
    """Test parser error handling with real error scenarios."""

    def test_missing_library_file_error(self):
        """Test parser raises proper error for missing library."""
        with pytest.raises(FileNotFoundError, match="Shared library not found"):
            Parser(DEMO_FILE, library_path="/nonexistent/path/libmanta_wrapper.so")

    def test_nonexistent_demo_file_error(self):
        """Test parser raises proper error for nonexistent demo file."""
        parser = Parser("/nonexistent/file.dem")

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(header=True)

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(game_info=True)

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(messages=True)

    def test_invalid_file_type_error(self):
        """Test parser handles invalid file types properly."""
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
