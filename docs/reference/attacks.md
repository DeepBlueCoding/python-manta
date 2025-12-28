
# Attacks Reference

??? info "AI Summary"
    Complete reference for attack tracking from both TE_Projectile (ranged) and combat log (melee). Captures ALL auto-attacks in the game with consistent fields: entity indices, names, timing, and damage. Typically 30,000+ events per match combining ranged projectiles and melee hits.

---

## Overview

The attacks collector unifies two data sources into a single consistent API:

- **Ranged attacks**: From `TE_Projectile` messages (projectile speed, dodgeable)
- **Melee attacks**: From combat log DAMAGE events with no ability (damage values)

Both types share the same `AttackEvent` model with all fields populated where data is available.

**Key Use Cases:**

- Last-hit analysis (who attacked which creep)
- Lane farming patterns
- Hero attack tracking (both melee and ranged heroes)
- Tower/creep/neutral combat analysis

---

## AttackEvent Fields

Every `AttackEvent` contains these fields, populated consistently for both ranged and melee:

### Timing

| Field | Type | Description |
|-------|------|-------------|
| `tick` | `int` | Game tick (~30/second) |
| `game_time` | `float` | Game time in seconds from horn |
| `game_time_str` | `str` | Formatted time (e.g., "15:34") |
| `launch_tick` | `int` | Tick when projectile was launched (ranged only) |

### Entity Identification

| Field | Type | Ranged | Melee | Description |
|-------|------|--------|-------|-------------|
| `source_index` | `int` | ✓ | ✓ | Entity ID of attacker |
| `target_index` | `int` | ✓ | ✓* | Entity ID of target |
| `attacker_name` | `str` | ✓ | ✓ | Unit name (e.g., `npc_dota_hero_troll_warlord`) |
| `target_name` | `str` | ✓ | ✓ | Target unit name |

*Melee target_index populated for heroes, may be 0 for creeps/neutrals

### Attack Properties

| Field | Type | Ranged | Melee | Description |
|-------|------|--------|-------|-------------|
| `is_melee` | `bool` | `False` | `True` | Attack type identifier |
| `damage` | `int` | 0 | ✓ | Damage dealt |
| `target_health` | `int` | 0 | ✓ | Target health AFTER attack |
| `projectile_speed` | `int` | ✓ | 0 | Projectile move speed |
| `dodgeable` | `bool` | ✓ | `False` | Can be disjointed |
| `location_x` | `float` | ✓ | ✓* | Attacker position X |
| `location_y` | `float` | ✓ | ✓* | Attacker position Y |
| `attacker_team` | `int` | 0 | ✓ | Attacker team (2=Radiant, 3=Dire) |
| `target_team` | `int` | 0 | ✓ | Target team (2=Radiant, 3=Dire) |
| `is_attacker_hero` | `bool` | `False` | ✓ | Attacker is a hero |
| `is_target_hero` | `bool` | `False` | ✓ | Target is a hero |

*Melee location from entity lookup (heroes ~37%, creeps 0)

### Raw Handles (Advanced)

| Field | Type | Description |
|-------|------|-------------|
| `source_handle` | `int` | Raw entity handle (ranged only) |
| `target_handle` | `int` | Raw entity handle (ranged only) |

---

## Basic Usage

```python
from python_manta import Parser

parser = Parser("match.dem")

# Collect all attack events (ranged + melee)
result = parser.parse(attacks={})

print(f"Total attacks: {result.attacks.total_events}")

# Separate by type
melee = [a for a in result.attacks.events if a.is_melee]
ranged = [a for a in result.attacks.events if not a.is_melee]

print(f"Melee: {len(melee)}, Ranged: {len(ranged)}")
```

### Limiting Events

```python
# First 1000 attacks only
result = parser.parse(attacks={"max_events": 1000})
```

---

## Hero Name Format

All hero names use the canonical Dota 2 format with underscores:

```python
# Correct format (matches combat log)
"npc_dota_hero_troll_warlord"
"npc_dota_hero_faceless_void"
"npc_dota_hero_shadow_shaman"
"npc_dota_hero_monkey_king"
"npc_dota_hero_storm_spirit"

# NOT: "npc_dota_hero_trollwarlord" (incorrect)
```

