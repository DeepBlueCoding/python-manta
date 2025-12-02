
# Data Models

??? info "AI Summary"
    All parsed data is returned as Pydantic models for type safety and easy serialization. Models include: `HeaderInfo` (match metadata), `CDotaGameInfo`/`CHeroSelectEvent` (draft), `CDotaGameInfo`/`CPlayerInfo` (pro match data with teams, league, players), `UniversalParseResult`/`MessageEvent` (messages), `GameEventsResult`/`GameEventData` (events), `CombatLogResult`/`CombatLogEntry` (combat), `ModifiersResult`/`ModifierEntry` (buffs), `EntitiesResult`/`EntityData` (entities), `StringTablesResult` (tables), `ParserInfo` (state). All have `.model_dump()` for dict conversion and `.model_dump_json()` for JSON.

---

## Header Models

### HeaderInfo

Match header metadata from the demo file.

```python
class HeaderInfo(BaseModel):
    map_name: str              # Map name (e.g., "dota")
    server_name: str           # Server identifier
    client_name: str           # Client type
    game_directory: str        # Game directory path
    network_protocol: int      # Network protocol version
    demo_file_stamp: str       # Demo file signature
    build_num: int             # Game build number
    game: str                  # Game identifier
    server_start_tick: int     # Server start tick
    success: bool              # Parse success flag
    error: Optional[str]       # Error message if failed
```

**Example:**
```python
header = parser.parse_header("match.dem")

# Access fields
print(header.map_name)
print(header.build_num)

# Convert to dict
data = header.model_dump()

# Convert to JSON
json_str = header.model_dump_json()
```

---

## Draft Models

### CDotaGameInfo

Draft information containing picks and bans.

```python
class CDotaGameInfo(BaseModel):
    picks_bans: List[CHeroSelectEvent]  # Draft sequence
    success: bool                        # Parse success flag
    error: Optional[str]                 # Error message if failed
```

### CHeroSelectEvent

Single pick or ban event in the draft.

```python
class CHeroSelectEvent(BaseModel):
    is_pick: bool    # True for pick, False for ban
    team: int        # 2 = Radiant, 3 = Dire
    hero_id: int     # Hero ID (see Dota 2 Wiki for mappings)
```

**Example:**
```python
draft = parser.parse_draft("match.dem")

radiant_picks = [e for e in draft.picks_bans if e.is_pick and e.team == 2]
dire_bans = [e for e in draft.picks_bans if not e.is_pick and e.team == 3]

# Hero IDs: 1=Anti-Mage, 2=Axe, etc.
for pick in radiant_picks:
    print(f"Radiant picked hero {pick.hero_id}")
```

---

## Match Info Models

### CDotaGameInfo

Complete match information including pro match data.

```python
class CDotaGameInfo(BaseModel):
    # Basic match info
    match_id: int              # Match ID
    game_mode: int             # Game mode ID
    game_winner: int           # Winner (2=Radiant, 3=Dire)
    league_id: int             # League ID (0 for pub matches)
    end_time: int              # End time (Unix timestamp)

    # Team info (pro matches only - 0/empty for pubs)
    radiant_team_id: int       # Radiant team ID
    dire_team_id: int          # Dire team ID
    radiant_team_tag: str      # Radiant team tag (e.g., "OG")
    dire_team_tag: str         # Dire team tag (e.g., "Secret")

    # Players
    players: List[CPlayerInfo]  # All players in match

    # Draft
    picks_bans: List[CHeroSelectEvent]  # Draft sequence

    # Playback info
    playback_time: float       # Total playback time in seconds
    playback_ticks: int        # Total ticks
    playback_frames: int       # Total frames

    success: bool              # Parse success flag
    error: Optional[str]       # Error message if failed

    def is_pro_match(self) -> bool:
        """Check if this is a pro/league match."""
```

### CPlayerInfo

Player information from match metadata.

```python
class CPlayerInfo(BaseModel):
    hero_name: str           # Hero internal name (e.g., "npc_dota_hero_axe")
    player_name: str         # Player display name
    is_fake_client: bool     # True for bots
    steamid: int             # Player Steam ID
    game_team: int           # Team (2=Radiant, 3=Dire)
```

