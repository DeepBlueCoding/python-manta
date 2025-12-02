
# MantaParser

??? info "AI Summary"
    `MantaParser` is the main class for parsing Dota 2 replays. Create an instance with `MantaParser()` and call methods like `parse_header()`, `parse_game_info()`, `parse_universal()`. For specialized data, use `parse_game_events()`, `parse_combat_log()`, `parse_modifiers()`, `query_entities()`, `get_string_tables()`. Use `parse_game_info()` to get match data (draft, teams, players, league). All methods take a file path and return Pydantic models. The same parser instance can be reused for multiple files.

---

## API Levels

MantaParser provides two levels of APIs:

### High-Level APIs (Recommended)

These methods process and structure the raw Manta data, resolving string table indices to names and returning typed Pydantic models:

| Method | Purpose |
|--------|---------|
| `parse_header()` | Demo file metadata |
| `parse_game_info()` | Game data (draft, teams, players, league) |
| `parse_entities()` | Entity snapshots with player stats/positions |
| `parse_game_events()` | Game events with field name resolution |
| `parse_combat_log()` | Combat log with name resolution |
| `parse_modifiers()` | Buff/debuff tracking |
| `query_entities()` | Entity properties at end of replay |
| `get_string_tables()` | String table data |
| `get_parser_info()` | Parser state metadata |

### Low-Level API (Raw Manta Data)

| Method | Purpose |
|--------|---------|
| `parse_universal()` | Raw protobuf messages from any Manta callback |

`parse_universal()` returns data exactly as Manta provides it - raw protobuf message fields serialized to JSON with no processing. Use this when you need access to message types not covered by high-level APIs, or when you need the raw unprocessed data.

---

## Constructor

```python
class MantaParser:
    def __init__(self, library_path: Optional[str] = None)
```

Creates a new parser instance.

**Parameters:**
- `library_path` (optional): Path to the shared library. If not provided, uses the bundled library.

**Example:**
```python
from python_manta import MantaParser

# Use bundled library (recommended)
parser = MantaParser()

# Use custom library path
parser = MantaParser("/path/to/libmanta_wrapper.so")
```

---

## Basic Parsing Methods

### parse_header

```python
def parse_header(self, demo_file_path: str) -> HeaderInfo
```

Parses the demo file header containing match metadata.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file

