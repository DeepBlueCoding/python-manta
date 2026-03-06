
# Wards Reference

??? info "AI Summary"
    Complete reference for ward lifecycle tracking. Captures observer and sentry ward placement, expiration, and dewarding from entity creation/deletion correlated with combat log death events. Typically 80-120 ward events per match with full placement position, team, placer hero, and deward details (killer, gold bounty).

---

## Overview

The wards collector tracks the full lifecycle of observer and sentry wards by correlating two data sources:

- **Entity system**: Ward entities (`CDOTA_NPC_Observer_Ward`, `CDOTA_NPC_Observer_Ward_TrueSight`) are created on placement and deleted on expiration/death. Provides position, entity ID, and owner hero.
- **Combat log**: Ward deaths appear as `DOTA_COMBATLOG_DEATH` targeting `npc_dota_observer_wards` or `npc_dota_sentry_wards`. Provides killer name, team, and gold bounty.

**Key Use Cases:**

- Vision control analysis (ward placement patterns per team)
- Dewarding detection (who killed which ward, gold earned)
- Ward duration tracking (placed at X, expired/killed at Y)
- Support performance metrics (wards placed per hero)

---

## WardEvent Fields

### Placement

| Field | Type | Description |
|-------|------|-------------|
| `tick` | `int` | Game tick when ward was placed |
| `game_time` | `float` | Game time in seconds from horn |
| `game_time_str` | `str` | Formatted time (e.g., "12:34") |
| `entity_id` | `int` | Entity index (for correlation with snapshots) |
| `ward_type` | `str` | `"observer"` or `"sentry"` |
| `team` | `int` | 2=Radiant, 3=Dire |
| `x` | `float` | Placement X position |
| `y` | `float` | Placement Y position |
| `placed_by` | `str` | Hero who placed it (e.g., `npc_dota_hero_chen`) |

### Death / Expiry

| Field | Type | Description |
|-------|------|-------------|
| `death_tick` | `int` | Tick when ward was removed (0 if still alive) |
| `death_game_time` | `float` | Game time when removed |
| `death_game_time_str` | `str` | Formatted death time |
| `was_killed` | `bool` | `True` = dewarded by hero, `False` = expired naturally |
| `killed_by` | `str` | Hero who dewarded (empty if expired) |
| `killer_team` | `int` | Team of killer (0 if expired) |
| `gold_bounty` | `int` | Gold earned from deward (typically 50) |

---

## Basic Usage

```python
from python_manta import Parser

parser = Parser("match.dem")

# Collect all ward events
result = parser.parse(wards={})

print(f"Total wards placed: {result.wards.total_events}")

# Separate by type
observers = [w for w in result.wards.events if w.ward_type == "observer"]
sentries = [w for w in result.wards.events if w.ward_type == "sentry"]

print(f"Observers: {len(observers)}, Sentries: {len(sentries)}")
```

### Limiting Events

```python
# First 50 ward events only
result = parser.parse(wards={"max_events": 50})
```

---

## Use Case Examples

### Dewarding Analysis

```python
result = parser.parse(wards={})

dewards = [w for w in result.wards.events if w.was_killed]
print(f"Total dewards: {len(dewards)}")

for ward in dewards:
    killer = ward.killed_by.replace("npc_dota_hero_", "")
    wtype = ward.ward_type
    print(f"[{ward.death_game_time_str}] {killer} dewarded {wtype} (team {ward.team}) +{ward.gold_bounty}g")
```

### Vision Control Timeline

```python
result = parser.parse(wards={})

# Radiant vs Dire ward counts over time
for ward in result.wards.events:
    team = "Radiant" if ward.team == 2 else "Dire"
    placer = ward.placed_by.replace("npc_dota_hero_", "") if ward.placed_by else "unknown"
    status = "KILLED" if ward.was_killed else "expired"
    if ward.death_tick == 0:
        status = "alive"
    print(f"[{ward.game_time_str}] {team} {ward.ward_type} by {placer} -> {status}")
```

### Support Ward Stats

```python
from collections import Counter

result = parser.parse(wards={})

# Count wards placed per hero
placer_counts = Counter(
    w.placed_by.replace("npc_dota_hero_", "")
    for w in result.wards.events
    if w.placed_by
)

print("Wards placed by hero:")
for hero, count in placer_counts.most_common():
    obs = sum(1 for w in result.wards.events if w.placed_by and hero in w.placed_by and w.ward_type == "observer")
    sen = sum(1 for w in result.wards.events if w.placed_by and hero in w.placed_by and w.ward_type == "sentry")
    print(f"  {hero}: {count} total ({obs} obs, {sen} sen)")
```

### Combining with Snapshots

```python
result = parser.parse(wards={})

# Find wards placed near Roshan pit
ROSHAN_X, ROSHAN_Y = -2480, 1840
RADIUS = 1500

rosh_wards = [
    w for w in result.wards.events
    if ((w.x - ROSHAN_X)**2 + (w.y - ROSHAN_Y)**2)**0.5 < RADIUS
]

print(f"Wards near Roshan: {len(rosh_wards)}")
for w in rosh_wards:
    team = "Radiant" if w.team == 2 else "Dire"
    print(f"  [{w.game_time_str}] {team} {w.ward_type} at ({w.x:.0f}, {w.y:.0f})")
```

---

## Statistics (Real Match Data)

From match 8447659831 (Team Spirit vs Tundra, ~46 min):

| Metric | Value |
|--------|-------|
| **Total wards** | 105 |
| Observer wards | 38 (36%) |
| Sentry wards | 67 (64%) |
| **Dewards** | 33 (31%) |
| Radiant wards | 48 |
| Dire wards | 48 |
| Gold bounty per deward | 50 |

---

## Notes

- **Team detection**: Ward team comes from combat log correlation, not entity properties. Wards still alive at match end may have `team=0`.
- **placed_by**: Resolved from the ward entity's `m_hOwnerEntity` handle. May be empty if the owner entity was not available at creation time.
- **Tick offset**: Entity deletion occurs ~200-400 ticks after the combat log death event. The collector handles this correlation automatically.
