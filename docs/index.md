# Python Manta

**Python bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Dota 2 replay parser**

??? info "AI Summary"
        Python Manta lets you parse Dota 2 replay files (.dem) in Python. Install with `pip install python-manta`. The library wraps the Go-based manta parser and provides:

    - Header/draft parsing for match metadata
    - 272 message callbacks for any replay data
    - Game events (364 types), combat log, modifiers, entity queries
    - Pydantic models for type-safe data access

    Quick start: `from python_manta import MantaParser; parser = MantaParser(); header = parser.parse_header("match.dem")`

---

## What is Python Manta?

Python Manta provides Python access to the [Manta](https://github.com/dotabuff/manta) Go library for parsing Dota 2 replay files. All parsing is done by Manta - this library provides:

1. **CGO bindings** - Wraps the Go parser as a shared library
2. **Pythonic API** - Clean, intuitive interface via `MantaParser`
3. **Type safety** - Pydantic models for all parsed data
4. **Comprehensive access** - All 272 Manta callbacks + specialized APIs

## Installation

```bash
pip install python-manta
```

Pre-built wheels available for Linux, macOS (Intel + Apple Silicon), and Windows.

## Quick Example

```python
from python_manta import MantaParser

parser = MantaParser()

# Get match metadata
header = parser.parse_header("match.dem")
print(f"Map: {header.map_name}, Build: {header.build_num}")

# Get game info (draft, players, teams)
game_info = parser.parse_game_info("match.dem")
for pb in game_info.picks_bans:
    action = "PICK" if pb.is_pick else "BAN"
    print(f"{action}: Hero {pb.hero_id}")

# Parse chat messages
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)
for msg in result.messages:
    print(f"[{msg.tick}] {msg.data}")
```

## Features Overview

| Feature | Method | Description |
|---------|--------|-------------|
| **Header** | `parse_header()` | Match metadata (map, build, server) |
| **Game Info** | `parse_game_info()` | Draft, players, teams, league |
| **Messages** | `parse_universal()` | Any of 272 message types |
| **Game Events** | `parse_game_events()` | 364 named event types |
| **Combat Log** | `parse_combat_log()` | Damage, heals, kills |
| **Modifiers** | `parse_modifiers()` | Buffs, debuffs, auras |
| **Entities** | `query_entities()` | Hero/unit state queries |
| **Positions** | `parse_entities()` | Hero positions over time |
| **String Tables** | `get_string_tables()` | Player info, baselines |

## Documentation

- [Getting Started](getting-started.md) - Installation and first steps
- [API Reference](api/index.md) - Complete API documentation
- [Guides](guides/index.md) - In-depth feature guides
- [Examples](examples.md) - Real-world code examples
- [Callbacks Reference](reference/callbacks.md) - All 272 supported callbacks

## Links

- [GitHub Repository](https://github.com/DeepBlueCoding/python-manta)
- [PyPI Package](https://pypi.org/project/python-manta/)
- [Original Manta (Go)](https://github.com/dotabuff/manta)
