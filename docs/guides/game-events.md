
# Game Events Guide

??? info "AI Summary"
    Dota 2 replays contain 364 Source 1 legacy game events with typed fields. Use `parse_game_events()` to capture events like player kills, rune pickups, tower destructions, and combat log entries. Filter by event name substring or specific names. Events have tick timestamps and typed field dictionaries. Common events: `dota_player_kill`, `dota_combatlog`, `dota_rune_activated`, `dota_tower_kill`, `dota_roshan_kill`. Use `capture_types=True` to get the full event type list.

---

## Overview

Dota 2 replays contain Source 1 legacy game events - structured notifications about game occurrences. There are **364 different event types**, each with specific typed fields.

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_game_events("match.dem", max_events=100)

for event in result.events:
    print(f"[{event.tick}] {event.name}: {event.fields}")
```

---

## Discovering Event Types

To see all available event types:

```python
result = parser.parse_game_events("match.dem", capture_types=True, max_events=0)

print(f"Total event types: {len(result.event_types)}")
for event_type in sorted(result.event_types):
    print(f"  {event_type}")
```

This returns 364 event type names like:
- `dota_player_kill`
- `dota_combatlog`
- `dota_rune_activated`
- `dota_tower_kill`
- `dota_roshan_kill`
- And many more...

---

## Filtering Events

### By Name Substring

```python
# All events containing "kill"
kills = parser.parse_game_events("match.dem", event_filter="kill", max_events=100)

# All combatlog events
combatlog = parser.parse_game_events("match.dem", event_filter="combatlog", max_events=500)

# All rune events
runes = parser.parse_game_events("match.dem", event_filter="rune", max_events=50)
```

### By Specific Event Names

```python
# Only player kills and tower kills
result = parser.parse_game_events(
    "match.dem",
    event_names=["dota_player_kill", "dota_tower_kill"],
    max_events=100
)
```

---

## Common Event Types

### Player Kills

```python
result = parser.parse_game_events("match.dem", event_filter="dota_player_kill", max_events=100)

for event in result.events:
    victim = event.fields.get("victim_userid")
    killer = event.fields.get("killer1_userid")
    print(f"[Tick {event.tick}] Player {killer} killed player {victim}")
```

### Tower Destruction

```python
result = parser.parse_game_events("match.dem", event_filter="dota_tower_kill", max_events=50)

for event in result.events:
    killer = event.fields.get("killer_userid")
    tower = event.fields.get("teamnumber")
    gold = event.fields.get("gold")
    print(f"[Tick {event.tick}] Tower destroyed by player {killer}, gold: {gold}")
```

### Roshan Kills

```python
result = parser.parse_game_events("match.dem", event_filter="dota_roshan_kill", max_events=10)

for event in result.events:
    team = event.fields.get("teamnumber")
    print(f"[Tick {event.tick}] Roshan killed by team {team}")
```

### Rune Activations

```python
result = parser.parse_game_events("match.dem", event_filter="dota_rune_activated", max_events=50)

for event in result.events:
    player = event.fields.get("player_id")
    rune_type = event.fields.get("rune")
    print(f"[Tick {event.tick}] Player {player} activated rune type {rune_type}")
```

### Combat Log Events

```python
result = parser.parse_game_events("match.dem", event_filter="dota_combatlog", max_events=200)

for event in result.events:
    log_type = event.fields.get("type")
    target = event.fields.get("targetname")
    source = event.fields.get("sourcename")
    value = event.fields.get("value")
    print(f"[Tick {event.tick}] Type {log_type}: {source} -> {target} ({value})")
```

---

## Event Field Types

Event fields are automatically typed based on their definition:

| Field Type | Python Type |
|------------|-------------|
| string | str |
| float | float |
| long | int |
| short | int |
| byte | int |
| bool | bool |
| uint64 | int |

---

## Full Event Type List

??? info "AI Summary"
    <summary>All 364 Event Types (click to expand)</summary>

Common Dota 2 events include:

**Player Events:**
- `dota_player_kill`
- `dota_player_deny`
- `dota_player_pick_hero`
- `dota_player_learned_ability`
- `dota_player_used_ability`
- `dota_player_gained_level`
- `dota_player_take_tower_damage`

**Unit Events:**
- `dota_tower_kill`
- `dota_barracks_kill`
- `dota_roshan_kill`
- `dota_courier_lost`
- `dota_npc_goal_reached`

**Item Events:**
- `dota_item_purchased`
- `dota_item_combined`
- `dota_item_picked_up`

**Rune Events:**
- `dota_rune_activated`
- `dota_rune_spawned`
- `dota_bounty_rune_pickup`

**Game State:**
- `dota_match_done`
- `dota_game_state_change`
- `dota_team_kill_credit`
- `game_rules_state_change`

**Combat:**
- `dota_combatlog`
- `dota_player_take_tower_damage`

**Other:**
- `dota_chase_hero`
- `dota_tutorial_*` (various tutorial events)

Use `capture_types=True` to get the complete list for your replay.



---

## Example: Kill Timeline

```python
from python_manta import MantaParser

parser = MantaParser()

# Get all player kills
result = parser.parse_game_events("match.dem", event_filter="dota_player_kill", max_events=500)

print("Kill Timeline:")
print("-" * 50)

for event in result.events:
    tick = event.tick
    killer = event.fields.get("killer1_userid", "Unknown")
    victim = event.fields.get("victim_userid", "Unknown")
    assisters = []

    # Check for assists
    for i in range(2, 6):
        assister = event.fields.get(f"killer{i}_userid")
        if assister:
            assisters.append(str(assister))

    assist_str = f" + {', '.join(assisters)}" if assisters else ""
    print(f"[Tick {tick:6d}] Player {killer}{assist_str} killed Player {victim}")
```

---

## Game Events vs Combat Log

Both provide combat information but differ:

| Aspect | Game Events | Combat Log |
|--------|-------------|------------|
| API | `parse_game_events()` | `parse_combat_log()` |
| Structure | Named events with typed fields | Structured entries with fixed schema |
| Types | 364 event types | 12 log types |
| Best for | High-level events (kills, runes) | Detailed damage/heal analysis |
| Timing | Throughout match | After ~12-17 minutes |

Use game events for discrete occurrences (kills, objectives) and combat log for continuous combat data (DPS, healing).

---

## Performance Tips

1. **Always set `max_events`** - Events can be numerous
2. **Use specific filters** - Narrow down with `event_filter` or `event_names`
3. **Discover first** - Use `capture_types=True` to find relevant events
4. **Combine with other APIs** - Use entity queries for context about players
