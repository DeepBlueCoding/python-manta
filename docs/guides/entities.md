
# Entity Queries Guide

??? info "AI Summary"
    Query game entities using `query_entities()`. Filter by class name (substring or exact match) and select specific properties. Use `at_tick` to query at a specific game tick (default: end of game). Common classes: `Hero` (player heroes), `Tower`, `Courier`, `Creep`, `CDOTA_Item_MagicStick`, `CDOTA_Item_MagicWand`. Hero properties include `m_iHealth`, `m_iMaxHealth`, `m_flMana`, `m_vecOrigin` (position). Item properties include `m_iCurrentCharges`, `m_iPlayerOwnerID`. Use property_filter for performance.

---

## Overview

Entity queries let you extract game state from the replay, including hero stats, positions, items, and unit properties.

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

for entity in result.entities:
    health = entity.properties.get("m_iHealth", 0)
    max_hp = entity.properties.get("m_iMaxHealth", 0)
    print(f"{entity.class_name}: {health}/{max_hp} HP")
```

---

## Filtering by Class

### Substring Filter

```python
# All entities with "Hero" in class name
heroes = parser.query_entities("match.dem", class_filter="Hero", max_entities=20)

# All tower entities
towers = parser.query_entities("match.dem", class_filter="Tower", max_entities=30)

# All courier entities
couriers = parser.query_entities("match.dem", class_filter="Courier", max_entities=10)
```

### Exact Class Names

```python
# Specific hero classes
result = parser.query_entities(
    "match.dem",
    class_names=[
        "CDOTA_Unit_Hero_Invoker",
        "CDOTA_Unit_Hero_Pudge",
        "CDOTA_Unit_Hero_AntiMage"
    ],
    max_entities=10
)

# Specific building types
buildings = parser.query_entities(
    "match.dem",
    class_names=[
        "CDOTA_BaseNPC_Tower",
        "CDOTA_BaseNPC_Barracks",
        "CDOTA_BaseNPC_Fort"
    ],
    max_entities=50
)
```

---

## Property Filtering

For better performance, specify only the properties you need:

```python
# Only get health and position
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth", "m_iMaxHealth", "m_vecOrigin"],
    max_entities=10
)

for entity in result.entities:
    pos = entity.properties.get("m_vecOrigin", [0, 0, 0])
    print(f"{entity.class_name} at ({pos[0]:.0f}, {pos[1]:.0f})")
```

---

## Common Entity Classes

| Class Pattern | Description |
|---------------|-------------|
| `Hero` | Player-controlled heroes |
| `Tower` | Tower buildings |
| `Barracks` | Barracks buildings |
| `Fort` | Ancient/Throne |
| `Courier` | Courier units |
| `Creep` | Lane creeps |
| `NeutralCreep` | Jungle creeps |
| `Roshan` | Roshan |
| `Ward` | Observer/Sentry wards |

---

## Hero Properties

### Core Stats

| Property | Type | Description |
|----------|------|-------------|
| `m_iHealth` | int | Current health |
| `m_iMaxHealth` | int | Maximum health |
| `m_flMana` | float | Current mana |
| `m_flMaxMana` | float | Maximum mana |
| `m_iCurrentLevel` | int | Hero level |
| `m_flStrength` | float | Strength attribute |
| `m_flAgility` | float | Agility attribute |
| `m_flIntellect` | float | Intelligence attribute |

### Position and Movement

| Property | Type | Description |
|----------|------|-------------|
| `m_vecOrigin` | list[float] | Position [x, y, z] |
| `m_angRotation` | list[float] | Rotation angles |
| `m_flMovementSpeed` | float | Movement speed |

### Economy

| Property | Type | Description |
|----------|------|-------------|
| `m_iTotalEarnedGold` | int | Total gold earned |
| `m_iUnreliableGold` | int | Unreliable gold |
| `m_iReliableGold` | int | Reliable gold |
| `m_iLastHits` | int | Last hits |
| `m_iDenies` | int | Denies |

### KDA

| Property | Type | Description |
|----------|------|-------------|
| `m_iKills` | int | Kills |
| `m_iDeaths` | int | Deaths |
| `m_iAssists` | int | Assists |

### Combat

| Property | Type | Description |
|----------|------|-------------|
| `m_flPhysicalArmorValue` | float | Armor |
| `m_flMagicalResistanceValue` | float | Magic resistance |
| `m_iDamageMin` | int | Minimum damage |
| `m_iDamageMax` | int | Maximum damage |
| `m_iAttackRange` | int | Attack range |

---

## Common Use Cases

### End Game Scoreboard

```python
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=[
        "m_iCurrentLevel",
        "m_iKills", "m_iDeaths", "m_iAssists",
        "m_iTotalEarnedGold", "m_iLastHits", "m_iDenies"
    ],
    max_entities=10
)

