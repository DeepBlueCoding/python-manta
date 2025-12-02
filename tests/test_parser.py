"""
Test MantaParser class business logic with REAL VALUES.
Focus on parser behavior, business rules, and data consistency.
"""

import pytest
from python_manta import MantaParser, HeaderInfo, CDotaGameInfo, UniversalParseResult

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


@pytest.mark.unit
class TestMantaParserBusinessLogic:
    """Test MantaParser business logic with real demo file."""

    def test_parser_produces_consistent_header_values(self):
        """Test parser consistently produces same header values across calls."""
        parser = MantaParser()
        
        # Parse multiple times - should be identical
        result1 = parser.parse_header(DEMO_FILE)
        result2 = parser.parse_header(DEMO_FILE)
        result3 = parser.parse_header(DEMO_FILE)
        
        # All results must be identical
        assert result1.map_name == result2.map_name == result3.map_name == "start"
        assert result1.build_num == result2.build_num == result3.build_num == 10512
        assert result1.server_name == result2.server_name == result3.server_name
        assert result1.success == result2.success == result3.success == True

    def test_parser_draft_business_rules(self):
        """Test draft parsing follows Dota 2 business rules."""
        parser = MantaParser()
        result = parser.parse_game_info(DEMO_FILE)
        
        # Business rule: Must have exactly 10 picks in 5v5 game
        picks = [e for e in result.picks_bans if e.is_pick]
        assert len(picks) == 10
        
        # Business rule: Each team gets exactly 5 picks
        radiant_picks = [e for e in picks if e.team == 2]
        dire_picks = [e for e in picks if e.team == 3]
        assert len(radiant_picks) == 5
        assert len(dire_picks) == 5
        
        # Business rule: All hero IDs must be positive
        for event in result.picks_bans:
            assert event.hero_id > 0
            
        # Business rule: Team IDs must be 2 (Radiant) or 3 (Dire)
        for event in result.picks_bans:
            assert event.team in [2, 3]

    def test_parser_universal_message_ordering(self):
        """Test universal parsing maintains correct message ordering."""
        parser = MantaParser()
        result = parser.parse_universal(DEMO_FILE, max_messages=20)
        
        # Business rule: Messages must be ordered by tick
        ticks = [msg.tick for msg in result.messages]
        assert ticks == sorted(ticks), "Messages must be in tick order"
        
        # Business rule: First message should always be CDemoFileHeader
        assert result.messages[0].type == "CDemoFileHeader"
        assert result.messages[0].tick == 0
        
        # Business rule: All net_ticks must be non-negative
        for msg in result.messages:
            assert msg.net_tick >= 0

    def test_multiple_parser_instances_independence(self):
        """Test multiple parser instances work independently with same results."""
        parser1 = MantaParser()
        parser2 = MantaParser()
        parser3 = MantaParser()
        
        # All parsers should produce identical results for same file
        header1 = parser1.parse_header(DEMO_FILE)
        header2 = parser2.parse_header(DEMO_FILE)
        header3 = parser3.parse_header(DEMO_FILE)
        
        assert header1.map_name == header2.map_name == header3.map_name == "start"
        assert header1.build_num == header2.build_num == header3.build_num == 10512
        
        # Test with draft parsing
        game_info1 = parser1.parse_game_info(DEMO_FILE)
        game_info2 = parser2.parse_game_info(DEMO_FILE)
        
        assert len(game_info1.picks_bans) == len(game_info2.picks_bans) == 24
        
        # Pick sequences must be identical
        picks1 = [e.hero_id for e in game_info1.picks_bans if e.is_pick and e.team == 2]
        picks2 = [e.hero_id for e in game_info2.picks_bans if e.is_pick and e.team == 2]
        assert picks1 == picks2 == [99, 123, 66, 114, 95]

    def test_parser_mixed_operations_consistency(self):
        """Test parser maintains consistency across different operation types."""
        parser = MantaParser()
        
        # Parse all types on same parser instance
        header = parser.parse_header(DEMO_FILE)
        game_info = parser.parse_game_info(DEMO_FILE)
        universal = parser.parse_universal(DEMO_FILE, max_messages=5)
        
        # All operations must succeed
        assert header.success is True
        assert game_info.success is True  
        assert universal.success is True
        
        # Verify consistent data across operations
        assert header.map_name == "start"
        assert len(game_info.picks_bans) == 24
        assert len(universal.messages) == 5
        assert universal.messages[0].type == "CDemoFileHeader"


