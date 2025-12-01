
# Combat Log Guide

??? info "AI Summary"
    Parse structured combat log entries with `parse_combat_log()`. Filter by 12 log types: DAMAGE (0), HEAL (1), MODIFIER_ADD (2), MODIFIER_REMOVE (3), DEATH (4), ABILITY (5), ITEM (6), GOLD (7), GAME_STATE (8), XP (9), PURCHASE (10), BUYBACK (11). Use `heroes_only=True` to filter hero-related entries. Entries include attacker/target names, damage values, timestamps, ability info. Note: Combat log starts appearing ~12-17 minutes into match due to HLTV delay.

---

## Overview

The combat log provides structured data about damage, healing, deaths, and other combat-related events with rich metadata.

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_combat_log("match.dem", max_entries=100)

for entry in result.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.type_name}: {entry.attacker_name} -> {entry.target_name}")
```

---

## Combat Log Types

| ID | Type Name | Description |
|----|-----------|-------------|
| 0 | DAMAGE | Damage dealt to units |
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

---

## Filtering by Type

### Damage Only

```python
result = parser.parse_combat_log("match.dem", types=[0], max_entries=500)

for entry in result.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.attacker_name} dealt {entry.value} damage to {entry.target_name}")
    if entry.inflictor_name:
        print(f"  via {entry.inflictor_name}")
```

### Healing Only

```python
result = parser.parse_combat_log("match.dem", types=[1], max_entries=200)

for entry in result.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.target_name} healed for {entry.value}")
    if entry.inflictor_name:
        print(f"  from {entry.inflictor_name}")
```

### Deaths Only

```python
result = parser.parse_combat_log("match.dem", types=[4], max_entries=100)

for entry in result.entries:
    print(f"[{entry.timestamp:.1f}s] {entry.target_name} was killed by {entry.attacker_name}")
```

### Multiple Types

```python
# Damage and deaths together
result = parser.parse_combat_log("match.dem", types=[0, 4], max_entries=500)

for entry in result.entries:
    if entry.type == 0:
        print(f"[{entry.timestamp:.1f}s] DAMAGE: {entry.attacker_name} -> {entry.target_name} ({entry.value})")
    elif entry.type == 4:
        print(f"[{entry.timestamp:.1f}s] DEATH: {entry.target_name} killed by {entry.attacker_name}")
```

---

## Hero-Only Filtering

Filter to only include entries where the attacker or target is a hero:

```python
result = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=500)

for entry in result.entries:
    hero_indicator = ""
    if entry.is_attacker_hero:
        hero_indicator += "[HERO ATK] "
    if entry.is_target_hero:
        hero_indicator += "[HERO TGT] "

    print(f"{hero_indicator}{entry.attacker_name} -> {entry.target_name}")
```

### Combining Filters

```python
# Hero damage only
result = parser.parse_combat_log(
    "match.dem",
    types=[0],           # Damage
    heroes_only=True,    # Hero involvement
    max_entries=500
)
```

---

## Entry Fields

Each `CombatLogEntry` contains:

### Identity Fields

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Game tick |
| `net_tick` | int | Network tick |
| `type` | int | Combat log type ID |
| `type_name` | str | Human-readable type name |
| `timestamp` | float | Game time in seconds |

### Unit Fields

| Field | Type | Description |
|-------|------|-------------|
| `target_name` | str | Target unit name |
| `target_source_name` | str | Target's source name |
| `attacker_name` | str | Attacker unit name |
| `damage_source_name` | str | Damage source name |
| `inflictor_name` | str | Ability/item that caused this |

### Boolean Flags

| Field | Type | Description |
|-------|------|-------------|
| `is_attacker_illusion` | bool | Attacker is an illusion |
| `is_attacker_hero` | bool | Attacker is a hero |
| `is_target_illusion` | bool | Target is an illusion |
| `is_target_hero` | bool | Target is a hero |
| `is_visible_radiant` | bool | Visible to Radiant team |
| `is_visible_dire` | bool | Visible to Dire team |

### Value Fields

| Field | Type | Description |
|-------|------|-------------|
| `value` | int | Damage/heal value |
| `health` | int | Target health after |
| `stun_duration` | float | Stun duration if applicable |
| `slow_duration` | float | Slow duration if applicable |
| `ability_level` | int | Ability level |
| `xp` | int | XP amount |
| `gold` | int | Gold amount |
| `last_hits` | int | Last hits at time |

### Team Fields

| Field | Type | Description |
|-------|------|-------------|
| `attacker_team` | int | Attacker team ID |
| `target_team` | int | Target team ID |

---

## Common Use Cases

### DPS Analysis

```python
from collections import defaultdict

