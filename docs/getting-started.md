# Getting Started

??? info "AI Summary"
        This page covers installation and basic usage of Python Manta. Install via `pip install python-manta` (no Go required). For development from source, either download pre-built libraries with `python scripts/download_library.py` or build with Go using `./build.sh`. The main entry point is `MantaParser()` which provides methods for parsing headers, drafts, and any message type from .dem replay files.

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
python -c "from python_manta import MantaParser; print('Success!')"
```

---

## Basic Usage

### Import the Library

```python
from python_manta import MantaParser

# Create a parser instance
parser = MantaParser()
```

### Parse Match Header

The header contains match metadata available without parsing the full replay:

```python
header = parser.parse_header("match.dem")

print(f"Map: {header.map_name}")
print(f"Server: {header.server_name}")
print(f"Build: {header.build_num}")
print(f"Network Protocol: {header.network_protocol}")
```

### Parse Game Info (Draft, Players, Teams)

```python
game_info = parser.parse_game_info("match.dem")

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

### Parse Any Message Type

Use `parse_universal()` to capture any of the 272 supported message types:

```python
# Get chat messages
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

for msg in result.messages:
    player = msg.data.get('source_player_id', 'Unknown')
    text = msg.data.get('message_text', '')
    print(f"[{msg.tick}] Player {player}: {text}")
```

---

## Error Handling

```python
from python_manta import MantaParser

parser = MantaParser()

try:
    header = parser.parse_header("match.dem")

    if header.success:
        print(f"Parsed: {header.map_name}")
    else:
        print(f"Parse error: {header.error}")

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
- [Game Events Guide](guides/game-events.md) - Parse 364 event types
- [Combat Log Guide](guides/combat-log.md) - Analyze damage and kills
- [Examples](examples.md) - Real-world code samples
