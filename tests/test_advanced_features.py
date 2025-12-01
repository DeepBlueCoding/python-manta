"""
Test advanced parser features with REAL VALUES from actual demo files.
Focus on game events, modifiers, entity queries, string tables, combat log, and parser info.
"""

import pytest
from python_manta import (
    MantaParser,
    GameEventsResult,
    ModifiersResult,
    EntitiesResult,
    StringTablesResult,
    CombatLogResult,
    ParserInfo,
)

DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


@pytest.mark.unit
class TestGameEvents:
    """Test game events parsing with real data."""

    def test_game_events_captures_364_event_types(self):
        """Test that we capture the expected number of event type definitions."""
        parser = MantaParser()
        result = parser.parse_game_events(DEMO_FILE, max_events=0, capture_types=True)

        assert result.success is True
        assert len(result.event_types) == 364

    def test_game_events_filter_by_name(self):
        """Test filtering events by name substring."""
        parser = MantaParser()
        result = parser.parse_game_events(DEMO_FILE, event_filter="dota_combatlog", max_events=100)

        assert result.success is True
        for event in result.events:
            assert "dota_combatlog" in event.name

    def test_game_events_have_expected_structure(self):
        """Test game event data has expected fields."""
        parser = MantaParser()
        result = parser.parse_game_events(DEMO_FILE, event_filter="dota", max_events=10)

        assert result.success is True
        assert len(result.events) == 10

        for event in result.events:
            assert len(event.name) > 0
            assert event.tick >= 0
            assert event.net_tick >= 0
            assert isinstance(event.fields, dict)

    def test_game_events_max_events_respected(self):
        """Test max_events parameter limits results."""
        parser = MantaParser()

        result5 = parser.parse_game_events(DEMO_FILE, max_events=5)
        result20 = parser.parse_game_events(DEMO_FILE, max_events=20)

        assert len(result5.events) == 5
        assert len(result20.events) == 20

    def test_game_events_dota_chase_hero_fields(self):
        """Test dota_chase_hero events have expected fields."""
        parser = MantaParser()
        result = parser.parse_game_events(DEMO_FILE, event_filter="dota_chase_hero", max_events=5)

        assert result.success is True
        if result.events:
            event = result.events[0]
            assert "eventtype" in event.fields or "target1" in event.fields


@pytest.mark.unit
class TestModifiers:
    """Test modifier/buff tracking with real data."""

    def test_modifiers_parsing_success(self):
        """Test basic modifier parsing works."""
        parser = MantaParser()
        result = parser.parse_modifiers(DEMO_FILE, max_modifiers=50)

        assert result.success is True
        assert result.total_modifiers == 50

    def test_modifiers_have_expected_structure(self):
        """Test modifier entries have expected fields."""
        parser = MantaParser()
        result = parser.parse_modifiers(DEMO_FILE, max_modifiers=10)

        assert result.success is True
        for mod in result.modifiers:
            assert mod.tick >= 0
            assert mod.parent > 0  # Entity handle
            assert isinstance(mod.duration, float)
            assert isinstance(mod.stack_count, int)
            assert isinstance(mod.is_aura, bool)

    def test_modifiers_auras_only_filter(self):
        """Test filtering for auras only."""
        parser = MantaParser()
        result = parser.parse_modifiers(DEMO_FILE, max_modifiers=100, auras_only=True)

        assert result.success is True
        for mod in result.modifiers:
            assert mod.is_aura is True


