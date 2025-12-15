
# Combat Log Reference

??? info "AI Summary"
    Complete reference for 12 combat log entry types parsed from Dota 2 replays. Types include: DAMAGE (0), HEAL (1), MODIFIER_ADD (2), MODIFIER_REMOVE (3), DEATH (4), ABILITY (5), ITEM (6), LOCATION (7), GOLD (8), GAME_STATE (9), XP (10), PURCHASE (11). Each entry contains attacker/target info, damage values, game_time (seconds from horn), and team visibility flags.

---

## Combat Log Types

| Type ID | Name | Description |
|---------|------|-------------|
| 0 | DAMAGE | Damage dealt to a unit |
| 1 | HEAL | Health restored to a unit |
| 2 | MODIFIER_ADD | Buff/debuff applied |
| 3 | MODIFIER_REMOVE | Buff/debuff removed |
| 4 | DEATH | Unit death |
| 5 | ABILITY | Ability used |
| 6 | ITEM | Item used |
| 7 | LOCATION | Location event |
| 8 | GOLD | Gold gained/lost |
| 9 | GAME_STATE | Game state change |
| 10 | XP | Experience gained |
| 11 | PURCHASE | Item purchased |

---

## Entry Fields

Every `CombatLogEntry` contains these fields:

### Identification

| Field | Type | Description |
|-------|------|-------------|
| `tick` | `int` | Game tick (~30/second) |
| `net_tick` | `int` | Network tick |
| `type` | `int` | Combat log type ID (0-11) |
| `type_name` | `str` | Human-readable type name |
| `game_time` | `float` | Game time in seconds (negative before horn) |
| `game_time_str` | `str` | Formatted game time (e.g., "-0:40", "5:32") |

### Participants

| Field | Type | Description |
|-------|------|-------------|
| `attacker_name` | `str` | Attacker unit name |
| `target_name` | `str` | Target unit name |
| `target_source_name` | `str` | Target source name |
| `damage_source_name` | `str` | Damage source name |
| `inflictor_name` | `str` | Ability/item causing the effect |

### Unit Flags

| Field | Type | Description |
|-------|------|-------------|
| `is_attacker_hero` | `bool` | Attacker is a hero |
| `is_attacker_illusion` | `bool` | Attacker is an illusion |
| `is_target_hero` | `bool` | Target is a hero |
| `is_target_illusion` | `bool` | Target is an illusion |
| `attacker_team` | `int` | Attacker team ID |
| `target_team` | `int` | Target team ID |

### Visibility

| Field | Type | Description |
|-------|------|-------------|
| `is_visible_radiant` | `bool` | Visible to Radiant team |
| `is_visible_dire` | `bool` | Visible to Dire team |

### Values

| Field | Type | Description |
|-------|------|-------------|
| `value` | `int` | Primary value (damage, heal, gold, XP) |
| `health` | `int` | Target health after event |
| `gold` | `int` | Gold value |
| `xp` | `int` | XP value |
| `last_hits` | `int` | Last hits at time of event |

### Ability Info

| Field | Type | Description |
|-------|------|-------------|
| `ability_level` | `int` | Level of ability used |
| `is_ability_toggle_on` | `bool` | Ability toggled on |
| `is_ability_toggle_off` | `bool` | Ability toggled off |

### Duration Effects

| Field | Type | Description |
|-------|------|-------------|
| `stun_duration` | `float` | Stun duration in seconds |
| `slow_duration` | `float` | Slow duration in seconds |

---

## Type-Specific Usage

### DAMAGE (Type 0)

```python
result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=100)

for entry in result.entries:
    print(f"[{entry.game_time_str}] {entry.attacker_name} -> {entry.target_name}: {entry.value} damage")
    if entry.inflictor_name:
        print(f"  via {entry.inflictor_name}")
```

### HEAL (Type 1)

```python
result = parser.parse_combat_log("match.dem", types=[1], max_entries=100)

for entry in result.entries:
    print(f"[{entry.game_time_str}] {entry.target_name} healed for {entry.value}")
```

### MODIFIER_ADD (Type 2)

```python
result = parser.parse_combat_log("match.dem", types=[2], max_entries=100)

for entry in result.entries:
    if entry.inflictor_name:
        print(f"[{entry.game_time_str}] {entry.inflictor_name} applied to {entry.target_name}")
```

### DEATH (Type 4)

```python
result = parser.parse_combat_log("match.dem", types=[4], heroes_only=True, max_entries=100)

for entry in result.entries:
    print(f"[{entry.game_time_str}] {entry.target_name} died")
    if entry.attacker_name:
        print(f"  killed by {entry.attacker_name}")
```

### GOLD (Type 8)

```python
result = parser.parse_combat_log("match.dem", types=[8], max_entries=100)

for entry in result.entries:
    if entry.gold > 0:
        print(f"[{entry.game_time_str}] {entry.target_name} gained {entry.gold} gold")
```

### XP (Type 10)

```python
result = parser.parse_combat_log("match.dem", types=[10], max_entries=100)

for entry in result.entries:
    if entry.xp > 0:
        print(f"[{entry.game_time_str}] {entry.target_name} gained {entry.xp} XP")
```

---

## Filtering

### By Type

```python
# Only damage and death
result = parser.parse_combat_log("match.dem", types=[0, 4], max_entries=500)
```

### By Hero

```python
# Only hero-to-hero combat
result = parser.parse_combat_log("match.dem", heroes_only=True, max_entries=500)
```

### Combined

```python
# Hero damage only
result = parser.parse_combat_log("match.dem", types=[0], heroes_only=True, max_entries=500)
```

---

## Unit Name Format

Unit names follow Dota 2's internal naming:

| Pattern | Example | Description |
|---------|---------|-------------|
| `npc_dota_hero_*` | `npc_dota_hero_axe` | Hero |
| `npc_dota_creep_*` | `npc_dota_creep_badguys_melee` | Lane creep |
| `npc_dota_neutral_*` | `npc_dota_neutral_centaur_khan` | Neutral creep |
| `npc_dota_*tower*` | `npc_dota_badguys_tower1_mid` | Tower |
| `npc_dota_roshan` | `npc_dota_roshan` | Roshan |

---

## Timing Note

Combat log entries typically appear after 12-17 minutes of game time. For early-game events, use `parse_game_events()` instead.
