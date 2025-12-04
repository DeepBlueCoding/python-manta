# Parser

??? info "AI Summary"
    `Parser` is the main class for parsing Dota 2 replays. Create an instance with `Parser("match.dem")` and call `parse()` with collectors like `header=True`, `game_info=True`, `messages={...}`. The parser supports single-pass collection of multiple data types. All methods return Pydantic models for type safety.

---

## Constructor

```python
class Parser:
    def __init__(self, demo_path: str, library_path: Optional[str] = None)
```

Creates a new parser instance for a specific demo file.

**Parameters:**
- `demo_path`: Path to the `.dem` replay file
- `library_path` (optional): Path to the shared library. If not provided, uses the bundled library.

**Example:**
```python
from python_manta import Parser

# Create parser for a demo file
parser = Parser("match.dem")

# Use custom library path
parser = Parser("match.dem", library_path="/path/to/libmanta_wrapper.so")
```

---

## Main Method

### parse

```python
def parse(
    self,
    header: bool = False,
    game_info: bool = False,
    messages: Optional[Union[bool, Dict[str, Any]]] = None
) -> ParseResult
```

Parses the demo file with the specified collectors enabled.

**Parameters:**
- `header`: Enable header collector (match metadata)
- `game_info`: Enable game info collector (draft, players, teams)
- `messages`: Enable messages collector. Can be:
  - `True` - collect all messages
  - `{"filter": "...", "max_messages": N}` - filter and limit messages