@pytest.mark.unit
class TestEntityQuery:
    """Test entity querying with real data."""

    def test_entity_query_hero_filter(self):
        """Test querying hero entities."""
        parser = MantaParser()
        result = parser.query_entities(DEMO_FILE, class_filter="Hero", max_entities=10)

        assert result.success is True
        assert result.total_entities == 10
        for entity in result.entities:
            assert "Hero" in entity.class_name

    def test_entity_query_returns_properties(self):
        """Test entities have properties dictionary."""
        parser = MantaParser()
        result = parser.query_entities(DEMO_FILE, class_filter="Hero", max_entities=1)

        assert result.success is True
        assert len(result.entities) == 1

        entity = result.entities[0]
        assert entity.index > 0
        assert len(entity.class_name) > 0
        assert isinstance(entity.properties, dict)
        assert len(entity.properties) > 0

    def test_entity_query_tower_entities(self):
        """Test querying tower entities."""
        parser = MantaParser()
        result = parser.query_entities(DEMO_FILE, class_filter="Tower", max_entities=20)

        assert result.success is True
        for entity in result.entities:
            assert "Tower" in entity.class_name

    def test_entity_query_property_filter(self):
        """Test filtering specific properties."""
        parser = MantaParser()
        result = parser.query_entities(
            DEMO_FILE,
            class_filter="Hero",
            property_filter=["m_iHealth", "m_iMaxHealth"],
            max_entities=1
        )

        assert result.success is True
        if result.entities and result.entities[0].properties:
            props = result.entities[0].properties
            assert len(props) <= 2  # Only requested properties

    def test_entity_query_tick_and_nettick(self):
        """Test query returns tick information."""
        parser = MantaParser()
        result = parser.query_entities(DEMO_FILE, max_entities=1)

        assert result.success is True
        assert result.tick > 0
        assert result.net_tick >= 0

    def test_entity_query_class_names_filter(self):
        """Test filtering by specific class names."""
        parser = MantaParser()
        result = parser.query_entities(
            DEMO_FILE,
            class_names=["CDOTA_Unit_Hero", "CDOTA_BaseNPC_Tower"],
            max_entities=20
        )

        assert result.success is True
        for entity in result.entities:
            assert "Hero" in entity.class_name or "Tower" in entity.class_name


@pytest.mark.unit
class TestStringTables:
    """Test string table extraction with real data."""

    def test_string_tables_extraction(self):
        """Test basic string table extraction."""
        parser = MantaParser()
        result = parser.get_string_tables(DEMO_FILE, max_entries=50)

        assert result.success is True
        assert len(result.table_names) > 0
        assert result.total_entries > 0

    def test_string_tables_known_tables_exist(self):
        """Test known string tables are present."""
        parser = MantaParser()
        result = parser.get_string_tables(DEMO_FILE)

        assert result.success is True
        known_tables = ["instancebaseline", "userinfo", "lightstyles"]
        for table in known_tables:
            assert table in result.table_names

    def test_string_tables_specific_table(self):
        """Test extracting specific table."""
        parser = MantaParser()
        result = parser.get_string_tables(DEMO_FILE, table_names=["userinfo"], max_entries=50)

        assert result.success is True
        assert "userinfo" in result.table_names


@pytest.mark.unit
class TestCombatLog:
    """Test structured combat log parsing with real data."""

    def test_combat_log_parsing(self):
        """Test basic combat log parsing."""
        parser = MantaParser()
        result = parser.parse_combat_log(DEMO_FILE, max_entries=50)

        assert result.success is True
        assert result.total_entries == 50

    def test_combat_log_entry_structure(self):
        """Test combat log entries have expected structure."""
        parser = MantaParser()
        result = parser.parse_combat_log(DEMO_FILE, max_entries=10)

        assert result.success is True
        for entry in result.entries:
            assert entry.tick >= 0
            assert len(entry.type_name) > 0
            assert isinstance(entry.timestamp, float)
            assert isinstance(entry.is_attacker_hero, bool)
            assert isinstance(entry.is_target_hero, bool)

    def test_combat_log_heroes_only_filter(self):
        """Test filtering for hero-related entries only."""
        parser = MantaParser()
        result = parser.parse_combat_log(DEMO_FILE, max_entries=100, heroes_only=True)

        assert result.success is True
        for entry in result.entries:
            assert entry.is_attacker_hero or entry.is_target_hero

    def test_combat_log_type_filter(self):
        """Test filtering by combat log type."""
        parser = MantaParser()
        # Type 0 = DOTA_COMBATLOG_DAMAGE
        result = parser.parse_combat_log(DEMO_FILE, types=[0], max_entries=50)

        assert result.success is True
        for entry in result.entries:
            assert entry.type == 0

    def test_combat_log_timestamp_progression(self):
        """Test combat log timestamps increase over time."""
        parser = MantaParser()
        result = parser.parse_combat_log(DEMO_FILE, max_entries=100)

        assert result.success is True
        if len(result.entries) > 1:
            timestamps = [e.timestamp for e in result.entries]
            # Timestamps should generally increase (allowing for some variance)
            assert timestamps[-1] >= timestamps[0]


