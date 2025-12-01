
# Combat Log Guide

??? info "AI Summary"
    Parse structured combat log entries with `parse_combat_log()`. Filter by 45 log types including DAMAGE (0), HEAL (1), MODIFIER_ADD (2), DEATH (4), ABILITY (5), ITEM (6), FIRST_BLOOD (18). 80+ fields per entry including health tracking, stun/slow durations, assist players, damage types, hero levels, and location. Use `heroes_only=True` for hero-related entries. Ideal for fight reconstruction and damage analysis. Note: `timestamp` is replay time (includes draft), not game clock - convert using `m_pGameRules.m_flPreGameStartTime`.

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
| 0 | DOTA_COMBATLOG_DAMAGE | Damage dealt to units |
| 1 | DOTA_COMBATLOG_HEAL | Healing received |
| 2 | DOTA_COMBATLOG_MODIFIER_ADD | Buff/debuff applied |
| 3 | DOTA_COMBATLOG_MODIFIER_REMOVE | Buff/debuff removed |
| 4 | DOTA_COMBATLOG_DEATH | Unit death |
| 5 | DOTA_COMBATLOG_ABILITY | Ability cast |
| 6 | DOTA_COMBATLOG_ITEM | Item used |
| 7 | DOTA_COMBATLOG_LOCATION | Location event |
| 8 | DOTA_COMBATLOG_GOLD | Gold gained |
| 9 | DOTA_COMBATLOG_GAME_STATE | Game state change |
| 10 | DOTA_COMBATLOG_XP | Experience gained |
| 11 | DOTA_COMBATLOG_PURCHASE | Item purchased |
| 12 | DOTA_COMBATLOG_BUYBACK | Buyback used |
| 13 | DOTA_COMBATLOG_ABILITY_TRIGGER | Ability triggered |
| 14 | DOTA_COMBATLOG_PLAYERSTATS | Player statistics |
| 15 | DOTA_COMBATLOG_MULTIKILL | Multi-kill event |
| 16 | DOTA_COMBATLOG_KILLSTREAK | Kill streak |
| 17 | DOTA_COMBATLOG_TEAM_BUILDING_KILL | Building destroyed |
| 18 | DOTA_COMBATLOG_FIRST_BLOOD | First blood |
| 19 | DOTA_COMBATLOG_MODIFIER_REFRESH | Modifier refreshed |
| 20 | DOTA_COMBATLOG_NEUTRAL_CAMP_STACK | Camp stacked |
| 21 | DOTA_COMBATLOG_PICKUP_RUNE | Rune picked up |
| 22 | DOTA_COMBATLOG_REVEALED_INVISIBLE | Invisibility revealed |
| 23 | DOTA_COMBATLOG_HERO_SAVED | Hero saved from death |
| 24 | DOTA_COMBATLOG_MANA_RESTORED | Mana restored |
| 25 | DOTA_COMBATLOG_HERO_LEVELUP | Hero level up |
| 26 | DOTA_COMBATLOG_BOTTLE_HEAL_ALLY | Bottle heal ally |
| 27 | DOTA_COMBATLOG_ENDGAME_STATS | End game statistics |
| 28 | DOTA_COMBATLOG_INTERRUPT_CHANNEL | Channel interrupted |
| 29 | DOTA_COMBATLOG_ALLIED_GOLD | Allied gold |
| 30 | DOTA_COMBATLOG_AEGIS_TAKEN | Aegis taken |
| 31 | DOTA_COMBATLOG_MANA_DAMAGE | Mana burned |
| 32 | DOTA_COMBATLOG_PHYSICAL_DAMAGE_PREVENTED | Physical damage blocked |
| 33 | DOTA_COMBATLOG_UNIT_SUMMONED | Unit summoned |
| 34 | DOTA_COMBATLOG_ATTACK_EVADE | Attack evaded |
| 35 | DOTA_COMBATLOG_TREE_CUT | Tree cut |
| 36 | DOTA_COMBATLOG_SUCCESSFUL_SCAN | Successful scan |
| 37 | DOTA_COMBATLOG_END_KILLSTREAK | Kill streak ended |
| 38 | DOTA_COMBATLOG_BLOODSTONE_CHARGE | Bloodstone charge |
| 39 | DOTA_COMBATLOG_CRITICAL_DAMAGE | Critical damage |
| 40 | DOTA_COMBATLOG_SPELL_ABSORB | Spell absorbed |
| 41 | DOTA_COMBATLOG_UNIT_TELEPORTED | Unit teleported |
| 42 | DOTA_COMBATLOG_KILL_EATER_EVENT | Kill eater (gem) event |
| 43 | DOTA_COMBATLOG_NEUTRAL_ITEM_EARNED | Neutral item earned |
| 44 | DOTA_COMBATLOG_TELEPORT_INTERRUPTED | Teleport interrupted |

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

## Entry Fields (80+ Total)

Each `CombatLogEntry` contains comprehensive data for fight analysis:

