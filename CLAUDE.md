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
│  ├── Parser (main interface)                                │
│  ├── Pydantic Models (HeaderInfo, MessageEvent, etc.)       │
│  └── ctypes bindings (FFI to shared library)                │
├─────────────────────────────────────────────────────────────┤
│  libmanta_wrapper.so (go_wrapper/)                          │
│  ├── CGO exports (Parse, BuildIndex, GetSnapshot, etc.)     │
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
| `src/python_manta/manta_python.py` | Main Python API - `Parser` class |
| `src/python_manta/__init__.py` | Public exports |
| `go_wrapper/manta_wrapper.go` | CGO exports (Parse, BuildIndex, GetSnapshot) |
| `go_wrapper/universal_parser.go` | Universal parsing with callback filtering |
| `go_wrapper/data_parser.go` | Game events, modifiers, entities, combat log, string tables |
| `go_wrapper/entity_parser.go` | Entity state snapshot tracking |
| `go_wrapper/callbacks_*.go` | All 272 callback implementations |
| `build.sh` | Build script for CGO shared library |
| `pyproject.toml` | Python package configuration |

### Data Flow

1. Python creates `Parser("demo.dem")` and calls `parse(**collectors)`
2. ctypes marshals parameters to C strings
3. CGO wrapper opens file, creates Manta parser
4. Manta Go library parses binary .dem file
5. Registered callbacks capture matching messages based on collectors
6. All data collected in single pass
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

### Test Caching System (CRITICAL)

Tests use a **global caching system** to avoid re-parsing replay files. This is essential for performance since parsing a full replay takes 5+ minutes.

#### Architecture

```
tests/
├── conftest.py           # ALL shared fixtures (module-scoped, cached)
├── caching_parser.py     # Parser wrapper with global cache
└── **/*.py               # Test files use fixtures from conftest.py
```

#### How It Works

1. **`caching_parser.py`**: Wraps the real Parser with global caches for `parse()`, `build_index()`, and `snapshot()` results
2. **`conftest.py`**: Defines module-scoped fixtures that use the caching parser
3. **Cache keys**: Based on `(demo_path, json.dumps(kwargs))` - different kwargs = different cache entries

#### Rules for Writing Tests

**DO:**
```python
# ✅ Use fixtures from conftest.py
def test_something(self, combat_log):
    assert len(combat_log.entries) > 1000

# ✅ Use the parser fixture for custom queries
def test_custom_query(self, parser):
    result = parser.parse(combat_log={"types": [4]})  # Will be cached
```

**DON'T:**
```python
# ❌ NEVER define local fixtures that duplicate conftest.py
@pytest.fixture(scope="module")
def parser():
    return Parser(DEMO_FILE)  # BAD - duplicates conftest.py

# ❌ NEVER import Parser directly in tests
from python_manta import Parser  # BAD
from caching_parser import Parser  # Only OK if using fixture pattern
```

#### Adding New Fixtures

When you need a new cached result:

1. **Add to `conftest.py`** (never in test files):
```python
@pytest.fixture(scope="module")
def my_new_fixture(parser):
    """Cached result for X."""
    result = parser.parse(some_collector={"some_option": value})
    assert result.success
    return result.some_collector
```

2. **Use consistent kwargs** - same kwargs = same cache entry

#### Available Fixtures

| Fixture | Returns | Description |
|---------|---------|-------------|
| `parser` | Parser | Shared parser instance |
| `header_result` | ParseResult | Header parsing result |
| `game_info_result` | ParseResult | Game info parsing result |
| `combat_log` | CombatLogResult | All combat log entries |
| `attacks_result` | AttacksResult | All attack events |
| `melee_attacks` | List[AttackEvent] | Filtered melee attacks |
| `ranged_attacks` | List[AttackEvent] | Filtered ranged attacks |
| `snapshot_30k` | HeroSnapshot | Hero state at tick 30000 |
| `demo_index` | DemoIndex | Keyframe index |

See `tests/conftest.py` for the full list.

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
    # Main parser class
    Parser,                # Unified API - single-pass parsing
    # Enums for type-safe filtering
    RuneType,              # Rune types (DOUBLE_DAMAGE, HASTE, etc.)
    EntityType,            # Entity types (HERO, LANE_CREEP, BUILDING, etc.)
    CombatLogType,         # Combat log types (DAMAGE, HEAL, PURCHASE, etc.)
    DamageType,            # Damage types (PHYSICAL, MAGICAL, PURE)
    Team,                  # Team identifiers (RADIANT, DIRE)
    Hero,                  # All heroes with ID/name lookup (145 heroes)
    NeutralItemTier,       # Neutral item tiers (TIER_1 through TIER_5)
    NeutralItem,           # All neutral items (100+ including retired)
    ChatWheelMessage,      # Chat wheel phrases
    GameActivity,          # Game activity types
    # Data models
    HeaderInfo,            # Demo header metadata
    DraftEvent,            # Draft pick/ban event
    PlayerInfo,            # Player info from match
    GameInfo,              # Complete game info (draft, teams, players)
    MessageEvent,          # Universal message wrapper
    MessagesResult,        # Messages collector result
    ParseResult,           # Main parse result container
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

