
# Attacks Reference

??? info "AI Summary"
    Complete reference for attack projectile parsing from TE_Projectile messages. Captures ALL auto-attacks in the game: hero attacks, tower attacks on creeps, creep-on-creep attacks, and neutral aggro. Each event contains source/target entity indices, projectile speed, and timing. Typically 15,000+ events per match with 87% being non-hero attacks (towers, creeps, neutrals).

---

## Overview

The attacks collector parses `TE_Projectile` messages with `is_attack=True`, capturing all auto-attack projectiles in the game. This data is NOT available in the combat log, which only records damage/kill events.

**Key Use Cases:**

- Tower attacks on creeps (not in combat log)
- Neutral creep aggro tracking
- Creep-on-creep combat analysis
- Hero attack patterns

---

## Attack Event Fields

Every `AttackEvent` contains these fields:

### Timing

| Field | Type | Description |
|-------|------|-------------|
| `tick` | `int` | Game tick (~30/second) |
| `game_time` | `float` | Game time in seconds from horn |
| `game_time_str` | `str` | Formatted time (e.g., "15:34") |
| `launch_tick` | `int` | Tick when projectile was launched |

### Entities

| Field | Type | Description |
|-------|------|-------------|
| `source_index` | `int` | Entity index of attacker |
| `target_index` | `int` | Entity index of target |
| `source_handle` | `int` | Raw entity handle (advanced use) |
| `target_handle` | `int` | Raw entity handle (advanced use) |

### Projectile

| Field | Type | Description |
|-------|------|-------------|
| `projectile_speed` | `int` | Projectile move speed |
| `dodgeable` | `bool` | Can be disjointed |

---

## Basic Usage

```python
from python_manta import Parser

parser = Parser("match.dem")

# Collect all attack events
result = parser.parse(attacks={})

print(f"Total attacks: {result.attacks.total_events}")
for attack in result.attacks.events[:10]:
    print(f"[{attack.game_time_str}] Entity {attack.source_index} -> {attack.target_index}")
```

### Limiting Events

```python
# First 1000 attacks only
result = parser.parse(attacks={"max_events": 1000})
```

---

## Entity Index Mapping

Entity indices identify units in the game. To map indices to names:

```python
# Get hero entity indices from snapshot
snap = parser.snapshot(target_tick=60000)
hero_indices = {h.index: h.hero_name for h in snap.heroes}

# Classify attacks
for attack in result.attacks.events:
    source_name = hero_indices.get(attack.source_index, f"entity_{attack.source_index}")
    target_name = hero_indices.get(attack.target_index, f"entity_{attack.target_index}")
    print(f"{source_name} -> {target_name}")
```

### Entity Index Ranges (Approximate)

| Range | Typical Units |
|-------|---------------|
| 300-600 | Heroes |
| 600-800 | Towers, buildings |
| 1000+ | Creeps, summons, other units |

---

## Use Case Examples

### Tower Attack Tracking

```python
result = parser.parse(attacks={})

# Entity 725 is typically Dire T1 top tower
tower_attacks = [e for e in result.attacks.events if e.source_index == 725]
print(f"Tower attacks: {len(tower_attacks)}")

# Find all tower attacks (entities in 600-800 range)
possible_towers = [e for e in result.attacks.events if 600 <= e.source_index <= 800]
print(f"Possible tower attacks: {len(possible_towers)}")
```

### Neutral Aggro Analysis

```python
result = parser.parse(attacks={})

# Get hero indices
snap = parser.snapshot(target_tick=60000)
hero_indices = {h.index for h in snap.heroes}

# Find attacks FROM non-heroes TO heroes (neutrals attacking heroes)
aggro_events = [
    e for e in result.attacks.events
    if e.source_index not in hero_indices and e.target_index in hero_indices
]

print(f"Neutral/creep aggro on heroes: {len(aggro_events)}")
```

### Hero Attack Patterns

```python
result = parser.parse(attacks={})

# Get hero indices
snap = parser.snapshot(target_tick=60000)
hero_indices = {h.index for h in snap.heroes}

# Count attacks per hero
hero_attack_counts = {}
for attack in result.attacks.events:
    if attack.source_index in hero_indices:
        hero_attack_counts[attack.source_index] = hero_attack_counts.get(attack.source_index, 0) + 1

# Display results
for hero in snap.heroes:
    count = hero_attack_counts.get(hero.index, 0)
    print(f"{hero.hero_name}: {count} attacks")
```

---

## Statistics (Real Match Data)

From match 8447659831 (Team Spirit vs Tundra, ~46 min):

| Metric | Value |
|--------|-------|
| Total attack events | 15,895 |
| Hero attacks | 2,018 (13%) |
| Non-hero attacks | 13,877 (87%) |
| Dire T1 top tower attacks | 276 |

---

## Combat Log vs Attacks

| Data Type | Combat Log | Attacks |
|-----------|------------|---------|
| Hero damage | Yes | Yes (as projectile) |
| Tower damage on heroes | Yes | Yes |
| Tower damage on creeps | **No** | **Yes** |
| Creep damage | No | Yes |
| Neutral attacks | No | Yes |
| Kill events | Yes | No |
| Ability damage | Yes | No |

**Rule of thumb:** Use combat log for damage/kill analysis. Use attacks for attack action tracking (who's hitting whom).

---

## Combining with Snapshots

```python
# Track a specific creep being attacked by tower
result = parser.parse(attacks={})

# Creep entity 2596 from our analysis
creep_2596_attacks = [e for e in result.attacks.events if e.target_index == 2596]

print(f"Attacks on creep 2596:")
for attack in creep_2596_attacks:
    print(f"  [{attack.game_time_str}] from entity {attack.source_index}")
```

---

## Performance Notes

- Attack events are numerous (15,000+ per match)
- Use `max_events` to limit for faster parsing
- Events are ordered by tick
- Handle-to-index conversion: `index = handle & 0x3FFF`