print("End Game Scoreboard:")
print("-" * 70)
print(f"{'Hero':<30} {'Lvl':>4} {'K':>3} {'D':>3} {'A':>3} {'LH':>5} {'Gold':>8}")
print("-" * 70)

for entity in result.entities:
    props = entity.properties
    print(f"{entity.class_name:<30} "
          f"{props.get('m_iCurrentLevel', 0):>4} "
          f"{props.get('m_iKills', 0):>3} "
          f"{props.get('m_iDeaths', 0):>3} "
          f"{props.get('m_iAssists', 0):>3} "
          f"{props.get('m_iLastHits', 0):>5} "
          f"{props.get('m_iTotalEarnedGold', 0):>8,}")
```

### Hero Positions Map

```python
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_vecOrigin", "m_iTeamNum"],
    max_entities=10
)

print("Hero Positions (end of game):")
for entity in result.entities:
    pos = entity.properties.get("m_vecOrigin", [0, 0, 0])
    team = entity.properties.get("m_iTeamNum", 0)
    team_name = "Radiant" if team == 2 else "Dire" if team == 3 else "Unknown"

    print(f"{entity.class_name}: ({pos[0]:.0f}, {pos[1]:.0f}) - {team_name}")
```

### Building Status

```python
# Check tower status
towers = parser.query_entities(
    "match.dem",
    class_filter="Tower",
    property_filter=["m_iHealth", "m_iMaxHealth", "m_iTeamNum"],
    max_entities=30
)

print("Tower Status:")
radiant_towers = 0
dire_towers = 0

for tower in towers.entities:
    health = tower.properties.get("m_iHealth", 0)
    max_health = tower.properties.get("m_iMaxHealth", 0)
    team = tower.properties.get("m_iTeamNum", 0)

    if health > 0:
        if team == 2:
            radiant_towers += 1
        elif team == 3:
            dire_towers += 1

print(f"Radiant towers remaining: {radiant_towers}")
print(f"Dire towers remaining: {dire_towers}")
```

### Item Slots

```python
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=[
        "m_hItems.0000", "m_hItems.0001", "m_hItems.0002",
        "m_hItems.0003", "m_hItems.0004", "m_hItems.0005"
    ],
    max_entities=10
)

for entity in result.entities:
    print(f"\n{entity.class_name} items:")
    for i in range(6):
        item_handle = entity.properties.get(f"m_hItems.{i:04d}")
        if item_handle and item_handle != 16777215:  # Invalid handle
            print(f"  Slot {i}: {item_handle}")
```

### Neutral Creeps

```python
result = parser.query_entities(
    "match.dem",
    class_filter="NeutralCreep",
    property_filter=["m_iHealth", "m_iMaxHealth", "m_vecOrigin"],
    max_entities=50
)