### Core Fields

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Game tick |
| `net_tick` | int | Network tick |
| `type` | int | Combat log type ID (0-44) |
| `type_name` | str | Human-readable type name |
| `timestamp` | float | Game time in seconds |
| `timestamp_raw` | float | Raw timestamp value |

### Participant Fields

| Field | Type | Description |
|-------|------|-------------|
| `target_name` | str | Target unit name (e.g., "npc_dota_hero_pudge") |
| `target_source_name` | str | Target's source name |
| `attacker_name` | str | Attacker unit name |
| `damage_source_name` | str | Damage source name |
| `inflictor_name` | str | Ability/item that caused this |

### Participant Flags

| Field | Type | Description |
|-------|------|-------------|
| `is_attacker_illusion` | bool | Attacker is an illusion |
| `is_attacker_hero` | bool | Attacker is a hero |
| `is_target_illusion` | bool | Target is an illusion |
| `is_target_hero` | bool | Target is a hero |
| `is_target_building` | bool | Target is a building |

### Combat Values

| Field | Type | Description |
|-------|------|-------------|
| `value` | int | Damage/heal amount |
| `health` | int | Target HP **after** this event |
| `damage_type` | int | Damage type (physical/magical/pure) |
| `damage_category` | int | Damage category |

### CC Durations

| Field | Type | Description |
|-------|------|-------------|
| `stun_duration` | float | Stun duration in seconds |
| `slow_duration` | float | Slow duration in seconds |
| `modifier_duration` | float | Total modifier duration |
| `modifier_elapsed_duration` | float | How long modifier has been active |

### Location

| Field | Type | Description |
|-------|------|-------------|
| `location_x` | float | X coordinate on map |
| `location_y` | float | Y coordinate on map |

### Assist Tracking

| Field | Type | Description |
|-------|------|-------------|
| `assist_player0` | int | First assist player ID |
| `assist_player1` | int | Second assist player ID |
| `assist_player2` | int | Third assist player ID |
| `assist_player3` | int | Fourth assist player ID |
| `assist_players` | List[int] | All assist player IDs |

### Modifier Flags

| Field | Type | Description |
|-------|------|-------------|
| `root_modifier` | bool | Is a root effect |
| `silence_modifier` | bool | Is a silence effect |
| `aura_modifier` | bool | Is an aura |
| `armor_debuff_modifier` | bool | Is armor reduction |
| `motion_controller_modifier` | bool | Is motion control (knockback) |
| `invisibility_modifier` | bool | Grants invisibility |
| `hidden_modifier` | bool | Is hidden modifier |
| `modifier_hidden` | bool | Modifier is hidden from UI |
| `modifier_purged` | bool | Modifier was purged |
| `no_physical_damage_modifier` | bool | Blocks physical damage |

### Ability Info

| Field | Type | Description |
|-------|------|-------------|
| `ability_level` | int | Ability level (1-4+) |
| `is_ability_toggle_on` | bool | Ability toggled on |
| `is_ability_toggle_off` | bool | Ability toggled off |
| `is_ultimate_ability` | bool | Is an ultimate ability |
| `inflictor_is_stolen_ability` | bool | Ability was stolen (Rubick) |
| `spell_generated_attack` | bool | Attack from spell |
| `uses_charges` | bool | Ability uses charges |

### Kill/Death Info

| Field | Type | Description |
|-------|------|-------------|
| `spell_evaded` | bool | Spell was evaded |
| `long_range_kill` | bool | Long range kill |
| `will_reincarnate` | bool | Target will reincarnate (Aegis/WK) |
| `total_unit_death_count` | int | Total deaths of this unit type |
| `heal_from_lifesteal` | bool | Heal is from lifesteal |
| `is_heal_save` | bool | Heal prevented death |

### Hero State

| Field | Type | Description |
|-------|------|-------------|
| `attacker_hero_level` | int | Attacker's hero level |
| `target_hero_level` | int | Target's hero level |
| `attacker_has_scepter` | bool | Attacker has Aghanim's Scepter |
| `attacker_team` | int | Attacker team (2=Radiant, 3=Dire) |
| `target_team` | int | Target team |

### Visibility

| Field | Type | Description |
|-------|------|-------------|
| `is_visible_radiant` | bool | Visible to Radiant team |
| `is_visible_dire` | bool | Visible to Dire team |
| `at_night_time` | bool | Event occurred at night |

### Economy

| Field | Type | Description |
|-------|------|-------------|
| `xp` | int | XP gained/reason |
| `gold` | int | Gold gained/reason |
| `last_hits` | int | Last hits at time |
| `networth` | int | Player networth |
| `xpm` | int | XP per minute |
| `gpm` | int | Gold per minute |

### Additional

| Field | Type | Description |
|-------|------|-------------|
| `stack_count` | int | Modifier stack count |
| `building_type` | int | Building type ID |
| `neutral_camp_type` | int | Neutral camp type |
| `neutral_camp_team` | int | Neutral camp team |
| `rune_type` | int | Rune type |
| `obs_wards_placed` | int | Observer wards placed |
| `regenerated_health` | float | Health regenerated |
| `target_is_self` | bool | Target is self |

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

