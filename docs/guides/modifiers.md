
# Modifiers Guide

??? info "AI Summary"
    Track buffs, debuffs, and auras using `parse_modifiers()`. Each modifier entry includes parent entity, caster, ability handle, creation time, duration (-1 for permanent), stack count, and flags for aura/debuff. Use `auras_only=True` to filter aura effects. Modifiers track status effects like stuns, slows, and item buffs throughout the match. Combine with entity queries to resolve entity handles to names.

---

## Overview

Modifiers represent buffs, debuffs, auras, and other status effects applied to units during the match.

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_modifiers("match.dem", max_modifiers=100)

for mod in result.modifiers:
    duration_str = f"{mod.duration}s" if mod.duration >= 0 else "permanent"
    print(f"[Tick {mod.tick}] Entity {mod.parent}: {duration_str}")
```

---

## Basic Usage

### All Modifiers

```python
result = parser.parse_modifiers("match.dem", max_modifiers=500)

print(f"Total modifiers captured: {result.total_modifiers}")

for mod in result.modifiers:
    mod_type = "DEBUFF" if mod.is_debuff else "BUFF"
    aura_tag = " (AURA)" if mod.is_aura else ""

    print(f"[{mod.tick}] {mod_type}{aura_tag} on entity {mod.parent}")
```

### Auras Only

```python
result = parser.parse_modifiers("match.dem", auras_only=True, max_modifiers=200)

print(f"Aura modifiers: {len(result.modifiers)}")

for mod in result.modifiers:
    print(f"[{mod.tick}] Aura on entity {mod.parent}, stacks: {mod.stack_count}")
```

---

## Modifier Entry Fields

Each `ModifierEntry` contains:

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Game tick when modifier was recorded |
| `net_tick` | int | Network tick |
| `parent` | int | Entity handle of unit with modifier |
| `caster` | int | Entity handle of caster |
| `ability` | int | Ability handle that created modifier |
| `modifier_class` | int | Modifier class ID |
| `serial_num` | int | Serial number for tracking |
| `index` | int | Modifier index |
| `creation_time` | float | Game time when created |
| `duration` | float | Duration in seconds (-1 = permanent) |
| `stack_count` | int | Number of stacks |
| `is_aura` | bool | Whether it's an aura |
| `is_debuff` | bool | Whether it's a debuff |

---

## Common Use Cases

### Duration Analysis

```python
result = parser.parse_modifiers("match.dem", max_modifiers=500)

permanent = []
timed = []

for mod in result.modifiers:
    if mod.duration < 0:
        permanent.append(mod)
    else:
        timed.append(mod)

print(f"Permanent modifiers: {len(permanent)}")
print(f"Timed modifiers: {len(timed)}")

if timed:
    durations = [m.duration for m in timed]
    print(f"Duration range: {min(durations):.1f}s - {max(durations):.1f}s")
    print(f"Average duration: {sum(durations)/len(durations):.1f}s")
```

### Buff vs Debuff Count

```python
result = parser.parse_modifiers("match.dem", max_modifiers=1000)

buffs = [m for m in result.modifiers if not m.is_debuff]
debuffs = [m for m in result.modifiers if m.is_debuff]

print(f"Buffs: {len(buffs)}")
print(f"Debuffs: {len(debuffs)}")
```

### Stacking Modifiers

```python
result = parser.parse_modifiers("match.dem", max_modifiers=500)

stacking = [m for m in result.modifiers if m.stack_count > 1]

print(f"Modifiers with stacks: {len(stacking)}")

for mod in stacking[:10]:
    print(f"  Entity {mod.parent}: {mod.stack_count} stacks")
```

### Modifier Timeline

```python
from collections import defaultdict

result = parser.parse_modifiers("match.dem", max_modifiers=1000)