**Returns:** [`HeaderInfo`](models#headerinfo)

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If parsing fails

**Example:**
```python
header = parser.parse_header("match.dem")

print(f"Map: {header.map_name}")
print(f"Server: {header.server_name}")
print(f"Build: {header.build_num}")
print(f"Protocol: {header.network_protocol}")
```

---

### parse_game_info

```python
def parse_game_info(self, demo_file_path: str) -> GameInfo
```

Parses complete game information including draft, players, and teams.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file

**Returns:** [`GameInfo`](models#gameinfo)

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If parsing fails

**Example:**
```python
game_info = parser.parse_game_info("match.dem")

print(f"Match ID: {game_info.match_id}")
print(f"Game Mode: {game_info.game_mode}")
print(f"Winner: {'Radiant' if game_info.game_winner == 2 else 'Dire'}")

# Team info (pro matches)
if game_info.league_id > 0:
    print(f"League ID: {game_info.league_id}")
    print(f"{game_info.radiant_team_tag} vs {game_info.dire_team_tag}")

# Draft
for event in game_info.picks_bans:
    action = "PICK" if event.is_pick else "BAN"
    team = "Radiant" if event.team == 2 else "Dire"
    print(f"{team} {action}: Hero {event.hero_id}")

# Player info
for player in game_info.players:
    team = "Radiant" if player.team == 2 else "Dire"
    print(f"  {player.player_name} ({team}): {player.hero_name}")
```

---

### parse_entities

```python
def parse_entities(
    self,
    demo_file_path: str,
    interval_ticks: int = 1800,
    max_snapshots: int = 0,
    target_ticks: Optional[List[int]] = None,
    target_heroes: Optional[List[str]] = None,
    entity_classes: Optional[List[str]] = None,
    include_raw: bool = False
) -> EntityParseResult
```

Parses entity state snapshots over time, capturing player stats and positions at regular intervals or specific ticks.

**Parameters:**

- `demo_file_path`: Path to the `.dem` replay file
- `interval_ticks`: Capture snapshot every N ticks (default 1800 ≈ 1 minute at 30 ticks/sec)
- `max_snapshots`: Maximum snapshots to return (0 = unlimited)
- `target_ticks`: Specific ticks to capture (overrides interval_ticks)
- `target_heroes`: Filter to specific hero names (e.g., `["npc_dota_hero_invoker"]`)
- `entity_classes`: Filter to specific entity classes
- `include_raw`: Include raw entity properties in output

**Returns:** [`EntityParseResult`](models#entityparseresult)

**Example:**
```python
# Capture every minute
result = parser.parse_entities("match.dem", interval_ticks=1800, max_snapshots=60)

for snapshot in result.snapshots:
    print(f"Tick {snapshot.tick}:")
    for player in snapshot.players:
        print(f"  {player.hero}: LH={player.last_hits}, DN={player.denies}, Gold={player.gold}")

# Capture at specific ticks
result = parser.parse_entities("match.dem", target_ticks=[30000, 45000, 60000])

# Track specific heroes
result = parser.parse_entities(
    "match.dem",
    target_ticks=[30000],
    target_heroes=["npc_dota_hero_invoker", "npc_dota_hero_antimage"]
)
```

---

## Low-Level API

### parse_universal

```python
def parse_universal(
    self,
    demo_file_path: str,
    message_filter: str = "",
    max_messages: int = 0
) -> UniversalParseResult
```

Low-level API for accessing raw Manta callback data. Returns protobuf messages exactly as Manta provides them, serialized to JSON with no processing or name resolution.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `message_filter`: Callback name filter (substring match, case-sensitive)
- `max_messages`: Maximum messages to return (0 = unlimited)

**Returns:** [`UniversalParseResult`](models#universalparseresult)

**Example:**
```python
# Get chat messages
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

for msg in result.messages:
    print(f"[{msg.tick}] {msg.type}: {msg.data}")

# Get all messages (no filter, limited)
all_msgs = parser.parse_universal("match.dem", "", 1000)

# Filter matches substrings
pings = parser.parse_universal("match.dem", "Ping", 50)  # Matches LocationPing, Ping, etc.
```

!!! warning

    Some message types generate thousands of entries per match (e.g., `CNETMsg_Tick`). Always use `max_messages` to prevent memory issues.

---

## Game Events

### parse_game_events

```python
def parse_game_events(
    self,
    demo_file_path: str,
    event_filter: str = "",
    event_names: List[str] = None,
    max_events: int = 0,
    capture_types: bool = False
) -> GameEventsResult
```

Parses Source 1 legacy game events with typed field access.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `event_filter`: Filter events by name (substring match)
- `event_names`: List of specific event names to capture
- `max_events`: Maximum events to return (0 = unlimited)
- `capture_types`: Include event type definitions in result

**Returns:** [`GameEventsResult`](models#gameeventsresult)

**Example:**
```python
# Get event type definitions
result = parser.parse_game_events("match.dem", capture_types=True, max_events=0)
print(f"Found {len(result.event_types)} event types")

# Filter by event name
combatlog = parser.parse_game_events("match.dem", event_filter="dota_combatlog", max_events=100)

# Get specific events
kills = parser.parse_game_events("match.dem", event_names=["dota_player_kill"], max_events=50)

for event in kills.events:
    print(f"[{event.tick}] {event.name}: {event.fields}")
```

---

## Combat Log

### parse_combat_log

```python
def parse_combat_log(
    self,
    demo_file_path: str,
    types: List[int] = None,
    max_entries: int = 0,
    heroes_only: bool = False
) -> CombatLogResult
```

Parses structured combat log entries with filtering.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `types`: Filter by combat log type IDs (see table below)
- `max_entries`: Maximum entries to return (0 = unlimited)
- `heroes_only`: Only include entries where attacker or target is a hero

**Returns:** [`CombatLogResult`](models#combatlogresult)

**Combat Log Types:**

| ID | Type Name | Description |
|----|-----------|-------------|
| 0 | DAMAGE | Damage dealt |
| 1 | HEAL | Healing received |
| 2 | MODIFIER_ADD | Buff/debuff applied |
| 3 | MODIFIER_REMOVE | Buff/debuff removed |
| 4 | DEATH | Unit death |
| 5 | ABILITY | Ability used |
| 6 | ITEM | Item used |
| 7 | GOLD | Gold gained/lost |
| 8 | GAME_STATE | Game state change |
| 9 | XP | Experience gained |
| 10 | PURCHASE | Item purchased |
| 11 | BUYBACK | Buyback used |

**Example:**
```python
# All combat log entries
result = parser.parse_combat_log("match.dem", max_entries=1000)

# Damage only
damage = parser.parse_combat_log("match.dem", types=[0], max_entries=500)

# Hero kills only
hero_combat = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=500)

for entry in hero_combat.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.type_name}: {entry.attacker_name} -> {entry.target_name} ({entry.value})")
```

!!! note

    Combat log entries only start appearing after ~12-17 minutes into a match due to HLTV broadcast delay. For early game data, use entity queries.

---

## Modifiers

### parse_modifiers

```python
def parse_modifiers(
    self,
    demo_file_path: str,
    max_modifiers: int = 0,
    auras_only: bool = False
) -> ModifiersResult
```

Tracks buffs, debuffs, and auras applied to units.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `max_modifiers`: Maximum modifiers to return (0 = unlimited)
- `auras_only`: Only include aura effects

**Returns:** [`ModifiersResult`](models#modifiersresult)

**Example:**
```python
# All modifiers
result = parser.parse_modifiers("match.dem", max_modifiers=200)

for mod in result.modifiers:
    duration = f"{mod.duration}s" if mod.duration >= 0 else "permanent"
    print(f"[{mod.tick}] Entity {mod.parent}: {duration}, stacks={mod.stack_count}")

# Auras only
auras = parser.parse_modifiers("match.dem", auras_only=True, max_modifiers=100)
```

---

## Entity Queries

### query_entities

```python
def query_entities(
    self,
    demo_file_path: str,
    class_filter: str = "",
    class_names: List[str] = None,
    property_filter: List[str] = None,
    max_entities: int = 0
) -> EntitiesResult
```

Queries entities at the end of the replay by class name and extracts properties.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `class_filter`: Filter by class name (substring match)
- `class_names`: List of specific class names to match
- `property_filter`: Only include these properties (empty = all)
- `max_entities`: Maximum entities to return (0 = unlimited)

**Returns:** [`EntitiesResult`](models#entitiesresult)

**Example:**
```python
# Query hero entities
heroes = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

for hero in heroes.entities:
    health = hero.properties.get("m_iHealth", 0)
    max_hp = hero.properties.get("m_iMaxHealth", 0)
    print(f"{hero.class_name}: {health}/{max_hp} HP")

# Query specific properties
heroes = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth", "m_iMaxHealth", "m_vecOrigin"],
    max_entities=10
)

# Query specific classes
result = parser.query_entities(
    "match.dem",
    class_names=["CDOTA_Unit_Hero_Invoker", "CDOTA_BaseNPC_Tower"],
    max_entities=20
)
```

---

## String Tables

### get_string_tables

```python
def get_string_tables(
    self,
    demo_file_path: str,
    table_names: List[str] = None,
    max_entries: int = 100
) -> StringTablesResult
```

Extracts string table data (player info, baselines, etc.).

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file
- `table_names`: Specific tables to extract (empty = all)
- `max_entries`: Maximum entries per table

**Returns:** [`StringTablesResult`](models#stringtablesresult)

**Common String Tables:**

| Table Name | Contents |
|------------|----------|
| `userinfo` | Player Steam IDs and names |
| `instancebaseline` | Entity baselines |
| `lightstyles` | Light configuration |
| `CombatLogNames` | Combat log name lookups |

**Example:**
```python
# Get all table names
result = parser.get_string_tables("match.dem")
print(f"Tables: {result.table_names}")

# Get player info
userinfo = parser.get_string_tables("match.dem", table_names=["userinfo"], max_entries=20)

for table_name, entries in userinfo.tables.items():
    for entry in entries:
        print(f"[{entry.index}] {entry.key}")
```

---

## Parser Info

### get_parser_info

```python
def get_parser_info(self, demo_file_path: str) -> ParserInfo
```

Gets parser state information after parsing completes.

**Parameters:**
- `demo_file_path`: Path to the `.dem` replay file

**Returns:** [`ParserInfo`](models#parserinfo)

**Example:**
```python
info = parser.get_parser_info("match.dem")

print(f"Final tick: {info.tick}")
print(f"Entity count: {info.entity_count}")
print(f"String tables: {info.string_tables}")
```
