# Python Manta

**Python bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Dota 2 replay parser**

??? info "AI Summary"
        Python Manta lets you parse Dota 2 replay files (.dem) in Python. Install with `pip install python-manta`. The library wraps the Go-based manta parser and provides:

    - Single-pass parsing for header, game info, and messages
    - 272 message callbacks for any replay data
    - Game events (364 types), combat log, modifiers, entity queries
    - Pydantic models for type-safe data access

    Quick start: `from python_manta import Parser; parser = Parser("match.dem"); result = parser.parse(header=True)`

---

## What is Python Manta?

Python Manta provides Python access to the [Manta](https://github.com/dotabuff/manta) Go library for parsing Dota 2 replay files. All parsing is done by Manta - this library provides:

1. **CGO bindings** - Wraps the Go parser as a shared library
2. **Pythonic API** - Clean, intuitive interface via `Parser`
3. **Type safety** - Pydantic models for all parsed data
4. **Comprehensive access** - All 272 Manta callbacks + specialized APIs

## Installation

```bash
pip install python-manta
```

Pre-built wheels available for Linux, macOS (Intel + Apple Silicon), and Windows.

### Version Pinning

Always use the latest release for your target Manta version:

```bash
# Latest release for Manta 1.4.5.x (recommended)
pip install "python-manta>=1.4.5,<1.4.6"

# Or use compatible release operator
pip install "python-manta~=1.4.5"
```

See [Getting Started](getting-started.md#version-pinning) for version format details.

## Quick Example

```python
from python_manta import Parser

# Create parser for a specific demo file
parser = Parser("match.dem")

# Parse header and game info in a single pass
result = parser.parse(header=True, game_info=True)

# Access header data
print(f"Map: {result.header.map_name}, Build: {result.header.build_num}")

# Access draft picks and bans
for pb in result.game_info.picks_bans:
    action = "PICK" if pb.is_pick else "BAN"
    print(f"{action}: Hero {pb.hero_id}")

# Parse messages separately
result = parser.parse(messages={"filter": "CDOTAUserMsg_ChatMessage", "max_messages": 100})
for msg in result.messages.messages:
    print(f"[{msg.tick}] {msg.data}")
```

## Features Overview

| Feature | Collector | Description |
|---------|-----------|-------------|
| **Header** | `header=True` | Match metadata (map, build, server) |
| **Game Info** | `game_info=True` | Draft, players, teams, league |
| **Messages** | `messages={...}` | Any of 272 message types |

## Documentation

- [Getting Started](getting-started.md) - Installation and first steps
- [API Reference](api/index.md) - Complete API documentation
- [Examples](examples.md) - Real-world code examples
- [Reference](reference/index.md) - Callbacks, game events, combat log

## Links

- [GitHub Repository](https://github.com/DeepBlueCoding/python-manta)
- [PyPI Package](https://pypi.org/project/python-manta/)
- [Original Manta (Go)](https://github.com/dotabuff/manta)
