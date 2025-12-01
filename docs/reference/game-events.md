
# Game Events Reference

??? info "AI Summary"
    Complete reference for 364 Source 1 legacy game events in Dota 2 replays. Events are organized by category: Player (kills, denies, abilities), Unit (towers, barracks, roshan), Item (purchases, pickups), Rune (spawns, activations), Game State (match events), and Combat (combatlog). Use `parse_game_events()` with `capture_types=True` to discover all available events in a replay.

---

## Event Categories

### Player Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_player_kill` | Player killed another player | `victim_userid`, `killer1_userid`, `killer2_userid`-`killer5_userid` |
| `dota_player_deny` | Player denied a unit | `killer_userid`, `denied_userid` |
| `dota_player_pick_hero` | Player picked a hero | `player`, `heroindex`, `hero` |
| `dota_player_learned_ability` | Player learned an ability | `player`, `abilityname` |
| `dota_player_used_ability` | Player used an ability | `player`, `abilityname` |
| `dota_player_gained_level` | Player leveled up | `player`, `level` |
| `dota_player_take_tower_damage` | Player took tower damage | `player`, `damage` |
| `dota_player_update_hero_selection` | Hero selection updated | `player` |
| `dota_player_update_selected_unit` | Selected unit changed | `player` |
| `dota_player_update_query_unit` | Query unit changed | `player` |
| `dota_player_update_killcam_unit` | Killcam unit changed | `player` |

### Unit Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_tower_kill` | Tower destroyed | `killer_userid`, `teamnumber`, `gold` |
| `dota_barracks_kill` | Barracks destroyed | `killer_userid`, `teamnumber` |
| `dota_roshan_kill` | Roshan killed | `teamnumber` |
| `dota_courier_lost` | Courier killed | `teamnumber` |
| `dota_npc_goal_reached` | NPC reached goal | `npc_entindex` |
| `dota_hero_swap` | Heroes swapped | `playerid1`, `playerid2` |

### Item Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_item_purchased` | Item purchased | `userid`, `itemname` |
| `dota_item_combined` | Items combined | `userid`, `itemname` |
| `dota_item_picked_up` | Item picked up | `userid`, `itemname` |
| `dota_inventory_changed` | Inventory changed | `userid` |
| `dota_item_given` | Item given to another | `userid`, `itemname`, `recipientuserid` |

### Rune Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_rune_activated` | Rune activated | `player_id`, `rune` |
| `dota_rune_spawned` | Rune spawned | `rune`, `pos_x`, `pos_y`, `pos_z` |
| `dota_bounty_rune_pickup` | Bounty rune picked up | `player_id`, `team`, `gold` |
| `dota_neutral_token_pickup` | Neutral token picked up | `player_id` |

### Game State Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_match_done` | Match ended | `winningteam`, `radiant_score`, `dire_score` |
| `dota_game_state_change` | Game state changed | `old_state`, `new_state` |
| `game_rules_state_change` | Game rules changed | `state` |
| `dota_team_kill_credit` | Team credited with kill | `killer_userid`, `victim_userid`, `teamnumber` |
| `dota_aegis_event` | Aegis event | `player_id`, `event` |
| `dota_buyback` | Player bought back | `player_id`, `cost` |
| `dota_glyph_used` | Glyph activated | `teamnumber` |

### Combat Events

| Event Name | Description | Key Fields |
|------------|-------------|------------|
| `dota_combatlog` | Combat log entry | `type`, `sourcename`, `targetname`, `value` |
| `dota_player_take_tower_damage` | Tower damage taken | `player`, `damage` |

---

## Event Field Types

Fields in game events are automatically typed:

| Go Type | Python Type | Example |
|---------|-------------|---------|
| `string` | `str` | `"npc_dota_hero_axe"` |
| `float` | `float` | `123.456` |
| `long` | `int` | `1234567890` |
| `short` | `int` | `12345` |
| `byte` | `int` | `255` |
| `bool` | `bool` | `True` |
| `uint64` | `int` | `76561198012345678` |

---

## Discovering Events

Get all event types available in a replay:

```python
from python_manta import MantaParser

parser = MantaParser()
result = parser.parse_game_events("match.dem", capture_types=True, max_events=0)

print(f"Total event types: {len(result.event_types)}")
for event_type in sorted(result.event_types):
    print(f"  {event_type}")
```

---

## Common Event Patterns

### Kill Events

```python
# dota_player_kill fields
{
    "victim_userid": int,      # Victim player ID
    "killer1_userid": int,     # Primary killer
    "killer2_userid": int,     # Assist 1 (optional)
    "killer3_userid": int,     # Assist 2 (optional)
    "killer4_userid": int,     # Assist 3 (optional)
    "killer5_userid": int,     # Assist 4 (optional)
}
```

### Tower Kill Events

```python
# dota_tower_kill fields
{
    "killer_userid": int,      # Killer player ID
    "teamnumber": int,         # 2=Radiant, 3=Dire (tower team)
    "gold": int,               # Gold awarded
}
```

### Combatlog Events

```python
# dota_combatlog fields
{
    "type": int,               # Combat log type
    "sourcename": str,         # Source unit
    "targetname": str,         # Target unit
    "value": int,              # Damage/heal amount
}
```

---

## All 364 Event Types

Use `capture_types=True` to get the complete list for your specific replay. The actual events available depend on the game version and what occurred during the match.

Common categories include:

- `dota_player_*` - Player actions
- `dota_npc_*` - NPC actions
- `dota_item_*` - Item events
- `dota_rune_*` - Rune events
- `dota_tower_*` - Tower events
- `dota_roshan_*` - Roshan events
- `dota_game_*` - Game state events
- `dota_tutorial_*` - Tutorial events
- `dota_ability_*` - Ability events
- `game_*` - Engine game events
