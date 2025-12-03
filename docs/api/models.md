
# Data Models

??? info "AI Summary"
    All parsed data is returned as Pydantic models for type safety and easy serialization. Models include: `HeaderInfo` (match metadata), `GameInfo`/`DraftEvent`/`PlayerInfo` (game data with draft, teams, players), `UniversalParseResult`/`MessageEvent` (messages), `GameEventsResult`/`GameEventData` (events), `CombatLogResult`/`CombatLogEntry` (combat), `ModifiersResult`/`ModifierEntry` (buffs), `EntitiesResult`/`EntityData` (entities), `StringTablesResult` (tables), `ParserInfo` (state). Enums include `RuneType` (rune tracking), `EntityType` (hero, creep, summon, building), `CombatLogType` (45 combat log event types), `DamageType` (physical/magical/pure), `Team` (Radiant/Dire), `NeutralItemTier` (tier unlock times), `NeutralItem` (100+ neutral items), `ChatWheelMessage` (voice line IDs), and `GameActivity` (animation/taunt detection). All models have `.model_dump()` for dict conversion and `.model_dump_json()` for JSON.

---

## Enums

### RuneType

Enum for Dota 2 power rune types with helper methods for combat log analysis.

```python
class RuneType(str, Enum):
    DOUBLE_DAMAGE = "modifier_rune_doubledamage"
    HASTE = "modifier_rune_haste"
    ILLUSION = "modifier_rune_illusion"
    INVISIBILITY = "modifier_rune_invis"
    REGENERATION = "modifier_rune_regen"
    ARCANE = "modifier_rune_arcane"
    SHIELD = "modifier_rune_shield"
    WATER = "modifier_rune_water"
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable name (e.g., "Double Damage") |
| `modifier_name` | str | Combat log modifier name |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_modifier(name)` | `RuneType \| None` | Get RuneType from modifier name |
| `is_rune_modifier(name)` | `bool` | Check if modifier is a rune |
| `all_modifiers()` | `List[str]` | Get all rune modifier names |

**Example:**
```python
from python_manta import RuneType

# Check if a combat log entry is a rune pickup
if RuneType.is_rune_modifier(entry.inflictor_name):
    rune = RuneType.from_modifier(entry.inflictor_name)
    print(f"Picked up {rune.display_name}")

# Direct enum access
print(RuneType.HASTE.display_name)  # "Haste"
print(RuneType.HASTE.modifier_name)  # "modifier_rune_haste"

# Get all rune modifiers for filtering
rune_modifiers = RuneType.all_modifiers()
```

---

### EntityType

Enum for classifying Dota 2 entity types from entity name strings. Useful for filtering combat log entries by attacker/target type.

```python
class EntityType(str, Enum):
    HERO = "hero"
    LANE_CREEP = "lane_creep"
    NEUTRAL_CREEP = "neutral_creep"
    SUMMON = "summon"
    BUILDING = "building"
    WARD = "ward"
    COURIER = "courier"
    ROSHAN = "roshan"
    UNKNOWN = "unknown"
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_hero` | bool | True if this is a hero |
| `is_creep` | bool | True if lane or neutral creep |
| `is_unit` | bool | True if controllable unit (not building/ward) |
| `is_structure` | bool | True if building or ward |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_name(entity_name)` | `EntityType` | Get EntityType from entity name string |

**Example:**
```python
from python_manta import MantaParser, EntityType

parser = MantaParser()
result = parser.parse_combat_log(demo_path, types=[0], max_entries=1000)

for entry in result.entries:
    attacker_type = EntityType.from_name(entry.attacker_name)
    target_type = EntityType.from_name(entry.target_name)

    # Self-buff detection
    is_self = entry.attacker_name == entry.target_name

    # Hero vs hero combat
    if attacker_type.is_hero and target_type.is_hero and not is_self:
        print(f"Hero combat: {entry.attacker_name} -> {entry.target_name}")

    # Hero farming creeps
    if attacker_type.is_hero and target_type.is_creep:
        print(f"Farming: {entry.attacker_name} hit {entry.target_name}")

    # Building damage
    if target_type == EntityType.BUILDING:
        print(f"Structure damage: {entry.target_name}")
