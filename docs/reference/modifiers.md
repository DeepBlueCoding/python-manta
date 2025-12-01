
# Modifiers Reference

??? info "AI Summary"
    Reference for parsing buff and debuff modifiers from Dota 2 replays. Modifiers are effects applied to units including stuns, slows, auras, and ability effects. Each modifier has parent entity, caster, ability source, duration, stack count, and aura/debuff flags. Use `parse_modifiers()` to capture modifier events with optional filtering by modifier class.

---

## Modifier Entry Fields

Every `ModifierEntry` contains:

| Field | Type | Description |
|-------|------|-------------|
| `tick` | `int` | Game tick when captured |
| `net_tick` | `int` | Network tick |
| `parent` | `int` | Entity handle of unit with modifier |
| `caster` | `int` | Entity handle of unit that applied modifier |
| `ability` | `int` | Ability handle that created modifier |
| `modifier_class` | `int` | Modifier class ID |
| `serial_num` | `int` | Serial number for tracking |
| `index` | `int` | Modifier index on the unit |
| `creation_time` | `float` | Game time when modifier was created |
| `duration` | `float` | Duration in seconds (-1 = permanent) |
| `stack_count` | `int` | Number of stacks |
| `is_aura` | `bool` | Whether this is an aura effect |
| `is_debuff` | `bool` | Whether this is a debuff |

---

## Basic Usage

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_modifiers("match.dem", max_modifiers=100)

for mod in result.modifiers:
    duration_str = f"{mod.duration}s" if mod.duration >= 0 else "permanent"
    buff_type = "debuff" if mod.is_debuff else "buff"
    aura_str = " (aura)" if mod.is_aura else ""

    print(f"Entity {mod.parent}: {buff_type}{aura_str}, duration={duration_str}, stacks={mod.stack_count}")
```

---

## Filtering by Class

```python
# Filter by specific modifier class IDs
result = parser.parse_modifiers("match.dem", modifier_class_filter=[1, 5, 10], max_modifiers=100)
```

---

## Duration Values

| Duration | Meaning |
|----------|---------|
| `-1` | Permanent modifier (e.g., passive abilities) |
| `0` | Instant effect |
| `> 0` | Timed duration in seconds |

---

## Common Modifier Types

Modifiers represent various game effects:

### Crowd Control
- Stuns
- Silences
- Hexes
- Roots
- Disarms

### Buffs
- Damage amplification
- Attack speed bonuses
- Move speed bonuses
- Armor bonuses

### Debuffs
- Damage reduction
- Slows
- Break effects
- Mutes

### Auras
- Team auras (from items like Vladmir's Offering)
- Hero auras (from abilities like Drow Ranger's Precision Aura)
- Building auras

---

## Entity Handles

The `parent`, `caster`, and `ability` fields are entity handles. To resolve these to actual entities, use `query_entities()`:

```python
# Get modifier data
mods = parser.parse_modifiers("match.dem", max_modifiers=50)

# Get entity data at same tick
entities = parser.query_entities("match.dem", tick=mods.modifiers[0].tick)

# Match entity handles to entity data
for mod in mods.modifiers:
    parent_entity = next(
        (e for e in entities.entities if e.index == mod.parent),
        None
    )
    if parent_entity:
        print(f"Modifier on {parent_entity.class_name}")
```

---

## Stack Count

`stack_count` indicates:

| Value | Meaning |
|-------|---------|
| `0` | No stacking / single application |
| `1+` | Current number of stacks |

Some abilities that use stacking:
- Flesh Heap (Pudge)
- Counter Helix (Axe) proc counter
- Essence Shift (Slark) stacks
- Silencer's Intelligence Steal