@pytest.mark.unit
class TestParserInfo:
    """Test parser state information extraction."""

    def test_parser_info_basic(self):
        """Test basic parser info extraction."""
        parser = MantaParser()
        result = parser.get_parser_info(DEMO_FILE)

        assert result.success is True
        assert result.tick > 0
        assert result.entity_count > 0

    def test_parser_info_string_tables_list(self):
        """Test parser info includes string tables list."""
        parser = MantaParser()
        result = parser.get_parser_info(DEMO_FILE)

        assert result.success is True
        assert len(result.string_tables) > 0
        assert "instancebaseline" in result.string_tables

    def test_parser_info_known_values(self):
        """Test parser info returns expected known values for test demo."""
        parser = MantaParser()
        result = parser.get_parser_info(DEMO_FILE)

        assert result.success is True
        assert result.tick == 109131  # Known tick count for test demo
        assert result.entity_count > 3000  # Should have many entities


@pytest.mark.unit
class TestAdvancedFeaturesCrossFunctional:
    """Cross-functional tests across multiple advanced features."""

    def test_multiple_features_same_parser(self):
        """Test using multiple features with same parser instance."""
        parser = MantaParser()

        events = parser.parse_game_events(DEMO_FILE, max_events=5)
        modifiers = parser.parse_modifiers(DEMO_FILE, max_modifiers=5)
        entities = parser.query_entities(DEMO_FILE, max_entities=5)
        combat_log = parser.parse_combat_log(DEMO_FILE, max_entries=5)
        info = parser.get_parser_info(DEMO_FILE)

        assert events.success is True
        assert modifiers.success is True
        assert entities.success is True
        assert combat_log.success is True
        assert info.success is True

    def test_entity_and_combat_log_tick_consistency(self):
        """Test tick values are consistent across features."""
        parser = MantaParser()

        entities = parser.query_entities(DEMO_FILE, max_entities=1)
        info = parser.get_parser_info(DEMO_FILE)

        # Both should report the same final tick
        assert entities.tick == info.tick

    def test_game_events_and_modifiers_tick_ordering(self):
        """Test events and modifiers maintain tick ordering."""
        parser = MantaParser()

        events = parser.parse_game_events(DEMO_FILE, max_events=100)
        modifiers = parser.parse_modifiers(DEMO_FILE, max_modifiers=100)

        # Check events are ordered
        event_ticks = [e.tick for e in events.events]
        assert event_ticks == sorted(event_ticks)

        # Check modifiers are ordered
        mod_ticks = [m.tick for m in modifiers.modifiers]
        assert mod_ticks == sorted(mod_ticks)


@pytest.mark.unit
class TestAdvancedFeaturesErrorHandling:
    """Test error handling for advanced features."""

    def test_game_events_nonexistent_file(self):
        """Test game events with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_game_events("/nonexistent/file.dem")

    def test_modifiers_nonexistent_file(self):
        """Test modifiers with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_modifiers("/nonexistent/file.dem")

    def test_entity_query_nonexistent_file(self):
        """Test entity query with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.query_entities("/nonexistent/file.dem")

    def test_string_tables_nonexistent_file(self):
        """Test string tables with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.get_string_tables("/nonexistent/file.dem")

    def test_combat_log_nonexistent_file(self):
        """Test combat log with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_combat_log("/nonexistent/file.dem")

    def test_parser_info_nonexistent_file(self):
        """Test parser info with nonexistent file."""
        parser = MantaParser()
        with pytest.raises(FileNotFoundError):
            parser.get_parser_info("/nonexistent/file.dem")
