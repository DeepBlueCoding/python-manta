# Missing Features Evaluation

## Overview

This document evaluates each missing feature request, assessing feasibility, implementation complexity, and approach.

---

## Bugs (High Priority)

### 1. ~~BUG~~ FIXED: `target_hero_level` always 0 in combat log entries

| Aspect | Details |
|--------|---------|
| **Status** | ✅ FIXED |
| **Impact** | Can now calculate respawn times directly from combat log |
| **Root Cause** | Dota 2 protobuf field is never populated, but hero levels ARE available from entity state |
| **Solution** | Track hero levels from `m_iCurrentLevel` entity property, inject into combat log entries at parse time |
| **Result** | 100% of hero deaths now have `target_hero_level` populated, 94%+ have `attacker_hero_level` (non-hero attackers like summons/neutrals are expected to have 0) |

### 2. ~~BUG~~ NOT A BUG: Entity snapshots missing some heroes (only returns ~5 heroes, not all 10)

| Aspect | Details |
|--------|---------|
| **Status** | ✅ INVESTIGATED - NOT A BUG |
| **Evidence** | Post-horn snapshots correctly return all 10 heroes |
| **Explanation** | Pre-horn snapshots may have fewer heroes because heroes spawn at different times during the picking phase. Once the horn sounds, all 10 heroes are present. |
| **Verified** | Tested with 8447659831.dem - snapshot at -0:28 has 10 heroes, all post-horn snapshots have 10 heroes |

### 3. ~~BUG~~ FIXED: Combat log `game_time` ~30s offset from entity snapshot time

| Aspect | Details |
|--------|---------|
| **Status** | ✅ FIXED |
| **Evidence** | Tested at 10-min mark: entity snapshot tick=48413 game_time=625.63s, combat log tick=48315 game_time=622.37s. Tick diff -98 → expected time diff -3.27s, actual -3.27s. Offset: 0.00s |
| **Resolution** | Fixed as part of FEATURE #12 (pre-horn positions) - both combat log and entity snapshots now use the same gameStartTick reference point |

### 4. ~~BUG~~ FIXED: `heroes_only` filter in combat_log collector not working

| Aspect | Details |
|--------|---------|
| **Status** | ✅ FIXED |
| **Impact** | Returns all units instead of just heroes |
| **Root Cause** | Filter only checked boolean flags, not name strings |
| **Location** | `go_wrapper/data_parser.go` |
| **Solution** | Added string check for "npc_dota_hero_" in attacker_name/target_name in addition to boolean flags |

---

## Features - Feasibility Assessment

### 5. ~~FEATURE~~ COMPLETED: HeroRespawnEvent model and derive_respawn_events utility

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED |
| **Solution** | Added `HeroRespawnEvent` model and `derive_respawn_events()` utility to derive respawns from DEATH events |
| **Usage** | `respawns = derive_respawn_events(combat_log_result, hero_levels={"npc_dota_hero_axe": 15})` |
| **Note** | Uses default level estimate when `target_hero_level` not available (data limitation) |

### 6. ~~FEATURE~~ IMPLEMENTED: Tower attacks on creeps

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED - Via `attacks` collector |
| **Solution** | New `attacks` collector exposes TE_Projectile data with `is_attack=True` |
| **Usage** | `parser.parse(attacks={})` returns all attack events including tower attacks on creeps |
| **Data** | `AttackEvent` with `source_index`, `target_index`, `game_time`, `projectile_speed` |

```python
# Example: Find tower attacks on creeps
result = parser.parse(attacks={})
for attack in result.attacks.events:
    if 600 <= attack.source_index <= 800:  # Tower entity range
        print(f"[{attack.game_time_str}] Tower {attack.source_index} -> {attack.target_index}")
```

### 7. FEATURE: Creep-on-creep damage

| Aspect | Details |
|--------|---------|
| **Feasibility** | ⚠️ MEDIUM - Data likely exists but volume is massive |
| **Why Missing** | Combat log filters to hero-related events |
| **Data Location** | Combat log DAMAGE events |
| **Complexity** | Medium |
| **Approach** | Add `include_creeps=True` option |
| **Performance Impact** | VERY HIGH - thousands of events per minute |
| **Recommendation** | Probably not worth it - use entity positions instead |

### 8. FEATURE: Creep-on-creep deaths

