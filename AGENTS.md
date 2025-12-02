# AGENTS.md

Guidelines for AI agents, LLMs, and coding assistants working with this repository.

## Project Summary

**Python Manta** is a Python wrapper for [dotabuff/manta](https://github.com/dotabuff/manta), a Go library that parses Dota 2 replay files (`.dem`). This library provides Python bindings via CGO, exposing all 272 Manta callbacks through a simple API.

**Key Point**: This is a wrapper/bindings library. The actual parsing logic lives in the Go [Manta](https://github.com/dotabuff/manta) project.

## Quick Start for AI Agents

### Installation
```bash
pip install python-manta
```

### Basic Usage
```python
from python_manta import MantaParser

parser = MantaParser()

# Parse header
header = parser.parse_header("match.dem")
print(f"Map: {header.map_name}, Build: {header.build_num}")

# Parse any message type (272 available)
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)
for msg in result.messages:
    print(f"[Tick {msg.tick}] {msg.data}")
```

## API Reference

### Classes

| Class | Purpose |
|-------|---------|
| `MantaParser` | Main parser class with `parse_header()`, `parse_game_info()`, `parse_universal()` |
| `HeaderInfo` | Demo file metadata (map_name, build_num, server_name, etc.) |
| `CDotaGameInfo` | Draft information with picks_bans list |
| `CHeroSelectEvent` | Single pick/ban (is_pick, team, hero_id) |
| `MessageEvent` | Universal message wrapper (type, tick, net_tick, data, timestamp) |
| `UniversalParseResult` | Parse result (success, count, messages, error) |

### MantaParser Methods

```python
parser = MantaParser()

# Parse header metadata
header: HeaderInfo = parser.parse_header("match.dem")

# Parse draft (picks/bans)
draft: CDotaGameInfo = parser.parse_game_info("match.dem")

# Parse any message type
result: UniversalParseResult = parser.parse_universal(
    "match.dem",                    # Demo file path
    "CDOTAUserMsg_ChatMessage",     # Callback filter (case-sensitive)
    100                              # Max messages (0 = unlimited)
)
```

## Common Callback Names

| Use Case | Callback Name | Typical Count |
|----------|---------------|---------------|
| Player chat | `CDOTAUserMsg_ChatMessage` | 10-100 |
| Map pings | `CDOTAUserMsg_LocationPing` | 50-500 |
| Item purchases | `CDOTAUserMsg_ItemPurchased` | 100-300 |
| Combat log | `CMsgDOTACombatLogEntry` | 5,000+ |
| Game state | `CDOTAUserMsg_GamerulesStateChanged` | 10-20 |
| Unit events | `CDOTAUserMsg_UnitEvent` | 5,000+ |
| Overhead events | `CDOTAUserMsg_OverheadEvent` | 2,000+ |
| Network ticks | `CNETMsg_Tick` | 50,000+ |
| Demo header | `CDemoFileHeader` | 1 |
| Demo info | `CDemoFileInfo` | 1 |

See README.md for complete list of all 272 callbacks organized by category.

## Message Data Structure

All messages from `parse_universal()` follow this structure:

```python
MessageEvent(
    type="CDOTAUserMsg_ChatMessage",  # Callback name
    tick=12345,                        # Game tick
    net_tick=12340,                    # Network tick
    data={                             # Message-specific fields (dict)
        "source_player_id": 3,
        "message_text": "glhf"
    },
    timestamp=1699900000000            # Unix timestamp (ms)
)
```

## Error Handling

```python
from python_manta import MantaParser

parser = MantaParser()

try:
    result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

    if result.success:
        for msg in result.messages:
            # Process msg.data dict
            pass
    else:
        print(f"Parse error: {result.error}")

except FileNotFoundError:
    print("Demo file not found")
except ValueError as e:
    print(f"Parsing failed: {e}")
```

## Important Constraints

1. **Callback names are case-sensitive** - Use exact names from callback list
2. **Filter uses substring matching** - `"Chat"` matches `CDOTAUserMsg_ChatMessage` AND `CDOTAUserMsg_ChatEvent`
3. **Use max_messages for large replays** - Some callbacks fire 50,000+ times
4. **Replay files are large** - Typical match is 100-200MB
5. **Team IDs**: 2 = Radiant, 3 = Dire

## Project Structure

```
python_manta/
├── src/python_manta/           # Python package
│   ├── __init__.py             # Public exports
│   ├── manta_python.py         # Main API (MantaParser class)
│   └── libmanta_wrapper.so     # Pre-built CGO library
├── go_wrapper/                 # Go CGO source
│   ├── manta_wrapper.go        # CGO exports
│   ├── universal_parser.go     # Universal parsing
│   └── callbacks_*.go          # 272 callback implementations
├── tests/                      # Test suite
├── examples/                   # Usage examples
├── build.sh                    # Build script
└── pyproject.toml              # Package config
```

## Build Commands

```bash
# Build CGO library (requires Go 1.19+, ../manta repo)
./build.sh

# Install in dev mode
pip install -e '.[dev]'

# Run tests
python run_tests.py --unit        # Fast, no demos needed
python run_tests.py --integration # Requires demo files
python run_tests.py --all --coverage
```

## Coding Conventions

- **Formatting**: Black (88 chars), isort
- **Type hints**: Strict, mypy compatible
- **Models**: Pydantic BaseModel with validation
- **Naming**: CamelCase for models, snake_case for functions
- **Tests**: pytest with markers (unit, integration, slow)
- **Coverage**: 90% requirement

## Related Links

- **This repo**: https://github.com/equilibrium-coach/python-manta
- **PyPI**: https://pypi.org/project/python-manta/
- **Manta (Go)**: https://github.com/dotabuff/manta
- **Dotabuff**: https://www.dotabuff.com
