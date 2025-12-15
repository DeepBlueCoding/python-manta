"""Shared pytest fixtures for python_manta tests.

Uses module-scoped fixtures to cache parsed results across tests,
significantly improving test performance by avoiding redundant parsing.
"""

import sys
from pathlib import Path

# Add tests directory to path for caching_parser import
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from caching_parser import Parser

# Primary test demo file (Team Spirit vs Tundra - TI match)
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"

# Secondary demo file for NeutralCampType and other tests
DEMO_FILE_SECONDARY = "/home/juanma/projects/equilibrium_coach/.data/replays/8461956309.dem"


@pytest.fixture(scope="module")
def parser():
    """Shared Parser instance for primary demo file."""
    return Parser(DEMO_FILE)


@pytest.fixture(scope="module")
def parser_secondary():
    """Shared Parser instance for secondary demo file."""
    return Parser(DEMO_FILE_SECONDARY)


@pytest.fixture(scope="module")
def header_result(parser):
    """Cached header parsing result."""
    return parser.parse(header=True)


@pytest.fixture(scope="module")
def game_info_result(parser):
    """Cached game_info parsing result."""
    return parser.parse(game_info=True)


@pytest.fixture(scope="module")
def header_and_game_info_result(parser):
    """Cached combined header and game_info parsing result."""
    return parser.parse(header=True, game_info=True)


@pytest.fixture(scope="module")
def messages_result(parser):
    """Cached messages parsing result (first 20 messages)."""
    return parser.parse(messages={"max_messages": 20})


@pytest.fixture(scope="module")
def combat_log_result(parser):
    """Cached combat log parsing result (all entries)."""
    return parser.parse(combat_log={"max_entries": 0})


@pytest.fixture(scope="module")
def combat_log_result_secondary(parser_secondary):
    """Cached combat log for secondary demo file (all entries)."""
    return parser_secondary.parse(combat_log={})


@pytest.fixture(scope="module")
def entities_result(parser):
    """Cached entities parsing result."""
    return parser.parse(entities={"interval_ticks": 1800, "max_snapshots": 50})


@pytest.fixture(scope="module")
def game_events_result(parser):
    """Cached game events parsing result."""
    return parser.parse(game_events={"max_events": 100})


@pytest.fixture(scope="module")
def modifiers_result(parser):
    """Cached modifiers parsing result."""
    return parser.parse(modifiers={"max_modifiers": 100})


@pytest.fixture(scope="module")
def string_tables_result(parser):
    """Cached string tables parsing result."""
    return parser.parse(string_tables={})


@pytest.fixture(scope="module")
def parser_info_result(parser):
    """Cached parser info result."""
    return parser.parse(parser_info=True)


@pytest.fixture(scope="module")
def demo_index(parser):
    """Cached demo index with keyframes."""
    return parser.build_index(interval_ticks=1800)


@pytest.fixture(scope="module")
def snapshot_30k(parser):
    """Cached hero snapshot at tick 30000."""
    return parser.snapshot(target_tick=30000)


@pytest.fixture(scope="module")
def snapshot_60k(parser):
    """Cached hero snapshot at tick 60000."""
    return parser.snapshot(target_tick=60000)


@pytest.fixture(scope="module")
def snapshot_90k(parser):
    """Cached hero snapshot at tick 90000."""
    return parser.snapshot(target_tick=90000)


@pytest.fixture(scope="module")
def snapshot_with_illusions(parser):
    """Cached hero snapshot at tick 30000 with illusions included."""
    return parser.snapshot(target_tick=30000, include_illusions=True)


@pytest.fixture(scope="module")
def full_parse_result(parser):
    """Cached full parsing with all collectors enabled."""
    return parser.parse(
        header=True,
        game_info=True,
        combat_log={"max_entries": 100},
        entities={"interval_ticks": 3600, "max_snapshots": 10},
        messages={"filter": "CDemoFileHeader", "max_messages": 5},
        parser_info=True,
    )


# ============================================================================
# Advanced features fixtures (for test_advanced_features.py)
# ============================================================================


@pytest.fixture(scope="module")
def game_events_with_types(parser):
    """Cached game events with event type definitions."""
    return parser.parse(game_events={"max_events": 0, "capture_types": True})


@pytest.fixture(scope="module")
def game_events_combatlog(parser):
    """Cached game events filtered to dota_combatlog."""
    return parser.parse(game_events={"event_filter": "dota_combatlog", "max_events": 100})


@pytest.fixture(scope="module")
def game_events_dota(parser):
    """Cached game events filtered to dota prefix."""
    return parser.parse(game_events={"event_filter": "dota", "max_events": 10})