| Aspect | Details |
|--------|---------|
| **Feasibility** | ⚠️ MEDIUM - Same as creep damage |
| **Why Missing** | Combat log filters |
| **Complexity** | Medium |
| **Performance Impact** | High |
| **Recommendation** | Same as above - derive from entity state |

### 9. ~~FEATURE~~ COMPLETED: Creep entity positions

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED |
| **Solution** | Added `include_creeps` option to EntityParseConfig |
| **Usage** | `parser.parse(entities={'include_creeps': True})` |
| **Data** | `snapshot.creeps` list with CreepSnapshot objects containing position, team, health |

```python
# Example usage
result = parser.parse(entities={'include_creeps': True, 'interval_ticks': 1800})
for snap in result.entities.snapshots:
    lane_creeps = [c for c in snap.creeps if c.is_lane]
    neutral_creeps = [c for c in snap.creeps if c.is_neutral]
    print(f"{snap.game_time_str}: {len(lane_creeps)} lane, {len(neutral_creeps)} neutral")
```

### 10. ~~FEATURE~~ IMPLEMENTED: Neutral creep aggro/attacks

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED - Via `attacks` collector |
| **Solution** | New `attacks` collector exposes TE_Projectile data including neutral creep attacks |
| **Usage** | `parser.parse(attacks={})` returns all attack events including neutral aggro |
| **Statistics** | 13,877 non-hero attacks per match (87% of all attacks) including neutral creep aggro |

```python
# Example: Find who neutrals are attacking (aggro targets)
result = parser.parse(attacks={})
snap = parser.snapshot(target_tick=60000)
hero_indices = {h.index for h in snap.heroes}

# Find attacks from non-heroes to heroes (neutrals attacking heroes)
aggro_events = [
    a for a in result.attacks.events
    if a.source_index not in hero_indices and a.target_index in hero_indices
]
print(f"Neutral/creep aggro on heroes: {len(aggro_events)}")
```

### 11. ~~FEATURE~~ COMPLETED: Stack count (neutral camp stacking)

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED |
| **Combat Log Type** | `NEUTRAL_CAMP_STACK` (type 20) exists in enum but game does NOT emit these events |
| **Solution** | Added `camps_stacked` field to `HeroSnapshot` extracted from entity properties |
| **Data Source** | `CDOTA_DataRadiant/CDOTA_DataDire` entities via `m_vecDataTeam.%04d.m_iCampsStacked` |
| **Usage** | `snap = parser.snapshot(target_tick=90000); print(hero.camps_stacked)` |
| **Note** | This is the same data source used by OpenDota for their camps_stacked stat |

```python
# Example usage
snap = parser.snapshot(target_tick=90000)
for hero in snap.heroes:
    if hero.camps_stacked > 0:
        print(f"{hero.hero_name}: {hero.camps_stacked} camps stacked")
```

### 12. ~~FEATURE~~ COMPLETED: High-res pre-horn positions

| Aspect | Details |
|--------|---------|
| **Status** | ✅ IMPLEMENTED |
| **Solution** | Pre-horn snapshots now captured with correct negative game_time |
| **Changes** | Post-process snapshots after parsing to recalculate game_time once gameStartTick is known |
| **Result** | Snapshots before horn have negative game_time (e.g., -1:46 means 1 min 46 sec before horn) |

```python
# Example pre-horn snapshot
result = parser.parse(entities={'interval_ticks': 1800})
for snap in result.entities.snapshots:
    if snap.game_time < 0:
        print(f"Pre-horn: tick={snap.tick}, time={snap.game_time_str}")
```

### 13. FEATURE: Lane creep spawn tracking

| Aspect | Details |
|--------|---------|
| **Feasibility** | ⚠️ MEDIUM - Spawn events exist but not creep-specific |
| **Why Missing** | No explicit "lane creep spawned" event |
| **Data Available** | `CNETMsg_SpawnGroup_*` callbacks exist |
| **Complexity** | High |
| **Approach** | Track creep entity creation at spawn locations |
| **Recommendation** | Derive from entity appearance at spawn points |

---

## Implementation Priority Matrix