alive_creeps = [e for e in result.entities if e.properties.get("m_iHealth", 0) > 0]
print(f"Neutral creeps alive: {len(alive_creeps)}")
```

---

## Entity Data Structure

Each `EntityData` object contains:

```python
class EntityData(BaseModel):
    index: int                    # Entity index
    serial: int                   # Entity serial number
    class_name: str               # Entity class name (e.g., "CDOTA_Unit_Hero_Invoker")
    properties: Dict[str, Any]    # Entity properties
```

The `properties` dictionary contains all requested or available properties for the entity.

---

## Result Information

The `EntitiesResult` includes metadata:

```python
result = parser.query_entities("match.dem", class_filter="Hero", max_entities=10)

print(f"Total entities returned: {result.total_entities}")
print(f"Captured at tick: {result.tick}")
print(f"Network tick: {result.net_tick}")
print(f"Parse success: {result.success}")
```

---

## Performance Tips

1. **Use property_filter** - Specify only needed properties to reduce memory and processing
2. **Use class_names for exact matches** - More efficient than substring filter
3. **Set max_entities** - Limit results when you only need a few entities
4. **Query once, process multiple times** - Entity queries are at end of replay, cache results

```python
# Efficient: specific properties
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth", "m_iKills"],
    max_entities=10
)

# Less efficient: all properties
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    max_entities=10
)
```

---

## Querying at Specific Ticks

Use the `at_tick` parameter to query entity state at a specific game tick instead of end of game:

```python
# Query heroes at tick 50000
result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth", "m_iMaxHealth"],
    at_tick=50000,
    max_entities=10
)

print(f"Hero health at tick {result.tick}:")
for entity in result.entities:
    health = entity.properties.get("m_iHealth", 0)
    max_hp = entity.properties.get("m_iMaxHealth", 0)
    print(f"  {entity.class_name}: {health}/{max_hp}")
```

### Item Charges at Specific Time

Get Magic Stick/Wand charges for all players at a specific tick:

```python
from python_manta import MantaParser

parser = MantaParser()

def get_magic_stick_charges(demo_path: str, at_tick: int = 0) -> dict:
    """
    Get magic stick/wand charges for all players at a specific game tick.

    Args:
        demo_path: Path to the .dem file
        at_tick: Game tick to query (0 = end of game)

    Returns:
        Dict mapping player_id -> charges
    """
    result = parser.query_entities(
        demo_path,
        class_names=['CDOTA_Item_MagicStick', 'CDOTA_Item_MagicWand'],
        property_filter=['m_iCurrentCharges', 'm_iPlayerOwnerID'],
        at_tick=at_tick
    )

    player_charges = {}
    for entity in result.entities:
        owner = entity.properties.get('m_iPlayerOwnerID', -1)
        charges = entity.properties.get('m_iCurrentCharges', 0)
        if owner >= 0:
            player_charges[owner] = max(player_charges.get(owner, 0), charges)

    return player_charges

# Get charges at tick 50000
charges = get_magic_stick_charges("match.dem", at_tick=50000)
# {0: 6, 2: 18, 4: 7, 6: 6, 8: 1, 10: 15, 12: 4, 14: 20, 16: 0, 18: 5}
```

---

## Important Notes

!!! note

    By default (`at_tick=0`), entity queries return the state at the **end of the replay**. Use `at_tick` to query state at a specific game tick.

### Entity Handles

Some properties reference other entities via handles:

```python
# Item handles reference item entities
item_handle = hero.properties.get("m_hItems.0000")

# These are internal entity references, not item IDs
# Use string tables or item events for item identification
```

### Team Numbers

| Team ID | Team |
|---------|------|
| 2 | Radiant |
| 3 | Dire |
| 0/1 | Neutral/Spectator |

---

## Hero Position Tracking with parse_entities()

For tracking hero positions over time (not just end of game), use `parse_entities()` instead of `query_entities()`.

### Basic Position Tracking

```python
from python_manta import MantaParser

parser = MantaParser()

