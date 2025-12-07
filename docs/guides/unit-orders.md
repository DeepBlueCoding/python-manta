
# Unit Orders Guide

??? info "AI Summary"
    Parse player commands using `CDOTAUserMsg_SpectatorPlayerUnitOrders`. Detect attack commands (`order_type=4`) to analyze creep aggro triggers, last-hit patterns, and harass behavior. Each order includes player entity, order type, target, position, and ability. Key for lane mechanics analysis: when a hero issues ATTACK_TARGET on enemy hero within 500 units of enemy creeps, it triggers creep aggro.

---

## Overview

The `CDOTAUserMsg_SpectatorPlayerUnitOrders` callback captures every command a player issues to their units. This is essential for analyzing:

- **Creep aggro triggers** - When players right-click enemy heroes
- **Last-hit patterns** - Attack commands on creeps
- **Ability usage** - Cast orders with targets
- **Movement patterns** - Move and patrol commands
- **Micro decisions** - Multi-unit control

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=10000
)

for msg in result.messages:
    order_type = msg.data.get("order_type", 0)
    target = msg.data.get("target_index", 0)
    print(f"[{msg.tick}] Order {order_type}, target={target}")
```

---

## Message Structure

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `entindex` | int | Entity index of the player/unit issuing the order |
| `order_type` | int | Type of order (see Order Types below) |
| `units` | list[int] | Entity indices of units receiving the order |
| `target_index` | int | Target entity index (for targeted orders) |
| `ability_id` | int | Ability ID (for cast orders) |
| `position` | dict | Target position `{x, y, z}` (for position orders) |
| `queue` | bool | Whether order is queued (shift-click) |
| `sequence_number` | int | Order sequence number |
| `flags` | int | Order flags |

---

## Order Types

The `order_type` field maps to `dotaunitorder_t` enum values:

### Movement Orders

| Value | Name | Description |
|-------|------|-------------|
| 0 | `NONE` | No order |
| 1 | `MOVE_TO_POSITION` | Move to ground position (right-click ground) |
| 2 | `MOVE_TO_TARGET` | Move to/follow a unit |
| 28 | `MOVE_TO_DIRECTION` | Move in direction |
| 29 | `PATROL` | Patrol command |
| 39 | `MOVE_RELATIVE` | Relative movement |

### Attack Orders

| Value | Name | Description |
|-------|------|-------------|
| 3 | `ATTACK_MOVE` | Attack-move (A-click ground) |
| 4 | `ATTACK_TARGET` | Attack specific target (right-click enemy) |

### Ability Orders

| Value | Name | Description |
|-------|------|-------------|
| 5 | `CAST_POSITION` | Cast ability on ground |
| 6 | `CAST_TARGET` | Cast ability on unit |
| 7 | `CAST_TARGET_TREE` | Cast ability on tree |
| 8 | `CAST_NO_TARGET` | Cast ability (no target) |
| 9 | `CAST_TOGGLE` | Toggle ability |
| 20 | `CAST_TOGGLE_AUTO` | Toggle autocast |
| 40 | `CAST_TOGGLE_ALT` | Alt toggle |

### Control Orders

| Value | Name | Description |
|-------|------|-------------|
| 10 | `HOLD_POSITION` | Hold position (H key) |
| 21 | `STOP` | Stop command (S key) |
| 33 | `CONTINUE` | Continue previous order |

### Item Orders

| Value | Name | Description |
|-------|------|-------------|
| 12 | `DROP_ITEM` | Drop item on ground |
| 13 | `GIVE_ITEM` | Give item to ally |
| 14 | `PICKUP_ITEM` | Pick up item |
| 15 | `PICKUP_RUNE` | Pick up rune |
| 16 | `PURCHASE_ITEM` | Purchase item |
| 17 | `SELL_ITEM` | Sell item |
| 18 | `DISASSEMBLE_ITEM` | Disassemble item |
| 19 | `MOVE_ITEM` | Move item in inventory |
| 41 | `CONSUME_ITEM` | Consume item |

### Other Orders

| Value | Name | Description |
|-------|------|-------------|
| 11 | `TRAIN_ABILITY` | Level up ability |
| 22 | `TAUNT` | Taunt |
| 23 | `BUYBACK` | Buyback |
| 24 | `GLYPH` | Activate glyph |
| 26 | `CAST_RUNE` | Use bottle on rune |
| 27 | `PING_ABILITY` | Ping ability cooldown |
| 30 | `VECTOR_TARGET_POSITION` | Vector targeted ability |
| 31 | `RADAR` | Scan ability |

---

## Creep Aggro Detection

### How Creep Aggro Works in Dota 2

Creep aggro is triggered when:
1. A hero issues an **attack command** (`order_type=4`) on an enemy hero
2. The hero is within **500 units** of enemy lane creeps
3. This puts creeps on a **2.5 second aggro cooldown**

### Detecting Aggro Triggers

```python
from python_manta import MantaParser

