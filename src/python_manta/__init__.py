"""
Python Manta - Python interface for the Manta Dota 2 replay parser

This package provides a Python wrapper for the dotabuff/manta Go library,
enabling parsing of modern Dota 2 replay files (.dem) from Python applications.

Basic Usage:
    from python_manta import MantaParser, parse_demo_header

    # Quick header parsing
    header = parse_demo_header("replay.dem")
    print(f"Map: {header.map_name}, Build: {header.build_num}")

    # Advanced usage
    parser = MantaParser()
    header = parser.parse_header("replay.dem")
"""

from .manta_python import (
    # Main parser class
    MantaParser,
    # Header/Draft models
    HeaderInfo,
    CHeroSelectEvent,
    CDotaGameInfo,
    # Match info (pro match data)
    PlayerMatchInfo,
    MatchInfo,
    # Universal parsing
    MessageEvent,
    UniversalParseResult,
    # Entity state snapshots
    PlayerState,
    TeamState,
    EntitySnapshot,
    EntityParseConfig,
    EntityParseResult,
    # Game events
    GameEventData,
    GameEventsConfig,
    GameEventsResult,
    # Modifiers/buffs
    ModifierEntry,
    ModifiersConfig,
    ModifiersResult,
    # Entity query
    EntityData,
    EntitiesConfig,
    EntitiesResult,
    # String tables
    StringTableData,
    StringTablesConfig,
    StringTablesResult,
    # Combat log
    CombatLogEntry,
    CombatLogConfig,
    CombatLogResult,
    # Parser info
    ParserInfo,
    # Convenience functions
    parse_demo_header,
    parse_demo_draft,
    parse_demo_match_info,
    parse_demo_universal,
    parse_demo_entities,
)

__version__ = "0.1.0"
__author__ = "Equilibrium Coach Team"
__description__ = "Python interface for Manta Dota 2 replay parser"

__all__ = [
    # Main parser class
    "MantaParser",
    # Header/Draft models
    "HeaderInfo",
    "CHeroSelectEvent",
    "CDotaGameInfo",
    # Match info (pro match data)
    "PlayerMatchInfo",
    "MatchInfo",
    # Universal parsing
    "MessageEvent",
    "UniversalParseResult",
    # Entity state snapshots
    "PlayerState",
    "TeamState",
    "EntitySnapshot",
    "EntityParseConfig",
    "EntityParseResult",
    # Game events
    "GameEventData",
    "GameEventsConfig",
    "GameEventsResult",
    # Modifiers/buffs
    "ModifierEntry",
    "ModifiersConfig",
    "ModifiersResult",
    # Entity query
    "EntityData",
    "EntitiesConfig",
    "EntitiesResult",
    # String tables
    "StringTableData",
    "StringTablesConfig",
    "StringTablesResult",
    # Combat log
    "CombatLogEntry",
    "CombatLogConfig",
    "CombatLogResult",
    # Parser info
    "ParserInfo",
    # Convenience functions
    "parse_demo_header",
    "parse_demo_draft",
    "parse_demo_match_info",
    "parse_demo_universal",
    "parse_demo_entities",
]