# Capture snapshots every 30 seconds (900 ticks at 30 ticks/sec)
result = parser.parse_entities("match.dem", interval_ticks=900, max_snapshots=100)

for snapshot in result.snapshots:
    print(f"Game time: {snapshot.game_time:.1f}s")
    for hero in snapshot.heroes:
        print(f"  {hero.hero_name}: ({hero.x:.0f}, {hero.y:.0f})")
```

### Position at Specific Ticks

Use `target_ticks` to capture state at exact moments:

```python
# Get hero positions at specific ticks
result = parser.parse_entities("match.dem", target_ticks=[30000, 45000, 60000])

for snapshot in result.snapshots:
    print(f"Tick {snapshot.tick}:")
    for hero in snapshot.heroes:
        print(f"  {hero.hero_name}: ({hero.x:.0f}, {hero.y:.0f})")
```

### Filtering by Hero

Use `target_heroes` to only get specific heroes. Use the `npc_dota_hero_*` format (same as combat log):

```python
# Get only specific heroes
result = parser.parse_entities(
    "match.dem",
    target_ticks=[50000],
    target_heroes=["npc_dota_hero_axe", "npc_dota_hero_lina"]
)
```

### Getting Death Positions

Combat log `location_x`/`location_y` are **always 0**. To get death positions, combine combat log with entity snapshots:

```python
# Get deaths from combat log
combat = parser.parse_combat_log("match.dem", types=[1])  # type 1 = deaths

for death in combat.entries:
    # Get victim's position at death tick
    result = parser.parse_entities(
        "match.dem",
        target_ticks=[death.tick],
        target_heroes=[death.target_name]  # e.g., "npc_dota_hero_axe"
    )

    if result.snapshots and result.snapshots[0].heroes:
        victim = result.snapshots[0].heroes[0]
        print(f"{victim.hero_name} died at ({victim.x:.0f}, {victim.y:.0f})")
```

### Position Coordinate System

Hero positions use world coordinates centered on the map:

- **X axis**: West (Radiant, negative) to East (Dire, positive)
- **Y axis**: South (negative) to North (positive)
- **Origin (0,0)**: Center of the map
- **Range**: Approximately -8000 to +8000 for both axes

### HeroSnapshot Fields

Each hero in a snapshot includes:

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | int | Player slot (0-9) |
| `hero_id` | int | Hero ID |
| `hero_name` | str | Hero name (`npc_dota_hero_*` format) |
| `team` | int | 2=Radiant, 3=Dire |
| `x` | float | X world coordinate |
| `y` | float | Y world coordinate |
| `health` | int | Current health |
| `max_health` | int | Maximum health |
| `mana` | float | Current mana |
| `max_mana` | float | Maximum mana |
| `level` | int | Hero level |
| `last_hits` | int | Last hits |
| `denies` | int | Denies |
| `gold` | int | Current gold |
| `net_worth` | int | Net worth |
| `gpm` | int | Gold per minute |
| `xpm` | int | XP per minute |
| `kills` | int | Kills |
| `deaths` | int | Deaths |
| `assists` | int | Assists |
| `armor` | float | Current armor |
| `magic_resistance` | float | Magic resistance (0-1) |
| `damage_min` | int | Minimum damage |
| `damage_max` | int | Maximum damage |
| `strength` | float | Strength attribute |
| `agility` | float | Agility attribute |
| `intellect` | float | Intellect attribute |
| `abilities` | list | List of `AbilitySnapshot` |
| `talents` | list | List of `TalentChoice` |
| `is_illusion` | bool | True if illusion |
| `is_clone` | bool | True if clone (e.g., Meepo) |

### Position Data Sources Comparison

| Method | Use Case | Position Data |
|--------|----------|---------------|
| `parse_entities()` | Time-series or specific ticks | ✅ `position_x`, `position_y` |
| `query_entities()` | End-of-game state | ✅ Raw `CBodyComponent.m_cellX/Y` |
| `parse_combat_log()` | Combat events | ❌ `location_x/y` always 0 |

---

## Hero Abilities and Talents

The `parser.snapshot()` method returns hero state including abilities and talent choices.

### Basic Ability Tracking

```python
from python_manta import Parser