**Returns:** [`ParseResult`](#parseresult)

**Example:**
```python
# Parse header only
result = parser.parse(header=True)
print(f"Map: {result.header.map_name}")

# Parse multiple collectors in single pass
result = parser.parse(header=True, game_info=True)
print(f"Map: {result.header.map_name}")
print(f"Match ID: {result.game_info.match_id}")

# Parse with message filtering
result = parser.parse(messages={
    "filter": "CDOTAUserMsg_ChatMessage",
    "max_messages": 100
})
for msg in result.messages.messages:
    print(f"[{msg.tick}] {msg.data}")
```

---

## Data Models

### ParseResult

The result returned by `parse()`.

```python
class ParseResult(BaseModel):
    success: bool
    header: Optional[HeaderInfo] = None
    game_info: Optional[GameInfo] = None
    messages: Optional[MessagesResult] = None
```

**Fields:**
- `success`: Whether parsing completed successfully
- `header`: Header data if `header=True` was specified
- `game_info`: Game info if `game_info=True` was specified
- `messages`: Messages if `messages=...` was specified

---

### HeaderInfo

Match metadata from the demo file header.

```python
class HeaderInfo(BaseModel):
    demo_file_stamp: str
    network_protocol: int
    server_name: str
    client_name: str
    map_name: str
    game_directory: str
    fullpackets_version: int
    allow_clientside_entities: bool
    allow_clientside_particles: bool
    addons: str
    demo_version_name: str
    demo_version_guid: str
    build_num: int
    game: int
    server_start_tick: int
```

**Example:**
```python
result = parser.parse(header=True)
header = result.header

print(f"Map: {header.map_name}")
print(f"Server: {header.server_name}")
print(f"Build: {header.build_num}")
```

---

### GameInfo

Complete game information including draft, players, and teams.

```python
class GameInfo(BaseModel):
    match_id: int = 0
    game_mode: int = 0
    game_winner: int = 0
    league_id: int = 0
    radiant_team_id: int = 0
    radiant_team_tag: str = ""
    radiant_team_name: str = ""
    dire_team_id: int = 0
    dire_team_tag: str = ""
    dire_team_name: str = ""
    picks_bans: List[DraftEvent] = []
    players: List[PlayerInfo] = []
```

**Example:**
```python
result = parser.parse(game_info=True)
game_info = result.game_info

print(f"Match ID: {game_info.match_id}")
print(f"Winner: {'Radiant' if game_info.game_winner == 2 else 'Dire'}")

# Players (10 players: 5 Radiant + 5 Dire)
for player in game_info.players:
    team = "Radiant" if player.team == 2 else "Dire"
    print(f"  {player.player_name} ({team}): {player.hero_name}")

# Draft
for event in game_info.picks_bans:
    action = "PICK" if event.is_pick else "BAN"
    team = "Radiant" if event.team == 2 else "Dire"
    print(f"{team} {action}: Hero {event.hero_id}")

# Pro match info
if game_info.league_id > 0:
    print(f"{game_info.radiant_team_tag} vs {game_info.dire_team_tag}")
```

---

### DraftEvent

A single pick or ban event.

```python
class DraftEvent(BaseModel):
    is_pick: bool
    team: int
    hero_id: int
```

**Fields:**
- `is_pick`: True for picks, False for bans
- `team`: 2 for Radiant, 3 for Dire
- `hero_id`: Dota 2 hero ID

---

### PlayerInfo

Information about a player in the match.

```python
class PlayerInfo(BaseModel):
    player_name: str = ""
    hero_name: str = ""       # npc_dota_hero_* format
    is_fake_client: bool = False
    steam_id: int = 0
    team: int = 0             # 2=Radiant, 3=Dire
```

**Fields:**
- `player_name`: Player's display name
- `hero_name`: Hero in `npc_dota_hero_*` format (e.g., "npc_dota_hero_axe")
- `is_fake_client`: True for bots
- `steam_id`: Player's Steam ID (64-bit)
- `team`: 2 for Radiant, 3 for Dire

**Example:**
```python
result = parser.parse(game_info=True)

# List all players with their heroes
for player in result.game_info.players:
    team = "Radiant" if player.team == 2 else "Dire"
    print(f"{player.player_name} ({team}): {player.hero_name}")
    print(f"  Steam ID: {player.steam_id}")
```

---

### MessagesResult

Container for parsed messages.

```python
class MessagesResult(BaseModel):
    messages: List[MessageEvent] = []
    total_captured: int = 0
```

---

### MessageEvent

A single message event from the replay.

```python
class MessageEvent(BaseModel):
    type: str
    tick: int
    net_tick: int
    data: Dict[str, Any]
```

**Fields:**
- `type`: Message type name (e.g., "CDOTAUserMsg_ChatMessage")
- `tick`: Game tick when message occurred
- `net_tick`: Network tick
- `data`: Message payload as dictionary

---

## Message Filtering

The `messages` parameter accepts a dictionary with these options:

| Key | Type | Description |
|-----|------|-------------|
| `filter` | str | Substring match for message types |
| `max_messages` | int | Maximum messages to capture (0 = unlimited) |

**Filter Examples:**
```python
# Chat messages only
result = parser.parse(messages={"filter": "CDOTAUserMsg_ChatMessage"})

# All ping-related messages
result = parser.parse(messages={"filter": "Ping"})

# First 50 messages of any type
result = parser.parse(messages={"max_messages": 50})

# All messages (use with caution - can be large)
result = parser.parse(messages=True)
```

!!! warning
    Some message types generate thousands of entries per match. Always use `max_messages` to prevent memory issues.

---

## Complete Example

```python
from python_manta import Parser, Hero

# Create parser
parser = Parser("match.dem")

# Parse everything in single pass
result = parser.parse(
    header=True,
    game_info=True,
    messages={"filter": "CDOTAUserMsg_ChatMessage", "max_messages": 50}
)

# Access header
print(f"Map: {result.header.map_name}")
print(f"Server: {result.header.server_name}")

# Access draft with Hero enum for readable names
for event in result.game_info.picks_bans:
    if event.is_pick:
        hero_name = Hero(event.hero_id).name
        team = "Radiant" if event.team == 2 else "Dire"
        print(f"{team} picked {hero_name}")

# Access messages
for msg in result.messages.messages:
    print(f"[{msg.tick}] {msg.type}: {msg.data}")
```