parser = MantaParser()

# Get all attack orders
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

ATTACK_TARGET = 4

attack_commands = []
for msg in orders.messages:
    order_type = msg.data.get("order_type", 0)

    if order_type == ATTACK_TARGET:
        attack_commands.append({
            "tick": msg.tick,
            "player_entity": msg.data.get("entindex"),
            "target_entity": msg.data.get("target_index"),
            "units": msg.data.get("units", []),
            "queued": msg.data.get("queue", False),
        })

print(f"Found {len(attack_commands)} attack commands")
```

### Identifying Hero-on-Hero Attacks

To determine if an attack triggers creep aggro, you need to:
1. Check if the attacker is a hero
2. Check if the target is an enemy hero
3. Check proximity to enemy creeps (requires entity position data)

```python
from python_manta import MantaParser

parser = MantaParser()

# Get attack orders
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

# Get entity data to identify heroes
entities = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    max_entities=20
)

# Build hero entity index set
hero_entities = {e.index for e in entities.entities}

ATTACK_TARGET = 4

potential_aggro_triggers = []
for msg in orders.messages:
    if msg.data.get("order_type") != ATTACK_TARGET:
        continue

    target = msg.data.get("target_index", 0)

    # Check if target is a hero (potential aggro trigger)
    if target in hero_entities:
        potential_aggro_triggers.append({
            "tick": msg.tick,
            "attacker": msg.data.get("entindex"),
            "target_hero": target,
        })

print(f"Potential aggro triggers: {len(potential_aggro_triggers)}")
```

### Full Aggro Analysis with Positions

For complete aggro analysis, combine orders with entity snapshots:

```python
from python_manta import MantaParser
import math

parser = MantaParser()

# Parse attack orders
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

# Get attack target orders
ATTACK_TARGET = 4
attack_ticks = []

for msg in orders.messages:
    if msg.data.get("order_type") == ATTACK_TARGET:
        attack_ticks.append(msg.tick)

# Sample entity positions at attack moments
# Use unique ticks to avoid duplicates
unique_ticks = sorted(set(attack_ticks))[:100]  # Limit for performance

if unique_ticks:
    snapshots = parser.parse_entities(
        "match.dem",
        target_ticks=unique_ticks,
        max_snapshots=100
    )

    # Analyze each snapshot for creep proximity
    AGGRO_RANGE = 500

    for snapshot in snapshots.snapshots:
        # Get hero positions
        heroes = {h.hero_name: (h.x, h.y) for h in snapshot.heroes if h.hero_name}

        # Would need creep positions from entity data
        # This is a simplified example
        print(f"Tick {snapshot.tick}: {len(heroes)} heroes tracked")
```

---

## Lane Mechanics Analysis

### Last-Hit Pattern Detection

```python
from python_manta import MantaParser
from collections import defaultdict

parser = MantaParser()
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=100000
)

ATTACK_TARGET = 4
ATTACK_MOVE = 3

player_attacks = defaultdict(list)

for msg in orders.messages:
    order_type = msg.data.get("order_type", 0)

    if order_type in [ATTACK_TARGET, ATTACK_MOVE]:
        player = msg.data.get("entindex")
        player_attacks[player].append({
            "tick": msg.tick,
            "type": "target" if order_type == ATTACK_TARGET else "move",
            "target": msg.data.get("target_index"),
        })