```

---

### CombatLogType

Enum for all 45+ combat log event types. Use this instead of magic numbers when filtering combat log entries.

```python
class CombatLogType(int, Enum):
    DAMAGE = 0
    HEAL = 1
    MODIFIER_ADD = 2
    MODIFIER_REMOVE = 3
    DEATH = 4
    ABILITY = 5
    ITEM = 6
    LOCATION = 7
    GOLD = 8
    GAME_STATE = 9
    XP = 10
    PURCHASE = 11
    BUYBACK = 12
    ABILITY_TRIGGER = 13
    PLAYERSTATS = 14
    MULTIKILL = 15
    KILLSTREAK = 16
    TEAM_BUILDING_KILL = 17
    FIRST_BLOOD = 18
    MODIFIER_REFRESH = 19
    NEUTRAL_CAMP_STACK = 20
    PICKUP_RUNE = 21
    REVEALED_INVISIBLE = 22
    HERO_SAVED = 23
    MANA_RESTORED = 24
    HERO_LEVELUP = 25
    BOTTLE_HEAL_ALLY = 26
    ENDGAME_STATS = 27
    INTERRUPT_CHANNEL = 28
    ALLIED_GOLD = 29
    AEGIS_TAKEN = 30
    MANA_DAMAGE = 31
    PHYSICAL_DAMAGE_PREVENTED = 32
    UNIT_SUMMONED = 33
    ATTACK_EVADE = 34
    TREE_CUT = 35
    SUCCESSFUL_SCAN = 36
    END_KILLSTREAK = 37
    BLOODSTONE_CHARGE = 38
    CRITICAL_DAMAGE = 39
    SPELL_ABSORB = 40
    UNIT_TELEPORTED = 41
    KILL_EATER_EVENT = 42
    NEUTRAL_ITEM_EARNED = 43
    TELEPORT_INTERRUPTED = 44
    MODIFIER_STACK_EVENT = 45
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable name (e.g., "Purchase") |
| `is_damage_related` | bool | True if type is damage/heal related |
| `is_modifier_related` | bool | True if type is buff/debuff related |
| `is_economy_related` | bool | True if type is gold/XP/item related |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_value(int)` | `CombatLogType \| None` | Get CombatLogType from integer value |

**Example:**
```python
from python_manta import MantaParser, CombatLogType

parser = MantaParser()

# Use enum instead of magic numbers
result = parser.parse_combat_log(
    demo_path,
    types=[CombatLogType.PURCHASE, CombatLogType.ITEM],
    max_entries=100
)

for entry in result.entries:
    log_type = CombatLogType.from_value(entry.type)
    if log_type == CombatLogType.PURCHASE:
        print(f"{entry.target_name} bought {entry.value_name}")
    elif log_type == CombatLogType.ITEM:
        print(f"{entry.attacker_name} used {entry.inflictor_name}")

# Check type categories
if log_type.is_economy_related:
    print("Economy event")
```

---

### DamageType

Enum for Dota 2 damage types.

```python
class DamageType(int, Enum):
    PHYSICAL = 0
    MAGICAL = 1
    PURE = 2
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable name (e.g., "Physical") |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_value(int)` | `DamageType \| None` | Get DamageType from integer value |

**Example:**
```python
from python_manta import MantaParser, DamageType, CombatLogType

parser = MantaParser()
result = parser.parse_combat_log(demo_path, types=[CombatLogType.DAMAGE], max_entries=100)

for entry in result.entries:
    dmg_type = DamageType.from_value(entry.damage_type)
    if dmg_type == DamageType.PURE:
        print(f"Pure damage: {entry.value} from {entry.inflictor_name}")
```

---

### Team

Enum for Dota 2 team identifiers.

```python
class Team(int, Enum):
    SPECTATOR = 0
    UNASSIGNED = 1
    RADIANT = 2
    DIRE = 3
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable name (e.g., "Radiant") |
| `is_playing` | bool | True if this is an actual playing team |
| `opposite` | `Team \| None` | The opposing team (None for non-playing) |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_value(int)` | `Team \| None` | Get Team from integer value |

**Example:**
```python
from python_manta import MantaParser, Team, CombatLogType

parser = MantaParser()
result = parser.parse_combat_log(demo_path, types=[CombatLogType.DEATH], heroes_only=True)

for entry in result.entries:
    attacker_team = Team.from_value(entry.attacker_team)
    target_team = Team.from_value(entry.target_team)

    if attacker_team and target_team and attacker_team != target_team:
        print(f"{attacker_team.display_name} killed {target_team.display_name} hero")

    # Use opposite property
    if attacker_team == Team.RADIANT:
        enemy = attacker_team.opposite  # Team.DIRE
