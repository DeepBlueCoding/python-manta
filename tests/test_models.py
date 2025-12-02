"""
Test models with REAL VALUES from actual demo file.
Golden Master approach: Test against verified expected values.
"""

import pytest
from python_manta import (
    MantaParser,
    HeaderInfo,
    CHeroSelectEvent,
    CPlayerInfo,
    CDotaGameInfo,
    MessageEvent,
    UniversalParseResult,
)

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


@pytest.fixture
def parser():
    return MantaParser()


@pytest.mark.unit
class TestHeaderInfoRealValues:
    """Test HeaderInfo contains EXACT values from real demo file."""

    def test_header_exact_values(self, parser):
        """Test header parsing produces exact expected values from real file."""
        result = parser.parse_header(DEMO_FILE)
        
        # EXACT values from the real demo file (verified manually)
        assert result.success is True
        assert result.map_name == "start"
        assert result.server_name == "Valve TI14 Server (srcds227-fra2.Hamburg.4)"
        assert result.client_name == "SourceTV Demo"
        assert result.game_directory == "/opt/srcds/dota/dota_v6536/dota"
        assert result.network_protocol == 48
        assert result.demo_file_stamp == "PBDEMS2\x00"
        assert result.build_num == 10512
        assert result.game == ""  # This specific demo file has empty game field
        assert result.server_start_tick == 381
        assert result.error is None

    def test_header_serialization_roundtrip(self, parser):
        """Test HeaderInfo JSON serialization preserves exact values."""
        original = parser.parse_header(DEMO_FILE)
        
        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = HeaderInfo.model_validate_json(json_str)
        
        # Must be identical to original
        assert restored == original
        assert restored.map_name == "start"
        assert restored.build_num == 10512


@pytest.mark.unit
class TestCHeroSelectEventRealValues:
    """Test CHeroSelectEvent with EXACT values from real draft."""

    def test_draft_exact_structure(self, parser):
        """Test draft contains exact pick/ban structure from real game."""
        game_info = parser.parse_game_info(DEMO_FILE)

        # EXACT values from real demo file
        assert game_info.success is True
        assert len(game_info.picks_bans) == 24  # Exact number of events
        assert game_info.error is None

        # Test first 5 events exact sequence
        first_5_events = [(e.is_pick, e.team, e.hero_id) for e in game_info.picks_bans[:5]]
        expected_first_5 = [(False, 3, 53), (False, 2, 74), (False, 2, 38), (False, 3, 11), (False, 2, 89)]
        assert first_5_events == expected_first_5

    def test_picks_exact_values(self, parser):
        """Test picks contain exact hero IDs from real game."""
        game_info = parser.parse_game_info(DEMO_FILE)

        picks = [e for e in game_info.picks_bans if e.is_pick]
        assert len(picks) == 10  # Standard 5v5 picks

        # Exact pick sequences by team
        radiant_picks = [e.hero_id for e in picks if e.team == 2]
        dire_picks = [e.hero_id for e in picks if e.team == 3]

        assert radiant_picks == [99, 123, 66, 114, 95]  # Real radiant picks
        assert dire_picks == [77, 45, 27, 17, 41]       # Real dire picks

    def test_bans_exact_values(self, parser):
        """Test bans contain exact hero IDs from real game."""
        game_info = parser.parse_game_info(DEMO_FILE)

        bans = [e for e in game_info.picks_bans if not e.is_pick]
        assert len(bans) == 14  # Exact number of bans in this game

        # Exact ban sequences by team
        radiant_bans = [e.hero_id for e in bans if e.team == 2]
        dire_bans = [e.hero_id for e in bans if e.team == 3]

        assert radiant_bans == [74, 38, 89, 136, 102, 70, 8]  # Real radiant bans
        assert dire_bans == [53, 11, 7, 16, 110, 13, 1]       # Real dire bans