---

## Use Case Examples

### Lane Farming Analysis

```python
result = parser.parse(attacks={})

# Find all attacks on lane creeps
lane_creep_attacks = [
    a for a in result.attacks.events
    if "creep_goodguys" in a.target_name or "creep_badguys" in a.target_name
]

# Group by attacker
from collections import Counter
attackers = Counter(a.attacker_name for a in lane_creep_attacks)
for name, count in attackers.most_common(10):
    print(f"{name}: {count} attacks on lane creeps")
```

### Contested Last Hits

```python
result = parser.parse(attacks={}, entity_deaths={"include_creeps": True})

# Find creeps that were attacked by multiple heroes before death
from collections import defaultdict

creep_attackers = defaultdict(set)
for attack in result.attacks.events:
    if "npc_dota_hero" in attack.attacker_name:
        creep_attackers[attack.target_name].add(attack.attacker_name)

contested = {k: v for k, v in creep_attackers.items() if len(v) > 1}
print(f"Creeps contested by multiple heroes: {len(contested)}")
```

### Hero vs Hero Combat

```python
result = parser.parse(attacks={})

# Find hero-on-hero attacks
hero_fights = [
    a for a in result.attacks.events
    if "npc_dota_hero" in a.attacker_name and "npc_dota_hero" in a.target_name
]

print(f"Hero vs hero attacks: {len(hero_fights)}")

# Sample output
for a in hero_fights[:5]:
    atk = a.attacker_name.replace("npc_dota_hero_", "")
    tgt = a.target_name.replace("npc_dota_hero_", "")
    dmg = f", dmg={a.damage}" if a.is_melee else ""
    print(f"[{a.game_time_str}] {atk} -> {tgt}{dmg}")
```

### Melee Hero Tracking (e.g., Troll Warlord)

```python
result = parser.parse(attacks={})

# Troll Warlord has both ranged and melee forms
troll_attacks = [a for a in result.attacks.events if "troll_warlord" in a.attacker_name]

troll_melee = [a for a in troll_attacks if a.is_melee]
troll_ranged = [a for a in troll_attacks if not a.is_melee]

print(f"Troll melee attacks: {len(troll_melee)}")
print(f"Troll ranged attacks: {len(troll_ranged)}")

# Melee attacks have damage
if troll_melee:
    avg_dmg = sum(a.damage for a in troll_melee) / len(troll_melee)
    print(f"Average melee damage: {avg_dmg:.1f}")
```

---

## Entity Index Consistency

Entity indices match between attacks and snapshots:

```python
result = parser.parse(attacks={})
snap = parser.snapshot(target_tick=30000)

# Build hero index map
hero_by_id = {h.entity_id: h.hero_name for h in snap.heroes}

# Verify consistency
for attack in result.attacks.events[:100]:
    if attack.source_index in hero_by_id:
        assert attack.attacker_name == hero_by_id[attack.source_index]
```

---

## Statistics (Real Match Data)

From match 8447659831 (Team Spirit vs Tundra, ~46 min):

| Metric | Value |
|--------|-------|
| **Total attacks** | 32,895 |
| Melee attacks | 17,000 (52%) |
| Ranged attacks | 15,895 (48%) |
| Troll Warlord melee | 2,791 |
| Pugna ranged | 235 |

---

## Combat Log vs Attacks

| Data Type | Combat Log | Attacks Collector |
|-----------|------------|-------------------|
| Hero damage | Yes (all) | Yes (auto-attacks only) |
| Melee auto-attacks | Yes (as damage) | Yes (with entity ID) |
| Ranged auto-attacks | No | Yes (with projectile data) |
| Tower attacks on creeps | No | Yes |
| Neutral attacks | No | Yes |
| Ability damage | Yes | No |
| Kill attribution | Yes | No |

**Rule of thumb:**
- Use **combat log** for damage analysis and kill tracking
- Use **attacks** for attack pattern analysis and entity correlation

---

## Performance Notes

- Total events: ~30,000+ per match (ranged + melee)
- Use `max_events` to limit for faster parsing
- Events are ordered by tick
- Entity name → index mapping is automatic for heroes