result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=5000)

damage_dealt = defaultdict(int)

for entry in result.entries:
    if entry.is_attacker_hero:
        damage_dealt[entry.attacker_name] += entry.value

print("Total Damage Dealt by Hero:")
for hero, damage in sorted(damage_dealt.items(), key=lambda x: -x[1]):
    print(f"  {hero}: {damage:,}")
```

### Kill Feed Reconstruction

```python
result = parser.parse_combat_log("match.dem", types=[4], heroes_only=True, max_entries=100)

print("Kill Feed:")
print("-" * 60)

for entry in result.entries:
    timestamp_min = int(entry.timestamp // 60)
    timestamp_sec = int(entry.timestamp % 60)
    print(f"[{timestamp_min:02d}:{timestamp_sec:02d}] {entry.attacker_name} killed {entry.target_name}")
```

### Ability Usage Tracking

```python
from collections import defaultdict

result = parser.parse_combat_log("match.dem", types=[5], max_entries=1000)

ability_usage = defaultdict(int)

for entry in result.entries:
    if entry.inflictor_name:
        ability_usage[entry.inflictor_name] += 1

print("Most Used Abilities:")
for ability, count in sorted(ability_usage.items(), key=lambda x: -x[1])[:20]:
    print(f"  {ability}: {count}")
```

### Gold Economy

```python
from collections import defaultdict

result = parser.parse_combat_log("match.dem", types=[7], max_entries=2000)

gold_gained = defaultdict(int)

for entry in result.entries:
    if entry.is_target_hero:
        gold_gained[entry.target_name] += entry.gold

print("Gold Gained:")
for hero, gold in sorted(gold_gained.items(), key=lambda x: -x[1]):
    print(f"  {hero}: {gold:,}")
```

### Healing Analysis

```python
from collections import defaultdict

result = parser.parse_combat_log("match.dem", types=[1], max_entries=2000)

healing_received = defaultdict(int)
healing_sources = defaultdict(lambda: defaultdict(int))

for entry in result.entries:
    healing_received[entry.target_name] += entry.value
    if entry.inflictor_name:
        healing_sources[entry.target_name][entry.inflictor_name] += entry.value

print("Healing Received:")
for unit, total in sorted(healing_received.items(), key=lambda x: -x[1])[:10]:
    print(f"\n{unit}: {total:,} total")
    for source, amount in sorted(healing_sources[unit].items(), key=lambda x: -x[1])[:3]:
        print(f"    {source}: {amount:,}")
```

---

## Important Notes

!!! warning

    Combat log entries only start appearing after approximately **12-17 minutes** into a match due to HLTV broadcast delay. For early game data, use entity queries instead.

### Timing Considerations

```python
result = parser.parse_combat_log("match.dem", max_entries=10)

if result.entries:
    first_entry = result.entries[0]
    print(f"First combat log entry at: {first_entry.timestamp:.1f}s ({first_entry.timestamp/60:.1f} minutes)")
else:
    print("No combat log entries found - match may be too short")
```

### Illusion Filtering

```python
# Filter out illusion damage for accurate stats
result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=5000)

real_damage = [
    entry for entry in result.entries
    if not entry.is_attacker_illusion and not entry.is_target_illusion
]

print(f"Total entries: {len(result.entries)}")
print(f"Real damage entries (no illusions): {len(real_damage)}")
```

---

## Combat Log vs Game Events

| Aspect | Combat Log | Game Events |
|--------|------------|-------------|
| API | `parse_combat_log()` | `parse_game_events()` |
| Structure | Fixed schema with 25+ fields | Variable fields per event type |
| Types | 12 log types | 364 event types |
| Best for | Detailed damage/heal analysis | Discrete game occurrences |
| Timing | Starts ~12-17 min | Throughout match |
| Filtering | By type ID, heroes_only | By event name |

Use combat log for continuous combat data (DPS, healing totals) and game events for discrete occurrences (tower kills, rune pickups).