@pytest.mark.unit
class TestCDotaGameInfoRealValues:
    """Test CDotaGameInfo with EXACT values from real demo file."""

    def test_game_info_exact_structure(self, parser):
        """Test game info contains exact structure from real file."""
        result = parser.parse_game_info(DEMO_FILE)

        assert result.success is True
        assert len(result.picks_bans) == 24
        assert result.error is None

        # Test team distribution is correct
        team_2_events = [e for e in result.picks_bans if e.team == 2]  # Radiant
        team_3_events = [e for e in result.picks_bans if e.team == 3]  # Dire

        assert len(team_2_events) == 12  # Radiant events (5 picks + 7 bans)
        assert len(team_3_events) == 12  # Dire events (5 picks + 7 bans)

    def test_game_info_serialization_roundtrip(self, parser):
        """Test CDotaGameInfo JSON serialization preserves exact values."""
        original = parser.parse_game_info(DEMO_FILE)

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = CDotaGameInfo.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert len(restored.picks_bans) == 24


@pytest.mark.unit
class TestMessageEventRealValues:
    """Test MessageEvent with EXACT values from real demo file."""

    def test_universal_exact_messages(self, parser):
        """Test universal parsing produces exact message sequence."""
        result = parser.parse_universal(DEMO_FILE, max_messages=10)
        
        assert result.success is True
        assert len(result.messages) == 10
        assert result.count == 10
        assert result.error is None
        
        # Test exact message types from real file
        message_types = [msg.type for msg in result.messages]
        expected_types = ['CDemoFileHeader', 'CDemoPacket', 'CDemoPacket', 'CDemoPacket', 
                         'CDemoPacket', 'CDemoPacket', 'CDemoPacket', 'CDemoPacket', 
                         'CDemoPacket', 'CDemoPacket']
        assert message_types == expected_types

    def test_first_message_exact_values(self, parser):
        """Test first message contains exact expected values."""
        result = parser.parse_universal(DEMO_FILE, max_messages=5)
        
        first_message = result.messages[0]
        assert first_message.type == "CDemoFileHeader"
        assert first_message.tick == 0
        assert first_message.net_tick == 0
        assert first_message.data is not None

    def test_tick_progression_exact_sequence(self, parser):
        """Test tick progression follows exact sequence from real file."""
        result = parser.parse_universal(DEMO_FILE, max_messages=10)
        
        ticks = [msg.tick for msg in result.messages]
        expected_ticks = [0, 4, 7, 9, 11, 13, 15, 17, 19, 21]
        assert ticks == expected_ticks
        
        # Ticks must be in ascending order
        assert ticks == sorted(ticks)


@pytest.mark.unit
class TestUniversalParseResultRealValues:
    """Test UniversalParseResult with EXACT values from real demo file."""

    def test_universal_result_exact_structure(self, parser):
        """Test universal result contains exact structure from real file."""
        result = parser.parse_universal(DEMO_FILE, max_messages=5)
        
        assert result.success is True
        assert len(result.messages) == 5
        assert result.count == 5  # Should match message count for small requests
        assert result.error is None

    def test_universal_result_serialization_roundtrip(self, parser):
        """Test UniversalParseResult JSON serialization preserves exact values."""
        original = parser.parse_universal(DEMO_FILE, max_messages=3)
        
        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = UniversalParseResult.model_validate_json(json_str)
        
        # Must be identical to original
        assert restored == original
        assert len(restored.messages) == 3
        assert restored.messages[0].type == "CDemoFileHeader"

    def test_filtered_messages_exact_results(self, parser):
        """Test message filtering produces exact expected results."""
        result = parser.parse_universal(DEMO_FILE, message_filter="CDemoFileHeader", max_messages=5)
        
        assert result.success is True
        assert len(result.messages) >= 1
        
        # All messages must match the filter
        for message in result.messages:
            assert "CDemoFileHeader" in message.type
            
        # First message should be the file header
        assert result.messages[0].type == "CDemoFileHeader"
        assert result.messages[0].tick == 0