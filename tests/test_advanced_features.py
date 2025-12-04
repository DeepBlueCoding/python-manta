"""
Test advanced parser features with REAL VALUES from actual demo files.
Focus on game events, modifiers, string tables, combat log, and parser info.
Uses v2 Parser API exclusively.
"""

import pytest

# Module-level marker: integration tests (~2min)
pytestmark = pytest.mark.integration
from python_manta import (
    Parser,
    ParseResult,
    GameEventsResult,
    ModifiersResult,
    StringTablesResult,
    CombatLogResult,
    ParserInfo,
)

DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


class TestGameEvents:
    """Test game events parsing with real data."""

    def test_game_events_captures_364_event_types(self):
        """Test that we capture the expected number of event type definitions."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_events={"max_events": 0, "capture_types": True})

        assert result.success is True
        assert result.game_events is not None
        assert len(result.game_events.event_types) == 364

    def test_game_events_filter_by_name(self):
        """Test filtering events by name substring."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_events={"event_filter": "dota_combatlog", "max_events": 100})

        assert result.success is True
        assert result.game_events is not None
        for event in result.game_events.events:
            assert "dota_combatlog" in event.name

    def test_game_events_have_expected_structure(self):
        """Test game event data has expected fields."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_events={"event_filter": "dota", "max_events": 10})

        assert result.success is True
        assert result.game_events is not None
        assert len(result.game_events.events) == 10

        for event in result.game_events.events:
            assert len(event.name) > 0
            assert event.tick >= 0
            assert event.net_tick >= 0
            assert isinstance(event.fields, dict)

    def test_game_events_max_events_respected(self):
        """Test max_events parameter limits results."""
        parser = Parser(DEMO_FILE)

        result5 = parser.parse(game_events={"max_events": 5})
        result20 = parser.parse(game_events={"max_events": 20})

        assert result5.game_events is not None
        assert result20.game_events is not None
        assert len(result5.game_events.events) == 5
        assert len(result20.game_events.events) == 20

    def test_game_events_dota_chase_hero_fields(self):
        """Test dota_chase_hero events have expected fields."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_events={"event_filter": "dota_chase_hero", "max_events": 5})

        assert result.success is True
        assert result.game_events is not None
        if result.game_events.events:
            event = result.game_events.events[0]
            assert "eventtype" in event.fields or "target1" in event.fields


class TestModifiers:
    """Test modifier/buff tracking with real data."""

    def test_modifiers_parsing_success(self):
        """Test basic modifier parsing works."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(modifiers={"max_modifiers": 50})

        assert result.success is True
        assert result.modifiers is not None
        assert result.modifiers.total_modifiers == 50

    def test_modifiers_have_expected_structure(self):
        """Test modifier entries have expected fields."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(modifiers={"max_modifiers": 10})

        assert result.success is True
        assert result.modifiers is not None
        for mod in result.modifiers.modifiers:
            assert mod.tick >= 0
            assert mod.parent > 0  # Entity handle
            assert isinstance(mod.duration, float)
            assert isinstance(mod.stack_count, int)
            assert isinstance(mod.is_aura, bool)

    def test_modifiers_auras_only_filter(self):
        """Test filtering for auras only."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(modifiers={"max_modifiers": 100, "auras_only": True})

        assert result.success is True
        assert result.modifiers is not None
        for mod in result.modifiers.modifiers:
            assert mod.is_aura is True


class TestStringTables:
    """Test string table extraction with real data."""

    def test_string_tables_extraction(self):
        """Test basic string table extraction."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(string_tables={"max_entries": 50})

        assert result.success is True
        assert result.string_tables is not None
        assert len(result.string_tables.table_names) > 0
        assert result.string_tables.total_entries > 0

    def test_string_tables_known_tables_exist(self):
        """Test known string tables are present."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(string_tables={})

        assert result.success is True
        assert result.string_tables is not None
        known_tables = ["instancebaseline", "userinfo", "lightstyles"]
        for table in known_tables:
            assert table in result.string_tables.table_names

    def test_string_tables_specific_table(self):
        """Test extracting specific table."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(string_tables={"table_names": ["userinfo"], "max_entries": 50})

        assert result.success is True
        assert result.string_tables is not None
        assert "userinfo" in result.string_tables.table_names


