"""
Test v2 Parser API with single-pass parsing.
Tests real data values from actual demo files.
"""

import pytest

# Module-level marker: core functionality tests (~30s)
pytestmark = pytest.mark.core
from python_manta import Parser, ParseResult, HeaderInfo, GameInfo, Hero

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


class TestV2ParserBasicFunctionality:
    """Test basic v2 Parser functionality."""

    def test_parser_initialization(self):
        """Test Parser initializes correctly with valid demo path."""
        parser = Parser(DEMO_FILE)
        assert parser._demo_path == DEMO_FILE

    def test_parse_header_only(self):
        """Test parsing header only returns correct real values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)

        assert result.success is True
        assert result.header is not None
        assert result.header.map_name == "start"
        assert result.header.build_num == 10512
        # Other collectors should be None
        assert result.game_info is None
        assert result.combat_log is None
        assert result.entities is None

    def test_parse_game_info_only(self):
        """Test parsing game_info only returns correct real values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        assert result.success is True
        assert result.game_info is not None
        assert len(result.game_info.picks_bans) == 24
        # Check actual pick values
        radiant_picks = [e.hero_id for e in result.game_info.picks_bans if e.is_pick and e.team == 2]
        assert radiant_picks == [99, 123, 66, 114, 95]
        # Header should be None
        assert result.header is None

    def test_parse_multiple_collectors(self):
        """Test parsing multiple collectors in single pass returns all data."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True, game_info=True)

        assert result.success is True
        # Both collectors should be populated
        assert result.header is not None
        assert result.game_info is not None
        # Verify real values
        assert result.header.map_name == "start"
        assert len(result.game_info.picks_bans) == 24

    def test_parse_parser_info(self):
        """Test parser_info collector returns metadata."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(parser_info=True)

        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick > 0
        assert result.parser_info.game_build > 0


class TestV2ParserCollectorConfigs:
    """Test v2 Parser with various collector configurations."""

    def test_parse_combat_log_with_config(self):
        """Test combat log collector with configuration."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [0], "max_entries": 10})

        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) <= 10

    def test_parse_messages_with_filter(self):
        """Test messages collector with filter."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"filter": "CDemoFileHeader", "max_messages": 5})

        assert result.success is True
        assert result.messages is not None
        assert len(result.messages.messages) >= 1
        assert result.messages.messages[0].type == "CDemoFileHeader"

    def test_parse_entities_with_interval(self):
        """Test entities collector with interval configuration."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(entities={"interval_ticks": 1800, "max_snapshots": 5})

        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) <= 5

    def test_parse_game_events_with_filter(self):
        """Test game events collector with filter."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_events={"event_filter": "dota", "max_events": 10})

        assert result.success is True
        assert result.game_events is not None


class TestV2ParserGameInfoFields:
    """Test v2 Parser game_info field values match actual demo data."""

    def test_game_info_match_id(self):
        """Test match_id is correct for known demo file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.match_id == 8447659831

    def test_game_info_game_mode(self):
        """Test game_mode is correct (2 = Captains Mode)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.game_mode == 2

    def test_game_info_game_winner(self):
        """Test game_winner is correct (2 = Radiant won this match)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.game_winner == 2

    def test_game_info_league_id_is_zero(self):
        """Test league_id is 0 for this pro match (not all pro matches have league_id)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.league_id == 0

    def test_game_info_team_ids(self):
        """Test team IDs are correct for known pro teams."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.radiant_team_id == 7119388  # Team Spirit
        assert result.game_info.dire_team_id == 8291895  # Tundra

    def test_game_info_team_tags(self):
        """Test team tags are correct for known pro teams."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert result.game_info.radiant_team_tag == "TSpirit"
        assert result.game_info.dire_team_tag == "Tundra"

    def test_game_info_is_pro_match_with_zero_league_id(self):
        """Test is_pro_match() returns True even when league_id is 0.

        This is the critical test - league_id can be 0 for pro matches,
        but is_pro_match() uses team_ids as fallback.
        """
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        # league_id is 0
        assert result.game_info.league_id == 0
        # But team_ids are set
        assert result.game_info.radiant_team_id > 0
        assert result.game_info.dire_team_id > 0
        # So is_pro_match() should return True
        assert result.game_info.is_pro_match() is True

    def test_game_info_playback_info(self):
        """Test playback information is populated."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        assert result.game_info.playback_time > 0
        assert result.game_info.playback_ticks > 0
        assert result.game_info.playback_frames > 0
        # Specific values for this demo
        assert result.game_info.playback_ticks == 109131

    def test_game_info_end_time(self):
        """Test end_time is populated (Unix timestamp)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        # Unix timestamp should be > 2020 (1577836800)
        assert result.game_info.end_time > 1577836800

    def test_game_info_picks_bans_count(self):
        """Test picks_bans has 24 events (CM draft)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        assert len(result.game_info.picks_bans) == 24


class TestV2ParserPlayerInfo:
    """Test v2 Parser game_info.players functionality."""

    def test_game_info_players_count(self):
        """Test game_info returns exactly 10 players."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        assert result.success is True
        assert result.game_info is not None
        assert len(result.game_info.players) == 10

    def test_game_info_players_have_required_fields(self):
        """Test all players have required fields populated."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        for player in result.game_info.players:
            assert player.player_name != ""
            assert player.hero_name != ""
            assert player.steam_id > 0
            assert player.team in [2, 3]  # Radiant=2, Dire=3

    def test_game_info_players_team_distribution(self):
        """Test players are correctly distributed between teams."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        radiant_players = [p for p in result.game_info.players if p.team == 2]
        dire_players = [p for p in result.game_info.players if p.team == 3]

        assert len(radiant_players) == 5
        assert len(dire_players) == 5

    def test_game_info_players_known_values(self):
        """Test specific known player values from demo file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        # Find Yatoro (known player in this match)
        yatoro = next((p for p in result.game_info.players if p.player_name == "Yatoro"), None)
        assert yatoro is not None
        assert yatoro.hero_name == "npc_dota_hero_troll_warlord"
        assert yatoro.team == 2  # Radiant
        assert yatoro.steam_id == 76561198281846390

    def test_game_info_players_hero_names_format(self):
        """Test hero names are in npc_dota_hero_* format."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        for player in result.game_info.players:
            assert player.hero_name.startswith("npc_dota_hero_")


