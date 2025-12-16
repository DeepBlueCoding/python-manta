"""
Test advanced parser collectors (game_events, modifiers, string_tables, combat_log, attacks).
Tests real data values from actual demo files.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.integration
from caching_parser import Parser
from tests.conftest import DEMO_FILE


class TestGameEvents:
    """Test game events parsing with real data."""

    def test_game_events_captures_364_event_types(self, game_events_with_types):
        """Test that we capture the expected number of event type definitions."""
        result = game_events_with_types
        assert result.success is True
        assert result.game_events is not None
        assert len(result.game_events.event_types) == 364

    def test_game_events_filter_by_name(self, game_events_combatlog):
        """Test filtering events by name substring."""
        result = game_events_combatlog
        assert result.success is True
        assert result.game_events is not None
        for event in result.game_events.events:
            assert "dota_combatlog" in event.name

    def test_game_events_have_expected_structure(self, game_events_dota):
        """Test game event data has expected fields."""
        result = game_events_dota
        assert result.success is True
        assert result.game_events is not None
        assert len(result.game_events.events) == 10

        for event in result.game_events.events:
            assert len(event.name) > 0
            assert event.tick >= 0
            assert event.net_tick >= 0
            assert isinstance(event.fields, dict)

    def test_game_events_max_events_respected(self, game_events_result, game_events_dota):
        """Test max_events parameter limits results."""
        # game_events_result has 100 events, game_events_dota has 10
        assert game_events_result.game_events is not None
        assert game_events_dota.game_events is not None
        assert len(game_events_result.game_events.events) == 100
        assert len(game_events_dota.game_events.events) == 10

    def test_game_events_dota_chase_hero_fields(self, game_events_chase_hero):
        """Test dota_chase_hero events have expected fields."""
        result = game_events_chase_hero
        assert result.success is True
        assert result.game_events is not None
        if result.game_events.events:
            event = result.game_events.events[0]
            assert "eventtype" in event.fields or "target1" in event.fields


class TestModifiers:
    """Test modifier/buff tracking with real data."""

    def test_modifiers_parsing_success(self, modifiers_50):
        """Test basic modifier parsing works."""
        result = modifiers_50
        assert result.success is True
        assert result.modifiers is not None
        assert result.modifiers.total_modifiers == 50

    def test_modifiers_have_expected_structure(self, modifiers_50):
        """Test modifier entries have expected fields."""
        result = modifiers_50
        assert result.success is True
        assert result.modifiers is not None
        for mod in result.modifiers.modifiers[:10]:
            assert mod.tick >= 0
            assert mod.parent > 0  # Entity handle
            assert isinstance(mod.duration, float)
            assert isinstance(mod.stack_count, int)
            assert isinstance(mod.is_aura, bool)

    def test_modifiers_auras_only_filter(self, modifiers_auras):
        """Test filtering for auras only."""
        result = modifiers_auras
        assert result.success is True
        assert result.modifiers is not None
        for mod in result.modifiers.modifiers:
            assert mod.is_aura is True


class TestStringTables:
    """Test string table extraction with real data."""

    def test_string_tables_extraction(self, string_tables_result):
        """Test basic string table extraction."""
        result = string_tables_result
        assert result.success is True
        assert result.string_tables is not None
        assert len(result.string_tables.table_names) > 0
        assert result.string_tables.total_entries > 0

    def test_string_tables_known_tables_exist(self, string_tables_result):
        """Test known string tables are present."""
        result = string_tables_result
        assert result.success is True
        assert result.string_tables is not None
        known_tables = ["instancebaseline", "userinfo", "lightstyles"]
        for table in known_tables:
            assert table in result.string_tables.table_names

    def test_string_tables_specific_table(self, string_tables_userinfo):
        """Test extracting specific table."""
        result = string_tables_userinfo
        assert result.success is True
        assert result.string_tables is not None
        assert "userinfo" in result.string_tables.table_names


class TestCombatLog:
    """Test structured combat log parsing with real data."""

    def test_combat_log_parsing(self, combat_log_50):
        """Test basic combat log parsing."""
        result = combat_log_50
        assert result.success is True
        assert result.combat_log is not None
        assert result.combat_log.total_entries == 50

    def test_combat_log_entry_structure(self, combat_log_10):
        """Test combat log entries have expected structure."""
        result = combat_log_10
        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.tick >= 0
            assert len(entry.type_name) > 0
            assert isinstance(entry.game_time, float)
            assert isinstance(entry.is_attacker_hero, bool)
            assert isinstance(entry.is_target_hero, bool)

    def test_combat_log_heroes_only_filter(self, combat_log_heroes_only):
        """Test filtering for hero-related entries only.

        heroes_only filter checks both boolean flags AND name strings,
        since some event types (GOLD, PURCHASE) have hero names but
        is_target_hero=False in the protobuf.
        """
        result = combat_log_heroes_only
        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            is_hero_related = (
                entry.is_attacker_hero or entry.is_target_hero or
                "npc_dota_hero_" in entry.attacker_name or
                "npc_dota_hero_" in entry.target_name
            )
            assert is_hero_related, f"Entry not hero-related: {entry.type_name}"

    def test_combat_log_type_filter(self, combat_log_damage_only):
        """Test filtering by combat log type."""
        result = combat_log_damage_only
        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.type == 0

    def test_combat_log_game_time_progression(self, combat_log_100):
        """Test combat log game_time increases over time."""
        result = combat_log_100
        assert result.success is True
        assert result.combat_log is not None
        if len(result.combat_log.entries) > 1:
            game_times = [e.game_time for e in result.combat_log.entries]
            # Game times should generally increase (allowing for some variance)
            assert game_times[-1] >= game_times[0]

    def test_combat_log_name_resolution(self, combat_log_heroes_only):
        """Test that names are properly resolved (not unknown_X)."""
        result = combat_log_heroes_only
        assert result.success is True
        assert result.combat_log is not None
        hero_entries = [e for e in result.combat_log.entries if e.is_attacker_hero or e.is_target_hero]
        assert len(hero_entries) > 0

        for entry in hero_entries:
            if entry.is_attacker_hero and entry.attacker_name:
                assert "npc_dota_hero" in entry.attacker_name
            if entry.is_target_hero and entry.target_name:
                assert "npc_dota_hero" in entry.target_name


class TestParserInfo:
    """Test parser state information extraction."""

    def test_parser_info_basic(self, parser_info_result):
        """Test basic parser info extraction."""
        result = parser_info_result
        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick > 0
        assert result.parser_info.entity_count > 0

    def test_parser_info_string_tables_list(self, parser_info_result):
        """Test parser info includes string tables list."""
        result = parser_info_result
        assert result.success is True
        assert result.parser_info is not None
        assert len(result.parser_info.string_tables) > 0
        assert "instancebaseline" in result.parser_info.string_tables

    def test_parser_info_known_values(self, parser_info_result):
        """Test parser info returns expected known values for test demo."""
        result = parser_info_result
        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick == 109131  # Known tick count for test demo
        assert result.parser_info.entity_count > 3000  # Should have many entities


class TestAdvancedFeaturesCrossFunctional:
    """Cross-functional tests across multiple advanced features."""

    def test_multiple_features_single_pass(self, full_parse_result):
        """Test using multiple features with single parse call."""
        result = full_parse_result
        assert result.success is True
        assert result.game_events is None  # full_parse_result doesn't include game_events
        assert result.combat_log is not None
        assert result.parser_info is not None

    def test_game_events_and_modifiers_tick_ordering(self, game_events_result, modifiers_result):
        """Test events and modifiers maintain tick ordering."""
        assert game_events_result.game_events is not None
        assert modifiers_result.modifiers is not None

        # Check events are ordered
        event_ticks = [e.tick for e in game_events_result.game_events.events]
        assert event_ticks == sorted(event_ticks)

        # Check modifiers are ordered
        mod_ticks = [m.tick for m in modifiers_result.modifiers.modifiers]
        assert mod_ticks == sorted(mod_ticks)


class TestAttacksCollector:
    """Test attacks parsing from TE_Projectile messages.

    Uses cached fixtures for efficient testing with real replay data.
    Match: Team Spirit vs Tundra (8447659831)
    """

    def test_attacks_collector_returns_events(self, attacks_limited):
        """Test that attacks collector returns attack events."""
        result = attacks_limited
        assert result.success is True
        assert result.attacks is not None
        assert result.attacks.total_events == 100
        assert len(result.attacks.events) == 100

    def test_attacks_total_count_matches_real_data(self, attacks_result):
        """Test that attacks collector captures expected number of events.

        Real data from match 8447659831:
        - Total attack events: 15,895
        - Hero attacks: 2,018 (13%)
        - Non-hero attacks: 13,877 (87%)
        """
        # attacks_result fixture returns AttacksResult directly
        assert attacks_result is not None
        # Exact value from our analysis (ranged + melee)
        assert attacks_result.total_events == 32895

    def test_attack_event_has_expected_fields(self, attacks_limited):
        """Test that AttackEvent has all expected fields."""
        result = attacks_limited
        assert result.attacks is not None
        assert len(result.attacks.events) > 0

        event = result.attacks.events[0]
        assert event.tick > 0
        assert event.source_index > 0
        assert event.target_index > 0
        assert event.source_handle > 0
        assert event.target_handle > 0
        assert event.projectile_speed > 0
        assert isinstance(event.dodgeable, bool)
        assert event.game_time_str != ""

    def test_attacks_tower_725_attack_count(self, attacks_result):
        """Test that Dire T1 top tower (entity 725) attacks are captured.

        Real data: Entity 725 (npc_dota_badguys_tower1_top) had 276 attacks.
        """
        assert attacks_result is not None

        tower_attacks = [e for e in attacks_result.events if e.source_index == 725]
        # Exact value from our analysis
        assert len(tower_attacks) == 276

    def test_attacks_hero_vs_nonhero_ratio(self, attacks_result, snapshot_60k):
        """Test that non-hero attacks outnumber hero attacks.

        Real data breakdown:
        - Hero attacks: 2,018 (13%)
        - Non-hero attacks: 25,508 (77%) - towers, creeps, neutrals
        """
        assert attacks_result is not None

        hero_indices = {h.index for h in snapshot_60k.heroes}

        hero_attacks = sum(1 for e in attacks_result.events if e.source_index in hero_indices)
        non_hero_attacks = attacks_result.total_events - hero_attacks

        # Exact values from our analysis (ranged + melee)
        assert hero_attacks == 7387
        assert non_hero_attacks == 25508

    def test_attacks_game_time_is_positive(self, attacks_limited):
        """Test that game_time values are positive (attacks after horn)."""
        result = attacks_limited
        assert result.attacks is not None

        for event in result.attacks.events:
            assert event.game_time > 0
            assert ":" in event.game_time_str

    def test_attacks_first_event_timing(self, attacks_result):
        """Test first attack event timing matches real data.

        First attack in match: tick=28038, game_time=15:34
        """
        assert attacks_result is not None
        assert len(attacks_result.events) > 0

        first = attacks_result.events[0]
        assert first.tick == 28038
        assert first.game_time_str == "15:34"

    def test_attacks_projectile_speeds_are_valid(self, attacks_limited):
        """Test that ranged attack projectile speeds are within expected range."""
        result = attacks_limited
        assert result.attacks is not None

        ranged_attacks = [e for e in result.attacks.events if not e.is_melee]
        for event in ranged_attacks:
            # Projectile speeds typically range from 400-1500 in Dota 2
            assert 0 < event.projectile_speed < 5000
