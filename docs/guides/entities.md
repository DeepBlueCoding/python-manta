
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
    for player in snapshot.players:
        print(f"  {player.hero_name}: ({player.position_x:.0f}, {player.position_y:.0f})")
```

### Position at Specific Ticks

Use `target_ticks` to capture state at exact moments:

```python
# Get hero positions at specific ticks
result = parser.parse_entities("match.dem", target_ticks=[30000, 45000, 60000])

for snapshot in result.snapshots:
    print(f"Tick {snapshot.tick}:")
    for player in snapshot.players:
        print(f"  {player.hero_name}: ({player.position_x:.0f}, {player.position_y:.0f})")
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

    if result.snapshots and result.snapshots[0].players:
        victim = result.snapshots[0].players[0]
        print(f"{victim.hero_name} died at ({victim.position_x:.0f}, {victim.position_y:.0f})")
```

### Position Coordinate System

Hero positions use world coordinates centered on the map:

- **X axis**: West (Radiant, negative) to East (Dire, positive)
- **Y axis**: South (negative) to North (positive)
- **Origin (0,0)**: Center of the map
- **Range**: Approximately -8000 to +8000 for both axes

### PlayerState Fields

Each player in a snapshot includes:

| Field | Type | Description |
|-------|------|-------------|
| `player_id` | int | Player slot (0-9) |
| `hero_id` | int | Hero ID |
| `hero_name` | str | Hero name (`npc_dota_hero_*` format) |
| `team` | int | 2=Radiant, 3=Dire |
| `position_x` | float | X world coordinate |
| `position_y` | float | Y world coordinate |
| `health` | int | Current health |
| `max_health` | int | Maximum health |
| `mana` | float | Current mana |
| `max_mana` | float | Maximum mana |
| `last_hits` | int | Last hits |
| `denies` | int | Denies |
| `gold` | int | Current gold |
| `net_worth` | int | Net worth |
| `kills` | int | Kills |
| `deaths` | int | Deaths |
| `assists` | int | Assists |

### Position Data Sources Comparison

| Method | Use Case | Position Data |
|--------|----------|---------------|
| `parse_entities()` | Time-series or specific ticks | ✅ `position_x`, `position_y` |
| `query_entities()` | End-of-game state | ✅ Raw `CBodyComponent.m_cellX/Y` |
| `parse_combat_log()` | Combat events | ❌ `location_x/y` always 0 |