@pytest.mark.unit
class TestMantaParserDataIntegrity:
    """Test parser data integrity and validation rules."""

    def test_draft_data_relationships(self):
        """Test draft data maintains proper relationships."""
        parser = MantaParser()
        result = parser.parse_game_info(DEMO_FILE)
        
        # Data integrity: Total events = picks + bans
        picks = [e for e in result.picks_bans if e.is_pick]
        bans = [e for e in result.picks_bans if not e.is_pick]
        assert len(picks) + len(bans) == len(result.picks_bans) == 24
        
        # Data integrity: No duplicate picks within same team
        radiant_picks = [e.hero_id for e in picks if e.team == 2]
        dire_picks = [e.hero_id for e in picks if e.team == 3]
        
        assert len(radiant_picks) == len(set(radiant_picks)), "No duplicate picks in radiant"
        assert len(dire_picks) == len(set(dire_picks)), "No duplicate picks in dire"
        
        # Data integrity: No hero picked by both teams
        assert len(set(radiant_picks) & set(dire_picks)) == 0, "No hero picked by both teams"

    def test_universal_message_data_consistency(self):
        """Test universal parsing maintains data consistency."""
        parser = MantaParser()
        result = parser.parse_universal(DEMO_FILE, max_messages=15)
        
        # Data consistency: All messages have required fields
        for msg in result.messages:
            assert len(msg.type) > 0, "Message type cannot be empty"
            assert msg.tick >= 0, "Tick must be non-negative"
            assert msg.net_tick >= 0, "Net tick must be non-negative"
            assert msg.data is not None, "Message data cannot be None"
        
        # Data consistency: Message count matches actual count
        assert len(result.messages) <= 15  # Requested max
        assert result.count >= len(result.messages)  # Total should be >= returned

    def test_header_data_validation(self):
        """Test header data passes validation rules."""
        parser = MantaParser()
        result = parser.parse_header(DEMO_FILE)
        
        # Data validation: Required fields must not be empty
        assert len(result.map_name) > 0, "Map name cannot be empty"
        assert len(result.server_name) > 0, "Server name cannot be empty"
        assert len(result.client_name) > 0, "Client name cannot be empty"
        
        # Data validation: Numeric fields must be reasonable
        assert result.network_protocol > 0, "Network protocol must be positive"
        assert result.build_num > 0, "Build number must be positive"
        assert result.server_start_tick >= 0, "Start tick must be non-negative"
        
        # Data validation: Demo file stamp must be valid
        assert len(result.demo_file_stamp) > 0, "Demo file stamp cannot be empty"


@pytest.mark.unit  
class TestMantaParserLibraryIntegration:
    """Test parser integration with underlying library."""

    def test_custom_library_path_works(self):
        """Test parser works with custom library path."""
        # Use explicit library path
        lib_path = "/home/juanma/projects/equilibrium_coach/python_manta/src/python_manta/libmanta_wrapper.so"
        parser = MantaParser(lib_path)
        
        # Should produce same results as default parser
        result = parser.parse_header(DEMO_FILE)
        assert result.success is True
        assert result.map_name == "start"
        assert result.build_num == 10512

    def test_library_function_signatures(self):
        """Test parser library has expected function signatures."""
        parser = MantaParser()
        
        # Verify ctypes functions exist and are callable
        assert hasattr(parser.lib, 'ParseHeader')
        assert hasattr(parser.lib, 'ParseMatchInfo')
        assert hasattr(parser.lib, 'ParseUniversal')
        
        # Verify functions can be called and return valid results
        result = parser.parse_header(DEMO_FILE)
        assert result.success is True

    def test_memory_consistency_multiple_calls(self):
        """Test parser handles memory consistently across multiple calls."""
        parser = MantaParser()
        
        # Multiple operations should not cause memory issues
        for i in range(5):
            header = parser.parse_header(DEMO_FILE)
            assert header.map_name == "start", f"Failed on iteration {i}"
            
            game_info = parser.parse_game_info(DEMO_FILE) 
            assert len(game_info.picks_bans) == 24, f"Failed on iteration {i}"
            
            universal = parser.parse_universal(DEMO_FILE, max_messages=3)
            assert len(universal.messages) == 3, f"Failed on iteration {i}"


@pytest.mark.unit
class TestMantaParserErrorHandling:
    """Test parser error handling with real error scenarios."""

    def test_missing_library_file_error(self):
        """Test parser raises proper error for missing library."""
        with pytest.raises(FileNotFoundError, match="Shared library not found"):
            MantaParser("/nonexistent/path/libmanta_wrapper.so")

    def test_nonexistent_demo_file_error(self):
        """Test parser raises proper error for nonexistent demo file."""
        parser = MantaParser()
        
        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse_header("/nonexistent/file.dem")
            
        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse_game_info("/nonexistent/file.dem")
            
        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse_universal("/nonexistent/file.dem")

    def test_invalid_file_type_error(self):
        """Test parser handles invalid file types properly."""
        parser = MantaParser()
        
        # Directory instead of file should fail
        with pytest.raises(ValueError) as exc_info:
            parser.parse_header("/tmp")
        assert "Parsing failed" in str(exc_info.value)
        assert "is a directory" in str(exc_info.value)
            
        with pytest.raises((ValueError, Exception)) as exc_info:
            parser.parse_game_info("/tmp")
        # May raise ValueError or ValidationError depending on implementation

    def test_empty_file_path_error(self):
        """Test parser handles empty file paths properly.""" 
        parser = MantaParser()
        
        with pytest.raises(FileNotFoundError):
            parser.parse_header("")
            
        with pytest.raises(FileNotFoundError):
            parser.parse_game_info("")
            
        with pytest.raises(FileNotFoundError):
            parser.parse_universal("")