# Analyze attack patterns
for player, attacks in player_attacks.items():
    target_attacks = [a for a in attacks if a["type"] == "target"]
    move_attacks = [a for a in attacks if a["type"] == "move"]

    print(f"Player entity {player}:")
    print(f"  Direct attacks: {len(target_attacks)}")
    print(f"  Attack-moves: {len(move_attacks)}")
```

### Harass Timing Analysis

Analyze when players harass vs last-hit:

```python
from python_manta import MantaParser

parser = MantaParser()

# Get orders and combat log for correlation
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

# Filter to laning phase (first 10 minutes ~ 18000 ticks at 30 ticks/sec)
LANING_END_TICK = 18000
ATTACK_TARGET = 4

laning_attacks = []
for msg in orders.messages:
    if msg.tick > LANING_END_TICK:
        break

    if msg.data.get("order_type") == ATTACK_TARGET:
        laning_attacks.append({
            "tick": msg.tick,
            "player": msg.data.get("entindex"),
            "target": msg.data.get("target_index"),
        })

print(f"Laning phase attacks: {len(laning_attacks)}")

# Group by time windows (30 second intervals)
from collections import defaultdict
TICKS_PER_30_SEC = 900

time_windows = defaultdict(int)
for attack in laning_attacks:
    window = attack["tick"] // TICKS_PER_30_SEC
    time_windows[window] += 1

print("\nAttack frequency by 30-second windows:")
for window, count in sorted(time_windows.items()):
    minutes = (window * 30) // 60
    seconds = (window * 30) % 60
    print(f"  {minutes}:{seconds:02d}: {count} attacks")
```

---

## Multi-Unit Control Analysis

For heroes with summons or illusions:

```python
from python_manta import MantaParser

parser = MantaParser()
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

# Find orders with multiple units
multi_unit_orders = []
for msg in orders.messages:
    units = msg.data.get("units", [])
    if len(units) > 1:
        multi_unit_orders.append({
            "tick": msg.tick,
            "order_type": msg.data.get("order_type"),
            "unit_count": len(units),
            "units": units,
        })

print(f"Multi-unit orders: {len(multi_unit_orders)}")

# Analyze micro patterns
from collections import Counter
order_types = Counter(o["order_type"] for o in multi_unit_orders)
print("\nMulti-unit order types:")
for order_type, count in order_types.most_common():
    print(f"  Type {order_type}: {count}")
```

---

## Queued Commands Analysis

Detect shift-queued commands:

```python
from python_manta import MantaParser

parser = MantaParser()
orders = parser.parse_universal(
    "match.dem",
    "CDOTAUserMsg_SpectatorPlayerUnitOrders",
    max_messages=50000
)

queued_orders = []
for msg in orders.messages:
    if msg.data.get("queue", False):
        queued_orders.append({
            "tick": msg.tick,
            "order_type": msg.data.get("order_type"),
            "player": msg.data.get("entindex"),
        })

print(f"Queued orders: {len(queued_orders)}")
print(f"Queue usage rate: {len(queued_orders) / len(orders.messages) * 100:.1f}%")
```

---

## Performance Considerations

!!! warning "High Volume Callback"

    `CDOTAUserMsg_SpectatorPlayerUnitOrders` fires frequently - expect 10,000-50,000+ messages per match. Always set `max_messages` appropriately.

### Recommended Limits

```python
# For full match analysis
orders = parser.parse_universal("match.dem", "SpectatorPlayerUnitOrders", 100000)

# For laning phase only
orders = parser.parse_universal("match.dem", "SpectatorPlayerUnitOrders", 20000)

# For sampling/overview
orders = parser.parse_universal("match.dem", "SpectatorPlayerUnitOrders", 5000)
```

### Efficient Filtering

Filter early to reduce memory:

```python
ATTACK_TARGET = 4
ATTACK_MOVE = 3