### Parser API

The `Parser` class provides single-pass parsing - all data collected in one file traversal.

```python
from python_manta import Parser

# Create parser bound to file
parser = Parser("match.dem")

# Single-pass parsing - collect all data types at once
result = parser.parse(
    header=True,
    game_info=True,
    combat_log={"types": [0, 4], "max_entries": 100},
    entities={"interval_ticks": 1800, "max_snapshots": 50},
    messages={"filter": "ChatMessage", "max_messages": 100},
)

# Access all results from single parse
print(result.header.map_name)
print(result.game_info.match_id)
print(len(result.combat_log.entries))

# Index/Seek API for random access
index = parser.build_index(interval_ticks=1800)  # Build keyframes
snap = parser.snapshot(target_tick=36000)         # Get hero state at tick
for hero in snap.heroes:
    print(f"{hero.hero_name}: HP={hero.health}/{hero.max_health} at ({hero.x:.0f}, {hero.y:.0f})")

# Include illusions/clones in snapshot
snap = parser.snapshot(target_tick=36000, include_illusions=True)
for hero in snap.heroes:
    if hero.is_clone:
        print(f"Clone: {hero.hero_name}")

# Parse specific tick range
result = parser.parse_range(start_tick=25000, end_tick=35000, combat_log=True)
```

### Which API to Use

| Task | Collector Config | Notes |
|------|-----------------|-------|
| Match metadata | `header=True` | Build number, map, server |
| Draft picks/bans | `game_info=True` | Picks/bans with hero IDs |
| Pro match info | `game_info=True` | Teams, league, players, winner |
| Hero positions | `entities={"interval_ticks": 900}` | Position, stats at intervals |
| Chat messages | `messages={"filter": "ChatMessage"}` | Player text chat |
| Item purchases | `messages={"filter": "ItemPurchased"}` | Item buy events |
| Map pings | `messages={"filter": "LocationPing"}` | Ping coordinates |
| Combat damage | `combat_log={"types": [0]}` | Structured damage events |
| Hero kills | `combat_log={"heroes_only": True}` | Hero-related combat |
| Buff tracking | `modifiers={}` | Active buffs/debuffs |
| Game events | `game_events={}` | 364 named event types |
| Player info | `string_tables={"table_names": ["userinfo"]}` | Steam IDs, names |

**Advanced Operations:**

| Task | Method |
|------|--------|
| Multiple data types | `parser.parse(header=True, game_info=True, ...)` |
| Hero state at tick | `parser.snapshot(target_tick=36000)` |
| Hero state with illusions | `parser.snapshot(target_tick=36000, include_illusions=True)` |
| Build keyframe index | `parser.build_index(interval_ticks=1800)` |
| Events in tick range | `parser.parse_range(start_tick=..., end_tick=..., combat_log=True)` |

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

### Time Formatting in Documentation
**NEVER** display time as decimal minutes (e.g., "77.9 minutes"). Always use proper human-readable formats:

```python
# ❌ WRONG - "77.9 minutes" is not valid time
print(f"Duration: {seconds / 60:.1f} minutes")

# ✅ CORRECT - H:MM:SS format
hours = int(seconds // 3600)
mins = int((seconds % 3600) // 60)
secs = int(seconds % 60)
print(f"Duration: {hours}:{mins:02d}:{secs:02d}")  # "1:17:54"

# ✅ CORRECT - MM:SS format for game time
mins = int(abs(game_time) // 60)
secs = int(abs(game_time) % 60)
sign = "-" if game_time < 0 else ""
print(f"[{sign}{mins:02d}:{secs:02d}]")  # "[05:32]" or "[-01:30]"
```

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

### Releasing a new version

All versions follow **PEP 440** format with a 4-part scheme: `{manta_major}.{manta_minor}.{manta_patch}.{python_manta_release}`.

#### Version Types
| Type | Example | Tag | Publish To |
|------|---------|-----|------------|
| Development | `1.4.5.2.dev11` | `v1.4.5.2.dev11` | TestPyPI |
| Final Release | `1.4.5.2` | `v1.4.5.2` | PyPI |

#### Development Workflow

```bash
# 1. Make changes and commit
git add .
git commit -m "feat: add new feature"

# 2. Update version in pyproject.toml (e.g., dev10 → dev11)
sed -i 's/1.4.5.2.dev10/1.4.5.2.dev11/g' pyproject.toml

# 3. Commit version bump
git add pyproject.toml
git commit -m "bump: version 1.4.5.2.dev10 → 1.4.5.2.dev11"

# 4. Tag and push
git tag v1.4.5.2.dev11
git push origin master --tags
```

#### Release Workflow

```bash
# 1. Update version (remove .devN suffix)
sed -i 's/1.4.5.2.dev11/1.4.5.2/g' pyproject.toml

# 2. Commit, tag, and push
git add pyproject.toml
git commit -m "bump: version 1.4.5.2.dev11 → 1.4.5.2"
git tag v1.4.5.2
git push origin master --tags
```

#### Commit Message Convention
```
<type>: <description>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Tests
- `bump:` - Version bump

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