```

---

### NeutralItemTier

Enum for neutral item tier classification. Tiers unlock at specific game times.

```python
class NeutralItemTier(int, Enum):
    TIER_1 = 0  # Unlocks at 5:00
    TIER_2 = 1  # Unlocks at 15:00
    TIER_3 = 2  # Unlocks at 25:00
    TIER_4 = 3  # Unlocks at 35:00
    TIER_5 = 4  # Unlocks at 55:00
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable name (e.g., "Tier 1") |
| `unlock_time_minutes` | int | Game time in minutes when tier unlocks |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_value(int)` | `NeutralItemTier \| None` | Get tier from integer value (0-4) |

**Example:**
```python
from python_manta import NeutralItemTier

tier = NeutralItemTier.TIER_3
print(f"{tier.display_name} unlocks at {tier.unlock_time_minutes} minutes")
# Output: Tier 3 unlocks at 25 minutes
```

---

### NeutralItem

Comprehensive enum of all Dota 2 neutral items (100+ items), including both active items and retired/rotated items from previous patches. Useful for tracking neutral item pickups and usage.

```python
class NeutralItem(str, Enum):
    # Tier 1 - Current (7.38+)
    CHIPPED_VEST = "item_chipped_vest"
    DORMANT_CURIO = "item_dormant_curio"
    KOBOLD_CUP = "item_kobold_cup"
    # ... 100+ items including retired ones

    # Tier 5 - Retired
    APEX = "item_apex"
    PIRATE_HAT = "item_pirate_hat"
    # etc.
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `item_name` | str | Internal item name (e.g., "item_kobold_cup") |
| `display_name` | str | Human-readable name (e.g., "Kobold Cup") |
| `tier` | int \| None | Item tier (0-4) or None for special items |
| `tier_enum` | NeutralItemTier \| None | Tier as enum |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_item_name(name)` | `NeutralItem \| None` | Get NeutralItem from internal name |
| `is_neutral_item(name)` | `bool` | Check if item name is a neutral item |
| `items_by_tier(tier)` | `List[NeutralItem]` | Get all items of a specific tier |
| `all_item_names()` | `List[str]` | Get all neutral item internal names |

**Example:**
```python
from python_manta import MantaParser, NeutralItem, NeutralItemTier, CombatLogType

parser = MantaParser()

# Track neutral item usage in combat log
result = parser.parse_combat_log(demo_path, types=[CombatLogType.ITEM], max_entries=1000)

for entry in result.entries:
    if NeutralItem.is_neutral_item(entry.inflictor_name):
        item = NeutralItem.from_item_name(entry.inflictor_name)
        print(f"{entry.attacker_name} used {item.display_name} (Tier {item.tier + 1})")

# Get all Tier 1 items
tier1_items = NeutralItem.items_by_tier(0)
print(f"Tier 1 has {len(tier1_items)} items")

# Check unlock times
tier = NeutralItemTier.TIER_3
print(f"{tier.display_name} items unlock at {tier.unlock_time_minutes} minutes")
```

**Tracking Neutral Item Drops:**
```python
# Use CDOTAUserMsg_FoundNeutralItem for neutral item pickups
result = parser.parse_universal(demo_path, "FoundNeutralItem", max_messages=100)

for msg in result.messages:
    player_id = msg.data.get('player_id')
    item_tier = msg.data.get('item_tier')  # 0-4
    tier = NeutralItemTier.from_value(item_tier)
    print(f"Player {player_id} found a {tier.display_name} neutral item")
```

---

### ChatWheelMessage

Enum for Dota 2 chat wheel message IDs. Maps voice line IDs to human-readable text.

```python
class ChatWheelMessage(int, Enum):
    # Standard phrases (0-232)
    OK = 0
    CAREFUL = 1
    GET_BACK = 2
    NEED_WARDS = 3
    STUN_NOW = 4
    HELP = 5
    PUSH_NOW = 6
    WELL_PLAYED = 7
    # ... many more standard phrases
    MY_BAD = 68
    SPACE_CREATED = 71
    BRUTAL_SAVAGE_REKT = 230
    # Dota Plus lines: 11000+
    # TI Battle Pass lines: 120000+
    # TI talent/team lines: 401000+
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable message text |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_id(id)` | `ChatWheelMessage \| None` | Get enum from message ID |
| `describe_id(id)` | `str` | Get description for any ID (including unmapped) |

**Example:**
```python
from python_manta import MantaParser, ChatWheelMessage

parser = MantaParser()
game_info = parser.parse_game_info("match.dem")
players = {i: p.player_name for i, p in enumerate(game_info.players)}

result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatWheel", 100)

