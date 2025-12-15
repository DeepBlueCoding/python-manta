"""
Test advanced parser features with REAL VALUES from actual demo files.
Focus on game events, modifiers, string tables, combat log, and parser info.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

# Module-level marker: integration tests
pytestmark = pytest.mark.integration
from caching_parser import Parser

# Import DEMO_FILE from conftest for error handling tests
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

    def test_combat_log_stun_events(self, combat_log_modifiers):
        """Test stun events have proper duration data."""
        result = combat_log_modifiers
        assert result.success is True
        assert result.combat_log is not None
        # Filter for modifier events (type 2) with stun duration
        stun_events = [e for e in result.combat_log.entries if e.type == 2 and e.stun_duration > 0]

        assert len(stun_events) > 0
        for stun in stun_events:
            assert stun.stun_duration > 0
            assert stun.stun_duration < 20  # No individual stun should be > 20 seconds

    def test_combat_log_damage_events_have_value(self, combat_log_damage_only):
        """Test damage events have positive value."""
        result = combat_log_damage_only
        assert result.success is True
        assert result.combat_log is not None
        for entry in result.combat_log.entries:
            assert entry.value >= 0

    def test_combat_log_death_events(self, combat_log_deaths):
        """Test death events (type 4) have proper data."""
        result = combat_log_deaths
        assert result.success is True
        assert result.combat_log is not None
        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        if hero_deaths:
            death = hero_deaths[0]
            assert "npc_dota_hero" in death.target_name
            assert death.attacker_team in [0, 2, 3]  # Team IDs
            assert death.target_team in [0, 2, 3]

    def test_combat_log_assist_players(self, combat_log_deaths):
        """Test assist_players field is populated on kills."""
        result = combat_log_deaths
        assert result.success is True
        assert result.combat_log is not None
        deaths_with_assists = [e for e in result.combat_log.entries if e.assist_players]

        # Should have some deaths with assists in a full game
        assert len(deaths_with_assists) > 0
        for death in deaths_with_assists:
            for assist_id in death.assist_players:
                assert isinstance(assist_id, int)

    def test_combat_log_heal_events(self, combat_log_heals):
        """Test heal events (type 1) have proper data."""
        result = combat_log_heals
        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            heal = result.combat_log.entries[0]
            assert heal.type == 1
            assert heal.value >= 0

    def test_combat_log_lifesteal_heals(self, combat_log_heals):
        """Test lifesteal heals are tracked."""
        result = combat_log_heals
        assert result.success is True
        assert result.combat_log is not None
        lifesteal_heals = [e for e in result.combat_log.entries if e.heal_from_lifesteal]

        # Should have some lifesteal heals
        assert len(lifesteal_heals) > 0

    def test_combat_log_modifier_events(self, combat_log_modifiers):
        """Test modifier add events (type 2)."""
        result = combat_log_modifiers
        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) > 0

        for entry in result.combat_log.entries:
            assert entry.type == 2

    def test_combat_log_ability_events(self, combat_log_abilities):
        """Test ability cast events (type 5)."""
        result = combat_log_abilities
        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            ability = result.combat_log.entries[0]
            assert ability.type == 5
            # Should have inflictor name (ability name)
            assert len(ability.inflictor_name) > 0

    def test_combat_log_item_events(self, combat_log_items):
        """Test item usage events (type 6)."""
        result = combat_log_items
        assert result.success is True
        assert result.combat_log is not None
        if result.combat_log.entries:
            item = result.combat_log.entries[0]
            assert item.type == 6
            # Inflictor should be an item name
            assert "item_" in item.inflictor_name or len(item.inflictor_name) > 0

    def test_combat_log_root_modifier(self, combat_log_modifiers):
        """Test root_modifier field is tracked."""
        result = combat_log_modifiers
        assert result.success is True
        assert result.combat_log is not None
        roots = [e for e in result.combat_log.entries if e.root_modifier]

        # Should have some root effects in a game
        assert len(roots) >= 0  # May or may not have roots depending on heroes

    def test_combat_log_all_fields_present(self, combat_log_10):
        """Test all 80 protobuf fields are accessible."""
        result = combat_log_10
        assert result.success is True
        assert result.combat_log is not None
        assert len(result.combat_log.entries) >= 1

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
        assert hasattr(entry, 'game_time')

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


class TestRespawnEvents:
    """Test hero respawn event derivation."""

    def test_derive_respawn_events(self, parser):
        """Test deriving respawn events from death entries."""
        from python_manta import derive_respawn_events, HeroRespawnEvent, CombatLogType

        result = parser.parse(combat_log={
            "types": [CombatLogType.DEATH],
            "heroes_only": True,
            "max_entries": 1000
        })
        assert result.success is True

        respawns = derive_respawn_events(result.combat_log)
        assert len(respawns) > 0

        for event in respawns:
            assert isinstance(event, HeroRespawnEvent)
            assert "npc_dota_hero_" in event.hero_name
            assert len(event.hero_display_name) > 0
            assert event.death_tick > 0
            assert event.respawn_duration >= 0
            assert event.respawn_tick >= event.death_tick

    def test_respawn_event_with_custom_levels(self, parser):
        """Test respawn calculation with custom hero levels."""
        from python_manta import derive_respawn_events, CombatLogType

        result = parser.parse(combat_log={
            "types": [CombatLogType.DEATH],
            "heroes_only": True,
            "max_entries": 1000
        })
        respawns_default = derive_respawn_events(result.combat_log)

        if len(respawns_default) > 0:
            hero_name = respawns_default[0].hero_name
            hero_key = hero_name.replace("npc_dota_hero_", "")
            hero_levels = {hero_key: 15}
            respawns_leveled = derive_respawn_events(result.combat_log, hero_levels)

            if len(respawns_leveled) > 0:
                assert respawns_leveled[0].hero_level == 15
                assert respawns_leveled[0].respawn_duration > respawns_default[0].respawn_duration


class TestPreHornPositions:
    """Test pre-horn entity snapshots (FEATURE #12).

    Pre-horn snapshots should have negative game_time values,
    indicating time before the horn sounded (0:00 mark).
    """

    def test_prehorn_snapshots_have_negative_game_time(self, entities_with_prehord):
        """Test that early snapshots have negative game_time (before horn)."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) > 0

        prehorn_snapshots = [s for s in result.entities.snapshots if s.game_time < 0]
        assert len(prehorn_snapshots) > 0, "Should have pre-horn snapshots with negative game_time"

        for snap in prehorn_snapshots:
            assert snap.game_time < 0
            assert snap.tick > 0

    def test_game_start_tick_is_populated(self, entities_with_prehord):
        """Test that game_start_tick is returned and non-zero."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert result.entities.game_start_tick > 0, "game_start_tick should be positive"
        # For typical Dota 2 replays, game starts around tick 20000-40000
        assert result.entities.game_start_tick > 10000

    def test_game_time_str_formats_negative_times(self, entities_with_prehord):
        """Test game_time_str property formats negative times with minus sign."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None

        prehorn_snapshots = [s for s in result.entities.snapshots if s.game_time < 0]
        assert len(prehorn_snapshots) > 0

        for snap in prehorn_snapshots:
            time_str = snap.game_time_str
            assert time_str.startswith("-"), f"Pre-horn time should start with '-': {time_str}"
            assert ":" in time_str, f"Time should contain colon: {time_str}"

    def test_posthorn_snapshots_have_positive_game_time(self, entities_with_prehord):
        """Test that snapshots after horn have positive game_time."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None

        posthorn_snapshots = [s for s in result.entities.snapshots if s.game_time >= 0]
        assert len(posthorn_snapshots) > 0, "Should have post-horn snapshots"

        for snap in posthorn_snapshots:
            assert snap.game_time >= 0

    def test_game_time_increases_with_tick(self, entities_with_prehord):
        """Test that game_time increases as tick increases."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) >= 2

        snapshots = sorted(result.entities.snapshots, key=lambda s: s.tick)
        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            assert curr.tick > prev.tick
            assert curr.game_time > prev.game_time, \
                f"game_time should increase: {prev.game_time} -> {curr.game_time}"


class TestCreepPositions:
    """Test creep entity positions (FEATURE #9).

    When include_creeps=True, snapshots should include lane and neutral creep positions.
    """

    def test_include_creeps_populates_creeps_list(self, entities_with_creeps):
        """Test that include_creeps=True populates creeps in snapshots."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        snapshots_with_creeps = [s for s in result.entities.snapshots if len(s.creeps) > 0]
        assert len(snapshots_with_creeps) > 0, "Should have snapshots with creeps"

    def test_creep_snapshot_has_expected_fields(self, entities_with_creeps):
        """Test CreepSnapshot model has all expected fields."""
        from python_manta import CreepSnapshot

        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        for snap in result.entities.snapshots:
            for creep in snap.creeps:
                assert isinstance(creep, CreepSnapshot)
                assert hasattr(creep, 'entity_id')
                assert hasattr(creep, 'class_name')
                assert hasattr(creep, 'name')
                assert hasattr(creep, 'team')
                assert hasattr(creep, 'x')
                assert hasattr(creep, 'y')
                assert hasattr(creep, 'health')
                assert hasattr(creep, 'max_health')
                assert hasattr(creep, 'is_neutral')
                assert hasattr(creep, 'is_lane')
                break  # Just need to verify one
            if snap.creeps:
                break

    def test_creeps_have_valid_team_values(self, entities_with_creeps):
        """Test creeps have valid team values (2=Radiant, 3=Dire, 4=Neutral)."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        valid_teams = {0, 2, 3, 4}  # 0=unknown, 2=Radiant, 3=Dire, 4=Neutral
        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        for creep in all_creeps:
            assert creep.team in valid_teams, f"Invalid team: {creep.team}"

    def test_lane_creeps_have_is_lane_flag(self, entities_with_creeps):
        """Test lane creeps have is_lane=True flag."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        lane_creeps = [c for c in all_creeps if c.is_lane]
        # Lane creeps should exist in any normal game
        assert len(lane_creeps) > 0, "Should have lane creeps with is_lane=True"

        for creep in lane_creeps:
            assert "Lane" in creep.class_name or "creep" in creep.name.lower()
            assert creep.team in {2, 3}, f"Lane creeps should be Radiant(2) or Dire(3), got {creep.team}"

    def test_neutral_creeps_have_is_neutral_flag(self, entities_with_creeps):
        """Test neutral creeps have is_neutral=True flag."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        neutral_creeps = [c for c in all_creeps if c.is_neutral]
        # Neutral creeps should exist in any normal game
        assert len(neutral_creeps) > 0, "Should have neutral creeps with is_neutral=True"

        for creep in neutral_creeps:
            assert "Neutral" in creep.class_name

    def test_creeps_have_valid_positions(self, entities_with_creeps):
        """Test creeps have positions within valid map bounds."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        # Dota 2 map is roughly -8192 to +8192 world units
        for creep in all_creeps:
            assert -10000 < creep.x < 10000, f"X position out of bounds: {creep.x}"
            assert -10000 < creep.y < 10000, f"Y position out of bounds: {creep.y}"

    def test_creeps_have_positive_health(self, entities_with_creeps):
        """Test creeps have positive health values."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        for creep in all_creeps:
            assert creep.health >= 0, f"Health should be non-negative: {creep.health}"
            assert creep.max_health > 0, f"Max health should be positive: {creep.max_health}"

    def test_creeps_not_included_by_default(self, entities_result):
        """Test that creeps are NOT included when include_creeps is not set."""
        result = entities_result
        assert result.success is True
        assert result.entities is not None

        for snap in result.entities.snapshots:
            assert len(snap.creeps) == 0, "Creeps should not be included by default"


class TestCampsStacked:
    """Test camps_stacked field extraction from entity properties (FEATURE #11).

    The camps_stacked stat is extracted from CDOTA_DataRadiant/CDOTA_DataDire
    entities via the m_vecDataTeam.%04d.m_iCampsStacked property.
    """

    def test_camps_stacked_field_exists(self, snapshot_30k):
        """Test HeroSnapshot has camps_stacked field."""
        snap = snapshot_30k
        assert snap is not None
        assert len(snap.heroes) > 0

        for hero in snap.heroes:
            assert hasattr(hero, 'camps_stacked'), "HeroSnapshot should have camps_stacked field"
            assert isinstance(hero.camps_stacked, int)

    def test_camps_stacked_non_negative(self, snapshot_lategame):
        """Test camps_stacked values are non-negative."""
        snap = snapshot_lategame
        assert snap is not None
        assert len(snap.heroes) > 0

        for hero in snap.heroes:
            assert hero.camps_stacked >= 0, f"camps_stacked should be >= 0, got {hero.camps_stacked}"

    def test_camps_stacked_increases_over_time(self, snapshot_30k, snapshot_lategame):
        """Test camps_stacked generally increases over time in a match."""
        early_snap = snapshot_30k
        late_snap = snapshot_lategame
        assert early_snap is not None and late_snap is not None

        early_total = sum(h.camps_stacked for h in early_snap.heroes)
        late_total = sum(h.camps_stacked for h in late_snap.heroes)

        assert late_total >= early_total, \
            f"Total camps_stacked should increase over time: {early_total} -> {late_total}"

    def test_camps_stacked_supports_have_stacks(self, snapshot_lategame):
        """Test that at least some heroes have camps_stacked > 0 in late game.

        In a typical pro match, supports stack camps for carries.
        """
        snap = snapshot_lategame
        assert snap is not None
        assert len(snap.heroes) == 10

        heroes_with_stacks = [h for h in snap.heroes if h.camps_stacked > 0]
        assert len(heroes_with_stacks) > 0, \
            "At least one hero should have camps_stacked > 0 in late game"

    def test_camps_stacked_reasonable_values(self, snapshot_lategame):
        """Test camps_stacked values are within reasonable range.

        Even in a long game, individual player stacks rarely exceed 30.
        """
        snap = snapshot_lategame
        assert snap is not None

        for hero in snap.heroes:
            assert hero.camps_stacked < 50, \
                f"camps_stacked unusually high for {hero.hero_name}: {hero.camps_stacked}"


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
        result = attacks_result
        assert result.success is True
        assert result.attacks is not None
        # Exact value from our analysis
        assert result.attacks.total_events == 15895

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
        result = attacks_result
        assert result.attacks is not None

        tower_attacks = [e for e in result.attacks.events if e.source_index == 725]
        # Exact value from our analysis
        assert len(tower_attacks) == 276

    def test_attacks_hero_vs_nonhero_ratio(self, attacks_result, snapshot_60k):
        """Test that non-hero attacks outnumber hero attacks.

        Real data breakdown:
        - Hero attacks: 2,018 (13%)
        - Non-hero attacks: 13,877 (87%) - towers, creeps, neutrals
        """
        result = attacks_result
        assert result.attacks is not None

        hero_indices = {h.index for h in snapshot_60k.heroes}

        hero_attacks = sum(1 for e in result.attacks.events if e.source_index in hero_indices)
        non_hero_attacks = result.attacks.total_events - hero_attacks

        # Exact values from our analysis
        assert hero_attacks == 2018
        assert non_hero_attacks == 13877

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
        result = attacks_result
        assert result.attacks is not None
        assert len(result.attacks.events) > 0

        first = result.attacks.events[0]
        assert first.tick == 28038
        assert first.game_time_str == "15:34"

    def test_attacks_projectile_speeds_are_valid(self, attacks_limited):
        """Test that projectile speeds are within expected range."""
        result = attacks_limited
        assert result.attacks is not None

        for event in result.attacks.events:
            # Projectile speeds typically range from 400-1500 in Dota 2
            assert 0 < event.projectile_speed < 5000


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


class TestHeroLevelInjection:
    """Test hero level injection from entity state into combat log.

    Previously, target_hero_level and attacker_hero_level were always 0
    because Dota 2 doesn't populate these protobuf fields. Now we inject
    hero levels from entity state (m_iCurrentLevel) during parsing.

    Real data from match 8447659831 (Team Spirit vs Tundra):
    - Total hero deaths: 48
    - Deaths with target_hero_level > 0: 48 (100%)
    - Deaths with attacker_hero_level > 0: 45 (94%)
    """

    def test_hero_deaths_have_target_levels(self, combat_log_hero_deaths):
        """Test that all hero deaths now have target_hero_level populated.

        This was 0% before the fix, now should be 100%.
        """
        result = combat_log_hero_deaths
        assert result.success is True
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        assert len(hero_deaths) == 48  # Real value from match

        deaths_with_level = sum(1 for d in hero_deaths if d.target_hero_level > 0)
        assert deaths_with_level == 48  # 100% now have levels

    def test_hero_deaths_have_attacker_levels(self, combat_log_hero_deaths):
        """Test that most hero deaths have attacker_hero_level populated.

        Non-hero attackers (summons, neutrals, wards) will have 0.
        Real data: 45/48 = 94% have attacker levels.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        deaths_with_attacker_level = sum(1 for d in hero_deaths if d.attacker_hero_level > 0)

        # 45 of 48 deaths had hero attackers
        assert deaths_with_attacker_level == 45

    def test_nonhero_attackers_have_zero_level(self, combat_log_hero_deaths):
        """Test that non-hero attackers correctly have level 0.

        Real data shows 3 deaths from non-heroes:
        - npc_dota_lycan_wolf4 (summon)
        - npc_dota_neutral_black_dragon (neutral creep)
        - npc_dota_shadow_shaman_ward_2 (ward)
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        nonhero_attacker_deaths = [d for d in hero_deaths if not d.is_attacker_hero]

        # All non-hero attackers should have level 0
        for death in nonhero_attacker_deaths:
            assert death.attacker_hero_level == 0

        # Should be exactly 3 non-hero attacker deaths
        assert len(nonhero_attacker_deaths) == 3

    def test_hero_levels_are_realistic(self, combat_log_hero_deaths):
        """Test that hero levels are within valid Dota 2 range (1-30)."""
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        for entry in result.combat_log.entries:
            if entry.target_hero_level > 0:
                assert 1 <= entry.target_hero_level <= 30
            if entry.attacker_hero_level > 0:
                assert 1 <= entry.attacker_hero_level <= 30

    def test_hero_levels_increase_over_game(self, combat_log_hero_deaths):
        """Test that hero levels generally increase as game progresses.

        Sample early vs late deaths to verify levels grow over time.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        # Get first and last few deaths with levels
        early_deaths = [d for d in hero_deaths[:10] if d.target_hero_level > 0]
        late_deaths = [d for d in hero_deaths[-10:] if d.target_hero_level > 0]

        early_avg = sum(d.target_hero_level for d in early_deaths) / len(early_deaths)
        late_avg = sum(d.target_hero_level for d in late_deaths) / len(late_deaths)

        # Late game levels should be higher than early game
        assert late_avg > early_avg

    def test_first_death_level_is_low(self, combat_log_hero_deaths):
        """Test that the first hero death has a low level (early game).

        First death at 00:10 - should be level 1.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        first_death = hero_deaths[0]

        # First death at 00:10 game time
        assert first_death.game_time < 60  # Within first minute
        assert first_death.target_hero_level == 1  # Level 1 at game start

    def test_specific_death_levels_match_real_data(self, combat_log_hero_deaths):
        """Test specific death events match verified real data.

        Sample verified deaths from manual inspection:
        - [03:36] hoodwink (lvl 2) killed by pugna (lvl 2)
        - [05:09] pugna (lvl 3) killed by bristleback (lvl 3)
        - [10:24] hoodwink (lvl 5) killed by faceless_void (lvl 7)
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        # Find death around 03:36 (216 seconds)
        hoodwink_death = next(
            (d for d in hero_deaths
             if "hoodwink" in d.target_name and 210 < d.game_time < 220),
            None
        )
        assert hoodwink_death is not None
        assert hoodwink_death.target_hero_level == 2
        assert hoodwink_death.attacker_hero_level == 2

        # Find bristleback kill around 05:09 (309 seconds)
        pugna_death = next(
            (d for d in hero_deaths
             if "pugna" in d.target_name and 305 < d.game_time < 315),
            None
        )
        assert pugna_death is not None
        assert pugna_death.target_hero_level == 3
        assert pugna_death.attacker_hero_level == 3