**Example:**
```python
match = parser.parse_game_info("match.dem")

# Basic match info
print(f"Match {match.match_id}")
print(f"Duration: {match.playback_time / 60:.1f} minutes")
winner = "Radiant" if match.game_winner == 2 else "Dire"
print(f"Winner: {winner}")

# Pro match info
if match.is_pro_match():
    print(f"League: {match.league_id}")
    print(f"{match.radiant_team_tag} vs {match.dire_team_tag}")

# Players
for player in match.players:
    team = "Radiant" if player.game_team == 2 else "Dire"
    print(f"  {player.player_name} ({team}): {player.hero_name}")
```

---

## Universal Parse Models

### UniversalParseResult

Result container for `parse_universal()`.

```python
class UniversalParseResult(BaseModel):
    messages: List[MessageEvent]  # Matched messages
    success: bool                 # Parse success flag
    error: Optional[str]          # Error message if failed
    count: int                    # Number of messages
```

### MessageEvent

Single message from the replay.

```python
class MessageEvent(BaseModel):
    type: str                    # Callback name (e.g., "CDOTAUserMsg_ChatMessage")
    tick: int                    # Game tick when message occurred
    net_tick: int                # Network tick
    data: Any                    # Message-specific data (dict)
    timestamp: Optional[int]     # Unix timestamp in milliseconds
```

**Example:**
```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

for msg in result.messages:
    # Access common fields
    print(f"Type: {msg.type}")
    print(f"Tick: {msg.tick}")

    # Access message-specific data
    player_id = msg.data.get('source_player_id')
    text = msg.data.get('message_text')
```

---

## Game Events Models

### GameEventsResult

Result container for `parse_game_events()`.

```python
class GameEventsResult(BaseModel):
    events: List[GameEventData]  # Parsed events
    event_types: List[str]       # Event type definitions (if capture_types=True)
    success: bool                # Parse success flag
    error: Optional[str]         # Error message if failed
    total_events: int            # Total events captured
```

### GameEventData

Single game event with typed fields.

```python
class GameEventData(BaseModel):
    name: str                     # Event name (e.g., "dota_combatlog")
    tick: int                     # Game tick
    net_tick: int                 # Network tick
    fields: Dict[str, Any]        # Event-specific fields
```

**Example:**
```python
result = parser.parse_game_events("match.dem", event_filter="dota_player_kill", max_events=50)

for event in result.events:
    print(f"Event: {event.name}")
    print(f"Tick: {event.tick}")

    # Fields depend on event type
    for field_name, value in event.fields.items():
        print(f"  {field_name}: {value}")
```

---

## Combat Log Models

### CombatLogResult

Result container for `parse_combat_log()`.

```python
class CombatLogResult(BaseModel):
    entries: List[CombatLogEntry]  # Combat log entries
    success: bool                  # Parse success flag
    error: Optional[str]           # Error message if failed
    total_entries: int             # Total entries captured
```

### CombatLogEntry

Single combat log entry with structured data.

```python
class CombatLogEntry(BaseModel):
    tick: int                     # Game tick
    net_tick: int                 # Network tick
    type: int                     # Combat log type ID
    type_name: str                # Human-readable type name
    target_name: str              # Target unit name
    target_source_name: str       # Target source name
    attacker_name: str            # Attacker unit name
    damage_source_name: str       # Damage source name
    inflictor_name: str           # Ability/item that caused this
    is_attacker_illusion: bool    # Attacker is illusion
    is_attacker_hero: bool        # Attacker is a hero
    is_target_illusion: bool      # Target is illusion
    is_target_hero: bool          # Target is a hero
    is_visible_radiant: bool      # Visible to Radiant
    is_visible_dire: bool         # Visible to Dire
    value: int                    # Damage/heal value
    health: int                   # Target health after
    timestamp: float              # Game time in seconds
    stun_duration: float          # Stun duration if applicable
    slow_duration: float          # Slow duration if applicable
    is_ability_toggle_on: bool    # Ability toggled on
    is_ability_toggle_off: bool   # Ability toggled off
    ability_level: int            # Ability level
    xp: int                       # XP reason/amount
    gold: int                     # Gold reason/amount
    last_hits: int                # Last hits at time
    attacker_team: int            # Attacker team ID
    target_team: int              # Target team ID
```

**Example:**
```python
result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=100)

for entry in result.entries:
    if entry.type == 0:  # DAMAGE
        print(f"[{entry.timestamp:.1f}s] {entry.attacker_name} hit {entry.target_name} for {entry.value}")
```