class TestV2ParserDataConsistency:
    """Test v2 Parser data consistency with real values."""

    def test_header_values_are_correct(self):
        """Test v2 Parser header values are correct for known demo file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)

        # Verify known values from this demo file
        assert result.header.map_name == "start"
        assert result.header.build_num == 10512
        assert result.header.network_protocol > 0
        assert len(result.header.server_name) > 0

    def test_game_info_values_are_correct(self):
        """Test v2 Parser game_info values are correct for known demo file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        # Total picks/bans
        assert len(result.game_info.picks_bans) == 24

        # Pick sequences for this demo using Hero enum
        radiant_picks = [e.hero_id for e in result.game_info.picks_bans if e.is_pick and e.team == 2]
        dire_picks = [e.hero_id for e in result.game_info.picks_bans if e.is_pick and e.team == 3]

        # Radiant: Bristleback, Hoodwink, Chen, Monkey King, Troll Warlord
        assert radiant_picks == [
            Hero.BRISTLEBACK.value,
            Hero.HOODWINK.value,
            Hero.CHEN.value,
            Hero.MONKEY_KING.value,
            Hero.TROLL_WARLORD.value,
        ]
        # Dire: Lycan, Pugna, Shadow Shaman, Storm Spirit, Faceless Void
        assert dire_picks == [
            Hero.LYCAN.value,
            Hero.PUGNA.value,
            Hero.SHADOW_SHAMAN.value,
            Hero.STORM_SPIRIT.value,
            Hero.FACELESS_VOID.value,
        ]

    def test_multiple_parses_produce_identical_results(self):
        """Test multiple parse calls produce identical results."""
        parser = Parser(DEMO_FILE)

        result1 = parser.parse(header=True, game_info=True)
        result2 = parser.parse(header=True, game_info=True)

        assert result1.header.map_name == result2.header.map_name
        assert result1.header.build_num == result2.header.build_num
        assert len(result1.game_info.picks_bans) == len(result2.game_info.picks_bans)

    def test_full_parse_with_all_collectors(self):
        """Test parsing with all collectors enabled."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(
            header=True,
            game_info=True,
            combat_log={"max_entries": 5},
            entities={"interval_ticks": 3600, "max_snapshots": 3},
            messages={"filter": "CDemoFileHeader", "max_messages": 1},
            parser_info=True,
        )

        assert result.success is True
        assert result.header is not None
        assert result.game_info is not None
        assert result.combat_log is not None
        assert result.entities is not None
        assert result.messages is not None
        assert result.parser_info is not None

        # Verify real data
        assert result.header.map_name == "start"
        assert len(result.game_info.picks_bans) == 24


class TestV2ParserErrorHandling:
    """Test v2 Parser error handling."""

    def test_nonexistent_file_error(self):
        """Test Parser raises proper error for nonexistent file."""
        parser = Parser("/nonexistent/file.dem")

        with pytest.raises(FileNotFoundError, match="Demo file not found"):
            parser.parse(header=True)

    def test_directory_instead_of_file_error(self):
        """Test Parser raises proper error for directory path."""
        parser = Parser("/tmp")

        with pytest.raises(ValueError) as exc_info:
            parser.parse(header=True)
        assert "is a directory" in str(exc_info.value)

    def test_missing_library_error(self):
        """Test Parser raises proper error for missing library."""
        with pytest.raises(FileNotFoundError, match="Shared library not found"):
            Parser(DEMO_FILE, library_path="/nonexistent/libmanta_wrapper.so")

    def test_empty_parse_still_succeeds(self):
        """Test parsing with no collectors still succeeds."""
        parser = Parser(DEMO_FILE)
        result = parser.parse()

        assert result.success is True
        # All collectors should be None
        assert result.header is None
        assert result.game_info is None


class TestV2ParserMultipleInstances:
    """Test multiple Parser instances work correctly."""

    def test_multiple_parser_instances_independence(self):
        """Test multiple parser instances produce identical results."""
        parser1 = Parser(DEMO_FILE)
        parser2 = Parser(DEMO_FILE)

        result1 = parser1.parse(header=True)
        result2 = parser2.parse(header=True)

        assert result1.header.map_name == result2.header.map_name == "start"
        assert result1.header.build_num == result2.header.build_num == 10512

    def test_parsers_with_different_files(self):
        """Test Parser instances bound to same file via explicit path."""
        # Both parsers use same file
        parser1 = Parser(DEMO_FILE)
        parser2 = Parser(DEMO_FILE)

        result1 = parser1.parse(game_info=True)
        result2 = parser2.parse(game_info=True)

        # Results must match
        picks1 = [e.hero_id for e in result1.game_info.picks_bans if e.is_pick and e.team == 2]
        picks2 = [e.hero_id for e in result2.game_info.picks_bans if e.is_pick and e.team == 2]
        assert picks1 == picks2 == [99, 123, 66, 114, 95]


class TestV2ParserIndexSeekFunctionality:
    """Test v2 Parser index/seek functionality for random access."""

    def test_build_index_returns_keyframes(self):
        """Test build_index returns keyframes with valid data."""
        parser = Parser(DEMO_FILE)
        index = parser.build_index(interval_ticks=1800)  # Every 60 seconds

        assert index.success is True
        assert index.total_ticks > 0
        assert len(index.keyframes) > 0

    def test_build_index_keyframes_have_valid_ticks(self):
        """Test keyframes have increasing tick values."""
        parser = Parser(DEMO_FILE)
        index = parser.build_index(interval_ticks=1800)

        assert len(index.keyframes) > 0
        # Keyframes should be in increasing tick order
        ticks = [kf.tick for kf in index.keyframes]
        assert ticks == sorted(ticks)
        assert all(t >= 0 for t in ticks)

    def test_build_index_keyframes_have_game_time(self):
        """Test keyframes have valid game_time values after game starts."""
        parser = Parser(DEMO_FILE)
        index = parser.build_index(interval_ticks=1800)

        # Find keyframes after game_started
        game_time_keyframes = [kf for kf in index.keyframes if kf.tick > index.game_started]
        assert len(game_time_keyframes) > 0

        # After game start, game_time should be positive
        for kf in game_time_keyframes:
            assert kf.game_time > 0.0

    def test_snapshot_returns_ten_heroes(self):
        """Test snapshot returns exactly 10 heroes (one per player)."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        assert snapshot.success is True
        assert len(snapshot.heroes) == 10

    def test_snapshot_heroes_have_valid_player_ids(self):
        """Test snapshot heroes have valid player IDs 0-9."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        player_ids = [h.player_id for h in snapshot.heroes]
        assert sorted(player_ids) == list(range(10))

    def test_snapshot_heroes_have_correct_teams(self):
        """Test snapshot heroes have correct team assignments."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        radiant_heroes = [h for h in snapshot.heroes if h.team == 2]
        dire_heroes = [h for h in snapshot.heroes if h.team == 3]

        assert len(radiant_heroes) == 5
        assert len(dire_heroes) == 5

        # Player IDs 0-4 are Radiant, 5-9 are Dire
        for hero in radiant_heroes:
            assert hero.player_id < 5
        for hero in dire_heroes:
            assert hero.player_id >= 5

    def test_snapshot_heroes_have_position_data(self):
        """Test snapshot heroes have valid position coordinates."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        for hero in snapshot.heroes:
            # Positions should be within Dota 2 map bounds (roughly -8000 to +8000)
            assert -10000 < hero.x < 10000
            assert -10000 < hero.y < 10000

    def test_snapshot_heroes_have_stats(self):
        """Test snapshot heroes have health, mana, and level data."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        for hero in snapshot.heroes:
            assert hero.max_health > 0
            assert hero.health >= 0
            assert hero.max_mana > 0
            assert hero.level >= 1

    def test_snapshot_game_time_is_valid(self):
        """Test snapshot game_time is valid for tick after game start."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        # At tick 30000, game should have started
        assert snapshot.game_time >= 0.0
        # Game time should be reasonable (less than an hour for early tick)
        assert snapshot.game_time < 3600.0

    def test_find_keyframe_returns_closest_keyframe(self):
        """Test find_keyframe returns the keyframe at or before target tick."""
        parser = Parser(DEMO_FILE)
        index = parser.build_index(interval_ticks=1800)

        result = parser.find_keyframe(index, target_tick=5000)

        assert result.success is True
        assert result.keyframe is not None
        assert result.keyframe.tick <= 5000

    def test_find_keyframe_exact_match(self):
        """Test find_keyframe identifies exact matches."""
        parser = Parser(DEMO_FILE)
        index = parser.build_index(interval_ticks=1800)

        # Use the tick of the first keyframe as target
        if len(index.keyframes) > 1:
            target_tick = index.keyframes[1].tick
            result = parser.find_keyframe(index, target_tick=target_tick)

            assert result.success is True
            assert result.exact is True
            assert result.keyframe.tick == target_tick

    def test_parse_range_returns_combat_log(self):
        """Test parse_range returns combat log events within tick range."""
        parser = Parser(DEMO_FILE)
        result = parser.parse_range(
            start_tick=25000,
            end_tick=35000,
            combat_log=True,
        )

        assert result.success is True
        # Should have some combat log entries in this range
        if result.combat_log:
            for entry in result.combat_log:
                assert entry["tick"] >= 25000
                assert entry["tick"] <= 35000

    def test_parse_range_resolves_combat_log_names(self):
        """Test parse_range resolves combat log string indices to names."""
        parser = Parser(DEMO_FILE)
        result = parser.parse_range(
            start_tick=25000,
            end_tick=35000,
            combat_log=True,
        )

        assert result.success is True
        if result.combat_log and len(result.combat_log) > 0:
            # Names should be strings, not numeric indices
            sample = result.combat_log[0]
            target_name = sample.get("target_name", "")
            # Should be a real name or "unknown_X" format, not just a number
            assert not target_name.isdigit()


class TestV2ParserIndexSeekEdgeCases:
    """Test edge cases for index/seek functionality."""

    def test_snapshot_early_tick_returns_success(self):
        """Test snapshot at early tick before game start."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=100)

        assert snapshot.success is True
        # May have fewer heroes before picking phase
        assert snapshot.tick >= 100

    def test_snapshot_very_late_tick_returns_success(self):
        """Test snapshot at very late tick."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=100000)

        assert snapshot.success is True
        # Should return last available state
        assert len(snapshot.heroes) <= 10

    def test_build_index_with_small_interval(self):
        """Test build_index with small interval creates more keyframes."""
        parser = Parser(DEMO_FILE)

        index_small = parser.build_index(interval_ticks=900)  # 30 seconds
        index_large = parser.build_index(interval_ticks=3600)  # 2 minutes

        assert len(index_small.keyframes) > len(index_large.keyframes)

    def test_parse_range_empty_range(self):
        """Test parse_range with range that has no events."""
        parser = Parser(DEMO_FILE)
        result = parser.parse_range(
            start_tick=0,
            end_tick=10,
            combat_log=True,
        )

        assert result.success is True
        # Very early range may have no combat log
        assert result.combat_log is not None


class TestV2ParserIncludeIllusions:
    """Test include_illusions functionality."""

    def test_snapshot_without_illusions_returns_ten_heroes(self):
        """Test snapshot without include_illusions returns exactly 10 heroes."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000)

        assert snapshot.success is True
        assert len(snapshot.heroes) == 10

    def test_snapshot_with_illusions_includes_extra_entities(self):
        """Test snapshot with include_illusions returns more than 10 heroes."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000, include_illusions=True)

        assert snapshot.success is True
        # This demo has Monkey King, so there should be clones
        assert len(snapshot.heroes) > 10

    def test_snapshot_illusions_have_flags_set(self):
        """Test snapshot with illusions has is_clone or is_illusion flags."""
        parser = Parser(DEMO_FILE)
        snapshot = parser.snapshot(target_tick=30000, include_illusions=True)

        # Count by type
        real_heroes = [h for h in snapshot.heroes if not h.is_illusion and not h.is_clone]
        illusions = [h for h in snapshot.heroes if h.is_illusion]
        clones = [h for h in snapshot.heroes if h.is_clone]

        assert len(real_heroes) == 10
        # Should have some illusions or clones (or both)
        assert len(illusions) + len(clones) > 0

    def test_snapshot_default_is_exclude_illusions(self):
        """Test snapshot default behavior excludes illusions."""
        parser = Parser(DEMO_FILE)

        # Default
        snap_default = parser.snapshot(target_tick=30000)
        # Explicit False
        snap_explicit = parser.snapshot(target_tick=30000, include_illusions=False)

        assert len(snap_default.heroes) == len(snap_explicit.heroes) == 10
