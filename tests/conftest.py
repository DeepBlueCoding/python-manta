"""Shared pytest fixtures for python_manta tests.

Uses module-scoped fixtures to cache parsed results across tests,
significantly improving test performance by avoiding redundant parsing.
"""

import pytest
from python_manta import Parser

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
