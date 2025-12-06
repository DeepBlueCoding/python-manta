"""
Python Manta - Python interface for the Manta Dota 2 replay parser

This package provides a Python wrapper for the dotabuff/manta Go library,
enabling parsing of modern Dota 2 replay files (.dem) from Python applications.

Usage:
    from python_manta import Parser

    parser = Parser("replay.dem")
    result = parser.parse(header=True)
    print(f"Map: {result.header.map_name}, Build: {result.header.build_num}")
"""

from .manta_python import (
    # Main parser class
    Parser,
    # V2 config/result types
    ParseConfig,
    ParseResult,
    # V2 streaming types
    StreamConfig,
    StreamEvent,
    StreamResult,
    # V2 index/seek types
    Keyframe,
    DemoIndex,
    AbilitySnapshot,
    TalentChoice,
    HeroSnapshot,
    EntityStateSnapshot,
    RangeParseConfig,
    RangeParseResult,
    KeyframeResult,
    # Enums
    RuneType,
    EntityType,
    CombatLogType,
    DamageType,
    Team,
    Hero,
    NeutralItemTier,
    NeutralItem,
    ChatWheelMessage,
    GameActivity,
    # Header model
    HeaderInfo,
    # Game info models
    DraftEvent,
    PlayerInfo,
    GameInfo,
    # Universal parsing (low-level API) / Messages collector
    MessageEvent,
    MessagesResult,
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

__version__ = "1.4.5.1"
__author__ = "Equilibrium Coach Team"
__description__ = "Python interface for Manta Dota 2 replay parser"

__all__ = [
    # Main parser class
    "Parser",
    # V2 config/result types
    "ParseConfig",
    "ParseResult",
    # V2 streaming types
    "StreamConfig",
    "StreamEvent",
    "StreamResult",
    # V2 index/seek types
    "Keyframe",
    "DemoIndex",
    "AbilitySnapshot",
    "TalentChoice",
    "HeroSnapshot",
    "EntityStateSnapshot",
    "RangeParseConfig",
    "RangeParseResult",
    "KeyframeResult",
    # Enums
    "RuneType",
    "EntityType",
    "CombatLogType",
    "DamageType",
    "Team",
    "Hero",
    "NeutralItemTier",
    "NeutralItem",
    "ChatWheelMessage",
    "GameActivity",
    # Header model
    "HeaderInfo",
    # Game info models
    "DraftEvent",
    "PlayerInfo",
    "GameInfo",
    # Universal parsing (low-level API) / Messages collector
    "MessageEvent",
    "MessagesResult",
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