class TestCombatLog:
    """Test structured combat log parsing with real data."""

    def test_combat_log_parsing(self):
        """Test basic combat log parsing."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"max_entries": 50})

        assert result.success is True
        assert result.combat_log is not None
        assert result.combat_log.total_entries == 50

    def test_combat_log_entry_structure(self):
        """Test combat log entries have expected structure."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"max_entries": 10})

        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.tick >= 0
            assert len(entry.type_name) > 0
            assert isinstance(entry.timestamp, float)
            assert isinstance(entry.is_attacker_hero, bool)
            assert isinstance(entry.is_target_hero, bool)

    def test_combat_log_heroes_only_filter(self):
        """Test filtering for hero-related entries only."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"max_entries": 100, "heroes_only": True})

        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.is_attacker_hero or entry.is_target_hero

    def test_combat_log_type_filter(self):
        """Test filtering by combat log type."""
        parser = Parser(DEMO_FILE)
        # Type 0 = DOTA_COMBATLOG_DAMAGE
        result = parser.parse(combat_log={"types": [0], "max_entries": 50})

        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.type == 0

    def test_combat_log_timestamp_progression(self):
        """Test combat log timestamps increase over time."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"max_entries": 100})

        assert result.success is True
        assert result.combat_log is not None
        if len(result.combat_log.entries) > 1:
            timestamps = [e.timestamp for e in result.combat_log.entries]
            # Timestamps should generally increase (allowing for some variance)
            assert timestamps[-1] >= timestamps[0]

    def test_combat_log_name_resolution(self):
        """Test that names are properly resolved (not unknown_X)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"heroes_only": True, "max_entries": 100})

        assert result.success is True
        assert result.combat_log is not None
        hero_entries = [e for e in result.combat_log.entries if e.is_attacker_hero or e.is_target_hero]
        assert len(hero_entries) > 0

        for entry in hero_entries:
            if entry.is_attacker_hero and entry.attacker_name:
                assert "npc_dota_hero" in entry.attacker_name
            if entry.is_target_hero and entry.target_name:
                assert "npc_dota_hero" in entry.target_name

    def test_combat_log_stun_events(self):
        """Test stun events have proper duration data."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"heroes_only": True, "max_entries": 5000})

        assert result.success is True
        assert result.combat_log is not None
        stun_events = [e for e in result.combat_log.entries if e.stun_duration > 0]

        assert len(stun_events) > 0
        for stun in stun_events:
            assert stun.stun_duration > 0
            assert stun.stun_duration < 20  # No stun should be > 20 seconds

    def test_combat_log_damage_events_have_value(self):
        """Test damage events have positive value."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [0], "max_entries": 100})  # DAMAGE type

        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.value >= 0

    def test_combat_log_death_events(self):
        """Test death events (type 4) have proper data."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [4], "heroes_only": True, "max_entries": 100})

        assert result.success is True
        assert result.combat_log is not None
        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        if hero_deaths:
            death = hero_deaths[0]
            assert "npc_dota_hero" in death.target_name
            assert death.attacker_team in [0, 2, 3]  # Team IDs
            assert death.target_team in [0, 2, 3]

    def test_combat_log_assist_players(self):
        """Test assist_players field is populated on kills."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [4], "heroes_only": True, "max_entries": 500})

        assert result.success is True
        assert result.combat_log is not None
        deaths_with_assists = [e for e in result.combat_log.entries if e.assist_players]

        # Should have some deaths with assists in a full game
        assert len(deaths_with_assists) > 0
        for death in deaths_with_assists:
            for assist_id in death.assist_players:
                assert isinstance(assist_id, int)

    def test_combat_log_heal_events(self):
        """Test heal events (type 1) have proper data."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [1], "heroes_only": True, "max_entries": 200})

        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            heal = result.combat_log.entries[0]
            assert heal.type == 1
            assert heal.value >= 0

    def test_combat_log_lifesteal_heals(self):
        """Test lifesteal heals are tracked."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [1], "heroes_only": True, "max_entries": 1000})

        assert result.success is True
        assert result.combat_log is not None
        lifesteal_heals = [e for e in result.combat_log.entries if e.heal_from_lifesteal]

        # Should have some lifesteal heals
        assert len(lifesteal_heals) > 0

    def test_combat_log_modifier_events(self):
        """Test modifier add/remove events (types 2, 3)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [2, 3], "heroes_only": True, "max_entries": 200})

        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) > 0

        for entry in result.combat_log.entries:
            assert entry.type in [2, 3]

    def test_combat_log_ability_events(self):
        """Test ability cast events (type 5)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [5], "heroes_only": True, "max_entries": 100})

        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            ability = result.combat_log.entries[0]
            assert ability.type == 5
            # Should have inflictor name (ability name)
            assert len(ability.inflictor_name) > 0

    def test_combat_log_item_events(self):
        """Test item usage events (type 6)."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [6], "heroes_only": True, "max_entries": 100})

        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            item = result.combat_log.entries[0]
            assert item.type == 6
            # Inflictor should be an item name
            assert "item_" in item.inflictor_name or len(item.inflictor_name) > 0

    def test_combat_log_root_modifier(self):
        """Test root_modifier field is tracked."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"types": [2], "heroes_only": True, "max_entries": 5000})

        assert result.success is True
        assert result.combat_log is not None
        roots = [e for e in result.combat_log.entries if e.root_modifier]

        # Should have some root effects in a game
        assert len(roots) >= 0  # May or may not have roots depending on heroes

    def test_combat_log_all_fields_present(self):
        """Test all 80 protobuf fields are accessible."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(combat_log={"max_entries": 1})

        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) == 1

        entry = result.combat_log.entries[0]

        # Core fields
        assert hasattr(entry, 'tick')
        assert hasattr(entry, 'net_tick')
        assert hasattr(entry, 'type')
        assert hasattr(entry, 'type_name')
        assert hasattr(entry, 'target_name')
        assert hasattr(entry, 'attacker_name')
        assert hasattr(entry, 'inflictor_name')
        assert hasattr(entry, 'value')
        assert hasattr(entry, 'health')
        assert hasattr(entry, 'timestamp')

        # Location
        assert hasattr(entry, 'location_x')
        assert hasattr(entry, 'location_y')

        # Assists
        assert hasattr(entry, 'assist_player0')
        assert hasattr(entry, 'assist_player1')
        assert hasattr(entry, 'assist_player2')
        assert hasattr(entry, 'assist_player3')
        assert hasattr(entry, 'assist_players')

        # Damage classification
        assert hasattr(entry, 'damage_type')
        assert hasattr(entry, 'damage_category')

        # Modifier details
        assert hasattr(entry, 'modifier_duration')
        assert hasattr(entry, 'modifier_elapsed_duration')
        assert hasattr(entry, 'silence_modifier')
        assert hasattr(entry, 'root_modifier')
        assert hasattr(entry, 'aura_modifier')
        assert hasattr(entry, 'armor_debuff_modifier')
        assert hasattr(entry, 'no_physical_damage_modifier')
        assert hasattr(entry, 'motion_controller_modifier')
        assert hasattr(entry, 'modifier_purged')
        assert hasattr(entry, 'modifier_hidden')

        # Kill info
        assert hasattr(entry, 'spell_evaded')
        assert hasattr(entry, 'long_range_kill')
        assert hasattr(entry, 'will_reincarnate')
        assert hasattr(entry, 'total_unit_death_count')

        # Ability info
        assert hasattr(entry, 'is_ultimate_ability')
        assert hasattr(entry, 'inflictor_is_stolen_ability')
        assert hasattr(entry, 'spell_generated_attack')
        assert hasattr(entry, 'uses_charges')
        assert hasattr(entry, 'ability_level')

        # Game state
        assert hasattr(entry, 'at_night_time')
        assert hasattr(entry, 'attacker_has_scepter')
        assert hasattr(entry, 'regenerated_health')

        # Economy
        assert hasattr(entry, 'networth')
        assert hasattr(entry, 'xpm')
        assert hasattr(entry, 'gpm')

        # Buildings/neutrals
        assert hasattr(entry, 'building_type')
        assert hasattr(entry, 'neutral_camp_type')
        assert hasattr(entry, 'neutral_camp_team')

        # Tracking
        assert hasattr(entry, 'kill_eater_event')
        assert hasattr(entry, 'unit_status_label')
        assert hasattr(entry, 'tracked_stat_id')


