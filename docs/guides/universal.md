
# Universal Messages Guide

??? info "AI Summary"
    Parse any of 272 message types using `parse_universal()`. Filter by callback name (substring match). Common messages: `CDOTAUserMsg_ChatMessage` (chat), `CDOTAUserMsg_LocationPing` (pings), `CDOTAUserMsg_ItemPurchased` (items), `CDOTAUserMsg_UnitEvent` (abilities), `CDOTAUserMsg_OverheadEvent` (damage numbers). Each message has tick, net_tick, type, and data dict. Always set max_messages to avoid memory issues. Message data structure varies by type.

---

## Overview

The universal parser can extract any of the 272 message callback types from a replay. It's the most flexible parsing method.

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)

for msg in result.messages:
    print(f"[{msg.tick}] {msg.type}: {msg.data}")
```

---

## Message Filtering

### Substring Matching

The filter matches callback names as substrings:

```python
# Matches CDOTAUserMsg_ChatMessage, CDOTAUserMsg_ChatEvent, etc.
chat = parser.parse_universal("match.dem", "Chat", 100)

# Matches CDOTAUserMsg_LocationPing
pings = parser.parse_universal("match.dem", "Ping", 50)

# Matches multiple message types containing "Unit"
units = parser.parse_universal("match.dem", "Unit", 200)
```

### Exact Callback Names

For precise matching, use the full callback name:

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 100)
```

### All Messages

Use empty string to capture all message types (use with caution):

```python
# WARNING: Can produce millions of messages!
all_messages = parser.parse_universal("match.dem", "", 1000)

# See what types were captured
types = set(msg.type for msg in all_messages.messages)
print(f"Captured {len(types)} different message types")
```

---

## Common Message Types

### Chat Messages

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 200)

for msg in result.messages:
    player_id = msg.data.get("source_player_id")
    text = msg.data.get("message_text", "")
    chat_type = msg.data.get("chat_type", 0)  # 1=all, 2=team, etc.

    type_name = {1: "All", 2: "Team", 3: "Spectator"}.get(chat_type, "Unknown")
    print(f"[{msg.tick}] Player {player_id} ({type_name}): {text}")
```

### Map Pings

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_LocationPing", 100)

for msg in result.messages:
    player_id = msg.data.get("player_id")
    ping_data = msg.data.get("location_ping", {})
    x = ping_data.get("x", 0)
    y = ping_data.get("y", 0)
    ping_type = ping_data.get("type", 0)

    print(f"[{msg.tick}] Player {player_id} pinged ({x}, {y}) type={ping_type}")
```

### Item Purchases

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ItemPurchased", 500)

from collections import defaultdict
purchases = defaultdict(list)

for msg in result.messages:
    player_id = msg.data.get("player_id")
    item_id = msg.data.get("item_ability")

    purchases[player_id].append(item_id)

for player_id, items in purchases.items():
    print(f"Player {player_id}: {len(items)} items purchased")
```

### Unit Events (Ability Usage)

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_UnitEvent", 200)

for msg in result.messages:
    event_type = msg.data.get("msg_type", 0)
    entity = msg.data.get("entity_index")

    # Event types: 1=spawn, 2=speech, 3=add_gesture, etc.
    print(f"[{msg.tick}] Entity {entity}: event type {event_type}")
```

### Overhead Events (Damage Numbers)

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_OverheadEvent", 300)

for msg in result.messages:
    event_type = msg.data.get("message_type", 0)
    value = msg.data.get("value", 0)
    target = msg.data.get("target_player_entindex")

    # Types: 1=gold, 2=crit, 3=heal, 4=damage, 5=mana, 6=miss, etc.
    print(f"[{msg.tick}] Type {event_type}: {value} on entity {target}")
```

### Game Rules State

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_GamerulesStateChanged", 20)

for msg in result.messages:
    state = msg.data.get("state", 0)

    state_names = {
        0: "INIT", 1: "WAIT_FOR_PLAYERS_TO_LOAD", 2: "HERO_SELECTION",
        3: "STRATEGY_TIME", 4: "PRE_GAME", 5: "GAME_IN_PROGRESS",
        6: "POST_GAME", 7: "DISCONNECT"
    }
    name = state_names.get(state, f"UNKNOWN({state})")
    print(f"[{msg.tick}] Game state changed to: {name}")
```

---

## Message Data Structure

Each `MessageEvent` contains:

| Field | Type | Description |
|-------|------|-------------|
| `type` | str | Callback name (e.g., "CDOTAUserMsg_ChatMessage") |
| `tick` | int | Game tick when message occurred |
| `net_tick` | int | Network tick |
| `data` | dict | Message-specific payload |
| `timestamp` | int | Unix timestamp in milliseconds (if available) |

The `data` dictionary structure varies by message type.

---

## Message Categories

### User Messages (CDOTAUserMsg_*)