parser = Parser("match.dem")
snap = parser.snapshot(target_tick=60000)  # ~33 minutes

for hero in snap.heroes:
    print(f"{hero.hero_name} (Level {hero.level})")

    # Show all abilities
    for ability in hero.abilities:
        if ability.level > 0:
            print(f"  {ability.short_name}: Level {ability.level}")
```

### Ability Properties

Each `AbilitySnapshot` includes:

| Field | Type | Description |
|-------|------|-------------|
| `slot` | int | Ability slot (0-5 for regular abilities) |
| `name` | str | Full ability class name |
| `level` | int | Current ability level (0-4) |
| `cooldown` | float | Current cooldown remaining |
| `max_cooldown` | float | Maximum cooldown length |
| `mana_cost` | int | Mana cost |
| `charges` | int | Current charges |
| `is_ultimate` | bool | True if slot 5 (ultimate) |

**Helper Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `short_name` | str | Name without "CDOTA_Ability_" prefix |
| `is_maxed` | bool | True if at max level |
| `is_on_cooldown` | bool | True if cooldown > 0 |

### Talent Tracking

Talents are tracked separately from abilities:

```python
snap = parser.snapshot(target_tick=120000)  # Late game

for hero in snap.heroes:
    print(f"{hero.hero_name}: {hero.talents_chosen}/4 talents")

    for talent in hero.talents:
        print(f"  Level {talent.tier}: {talent.side}")
```

Each `TalentChoice` includes:

| Field | Type | Description |
|-------|------|-------------|
| `tier` | int | Talent tier (10, 15, 20, or 25) |
| `slot` | int | Raw ability slot index |
| `is_left` | bool | True if left talent chosen |
| `name` | str | Talent ability name |
| `side` | str | "left" or "right" |

### Finding Specific Abilities

Use helper methods to find abilities:

```python
for hero in snap.heroes:
    # Find ability by name (partial match)
    omnislash = hero.get_ability("Omnislash")
    if omnislash and omnislash.level > 0:
        print(f"Omnislash level {omnislash.level}")

    # Check if ultimate is learned
    if hero.has_ultimate:
        print("Has ultimate!")

    # Get talent at specific tier
    lvl20_talent = hero.get_talent_at_tier(20)
    if lvl20_talent:
        print(f"Level 20 talent: {lvl20_talent.side}")
```

### Tracking Skill Builds Over Time

Combine multiple snapshots to track skill progression:

```python
from python_manta import Parser

parser = Parser("match.dem")

# Get snapshots at different times
ticks = [30000, 60000, 90000, 120000]

for tick in ticks:
    snap = parser.snapshot(target_tick=tick)

    for hero in snap.heroes:
        if "Juggernaut" in hero.hero_name:
            print(f"Tick {tick} - Level {hero.level}")
            for ab in hero.abilities:
                if ab.level > 0:
                    print(f"  {ab.short_name}: {ab.level}")
            break
```

### Cooldown Analysis

Track ability cooldowns for timing analysis:

```python
snap = parser.snapshot(target_tick=60000)

for hero in snap.heroes:
    print(f"\n{hero.hero_name} cooldowns:")
    for ability in hero.abilities:
        if ability.is_on_cooldown:
            print(f"  {ability.short_name}: {ability.cooldown:.1f}s remaining")
        elif ability.level > 0:
            print(f"  {ability.short_name}: ready")
```

---

## Pre-Horn Positions

Entity snapshots can capture hero positions **before the horn sounds** (during the strategy phase). Pre-horn snapshots have negative `game_time` values.

### Basic Pre-Horn Tracking

```python
from python_manta import Parser

parser = Parser("match.dem")