@pytest.fixture(scope="module")
def game_events_chase_hero(parser):
    """Cached dota_chase_hero events."""
    return parser.parse(game_events={"event_filter": "dota_chase_hero", "max_events": 5})


@pytest.fixture(scope="module")
def modifiers_50(parser):
    """Cached modifiers result with 50 entries."""
    return parser.parse(modifiers={"max_modifiers": 50})


@pytest.fixture(scope="module")
def modifiers_auras(parser):
    """Cached auras-only modifiers."""
    return parser.parse(modifiers={"auras_only": True, "max_modifiers": 50})


@pytest.fixture(scope="module")
def string_tables_userinfo(parser):
    """Cached userinfo string table."""
    return parser.parse(string_tables={"table_names": ["userinfo"]})


@pytest.fixture(scope="module")
def combat_log_10(parser):
    """Cached combat log with 10 entries."""
    return parser.parse(combat_log={"max_entries": 10})


@pytest.fixture(scope="module")
def combat_log_50(parser):
    """Cached combat log with 50 entries."""
    return parser.parse(combat_log={"max_entries": 50})


@pytest.fixture(scope="module")
def combat_log_100(parser):
    """Cached combat log with 100 entries."""
    return parser.parse(combat_log={"max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_heroes_only(parser):
    """Cached combat log heroes only."""
    return parser.parse(combat_log={"max_entries": 100, "heroes_only": True})


@pytest.fixture(scope="module")
def combat_log_damage_only(parser):
    """Cached combat log with only DAMAGE type (type 0)."""
    return parser.parse(combat_log={"types": [0], "max_entries": 50})


@pytest.fixture(scope="module")
def combat_log_heals(parser):
    """Cached combat log HEAL events (type 1)."""
    return parser.parse(combat_log={"types": [1], "max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_deaths(parser):
    """Cached combat log DEATH events (type 4)."""
    return parser.parse(combat_log={"types": [4], "max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_abilities(parser):
    """Cached combat log ABILITY events (type 5)."""
    return parser.parse(combat_log={"types": [5], "max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_items(parser):
    """Cached combat log ITEM events (type 6)."""
    return parser.parse(combat_log={"types": [6], "max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_gold(parser):
    """Cached combat log GOLD events (type 8)."""
    return parser.parse(combat_log={"types": [8], "max_entries": 100})


@pytest.fixture(scope="module")
def combat_log_modifiers(parser):
    """Cached combat log MODIFIER_ADD events (type 2)."""
    return parser.parse(combat_log={"types": [2], "max_entries": 100})


# ============================================================================
# New feature fixtures (pre-horn positions, creep positions)
# ============================================================================


@pytest.fixture(scope="module")
def entities_with_prehord(parser):
    """Cached entities parsing with pre-horn snapshots included.

    Uses small interval to capture early-game ticks before horn.
    """
    return parser.parse(entities={"interval_ticks": 900, "max_snapshots": 200})


@pytest.fixture(scope="module")
def entities_with_creeps(parser):
    """Cached entities parsing with creep positions included."""
    return parser.parse(entities={
        "interval_ticks": 1800,
        "max_snapshots": 50,
        "include_creeps": True
    })


@pytest.fixture(scope="module")
def entities_midgame_with_creeps(parser):
    """Cached entities at midgame (10-15 min) with creeps for lane/neutral testing."""
    return parser.parse(entities={
        "interval_ticks": 900,
        "max_snapshots": 20,
        "include_creeps": True,
        "start_tick": 18000,  # ~10 minutes
    })


@pytest.fixture(scope="module")
def snapshot_lategame(parser):
    """Cached hero snapshot at tick 90000 (~30 min) for camps_stacked testing."""
    return parser.snapshot(target_tick=90000)


# ============================================================================
# Attacks fixtures (from TE_Projectile)
# ============================================================================


@pytest.fixture(scope="module")
def attacks_result(parser):
    """Cached attacks parsing result (all attack events)."""
    return parser.parse(attacks={})


@pytest.fixture(scope="module")
def attacks_limited(parser):
    """Cached attacks parsing result (first 100 events)."""
    return parser.parse(attacks={"max_events": 100})


# ============================================================================
# Hero Level fixtures (from entity state injection)
# ============================================================================


@pytest.fixture(scope="module")
def combat_log_hero_deaths(parser):
    """Cached combat log with hero DEATH events only."""
    return parser.parse(combat_log={"types": [4], "heroes_only": True})


@pytest.fixture(scope="module")
def combat_log_all_deaths(parser):
    """Cached combat log with all DEATH events (type 4)."""
    return parser.parse(combat_log={"types": [4], "max_entries": 0})
