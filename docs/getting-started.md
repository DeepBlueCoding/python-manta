# Getting Started

??? info "AI Summary"
        This page covers installation and basic usage of Python Manta. Install via `pip install python-manta` (no Go required). For development from source, either download pre-built libraries with `python scripts/download_library.py` or build with Go using `./build.sh`. The main entry point is `Parser(demo_path)` which provides methods for parsing headers, drafts, and any message type from .dem replay files.

---

## Installation

### From PyPI (Recommended)

```bash
pip install python-manta
```

Pre-built wheels include the compiled library for:

- **Linux** x86_64
- **macOS** Intel (x86_64) and Apple Silicon (arm64)
- **Windows** AMD64

No Go installation required when installing from PyPI.

### Version Pinning

Python Manta versions follow the format `X.Y.Z.M-devN` where:

- `X.Y.Z` - Python Manta major/minor/patch
- `M` - Manta (Go) library version compatibility
- `devN` - Development release number

**Always use the latest release for your target Manta version** to get bug fixes and improvements:

```bash
# Latest release for Manta 1.4.5.x (recommended)
pip install "python-manta>=1.4.5,<1.4.6"

# Or use compatible release operator
pip install "python-manta~=1.4.5"

# Exact version (not recommended - misses updates)
pip install "python-manta==1.4.5.2"
```

### From Source

If you're developing or need to build from source:

#### Option 1: Download Pre-built Library

```bash
git clone https://github.com/DeepBlueCoding/python-manta.git
cd python-manta
python scripts/download_library.py
pip install -e '.[dev]'
```

#### Option 2: Build with Go

Requires Go 1.19+ installed.

```bash
git clone https://github.com/DeepBlueCoding/python-manta.git
cd python-manta
git clone https://github.com/dotabuff/manta.git ../manta
./build.sh
pip install -e '.[dev]'
```

### Verify Installation

```bash
python -c "from python_manta import Parser; print('Success!')"
```

---

## Basic Usage

### Import the Library

```python
from python_manta import Parser

# Create a parser instance for a demo file
parser = Parser("match.dem")
```

### Parse Match Header

The header contains match metadata available without parsing the full replay:

```python
result = parser.parse(header=True)
header = result.header

print(f"Map: {header.map_name}")
print(f"Server: {header.server_name}")
print(f"Build: {header.build_num}")
print(f"Network Protocol: {header.network_protocol}")
```

### Parse Game Info (Draft, Players, Teams)

```python
result = parser.parse(game_info=True)
game_info = result.game_info

# Match basics
print(f"Match ID: {game_info.match_id}")
print(f"Winner: {'Radiant' if game_info.game_winner == 2 else 'Dire'}")

# Draft picks and bans
for event in game_info.picks_bans:
    action = "PICK" if event.is_pick else "BAN"
    team = "Radiant" if event.team == 2 else "Dire"
    print(f"{team} {action}: Hero ID {event.hero_id}")

# Team data (pro/league matches)
if game_info.league_id > 0:
    print(f"League: {game_info.league_id}")
    print(f"{game_info.radiant_team_tag} vs {game_info.dire_team_tag}")

# Player info
for player in game_info.players:
    team = "Radiant" if player.team == 2 else "Dire"
    print(f"  {player.player_name} ({team}): {player.hero_name}")
```

### Parse Multiple Data Types in Single Pass

```python
# Parse header and game info together
result = parser.parse(header=True, game_info=True)

print(f"Map: {result.header.map_name}")
print(f"Match ID: {result.game_info.match_id}")
```

### Parse Messages

Use the messages collector to capture any of the 272 supported message types:

```python
# Get chat messages
result = parser.parse(messages={
    "filter": "CDOTAUserMsg_ChatMessage",
    "max_messages": 100
})

for msg in result.messages.messages:
    player = msg.data.get('source_player_id', 'Unknown')
    text = msg.data.get('message_text', '')
    print(f"[{msg.tick}] Player {player}: {text}")
```

---

## Error Handling

```python
from python_manta import Parser

try:
    parser = Parser("match.dem")
    result = parser.parse(header=True)

    if result.success:
        print(f"Parsed: {result.header.map_name}")
    else:
        print("Parse failed")

except FileNotFoundError:
    print("Demo file not found")
except ValueError as e:
    print(f"Invalid file: {e}")
```

---

## Getting Replay Files

Dota 2 replay files (`.dem`) can be obtained from:

1. **Local replays** - `Steam/steamapps/common/dota 2 beta/game/dota/replays/`
2. **OpenDota API** - [api.opendota.com](https://docs.opendota.com/)
3. **Valve API** - Match history endpoints provide replay URLs

Replay files are typically 100-200MB for a full match.

---

## Next Steps

- [API Reference](api/index.md) - Complete method documentation
- [Examples](examples.md) - Real-world code samples
