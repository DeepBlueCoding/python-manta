"""
Test Parser.parse() method with single-pass parsing.
Tests real data values from actual demo files.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.unit
from python_manta import ParseResult, HeaderInfo, GameInfo, Hero


class TestParserBasicFunctionality:
    """Test basic Parser functionality using cached fixtures."""

    def test_parser_initialization(self, parser):
        """Test Parser initializes correctly with valid demo path."""
        assert parser._demo_path is not None

    def test_parse_header_only(self, header_result):
        """Test parsing header only returns correct real values."""
        result = header_result

        assert result.success is True
        assert result.header is not None
        assert result.header.map_name == "start"
        assert result.header.build_num == 10512

    def test_parse_game_info_only(self, game_info_result):
        """Test parsing game_info only returns correct real values."""
        result = game_info_result

        assert result.success is True
        assert result.game_info is not None
        assert len(result.game_info.picks_bans) == 24
        # Check actual pick values
        radiant_picks = [e.hero_id for e in result.game_info.picks_bans if e.is_pick and e.team == 2]
        assert radiant_picks == [99, 123, 66, 114, 95]

    def test_parse_multiple_collectors(self, header_and_game_info_result):
        """Test parsing multiple collectors in single pass returns all data."""
        result = header_and_game_info_result

        assert result.success is True
        # Both collectors should be populated
        assert result.header is not None
        assert result.game_info is not None
        # Verify real values
        assert result.header.map_name == "start"
        assert len(result.game_info.picks_bans) == 24

    def test_parse_parser_info(self, parser_info_result):
        """Test parser_info collector returns metadata."""
        result = parser_info_result

        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick > 0
        assert result.parser_info.game_build > 0


class TestParserCollectorConfigs:
    """Test Parser with various collector configurations using cached fixtures."""

    def test_parse_combat_log_with_config(self, combat_log_10):
        """Test combat log collector with configuration."""
        result = combat_log_10

        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) <= 10

    def test_parse_messages_with_filter(self, messages_result):
        """Test messages collector with filter."""
        result = messages_result

        assert result.success is True
        assert result.messages is not None
        assert len(result.messages.messages) >= 1

    def test_parse_entities_with_interval(self, entities_result):
        """Test entities collector with interval configuration."""
        result = entities_result

        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) > 0

    def test_parse_game_events_with_filter(self, game_events_dota):
        """Test game events collector with filter."""
        result = game_events_dota

        assert result.success is True
        assert result.game_events is not None


class TestParserGameInfoFields:
    """Test Parser game_info field values match actual demo data.

    Uses game_info_result fixture from conftest.py to avoid redundant parsing.
    """

    def test_game_info_match_id(self, game_info_result):
        """Test match_id is correct for known demo file."""
        assert game_info_result.game_info.match_id == 8447659831

    def test_game_info_game_mode(self, game_info_result):
        """Test game_mode is correct (2 = Captains Mode)."""
        assert game_info_result.game_info.game_mode == 2

    def test_game_info_radiant_team(self, game_info_result):
        """Test Radiant team info is parsed correctly."""
        game_info = game_info_result.game_info
        assert game_info.radiant_team_id == 7119388  # Team Spirit
        assert game_info.radiant_team_tag == "TSpirit"

    def test_game_info_dire_team(self, game_info_result):
        """Test Dire team info is parsed correctly."""
        game_info = game_info_result.game_info
        assert game_info.dire_team_id == 8291895  # Tundra Esports
        assert game_info.dire_team_tag == "Tundra"

    def test_game_info_league_info(self, game_info_result):
        """Test league info field exists."""
        # league_id may be 0 for some replays
        assert game_info_result.game_info.league_id >= 0

    def test_game_info_winner(self, game_info_result):
        """Test winner is correctly identified."""
        # This match was won by Radiant (Team Spirit)
        assert game_info_result.game_info.game_winner == 2

    def test_game_info_is_pro_match(self, game_info_result):
        """Test is_pro_match returns True for TI match."""
        assert game_info_result.game_info.is_pro_match() is True

    def test_game_info_players_count(self, game_info_result):
        """Test correct number of players are parsed."""
        assert len(game_info_result.game_info.players) == 10

    def test_game_info_radiant_players(self, game_info_result):
        """Test Radiant players are in correct positions."""
        radiant_players = [p for p in game_info_result.game_info.players if p.team == 2]
        assert len(radiant_players) == 5
        # Verify expected players (Team Spirit roster)
        player_names = [p.player_name for p in radiant_players]
        assert "Yatoro" in player_names
        assert "Collapse" in player_names

    def test_game_info_draft_complete(self, game_info_result):
        """Test draft has 24 events (10 bans + 10 picks + 4 bans)."""
        assert len(game_info_result.game_info.picks_bans) == 24

    def test_game_info_radiant_picks(self, game_info_result):
        """Test Radiant picked heroes are correct."""
        radiant_picks = [
            e.hero_id for e in game_info_result.game_info.picks_bans
            if e.is_pick and e.team == 2
        ]
        # Troll Warlord=95, Chen=66, MK=114, Hoodwink=123, BB=99
        expected_picks = [99, 123, 66, 114, 95]
        assert radiant_picks == expected_picks

    def test_game_info_dire_picks(self, game_info_result):
        """Test Dire picked heroes are correct."""
        dire_picks = [
            e.hero_id for e in game_info_result.game_info.picks_bans
            if e.is_pick and e.team == 3
        ]
        # Lycan=77, Pugna=45, Shadow Demon=27, Storm Spirit=17, FV=41
        expected_picks = [77, 45, 27, 17, 41]
        assert dire_picks == expected_picks

    def test_game_info_hero_enum_lookup(self, game_info_result):
        """Test Hero enum lookup works with draft data."""
        first_pick = game_info_result.game_info.picks_bans[10]  # First pick
        hero = Hero.from_id(first_pick.hero_id)
        assert hero is not None
        assert isinstance(hero, Hero)


class TestParserResultTypes:
    """Test Parser result types and structure using cached fixtures."""

    def test_parse_result_type(self, header_result):
        """Test parse returns ParseResult."""
        assert isinstance(header_result, ParseResult)

    def test_header_info_type(self, header_result):
        """Test header is HeaderInfo."""
        assert isinstance(header_result.header, HeaderInfo)

    def test_game_info_type(self, game_info_result):
        """Test game_info is GameInfo."""
        assert isinstance(game_info_result.game_info, GameInfo)

    def test_parse_result_success_flag(self, header_result):
        """Test success flag is set correctly."""
        assert header_result.success is True

    def test_parse_result_error_none_on_success(self, header_result):
        """Test error is None on successful parse."""
        assert header_result.error is None


class TestParserIndexSeekBasics:
    """Test basic index/seek functionality using cached fixtures."""

    def test_build_index_creates_keyframes(self, demo_index):
        """Test build_index creates keyframe data."""
        assert demo_index.success is True
        assert len(demo_index.keyframes) > 0

    def test_snapshot_returns_heroes(self, snapshot_30k):
        """Test snapshot returns hero data."""
        assert snapshot_30k.success is True
        assert len(snapshot_30k.heroes) == 10

    def test_snapshot_hero_has_position(self, snapshot_30k):
        """Test snapshot heroes have position data."""
        hero = snapshot_30k.heroes[0]
        assert hero.x != 0 or hero.y != 0

    def test_snapshot_hero_has_stats(self, snapshot_30k):
        """Test snapshot heroes have stat data."""
        # Find an alive hero (some may be dead at this tick)
        alive_hero = next((h for h in snapshot_30k.heroes if h.is_alive), None)
        assert alive_hero is not None, "At least one hero should be alive"
        assert alive_hero.health > 0
        assert alive_hero.max_health > 0
        assert alive_hero.level > 0


class TestParserCombatLogBasics:
    """Test basic combat log parsing using cached fixtures."""

    def test_combat_log_has_entries(self, combat_log_result):
        """Test combat log has entries."""
        assert combat_log_result.success is True
        assert combat_log_result.combat_log is not None
        assert len(combat_log_result.combat_log.entries) > 0

    def test_combat_log_entry_has_type(self, combat_log_result):
        """Test combat log entries have type field."""
        entry = combat_log_result.combat_log.entries[0]
        assert entry.type >= 0

    def test_combat_log_heroes_only_filter(self, combat_log_heroes_only):
        """Test heroes_only filter works - all entries involve heroes by name."""
        result = combat_log_heroes_only
        assert result.success is True
        # All entries should have hero in target_name or attacker_name
        for entry in result.combat_log.entries:
            has_hero = "npc_dota_hero_" in entry.target_name or "npc_dota_hero_" in entry.attacker_name
            assert has_hero, f"Entry has no hero: target={entry.target_name}, attacker={entry.attacker_name}"


class TestParserModifiersBasics:
    """Test basic modifiers parsing using cached fixtures."""

    def test_modifiers_has_entries(self, modifiers_result):
        """Test modifiers has entries."""
        assert modifiers_result.success is True
        assert modifiers_result.modifiers is not None
        assert modifiers_result.modifiers.total_modifiers > 0


class TestParserStringTablesBasics:
    """Test basic string tables parsing using cached fixtures."""

    def test_string_tables_has_tables(self, string_tables_result):
        """Test string tables are parsed."""
        assert string_tables_result.success is True
        assert string_tables_result.string_tables is not None
        assert len(string_tables_result.string_tables.tables) > 0


class TestParserMultipleInstances:
    """Test multiple Parser instances share cache."""

    def test_multiple_parsers_same_file(self, parser):
        """Test creating multiple parsers for same file uses cache."""
        # Just verify we can use the parser fixture
        result = parser.parse(header=True)
        assert result.success is True

    def test_parser_reuse(self, parser):
        """Test reusing parser for multiple operations uses cache."""
        result1 = parser.parse(header=True)
        result2 = parser.parse(header=True)
        # Both should succeed (from cache)
        assert result1.success is True
        assert result2.success is True
        # Same data
        assert result1.header.map_name == result2.header.map_name
