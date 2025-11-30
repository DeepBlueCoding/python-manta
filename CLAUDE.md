# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Python Manta** is a Python wrapper/bindings for the [dotabuff/manta](https://github.com/dotabuff/manta) Go library that parses Dota 2 replay files (`.dem`). It uses CGO to create Python bindings for the Go parser, implementing all 272 Manta callbacks for comprehensive replay data extraction.

**Important**: This is a wrapper library. The actual parsing is done by [dotabuff/manta](https://github.com/dotabuff/manta) - we just provide Python bindings.

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
│  ├── CGO exports (ParseHeader, ParseDraft, ParseUniversal)  │
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
| `go_wrapper/manta_wrapper.go` | CGO exports (ParseHeader, ParseDraft) |
| `go_wrapper/universal_parser.go` | Universal parsing with callback filtering |
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
    CHeroSelectEvent,      # Draft pick/ban event
    CDotaGameInfo,         # Draft information
    MessageEvent,          # Universal message wrapper
    UniversalParseResult,  # Parse result container
    parse_demo_header,     # Quick header parsing
    parse_demo_draft,      # Quick draft parsing
    parse_demo_universal,  # Quick universal parsing
)
```

### Basic Usage Pattern

```python
from python_manta import MantaParser

parser = MantaParser()  # Uses bundled library

# Parse header
header = parser.parse_header("match.dem")
print(f"Map: {header.map_name}, Build: {header.build_num}")

# Parse draft
draft = parser.parse_draft("match.dem")
for pb in draft.picks_bans:
    print(f"{'PICK' if pb.is_pick else 'BAN'}: Hero {pb.hero_id}")

# Parse any message type
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)
for msg in result.messages:
    print(f"[{msg.tick}] {msg.data}")
```

### Common Callback Names

| Use Case | Callback Name |
|----------|---------------|
| Chat messages | `CDOTAUserMsg_ChatMessage` |
| Map pings | `CDOTAUserMsg_LocationPing` |
| Item purchases | `CDOTAUserMsg_ItemPurchased` |
| Combat log | `CMsgDOTACombatLogEntry` |
| Game state | `CDOTAUserMsg_GamerulesStateChanged` |
| Unit events | `CDOTAUserMsg_UnitEvent` |
| Overhead events | `CDOTAUserMsg_OverheadEvent` |
| Demo header | `CDemoFileHeader` |
| Demo info | `CDemoFileInfo` |

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

### Releasing a new version
1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.x.x`
4. Push tag: `git push origin v1.x.x`
5. CI builds and publishes to PyPI

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

- **This repo**: https://github.com/equilibrium-coach/python-manta
- **PyPI**: https://pypi.org/project/python-manta/
- **Manta (Go)**: https://github.com/dotabuff/manta
- **Dotabuff**: https://www.dotabuff.com
