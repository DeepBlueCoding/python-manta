"""
Python Manta - Python interface for the Manta Dota 2 replay parser

This package provides a Python wrapper for the dotabuff/manta Go library,
enabling parsing of modern Dota 2 replay files (.dem) from Python applications.

Usage:
    from python_manta import MantaParser

    parser = MantaParser()
    header = parser.parse_header("replay.dem")
    print(f"Map: {header.map_name}, Build: {header.build_num}")
"""

from .manta_python import (
    # Main parser class
    MantaParser,
    # Header model
    HeaderInfo,
    # Game info models (match Manta's CGameInfo.CDotaGameInfo)
    CHeroSelectEvent,
    CPlayerInfo,
    CDotaGameInfo,
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
)

__version__ = "0.1.0"
__author__ = "Equilibrium Coach Team"
__description__ = "Python interface for Manta Dota 2 replay parser"

__all__ = [
    # Main parser class
    "MantaParser",
    # Header model
    "HeaderInfo",
    # Game info models (match Manta's CGameInfo.CDotaGameInfo)
    "CHeroSelectEvent",
    "CPlayerInfo",
    "CDotaGameInfo",
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
]
