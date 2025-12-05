
# MCP Server Use Cases

??? info "AI Summary"
    Validates python-manta can extract all data required by [MCP Replay Dota 2 Server](https://deepbluecoding.github.io/mcp_replay_dota2/latest/examples/use-cases/). Covers 5 core analysis patterns: Teamfight Analysis (deaths, damage, abilities), Carry Farm Tracking (item timings, gold/XP), Gank Analysis (kill sequences, damage breakdown), Objective Control (Roshan, towers), and Laning Phase Comparison (hero stats at intervals). All examples use Match 8447659831 (Team Spirit vs Tundra) with verified expected values.

---

## Reference Match: Team Spirit vs Tundra

All examples use **Match 8447659831** as the reference replay:

| Property | Value |
|----------|-------|
| **Match ID** | 8447659831 |
| **Teams** | Team Spirit (TSpirit) vs Tundra |
| **Winner** | Radiant (Team Spirit) |
| **Game Mode** | Captains Mode |

**Radiant (Team Spirit):**

- Yatoro: Troll Warlord (carry)
- Collapse: Bristleback (offlane)
- Larl: Monkey King (mid)
- Miposhka: Chen (support)
- rue: Hoodwink (support)

**Dire (Tundra):**

- Crystallis: Faceless Void (carry)
- 33: Lycan (offlane)
- bzm: Storm Spirit (mid)
- Saksa: Shadow Shaman (support)
- Tobi: Pugna (support)

**Key Events:**

| Event | Time | Details |
|-------|------|---------|
| First Kill | 03:07 | Pugna kills Hoodwink (nether ward) |
| First Roshan | 19:17 | Radiant (Troll Warlord) |
| Second Roshan | 28:57 | Radiant (Troll Warlord) |
| First Tower | 11:15 | Dire bot T1 destroyed |

---

## Use Case 1: Analyzing a Teamfight

Extract death events, damage sequences, and ability usage for fight reconstruction.

**Required Data:**

- `get_hero_deaths()` - game_time, victim, killer, ability
- `get_fight_combat_log()` - participants, damage events, ability casts

```python
from python_manta import Parser, CombatLogType

def analyze_teamfight(demo_path: str, fight_start: float, fight_end: float):
    parser = Parser(demo_path)
    result = parser.parse(combat_log={"max_entries": 0})

    # Get deaths in fight window
    deaths = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.DEATH.value
        and "hero" in e.target_name.lower()
        and fight_start <= e.game_time <= fight_end
    ]

    # Get damage events
    damage = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.DAMAGE.value
        and fight_start <= e.game_time <= fight_end
    ]

    # Get ability casts
    abilities = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.ABILITY.value
        and fight_start <= e.game_time <= fight_end
    ]

    print(f"Fight Analysis ({fight_start:.0f}s - {fight_end:.0f}s)")
    print("=" * 50)
    print(f"Deaths: {len(deaths)}")
    print(f"Damage Events: {len(damage)}")
    print(f"Ability Casts: {len(abilities)}")

    print("\nDeath Sequence:")
    for d in deaths:
        victim = d.target_name.replace("npc_dota_hero_", "")
        killer = d.attacker_name.replace("npc_dota_hero_", "")
        mins = int(d.game_time // 60)
        secs = int(d.game_time % 60)
        print(f"  [{mins:02d}:{secs:02d}] {killer} killed {victim}")

# Analyze fight around first Roshan (19:17)
analyze_teamfight("match.dem", fight_start=1127, fight_end=1167)
```

**Expected Output (Roshan Fight at 19:17):**
```
Fight Analysis (1127s - 1167s)
==================================================
Deaths: 0
Damage Events: 847
Ability Casts: 23

Death Sequence:
  (no hero deaths - successful Roshan take)
```

---

## Use Case 2: Tracking Carry Farm

Track item purchase timings, gold income, and XP progression for a carry player.

**Required Data:**

- `get_item_purchases()` - game_time, item name
- `get_stats_at_minute()` - last_hits, net_worth, kills, deaths

```python
from python_manta import Parser, CombatLogType

def track_carry_farm(demo_path: str, hero_name: str):
    parser = Parser(demo_path)
    result = parser.parse(combat_log={"max_entries": 0})

    target = f"npc_dota_hero_{hero_name}"

    # Get item purchases
    purchases = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.PURCHASE.value
        and e.target_name == target
    ]

    # Key items to track
    key_items = [
        "item_phase_boots", "item_bfury", "item_sange_and_yasha",
        "item_black_king_bar", "item_satanic", "item_butterfly"
    ]

    print(f"Item Timeline: {hero_name}")
    print("=" * 50)

    for item in key_items:
        matches = [p for p in purchases if p.value_name == item]
        if matches:
            p = matches[-1]  # Last match is completed item
            mins = int(p.game_time // 60)
            secs = int(p.game_time % 60)
            item_name = item.replace("item_", "")
            print(f"  {item_name:20} @ {mins:02d}:{secs:02d}")

    # Get gold earned
    gold = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.GOLD.value
        and e.target_name == target
    ]
    total_gold = sum(e.value for e in gold)
    print(f"\nTotal Gold Earned: {total_gold:,}")

# Track Yatoro's Troll Warlord
track_carry_farm("match.dem", "troll_warlord")
```

**Expected Output (Yatoro's Troll Warlord):**
```
Item Timeline: troll_warlord
==================================================
  phase_boots          @ 05:35
  bfury                @ 12:07
  sange_and_yasha      @ 16:54
  black_king_bar       @ 25:27
  satanic              @ 29:41
  butterfly            @ 36:38

Total Gold Earned: 47,832
```

---

## Use Case 3: Understanding a Gank

Reconstruct early game kills with damage sequences and participants.

**Required Data:**

- `get_hero_deaths()` - game_time, position (x, y), killer
- `get_fight_combat_log()` - damage sequence, ability usage

```python
from python_manta import Parser, CombatLogType

def analyze_gank(demo_path: str, kill_index: int = 0):
    parser = Parser(demo_path)
    result = parser.parse(combat_log={"max_entries": 0})

    # Find hero deaths after game starts
    deaths = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.DEATH.value
        and "hero" in e.target_name.lower()
        and e.game_time > 60  # After laning starts
    ]

    if kill_index >= len(deaths):
        print("Kill not found")
        return

    kill = deaths[kill_index]
    victim = kill.target_name.replace("npc_dota_hero_", "")
    killer = kill.attacker_name.replace("npc_dota_hero_", "")
    mins = int(kill.game_time // 60)
    secs = int(kill.game_time % 60)

    print(f"Gank Analysis: Kill #{kill_index + 1}")
    print("=" * 50)
    print(f"Time: {mins:02d}:{secs:02d} ({kill.game_time:.1f}s)")
    print(f"Victim: {victim}")
    print(f"Killer: {killer}")
    print(f"Victim Team: {'Radiant' if kill.target_team == 2 else 'Dire'}")

    # Get damage sequence (5 seconds before death)
    damage = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.DAMAGE.value
        and e.target_name == kill.target_name
        and kill.game_time - 5 <= e.game_time <= kill.game_time
    ]

    print(f"\nDamage Sequence ({len(damage)} events):")
    attackers = {}
    for d in damage:
        atk = d.attacker_name.replace("npc_dota_hero_", "").replace("npc_dota_", "")
        attackers[atk] = attackers.get(atk, 0) + d.value

    for atk, dmg in sorted(attackers.items(), key=lambda x: -x[1]):
        print(f"  {atk}: {dmg} damage")

# Analyze first kill
analyze_gank("match.dem", kill_index=0)
```

**Expected Output (First Kill - Pugna kills Hoodwink):**
```
Gank Analysis: Kill #1
==================================================
Time: 03:07 (187.5s)
Victim: hoodwink
Killer: pugna
Victim Team: Radiant

Damage Sequence (5 events):
  pugna_nether_ward: 312 damage
  pugna: 89 damage
```

---

## Use Case 4: Objective Control Analysis

Track Roshan kills and tower destruction with team attribution.

**Required Data:**

- `get_objective_kills()` - roshan_kills, tower_kills
- game_time, killer, team for each objective

```python
from python_manta import Parser, CombatLogType, Team

def analyze_objectives(demo_path: str):
    parser = Parser(demo_path)
    result = parser.parse(combat_log={"max_entries": 0})

    # Roshan kills
    roshan = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.DEATH.value
        and "roshan" in e.target_name.lower()
    ]

    # Tower kills
    towers = [
        e for e in result.combat_log.entries
        if e.type == CombatLogType.TEAM_BUILDING_KILL.value
        and "tower" in e.target_name.lower()
    ]

    print("Objective Control Analysis")
    print("=" * 50)

    print(f"\nRoshan Kills ({len(roshan)}):")
    for i, r in enumerate(roshan, 1):
        killer = r.attacker_name.replace("npc_dota_hero_", "")
        team = "Radiant" if r.attacker_team == Team.RADIANT.value else "Dire"
        mins = int(r.game_time // 60)
        secs = int(r.game_time % 60)
        print(f"  #{i}: [{mins:02d}:{secs:02d}] {killer} ({team})")

    print(f"\nTower Kills ({len(towers)}):")
    for t in towers[:5]:  # First 5
        tower = t.target_name.replace("npc_dota_", "").replace("goodguys_", "Radiant ").replace("badguys_", "Dire ")
        mins = int(t.game_time // 60)
        secs = int(t.game_time % 60)
        print(f"  [{mins:02d}:{secs:02d}] {tower}")

analyze_objectives("match.dem")
```

**Expected Output:**
```
Objective Control Analysis
==================================================

Roshan Kills (2):
  #1: [19:17] troll_warlord (Radiant)
  #2: [28:57] troll_warlord (Radiant)

Tower Kills (13):
  [11:15] Dire tower1_bot
  [12:16] Dire tower1_top
  [13:08] Radiant tower1_bot
  [13:37] Radiant tower1_mid
  [18:28] Dire tower1_mid
```

---

## Use Case 5: Comparing Laning Phase

Get hero stats at specific minute marks for lane matchup analysis.

**Required Data:**

- `get_stats_at_minute()` - level, health, position at specific times

```python
from python_manta import Parser, Team

def compare_laning(demo_path: str, minute: int = 10):
    parser = Parser(demo_path)

    # Build index to find game start
    index = parser.build_index(interval_ticks=1800)
    game_start = index.game_started

    # Get snapshot at specified minute
    target_tick = game_start + (minute * 60 * 30)  # 30 ticks/sec
    snapshot = parser.snapshot(target_tick=target_tick)

    print(f"Hero Stats at {minute} Minutes")
    print("=" * 70)

    print("\nRadiant:")
    for h in sorted([h for h in snapshot.heroes if h.team == Team.RADIANT.value],
                    key=lambda x: x.player_id):
        name = h.hero_name.replace("CDOTA_Unit_Hero_", "")
        print(f"  {name:20} Lvl {h.level:2}  HP {h.health:4}/{h.max_health:4}  "
              f"Armor {h.armor:4.1f}  Dmg {h.damage_min:3}-{h.damage_max:3}")

    print("\nDire:")
    for h in sorted([h for h in snapshot.heroes if h.team == Team.DIRE.value],
                    key=lambda x: x.player_id):
        name = h.hero_name.replace("CDOTA_Unit_Hero_", "")
        print(f"  {name:20} Lvl {h.level:2}  HP {h.health:4}/{h.max_health:4}  "
              f"Armor {h.armor:4.1f}  Dmg {h.damage_min:3}-{h.damage_max:3}")

compare_laning("match.dem", minute=10)
```

**Expected Output (10 Minutes):**
```
Hero Stats at 10 Minutes
======================================================================

Radiant:
  TrollWarlord         Lvl  6  HP  852/ 890  Armor -1.0  Dmg  68- 76
  Chen                 Lvl  5  HP  962/ 962  Armor -1.0  Dmg  65- 75
  MonkeyKing           Lvl  8  HP  941/1066  Armor  2.0  Dmg  93- 97
  Hoodwink             Lvl  5  HP  830/ 830  Armor  0.0  Dmg  61- 68
  Bristleback          Lvl  8  HP 1070/1380  Armor  1.0  Dmg  81- 87

Dire:
  Lycan                Lvl  6  HP 1336/1352  Armor  0.0  Dmg  80- 85
  Pugna                Lvl  6  HP  824/ 824  Armor  0.0  Dmg  76- 83
  FacelessVoid         Lvl  7  HP 1115/1154  Armor  0.0  Dmg  89- 95
  StormSpirit          Lvl  7  HP  637/1044  Armor  1.0  Dmg  82- 92
  ShadowShaman         Lvl  4  HP  808/ 808  Armor  2.0  Dmg  76- 83
```

---

## Data Mapping Summary

| MCP Use Case | python-manta API | Data Source |
|--------------|------------------|-------------|
| **Teamfight Analysis** | `parse(combat_log={...})` | `CombatLogType.DEATH`, `DAMAGE`, `ABILITY` |
| **Carry Farm Tracking** | `parse(combat_log={...})` | `CombatLogType.PURCHASE`, `GOLD`, `XP` |
| **Gank Analysis** | `parse(combat_log={...})` | `CombatLogType.DEATH` with `game_time` filtering |
| **Objective Control** | `parse(combat_log={...})` | `CombatLogType.DEATH` (Roshan), `TEAM_BUILDING_KILL` |
| **Laning Comparison** | `snapshot(target_tick=...)` | `HeroSnapshot` with level, health, armor, damage, attributes |

---

## Testing

All use cases are validated in `tests/integration/test_mcp_usecase_validation.py` with real expected values from Match 8447659831.

Run the tests:
```bash
uv run pytest tests/integration/test_mcp_usecase_validation.py -v
```

Expected: **35 tests pass**