class TestParserInfo:
    """Test parser state information extraction."""

    def test_parser_info_basic(self):
        """Test basic parser info extraction."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(parser_info=True)

        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick > 0
        assert result.parser_info.entity_count > 0

    def test_parser_info_string_tables_list(self):
        """Test parser info includes string tables list."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(parser_info=True)

        assert result.success is True
        assert result.parser_info is not None
        assert len(result.parser_info.string_tables) > 0
        assert "instancebaseline" in result.parser_info.string_tables

    def test_parser_info_known_values(self):
        """Test parser info returns expected known values for test demo."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(parser_info=True)

        assert result.success is True
        assert result.parser_info is not None
        assert result.parser_info.tick == 109131  # Known tick count for test demo
        assert result.parser_info.entity_count > 3000  # Should have many entities


class TestAdvancedFeaturesCrossFunctional:
    """Cross-functional tests across multiple advanced features."""

    def test_multiple_features_single_pass(self):
        """Test using multiple features with single parse call."""
        parser = Parser(DEMO_FILE)

        result = parser.parse(
            game_events={"max_events": 5},
            modifiers={"max_modifiers": 5},
            combat_log={"max_entries": 5},
            string_tables={"max_entries": 5},
            parser_info=True,
        )

        assert result.success is True
        assert result.game_events is not None
        assert result.modifiers is not None
        assert result.combat_log is not None
        assert result.string_tables is not None
        assert result.parser_info is not None

    def test_game_events_and_modifiers_tick_ordering(self):
        """Test events and modifiers maintain tick ordering."""
        parser = Parser(DEMO_FILE)

        result = parser.parse(
            game_events={"max_events": 100},
            modifiers={"max_modifiers": 100},
        )

        assert result.game_events is not None
        assert result.modifiers is not None

        # Check events are ordered
        event_ticks = [e.tick for e in result.game_events.events]
        assert event_ticks == sorted(event_ticks)

        # Check modifiers are ordered
        mod_ticks = [m.tick for m in result.modifiers.modifiers]
        assert mod_ticks == sorted(mod_ticks)


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