# Group by tick ranges (every 1000 ticks)
timeline = defaultdict(list)
for mod in result.modifiers:
    bucket = (mod.tick // 1000) * 1000
    timeline[bucket].append(mod)

print("Modifier Activity Timeline:")
for tick in sorted(timeline.keys()):
    mods = timeline[tick]
    debuff_count = sum(1 for m in mods if m.is_debuff)
    buff_count = len(mods) - debuff_count
    print(f"  Tick {tick:>6}: {buff_count} buffs, {debuff_count} debuffs")
```

### Entity Modifier History

```python
from collections import defaultdict

result = parser.parse_modifiers("match.dem", max_modifiers=2000)

# Group modifiers by parent entity
entity_mods = defaultdict(list)
for mod in result.modifiers:
    entity_mods[mod.parent].append(mod)

# Find entities with most modifiers
sorted_entities = sorted(entity_mods.items(), key=lambda x: -len(x[1]))

print("Entities with Most Modifiers:")
for entity_id, mods in sorted_entities[:10]:
    debuff_count = sum(1 for m in mods if m.is_debuff)
    aura_count = sum(1 for m in mods if m.is_aura)
    print(f"  Entity {entity_id}: {len(mods)} total ({debuff_count} debuffs, {aura_count} auras)")
```

### Long Duration Debuffs

```python
result = parser.parse_modifiers("match.dem", max_modifiers=1000)

# Find long-duration debuffs (potential stuns/silences)
long_debuffs = [
    m for m in result.modifiers
    if m.is_debuff and m.duration > 2.0
]

print(f"Long duration debuffs (>2s): {len(long_debuffs)}")

for mod in sorted(long_debuffs, key=lambda m: -m.duration)[:10]:
    print(f"  Duration: {mod.duration:.1f}s on entity {mod.parent}")
```

---

## Combining with Entity Queries

Since modifiers reference entities by handle, you can combine with entity queries:

```python
# Get modifiers
mods_result = parser.parse_modifiers("match.dem", max_modifiers=200)

# Get hero entities for reference
entities_result = parser.query_entities(
    "match.dem",
    class_filter="Hero",
    property_filter=["m_iHealth"],
    max_entities=10
)

# Build entity index map
entity_map = {e.index: e.class_name for e in entities_result.entities}

# Report modifiers on known entities
for mod in mods_result.modifiers[:20]:
    entity_name = entity_map.get(mod.parent, f"Unknown({mod.parent})")
    mod_type = "DEBUFF" if mod.is_debuff else "BUFF"
    print(f"{mod_type} on {entity_name}")
```

---

## Aura Effects

Auras are special modifiers that affect units in an area:

```python
result = parser.parse_modifiers("match.dem", auras_only=True, max_modifiers=300)

print("Aura Analysis:")
print("-" * 50)

# Group by caster
from collections import defaultdict
caster_auras = defaultdict(list)

for mod in result.modifiers:
    caster_auras[mod.caster].append(mod)

print(f"Unique aura casters: {len(caster_auras)}")

for caster, auras in sorted(caster_auras.items(), key=lambda x: -len(x[1]))[:5]:
    affected_units = len(set(m.parent for m in auras))
    print(f"  Caster {caster}: {len(auras)} aura applications to {affected_units} units")
```

---

## Performance Tips

1. **Set max_modifiers** - Modifiers can be numerous in long matches
2. **Use auras_only** - When only interested in aura effects
3. **Filter client-side** - Parse once, filter the results multiple times

```python
# Efficient: get all modifiers once
all_mods = parser.parse_modifiers("match.dem", max_modifiers=2000)

# Filter in Python
debuffs = [m for m in all_mods.modifiers if m.is_debuff]
auras = [m for m in all_mods.modifiers if m.is_aura]
permanent = [m for m in all_mods.modifiers if m.duration < 0]
```

---

## Common Modifier Patterns

### Permanent Buffs (Passives/Items)

```python
permanent_buffs = [
    m for m in result.modifiers
    if m.duration < 0 and not m.is_debuff
]
```

### Control Effects (Stuns/Roots)

```python
# Long-duration debuffs are often control effects
control_effects = [
    m for m in result.modifiers
    if m.is_debuff and 0 < m.duration <= 5.0
]
```

### DoT/HoT Effects

```python
# Short-duration stackable effects
dot_hot = [
    m for m in result.modifiers
    if m.stack_count > 0 and 0 < m.duration < 15
]
```

---

## Important Notes

!!! note

    Modifiers track when effects are applied. The `parent` and `caster` fields are entity handles, not player IDs. Use entity queries to resolve these to unit types.

### Duration Values

| Duration | Meaning |
|----------|---------|
| `-1` | Permanent (passives, items) |
| `0` | Instant effect |
| `> 0` | Timed effect in seconds |

### Entity Handles

The `parent`, `caster`, and `ability` fields are entity handles:
- Use entity queries to get entity details by index
- Handles may reference entities no longer in the game
- Handle 0 typically means no specific source
