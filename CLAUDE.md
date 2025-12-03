# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Python Manta** is a Python wrapper/bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Go library that parses Dota 2 replay files (`.dem`). It uses CGO to create Python bindings for the Go parser, implementing all 272 Manta callbacks for comprehensive replay data extraction.

**Important**: This is a wrapper library. The actual parsing is done by [dotabuff/manta](https://github.com/dotabuff/manta) - we just provide Python bindings.

## Library Philosophy

Python Manta is a **low-level data extraction library**, not an analytics tool.

**✅ In Scope:**
- Raw data extraction from replay files
- Enums/constants for game data (e.g., `RuneType`, hero IDs)
- Type-safe Pydantic models
- Simple helper properties (e.g., `is_pro_match()`)

**❌ Out of Scope:**
- Analysis/aggregation logic (e.g., fight detection)
- Statistics computation
- Data interpretation
- High-level game understanding

**The rule**: If it's mapping/typing game data → add to library. If it's interpreting/analyzing → belongs in user code.

When adding new features, ask: "Is this raw data access or analysis?" Only raw data access belongs here.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Python Application                      │
├─────────────────────────────────────────────────────────────┤
│  python_manta Package (src/python_manta/)                   │
│  ├── MantaParser (main interface)                           │
│  ├── Pydantic Models (HeaderInfo, MessageEvent, etc.)       │
│  └── ctypes bindings (FFI to shared library)                │
├─────────────────────────────────────────────────────────────┤
│  libmanta_wrapper.so (go_wrapper/)                          │
│  ├── CGO exports (ParseHeader, ParseMatchInfo, ParseUniversal)  │
│  ├── 272 callback implementations (callbacks_*.go)          │
│  └── JSON serialization                                      │
├─────────────────────────────────────────────────────────────┤
│  dotabuff/manta (external Go library at ../manta)           │
│  ├── PBDEMS2 format parser                                  │
│  ├── Protobuf message decoding                              │
│  └── Callback system                                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `src/python_manta/manta_python.py` | Main Python API - `MantaParser` class |
| `src/python_manta/__init__.py` | Public exports |
| `go_wrapper/manta_wrapper.go` | CGO exports (ParseHeader, ParseMatchInfo) |
| `go_wrapper/universal_parser.go` | Universal parsing with callback filtering |
| `go_wrapper/data_parser.go` | Game events, modifiers, entities, combat log, string tables |
| `go_wrapper/entity_parser.go` | Entity state snapshot tracking |
| `go_wrapper/callbacks_*.go` | All 272 callback implementations |
| `build.sh` | Build script for CGO shared library |
| `pyproject.toml` | Python package configuration |

### Data Flow

1. Python calls `parse_universal("demo.dem", "CDOTAUserMsg_ChatMessage", 100)`
2. ctypes marshals parameters to C strings
3. CGO wrapper opens file, creates Manta parser
4. Manta Go library parses binary .dem file
5. Registered callbacks capture matching messages
6. Messages serialized to JSON
7. JSON returned to Python via ctypes
8. Pydantic models validate and structure data

## Essential Commands

### Build the library
```bash
./build.sh
```
Requires: Go 1.19+, Python 3.8+, Manta repo at `../manta`

### Run tests
```bash
# Unit tests (fast, no demo files)
python run_tests.py --unit

# Integration tests (requires demo files)
python run_tests.py --integration

# All tests with coverage
python run_tests.py --all --coverage
```

### Install in development mode
```bash
pip install -e '.[dev]'
# OR with uv
uv pip install -e '.[dev]'
```

### Quick validation
```bash
python simple_example.py
```

## API Quick Reference

### Main Classes and Functions

```python
from python_manta import (
    MantaParser,           # Main parser class
    HeaderInfo,            # Demo header metadata
    DraftEvent,            # Draft pick/ban event
    PlayerInfo,            # Player info from match
    GameInfo,              # Complete game info (draft, teams, players)
    MessageEvent,          # Universal message wrapper
    UniversalParseResult,  # Parse result container
    # Entity snapshots (positions, stats over time)
    PlayerState,           # Player state with position
    TeamState,             # Team state
    EntitySnapshot,        # Snapshot at a tick
    EntityParseResult,     # Entity parsing result
    GameEventsResult,      # Game events result
    ModifiersResult,       # Modifiers result
    EntitiesResult,        # Entity query result
    StringTablesResult,    # String tables result
    CombatLogResult,       # Combat log result
    ParserInfo,            # Parser state info
)
```

### Basic Usage

```python
from python_manta import MantaParser

parser = MantaParser()

# Header metadata
header = parser.parse_header("match.dem")

# Game info (draft, players, teams)
game_info = parser.parse_game_info("match.dem")
print(f"Match {game_info.match_id}: {game_info.radiant_team_tag} vs {game_info.dire_team_tag}")

# Hero positions over time (see docs/guides/entities.md for details)
snapshots = parser.parse_entities("match.dem", interval_ticks=900, max_snapshots=100)
# Supports target_ticks=[tick1, tick2] and target_heroes=["npc_dota_hero_axe"]

# Universal message parsing
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

# Game events (364 event types)
events = parser.parse_game_events("match.dem", event_filter="dota_combatlog", max_events=100)

# Modifiers/buffs
modifiers = parser.parse_modifiers("match.dem", max_modifiers=100, auras_only=True)

# Entity queries (end-of-game state)
entities = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

# String tables
tables = parser.get_string_tables("match.dem", table_names=["userinfo"])

# Combat log (structured)
combat = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=100)

# Parser info
info = parser.get_parser_info("match.dem")
```

### Which API to Use

| Task | Method |
|------|--------|
| Match metadata | `parse_header()` |
| Draft picks/bans | `parse_game_info()` |
| Pro match info | `parse_game_info()` |
| Hero positions | `parse_entities()` |
| Chat messages | `parse_universal("CDOTAUserMsg_ChatMessage")` |
| Item purchases | `parse_universal("CDOTAUserMsg_ItemPurchased")` |
| Combat damage | `parse_combat_log(types=[0])` |
| Buff tracking | `parse_modifiers()` |
| Hero state (end) | `query_entities(class_filter="Hero")` |
| Game events | `parse_game_events()` |
| Player info | `get_string_tables(table_names=["userinfo"])` |

See README.md for complete list of all 272 callbacks.

## Testing Strategy

- **Unit tests** (`-m unit`): Test models and pure Python code
- **Integration tests** (`-m integration`): Test full parsing with real demos
- **Performance tests** (`-m slow`): Test with large files

Coverage requirement: 90% (configured in `pytest.ini`)

## Key Implementation Details

### Memory Management
The Go code allocates C strings via `C.CString()`. The Python code should call `FreeString` to release memory, but currently skips this to avoid memory issues (creates minor leak - TODO).

### Message Filtering
The `parse_universal` filter uses substring matching:
- `"Chat"` matches both `CDOTAUserMsg_ChatMessage` and `CDOTAUserMsg_ChatEvent`
- Empty string `""` matches all callbacks

### JSON Serialization
All Go→Python data exchange uses JSON to avoid complex struct marshaling.

### Callback Registration
All 272 callbacks are registered on every parse, but filtering happens in `addFilteredMessage()` which skips non-matching types.

## Common Development Tasks

### Adding a new callback
1. Check if callback exists in `callbacks_*.go` files
2. If not, add to appropriate file following pattern:
```go
parser.Callbacks.OnNewCallbackName(func(m *dota.NewCallbackName) error {
    return addFilteredMessage(messages, "NewCallbackName", parser.Tick, parser.NetTick, m, filter, maxMsgs)
})
```
3. Rebuild with `./build.sh`

### Debugging parsing issues
1. Verify demo file exists and is readable
2. Check callback name is exact (case-sensitive)
3. Try smaller `max_messages` to isolate issues
4. Try empty filter `""` to see all messages
5. Check Go build for CGO warnings

### Releasing a new version (CRITICAL - follow exactly)
1. **Read `pyproject.toml`** to check the current version
2. **Increment the version** appropriately (e.g., `1.4.5.1-dev11` → `1.4.5.1-dev12`)
3. **Update `pyproject.toml`** with the new version
4. **Commit the version bump**: `git commit -m "chore: bump version to X.Y.Z"`
5. **Push to master**: `git push origin master`
6. **Create git tag** matching the version: `git tag vX.Y.Z` (note the `v` prefix)
7. **Push the tag**: `git push origin vX.Y.Z`

**Version format**: `MAJOR.MINOR.PATCH.BUILD-devN` (e.g., `1.4.5.1-dev12`)
**Tag format**: `v` + version (e.g., `v1.4.5.1-dev12`)

⚠️ **NEVER guess the version number** - always read pyproject.toml first!

## Dependencies

**Build Requirements:**
- Go 1.19+
- Python 3.8+
- Manta repository at `../manta`

**Python Runtime:**
- pydantic>=2.0.0

**Development:**
- pytest>=7.0.0
- pytest-cov>=4.0.0
- black>=22.0.0
- isort>=5.0.0
- mypy>=1.0.0

## Project Links

- **GitHub**: https://github.com/DeepBlueCoding/python-manta
- **Documentation**: https://deepbluecoding.github.io/python-manta/
- **PyPI**: https://pypi.org/project/python-manta/
- **Manta (Go)**: https://github.com/dotabuff/manta
- **Dotabuff**: https://www.dotabuff.com