# Process in batches if needed
attack_orders = []
result = parser.parse_universal("match.dem", "SpectatorPlayerUnitOrders", 50000)

for msg in result.messages:
    order_type = msg.data.get("order_type", 0)
    if order_type in [ATTACK_TARGET, ATTACK_MOVE]:
        attack_orders.append(msg)

# Now work with filtered subset
print(f"Attack orders: {len(attack_orders)} of {len(result.messages)} total")
```

---

## Related APIs

| Task | API |
|------|-----|
| Entity positions | `parse_entities()` |
| Combat damage | `parse_combat_log()` |
| Hero state | `query_entities(class_filter="Hero")` |
| Ability usage | `parse_universal("CDOTAUserMsg_UnitEvent")` |

---

## Order Type Reference

Complete `dotaunitorder_t` enum:

```
0  = DOTA_UNIT_ORDER_NONE
1  = DOTA_UNIT_ORDER_MOVE_TO_POSITION
2  = DOTA_UNIT_ORDER_MOVE_TO_TARGET
3  = DOTA_UNIT_ORDER_ATTACK_MOVE
4  = DOTA_UNIT_ORDER_ATTACK_TARGET
5  = DOTA_UNIT_ORDER_CAST_POSITION
6  = DOTA_UNIT_ORDER_CAST_TARGET
7  = DOTA_UNIT_ORDER_CAST_TARGET_TREE
8  = DOTA_UNIT_ORDER_CAST_NO_TARGET
9  = DOTA_UNIT_ORDER_CAST_TOGGLE
10 = DOTA_UNIT_ORDER_HOLD_POSITION
11 = DOTA_UNIT_ORDER_TRAIN_ABILITY
12 = DOTA_UNIT_ORDER_DROP_ITEM
13 = DOTA_UNIT_ORDER_GIVE_ITEM
14 = DOTA_UNIT_ORDER_PICKUP_ITEM
15 = DOTA_UNIT_ORDER_PICKUP_RUNE
16 = DOTA_UNIT_ORDER_PURCHASE_ITEM
17 = DOTA_UNIT_ORDER_SELL_ITEM
18 = DOTA_UNIT_ORDER_DISASSEMBLE_ITEM
19 = DOTA_UNIT_ORDER_MOVE_ITEM
20 = DOTA_UNIT_ORDER_CAST_TOGGLE_AUTO
21 = DOTA_UNIT_ORDER_STOP
22 = DOTA_UNIT_ORDER_TAUNT
23 = DOTA_UNIT_ORDER_BUYBACK
24 = DOTA_UNIT_ORDER_GLYPH
25 = DOTA_UNIT_ORDER_EJECT_ITEM_FROM_STASH
26 = DOTA_UNIT_ORDER_CAST_RUNE
27 = DOTA_UNIT_ORDER_PING_ABILITY
28 = DOTA_UNIT_ORDER_MOVE_TO_DIRECTION
29 = DOTA_UNIT_ORDER_PATROL
30 = DOTA_UNIT_ORDER_VECTOR_TARGET_POSITION
31 = DOTA_UNIT_ORDER_RADAR
32 = DOTA_UNIT_ORDER_SET_ITEM_COMBINE_LOCK
33 = DOTA_UNIT_ORDER_CONTINUE
34 = DOTA_UNIT_ORDER_VECTOR_TARGET_CANCELED
35 = DOTA_UNIT_ORDER_CAST_RIVER_PAINT
36 = DOTA_UNIT_ORDER_PREGAME_ADJUST_ITEM_ASSIGNMENT
37 = DOTA_UNIT_ORDER_DROP_ITEM_AT_FOUNTAIN
38 = DOTA_UNIT_ORDER_TAKE_ITEM_FROM_NEUTRAL_ITEM_STASH
39 = DOTA_UNIT_ORDER_MOVE_RELATIVE
40 = DOTA_UNIT_ORDER_CAST_TOGGLE_ALT
41 = DOTA_UNIT_ORDER_CONSUME_ITEM
42 = DOTA_UNIT_ORDER_SET_ITEM_MARK_FOR_SELL
```