---

## Modifier Models

### ModifiersResult

Result container for `parse_modifiers()`.

```python
class ModifiersResult(BaseModel):
    modifiers: List[ModifierEntry]  # Modifier entries
    success: bool                   # Parse success flag
    error: Optional[str]            # Error message if failed
    total_modifiers: int            # Total modifiers captured
```

### ModifierEntry

Single modifier/buff entry.

```python
class ModifierEntry(BaseModel):
    tick: int               # Game tick
    net_tick: int           # Network tick
    parent: int             # Entity handle of unit with modifier
    caster: int             # Entity handle of caster
    ability: int            # Ability that created modifier
    modifier_class: int     # Modifier class ID
    serial_num: int         # Serial number
    index: int              # Modifier index
    creation_time: float    # When modifier was created
    duration: float         # Duration in seconds (-1 = permanent)
    stack_count: int        # Number of stacks
    is_aura: bool           # Whether it's an aura
    is_debuff: bool         # Whether it's a debuff
```

**Example:**
```python
result = parser.parse_modifiers("match.dem", max_modifiers=100)

for mod in result.modifiers:
    duration_str = f"{mod.duration}s" if mod.duration >= 0 else "permanent"
    print(f"Entity {mod.parent}: duration={duration_str}, stacks={mod.stack_count}")
```

---

## Entity Models

### EntitiesResult

Result container for `query_entities()`.

```python
class EntitiesResult(BaseModel):
    entities: List[EntityData]  # Entity data
    success: bool               # Parse success flag
    error: Optional[str]        # Error message if failed
    total_entities: int         # Total entities returned
    tick: int                   # Tick when captured
    net_tick: int               # Network tick when captured
```

### EntityData

Single entity with properties.

```python
class EntityData(BaseModel):
    index: int                    # Entity index
    serial: int                   # Entity serial number
    class_name: str               # Entity class name
    properties: Dict[str, Any]    # Entity properties
```

**Common Hero Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `m_iHealth` | int | Current health |
| `m_iMaxHealth` | int | Maximum health |
| `m_flMana` | float | Current mana |
| `m_flMaxMana` | float | Maximum mana |
| `m_vecOrigin` | list | Position [x, y, z] |
| `m_iCurrentLevel` | int | Hero level |
| `m_iTotalEarnedGold` | int | Total gold earned |
| `m_iKills` | int | Kills |
| `m_iDeaths` | int | Deaths |
| `m_iAssists` | int | Assists |

**Example:**
```python
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

for entity in result.entities:
    print(f"\n{entity.class_name} (index={entity.index})")
    print(f"  Health: {entity.properties.get('m_iHealth')}/{entity.properties.get('m_iMaxHealth')}")
    print(f"  Level: {entity.properties.get('m_iCurrentLevel')}")
```

---

## String Table Models

### StringTablesResult

Result container for `get_string_tables()`.

```python
class StringTablesResult(BaseModel):
    tables: Dict[str, List[StringTableData]]  # Table name -> entries
    table_names: List[str]                    # List of table names
    success: bool                             # Parse success flag
    error: Optional[str]                      # Error message if failed
    total_entries: int                        # Total entries
```

### StringTableData

Single string table entry.

```python
class StringTableData(BaseModel):
    table_name: str         # Table name
    index: int              # Entry index
    key: str                # Entry key
    value: Optional[str]    # Entry value (may be binary/base64)
```

---

## Parser Info Model

### ParserInfo

Parser state information.

```python
class ParserInfo(BaseModel):
    game_build: int           # Game build number
    tick: int                 # Final parser tick
    net_tick: int             # Final network tick
    string_tables: List[str]  # List of string table names
    entity_count: int         # Number of entities
    success: bool             # Parse success flag
    error: Optional[str]      # Error message if failed
```

**Example:**
```python
info = parser.get_parser_info("match.dem")

print(f"Game lasted {info.tick} ticks")
print(f"Final entity count: {info.entity_count}")
print(f"String tables: {', '.join(info.string_tables)}")
```

---

## Serialization

All models support Pydantic serialization:

```python
# To dictionary
data = model.model_dump()

# To JSON string
json_str = model.model_dump_json()

# From dictionary
model = HeaderInfo.model_validate(data)

# From JSON
model = HeaderInfo.model_validate_json(json_str)
```