| Priority | Feature | Effort | Impact |
|----------|---------|--------|--------|
| 1 | ~~BUG #1: target_hero_level~~ | ✅ FIXED | High |
| 2 | ~~BUG #4: heroes_only filter~~ | ✅ FIXED | Medium |
| 3 | ~~BUG #2: Missing heroes~~ | ✅ NOT A BUG | High |
| 4 | ~~BUG #3: game_time offset~~ | ✅ FIXED | Medium |
| 5 | ~~FEATURE #5: Respawn events~~ | ✅ DONE | High |
| 6 | ~~FEATURE #12: Pre-horn positions~~ | ✅ DONE | Medium |
| 7 | ~~FEATURE #9: Creep positions~~ | ✅ DONE | High |
| 8 | ~~FEATURE #6: Tower attacks on creeps~~ | ✅ IMPLEMENTED (attacks collector) | Medium |
| 9 | ~~FEATURE #11: Stack count~~ | ✅ DONE | Medium |
| 10 | FEATURE #13: Creep spawn tracking | High | Medium |
| 11 | FEATURE #7: Creep-on-creep damage | Medium | Low |
| 12 | FEATURE #8: Creep-on-creep deaths | Medium | Low |
| 13 | ~~FEATURE #10: Neutral aggro~~ | ✅ IMPLEMENTED (attacks collector) | Medium |

---

## Quick Wins (Can implement immediately)

1. ~~**Fix `target_hero_level`**~~ - ✅ FIXED - Now populated from entity state during parsing
2. ~~**Fix `heroes_only` filter**~~ - ✅ DONE - Added string check in addition to boolean flags
3. ~~**Add respawn event utility**~~ - ✅ DONE - HeroRespawnEvent, derive_respawn_events()
4. ~~**Enable pre-horn snapshots**~~ - ✅ DONE - Post-process game_time after parsing
5. ~~**BUG #2: Missing heroes**~~ - ✅ NOT A BUG - Heroes spawn at different times pre-horn
6. ~~**BUG #3: game_time offset**~~ - ✅ FIXED - Fixed by pre-horn positions feature

## Requires Significant Work

1. ~~**Creep entity positions**~~ - ✅ DONE - Added `include_creeps` option
2. ~~**Stack detection**~~ - ✅ DONE - Added `camps_stacked` field to `HeroSnapshot` from entity properties
3. **Creep spawn tracking** - Track entity creation events

## Probably Not Worth It

1. **Creep-on-creep damage** - Too much data, better to infer from positions

## Newly Discovered (Now Implemented via attacks collector)

1. ~~**Tower attacks on creeps**~~ - ✅ IMPLEMENTED via `attacks` collector
2. ~~**Neutral aggro**~~ - ✅ IMPLEMENTED via `attacks` collector

---

## Technical Notes

### Entity Classes Available in Manta

```
CDOTA_Unit_Hero_*           - Heroes
CDOTA_BaseNPC_Creep_*       - Lane creeps
CDOTA_BaseNPC_Creep_Neutral - Neutral creeps
CDOTA_BaseNPC_Tower         - Towers
CDOTA_BaseNPC_Barracks      - Barracks
CDOTA_BaseNPC_Building      - Buildings
CDOTA_BaseNPC_Fort          - Ancient
CDOTA_BaseNPC_Courier       - Couriers
CDOTA_Unit_*                - Summons, wards, etc.
```

### TE_Projectile for Attack Tracking (KEY DISCOVERY)

The `TE_Projectile` message tracks ALL attack projectiles in the game, including:
- Hero auto-attacks
- Tower attacks (including on creeps!)
- Creep attacks (lane and neutral)
- Summon attacks

```python
# TE_Projectile message structure
{
    'source': 3506901,      # Entity handle (& 0x3FFF = entity index)
    'target': 3197622,      # Target entity handle
    'is_attack': True,      # True for auto-attacks
    'move_speed': 900,      # Projectile speed
    'dodgeable': True,
    'launch_tick': 31571,   # When projectile was launched
    'handle': 1073742028    # Projectile handle
}

# Convert handles to entity indices
def handle_to_index(handle):
    return handle & 0x3FFF

# Entity index ranges (approximate):
# 300-600:  Heroes
# 600-800:  Towers and buildings
# 1000+:    Creeps, summons, other units
```

**Statistics from a real match:**
- Total attack projectiles: 15,895
- Hero attacks: 2,018 (13%)
- Non-hero attacks: 13,877 (87%) - towers, creeps, neutrals

### Callbacks Available for Tracking

```
CDOTAUserMsg_NeutralCampAlert  - Neutral camp alerts
CDOTAUserMsg_FoundNeutralItem  - Neutral items found
CNETMsg_SpawnGroup_*           - Spawn group events
CDemoSpawnGroups               - Demo spawn groups
```