# Parse with interval that captures pre-horn
result = parser.parse(entities={'interval_ticks': 900, 'max_snapshots': 20})

for snap in result.entities.snapshots:
    if snap.game_time < 0:
        print(f"Pre-horn ({snap.game_time_str}): {len(snap.heroes)} heroes")
        for hero in snap.heroes:
            print(f"  {hero.hero_name} at ({hero.x:.0f}, {hero.y:.0f})")
```

### Understanding Pre-Horn Time

| `game_time` | Meaning |
|-------------|---------|
| `-90.0` | 1 minute 30 seconds before horn |
| `-45.0` | 45 seconds before horn |
| `0.0` | Horn sounds (game starts) |
| `60.0` | 1 minute into the game |

### Game Start Tick

The `game_start_tick` field tells you when the horn sounded:

```python
result = parser.parse(entities={'interval_ticks': 1800})

print(f"Game started at tick: {result.entities.game_start_tick}")

# All snapshots with tick < game_start_tick are pre-horn
for snap in result.entities.snapshots:
    if snap.tick < result.entities.game_start_tick:
        print(f"Pre-horn snapshot at tick {snap.tick}")
```

---

## Creep Positions

Track lane and neutral creep positions with the `include_creeps` option.

!!! warning "Performance Note"
    Including creeps significantly increases data volume. A typical snapshot may have 100-200 creeps vs 10 heroes. Use judiciously.

### Basic Creep Tracking

```python
from python_manta import Parser

parser = Parser("match.dem")

# Enable creep tracking
result = parser.parse(entities={
    'interval_ticks': 1800,
    'max_snapshots': 10,
    'include_creeps': True
})

for snap in result.entities.snapshots:
    lane_creeps = [c for c in snap.creeps if c.is_lane]
    neutral_creeps = [c for c in snap.creeps if c.is_neutral]
    print(f"{snap.game_time_str}: {len(lane_creeps)} lane, {len(neutral_creeps)} neutral creeps")
```

### CreepSnapshot Fields

Each creep in `snapshot.creeps` includes:

| Field | Type | Description |
|-------|------|-------------|
| `entity_id` | int | Entity index |
| `class_name` | str | Entity class (e.g., `CDOTA_BaseNPC_Creep_Lane`) |
| `name` | str | Unit name (may be empty) |
| `team` | int | 2=Radiant, 3=Dire, 4=Neutral |
| `x` | float | X world coordinate |
| `y` | float | Y world coordinate |
| `health` | int | Current health |
| `max_health` | int | Maximum health |
| `is_lane` | bool | True for lane creeps |
| `is_neutral` | bool | True for neutral creeps |

### Filtering Creeps by Team

```python
for snap in result.entities.snapshots:
    radiant_creeps = [c for c in snap.creeps if c.team == 2]
    dire_creeps = [c for c in snap.creeps if c.team == 3]
    neutral_creeps = [c for c in snap.creeps if c.team == 4]

    print(f"{snap.game_time_str}:")
    print(f"  Radiant creeps: {len(radiant_creeps)}")
    print(f"  Dire creeps: {len(dire_creeps)}")
    print(f"  Neutral creeps: {len(neutral_creeps)}")
```

### Creep Wave Analysis

```python
# Track creep waves by position
for snap in result.entities.snapshots:
    if snap.game_time < 0:
        continue  # Skip pre-horn

    # Group lane creeps by approximate lane position
    for creep in snap.creeps:
        if creep.is_lane and creep.team == 2:  # Radiant lane creeps
            # Mid lane is roughly where x ≈ y
            # Top lane: high y, low x
            # Bot lane: low y, high x
            if abs(creep.x - creep.y) < 2000:
                lane = "mid"
            elif creep.y > creep.x:
                lane = "top"
            else:
                lane = "bot"
            print(f"Radiant creep at ({creep.x:.0f}, {creep.y:.0f}) - {lane} lane")
```