for msg in result.messages:
    player_id = msg.data.get('player_id', -1)
    player_name = players.get(player_id, f'Player {player_id}')
    msg_id = msg.data.get('chat_message_id', 0)

    # Use enum for known IDs, describe_id for all
    text = ChatWheelMessage.describe_id(msg_id)
    print(f"{player_name}: {text}")

# Output:
# Malr1ne: TI Battle Pass Voice Line #120009
# AMMAR_THE_F: > Space created
# Malr1ne: My bad
```

---

### GameActivity

Enum for Dota 2 unit animation activity codes. Used in `CDOTAUserMsg_TE_UnitAnimation` messages to identify what animation a unit is playing. Useful for detecting taunts.

```python
class GameActivity(int, Enum):
    # Basic states
    IDLE = 1500
    IDLE_RARE = 1501
    RUN = 1502
    ATTACK = 1503
    ATTACK2 = 1504
    DIE = 1506
    DISABLED = 1509
    # Ability casting
    CAST_ABILITY_1 = 1510
    CAST_ABILITY_2 = 1511
    # ... through CAST_ABILITY_6
    # Channeling
    CHANNEL_ABILITY_1 = 1520
    # ... through CHANNEL_ABILITY_6
    # Taunts
    KILLTAUNT = 1535
    TAUNT = 1536
    TAUNT_SNIPER = 1641
    TAUNT_SPECIAL = 1752
    CUSTOM_TOWER_TAUNT = 1756
```

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `display_name` | str | Human-readable activity name |
| `is_taunt` | bool | True if this is a taunt animation |
| `is_attack` | bool | True if this is an attack animation |
| `is_ability_cast` | bool | True if this is an ability cast |
| `is_channeling` | bool | True if this is a channeling animation |

**Class Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `from_value(int)` | `GameActivity \| None` | Get activity from integer value |
| `get_taunt_activities()` | `List[GameActivity]` | Get all taunt-related activities |

**Example:**
```python
from python_manta import MantaParser, GameActivity

parser = MantaParser()
result = parser.parse_universal("match.dem", "CDOTAUserMsg_TE_UnitAnimation", 10000)

# Find taunts
for msg in result.messages:
    activity_code = msg.data.get('activity', 0)
    activity = GameActivity.from_value(activity_code)

    if activity and activity.is_taunt:
        print(f"Taunt detected at tick {msg.tick}: {activity.display_name}")

# Check activity types
activity = GameActivity.ATTACK
print(activity.is_attack)      # True
print(activity.is_ability_cast) # False
```

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

## Game Info Models

### GameInfo

Complete game information including draft, players, and teams.

```python
class GameInfo(BaseModel):
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
    players: List[PlayerInfo]  # All players in match

    # Draft
    picks_bans: List[DraftEvent]  # Draft sequence

    # Playback info
    playback_time: float       # Total playback time in seconds
    playback_ticks: int        # Total ticks
    playback_frames: int       # Total frames

    success: bool              # Parse success flag
    error: Optional[str]       # Error message if failed
```

### DraftEvent

Single pick or ban event in the draft.

```python
class DraftEvent(BaseModel):
    is_pick: bool    # True for pick, False for ban
    team: int        # 2 = Radiant, 3 = Dire
    hero_id: int     # Hero ID (see Dota 2 Wiki for mappings)
```

### PlayerInfo

Player information from match metadata.

```python
class PlayerInfo(BaseModel):
    hero_name: str           # Hero internal name (e.g., "npc_dota_hero_axe")
    player_name: str         # Player display name
    is_fake_client: bool     # True for bots
    steam_id: int            # Player Steam ID
    team: int                # Team (2=Radiant, 3=Dire)
```

**Example:**
```python
game_info = parser.parse_game_info("match.dem")

# Basic match info
print(f"Match {game_info.match_id}")
print(f"Duration: {game_info.playback_time / 60:.1f} minutes")
winner = "Radiant" if game_info.game_winner == 2 else "Dire"
print(f"Winner: {winner}")

# Team info (pro matches)
if game_info.league_id > 0:
    print(f"League: {game_info.league_id}")
    print(f"{game_info.radiant_team_tag} vs {game_info.dire_team_tag}")

# Players
for player in game_info.players:
    team = "Radiant" if player.team == 2 else "Dire"
    print(f"  {player.player_name} ({team}): {player.hero_name}")

# Draft
radiant_picks = [e for e in game_info.picks_bans if e.is_pick and e.team == 2]
dire_bans = [e for e in game_info.picks_bans if not e.is_pick and e.team == 3]

# Hero IDs: 1=Anti-Mage, 2=Axe, etc.
for pick in radiant_picks:
    print(f"Radiant picked hero {pick.hero_id}")
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