### Timestamp is Replay Time, Not Game Time

!!! warning

    The `timestamp` field in combat log entries is **replay time** (from recording start), NOT game clock time. Replay time includes draft and pre-game phases, so early game events may appear to have timestamps of 10-15+ minutes.

To convert to actual game time:

```python
from python_manta import MantaParser

parser = MantaParser()

# Get pre-game start time from game rules
rules = parser.query_entities("match.dem", class_filter="GamerulesProxy", at_tick=30000)
pre_game_start = rules.entities[0].properties.get("m_pGameRules.m_flPreGameStartTime", 0)

# Convert replay timestamp to game time
# Pre-game phase is 90 seconds before 0:00 (creep spawn)
def replay_to_game_time(replay_timestamp: float) -> float:
    return replay_timestamp - pre_game_start - 90

# Example: First blood at replay timestamp 1011.6s
# With pre_game_start = 910.77s
# Game time = 1011.6 - 910.77 - 90 = 10.83s (0:10)
```

### Quick Timing Check

```python
result = parser.parse_combat_log("match.dem", types=[18], max_entries=1)  # First blood

if result.entries:
    entry = result.entries[0]
    game_time = replay_to_game_time(entry.timestamp)
    mins = int(game_time // 60)
    secs = int(game_time % 60)
    print(f"First blood at game time: {mins}:{secs:02d}")
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
| Structure | Fixed schema with 80+ fields | Variable fields per event type |
| Types | 45 log types | 364 event types |
| Best for | Detailed damage/heal analysis | Discrete game occurrences |
| Timing | Full match (timestamp is replay time) | Full match |
| Filtering | By type ID, heroes_only | By event name |

Use combat log for continuous combat data (DPS, healing totals) and game events for discrete occurrences (tower kills, rune pickups).

---

## Available Data Fields

The combat log exposes raw data that can be used by other tools for analysis or narrative generation.

### Data Available Per Event

| Data Point | Field | Notes |
|------------|-------|-------|
| HP after event | `health` | Target's HP after this event |
| Damage/heal amount | `value` | Raw numeric value |
| Ability/item name | `inflictor_name` | Internal name (e.g., "pugna_nether_blast") |
| Ability level | `ability_level` | 1-4+ |
| Assist player IDs | `assist_players` | List of player IDs |
| Stun duration | `stun_duration` | Seconds |
| Slow duration | `slow_duration` | Seconds |
| Root applied | `root_modifier` | Boolean |
| Lifesteal heal | `heal_from_lifesteal` | Boolean |
| Will reincarnate | `will_reincarnate` | Boolean (Aegis/WK) |
| Night time | `at_night_time` | Boolean |
| Has Aghanim's | `attacker_has_scepter` | Boolean |
| Hero levels | `attacker_hero_level`, `target_hero_level` | Integer |
| Position | `location_x`, `location_y` | Map coordinates |
| Timestamp | `timestamp` | Game time in seconds |

### Data NOT Available in Combat Log

| Data Point | Notes |
|------------|-------|
| `stack_count` | Always 0 - Valve doesn't populate this field |
| `uses_charges` | Always false - Valve doesn't populate this field |
| Cooldowns | Not in combat log |
| Mana costs | Not in combat log |
| Exact max HP | Only current HP after event |

!!! tip "Getting Item Charges"

    The combat log `stack_count` field is NOT populated by Valve. To get actual item charges (e.g., Magic Stick/Wand), use entity queries instead:

    ```python
    from python_manta import MantaParser

    parser = MantaParser()

    def get_magic_stick_charges(demo_path: str, at_tick: int = 0) -> dict:
        """
        Get magic stick/wand charges for all players at a specific game tick.

        Args:
            demo_path: Path to the .dem file
            at_tick: Game tick to query (0 = end of game)

        Returns:
            Dict mapping player_id -> charges
        """
        result = parser.query_entities(
            demo_path,
            class_names=['CDOTA_Item_MagicStick', 'CDOTA_Item_MagicWand'],
            property_filter=['m_iCurrentCharges', 'm_iPlayerOwnerID'],
            at_tick=at_tick
        )

        player_charges = {}
        for entity in result.entities:
            owner = entity.properties.get('m_iPlayerOwnerID', -1)
            charges = entity.properties.get('m_iCurrentCharges', 0)
            if owner >= 0:
                player_charges[owner] = max(player_charges.get(owner, 0), charges)

        return player_charges

    # Get charges at a specific tick
    charges = get_magic_stick_charges("match.dem", at_tick=50000)
    # {0: 6, 2: 18, 4: 7, 6: 6, 8: 1, 10: 15, 12: 4, 14: 20, 16: 0, 18: 5}
    ```

    **Alternative**: Calculate charges from HEAL event value (Magic Stick/Wand heal 15 HP per charge):

    ```python
    # From a combat log HEAL entry with inflictor_name containing "magic_stick" or "magic_wand"
    charges_used = entry.value // 15  # e.g., 150 HP healed = 10 charges
    ```