Game events visible to players:
- `CDOTAUserMsg_ChatMessage` - Chat text
- `CDOTAUserMsg_ChatEvent` - Chat events (kills, items)
- `CDOTAUserMsg_LocationPing` - Map pings
- `CDOTAUserMsg_ItemPurchased` - Item buys
- `CDOTAUserMsg_UnitEvent` - Unit actions
- `CDOTAUserMsg_OverheadEvent` - Floating numbers
- `CDOTAUserMsg_ParticleManager` - Visual effects
- `CDOTAUserMsg_CreateLinearProjectile` - Projectiles

### Network Messages (CNETMsg_*)

Low-level network data:
- `CNETMsg_Tick` - Tick sync (very frequent!)
- `CNETMsg_SetConVar` - Console variables
- `CNETMsg_StringCmd` - String commands

### Service Messages (CSVCMsg_*)

Server-to-client:
- `CSVCMsg_ServerInfo` - Server info
- `CSVCMsg_CreateStringTable` - String tables
- `CSVCMsg_UpdateStringTable` - Table updates
- `CSVCMsg_PacketEntities` - Entity updates

### Demo Messages (CDemo*)

Recording-related:
- `CDemoFileHeader` - File header
- `CDemoFileInfo` - Match info
- `CDemoFullPacket` - Full state snapshot

---

## Analysis Examples

### Chat Timeline

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ChatMessage", 500)

print("Chat Timeline:")
print("-" * 60)

for msg in result.messages:
    tick = msg.tick
    player = msg.data.get("source_player_id", "?")
    text = msg.data.get("message_text", "")

    if text:  # Skip empty messages
        print(f"[{tick:>7}] Player {player}: {text}")
```

### Ping Heatmap Data

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_LocationPing", 500)

from collections import defaultdict
ping_locations = defaultdict(int)

for msg in result.messages:
    ping = msg.data.get("location_ping", {})
    # Bucket to 500-unit grid
    x = (ping.get("x", 0) // 500) * 500
    y = (ping.get("y", 0) // 500) * 500
    ping_locations[(x, y)] += 1

print("Ping Hotspots:")
for loc, count in sorted(ping_locations.items(), key=lambda x: -x[1])[:10]:
    print(f"  ({loc[0]}, {loc[1]}): {count} pings")
```

### Message Type Statistics

```python
result = parser.parse_universal("match.dem", "", 10000)

from collections import Counter
type_counts = Counter(msg.type for msg in result.messages)

print("Message Type Distribution:")
for msg_type, count in type_counts.most_common(20):
    print(f"  {msg_type}: {count}")
```

### Item Build Order

```python
result = parser.parse_universal("match.dem", "CDOTAUserMsg_ItemPurchased", 1000)

from collections import defaultdict
player_items = defaultdict(list)

for msg in result.messages:
    player_id = msg.data.get("player_id")
    item_id = msg.data.get("item_ability")

    player_items[player_id].append({
        "tick": msg.tick,
        "item": item_id
    })

# Print build order for each player
for player_id, items in sorted(player_items.items()):
    print(f"\nPlayer {player_id} item order:")
    for i, item in enumerate(items, 1):
        print(f"  {i}. Item {item['item']} at tick {item['tick']}")
```

---

## Performance Warning

!!! warning

    Some message types generate thousands or millions of entries per match. Always set `max_messages` to prevent memory exhaustion.

### High-Frequency Messages

| Message Type | Frequency | Notes |
|--------------|-----------|-------|
| `CNETMsg_Tick` | ~1M+ | Every network tick |
| `CSVCMsg_PacketEntities` | ~500K+ | Entity updates |
| `CDOTAUserMsg_ParticleManager` | ~100K+ | Visual effects |
| `CDOTAUserMsg_OverheadEvent` | ~50K+ | Damage/heal numbers |

### Recommended Limits

```python
# Safe limits for common types
chat = parser.parse_universal("match.dem", "ChatMessage", 1000)
pings = parser.parse_universal("match.dem", "LocationPing", 500)
items = parser.parse_universal("match.dem", "ItemPurchased", 2000)

# For analysis, sample large types
tick_sample = parser.parse_universal("match.dem", "CNETMsg_Tick", 100)
```

---

## All 272 Callbacks Reference

For a complete list of all available callbacks, see the [Callbacks Reference](../reference/callbacks).

Common useful callbacks:

| Callback | Use Case |
|----------|----------|
| `CDOTAUserMsg_ChatMessage` | Player chat |
| `CDOTAUserMsg_LocationPing` | Map pings |
| `CDOTAUserMsg_ItemPurchased` | Item builds |
| `CDOTAUserMsg_UnitEvent` | Unit actions |
| `CDOTAUserMsg_OverheadEvent` | Combat numbers |
| `CDOTAUserMsg_GamerulesStateChanged` | Game phase changes |
| `CDOTAUserMsg_ChatEvent` | Kill/event notifications |
| `CMsgDOTACombatLogEntry` | Detailed combat data |
| `CDemoFileInfo` | Match metadata |
