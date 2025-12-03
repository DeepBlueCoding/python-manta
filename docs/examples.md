
# Examples

??? info "AI Summary"
    Complete working examples for common Dota 2 replay analysis tasks. All examples use **TI 2025 Grand Finals Game 5** (XG vs Falcons, Match ID: 8461956309) as the reference replay. Includes: match summary generator (header + draft + final stats), kill timeline builder, item build tracker (via combat log type 11), item usage tracker (combat log type 6), Lotus Orb detection (ability triggers type 13), neutral item tracker (pickups via FoundNeutralItem, usage via combat log, buffs via modifiers), ward placement analyzer, damage report generator, rune tracking, and defensive item analysis (Outworld Staff vs Omnislash). Each example demonstrates combining multiple API methods for real analysis workflows.

---

## Example Match: TI 2025 Grand Finals Game 5

All examples in this documentation use **The International 2025 Grand Finals Game 5** as the reference replay:

| Property | Value |
|----------|-------|
| **Match ID** | 8461956309 |
| **Event** | The International 2025 Grand Finals |
| **Teams** | Xtreme Gaming (XG) vs Team Falcons (FLCN) |
| **Winner** | Falcons (Dire) |
| **Duration** | 77.9 minutes |
| **Server** | Valve TI14 Server (Hamburg) |

**XG (Radiant):**
- Ame: Juggernaut
- Xm: Shadow Fiend
- Xxs: Earthshaker
- XinQ: Shadow Demon
- xNova: Pugna

**Falcons (Dire):**
- Sneyking: Naga Siren
- skiter: Medusa
- Malr1ne: Pangolier
- AMMAR_THE_F: Magnus
- Cr1t-: Disruptor

---

## Match Summary

Extract a complete match summary with draft, players, and final scores.

```python
from python_manta import MantaParser

def generate_match_summary(demo_path: str):
    parser = MantaParser()

    # Get header
    header = parser.parse_header(demo_path)
    print(f"Match Summary")
    print(f"{'='*50}")
    print(f"Map: {header.map_name}")
    print(f"Build: {header.build_num}")
    print(f"Server: {header.server_name}")

    # Get game info (draft)
    game_info = parser.parse_game_info(demo_path)
    print(f"\nDraft:")
    print("-" * 30)

    radiant_picks = []
    dire_picks = []
    for event in game_info.picks_bans:
        if event.is_pick:
            if event.team == 2:
                radiant_picks.append(event.hero_id)
            else:
                dire_picks.append(event.hero_id)

    print(f"Radiant picks: {radiant_picks}")
    print(f"Dire picks: {dire_picks}")

    # Get final hero stats
    heroes = parser.query_entities(
        demo_path,
        class_filter="Hero",
        property_filter=[
            "m_iCurrentLevel", "m_iKills", "m_iDeaths", "m_iAssists",
            "m_iTotalEarnedGold", "m_iLastHits", "m_iTeamNum"
        ],
        max_entities=10
    )

    print(f"\nFinal Scoreboard:")
    print("-" * 70)
    print(f"{'Hero':<35} {'Lvl':>4} {'K':>3} {'D':>3} {'A':>3} {'LH':>5} {'Gold':>7}")
    print("-" * 70)

    radiant = []
    dire = []
    for hero in heroes.entities:
        p = hero.properties
        team = p.get("m_iTeamNum", 0)
        stats = (hero.class_name, p.get("m_iCurrentLevel", 0), p.get("m_iKills", 0),
                 p.get("m_iDeaths", 0), p.get("m_iAssists", 0), p.get("m_iLastHits", 0),
                 p.get("m_iTotalEarnedGold", 0))

        if team == 2:
            radiant.append(stats)
        elif team == 3:
            dire.append(stats)

    print("RADIANT:")
    for name, lvl, k, d, a, lh, gold in radiant:
        print(f"  {name:<33} {lvl:>4} {k:>3} {d:>3} {a:>3} {lh:>5} {gold:>7,}")

    print("\nDIRE:")
    for name, lvl, k, d, a, lh, gold in dire:
        print(f"  {name:<33} {lvl:>4} {k:>3} {d:>3} {a:>3} {lh:>5} {gold:>7,}")

# Usage
generate_match_summary("match.dem")
```

**Expected Output (TI 2025 Grand Finals Game 5):**
```
Match Summary
==================================================
Map: start
Build: 10512
Server: Valve TI14 Server (srcds427-fra2.Hamburg.5)

Match ID: 8461956309
Duration: 77.9 minutes
Winner: Dire

Teams:
  Radiant: XG (ID: 8261500)
  Dire: FLCN (ID: 9247354)

Draft:
  Radiant picks: [7, 79, 11, 45, 8]  # Juggernaut, Shadow Fiend, Shadow Demon, Pugna, Earthshaker
  Dire picks: [89, 120, 87, 94, 97]  # Naga Siren, Pangolier, Disruptor, Medusa, Magnus

Players:
  [Radiant] Ame: juggernaut
  [Radiant] Xm: nevermore
  [Radiant] Xxs: earthshaker
  [Radiant] XinQ: shadow_demon
  [Radiant] xNova: pugna
  [Dire] Sneyking: naga_siren
  [Dire] skiter: medusa
  [Dire] Malr1ne: pangolier
  [Dire] AMMAR_THE_F: magnataur
  [Dire] Cr1t-: disruptor
```

---

## Kill Timeline

Build a chronological kill feed with timestamps.

```python
from python_manta import MantaParser

def build_kill_timeline(demo_path: str):
    parser = MantaParser()

    # Use game events for kills
    result = parser.parse_game_events(
        demo_path,
        event_filter="dota_player_kill",
        max_events=500
    )

    print("Kill Timeline")
    print("=" * 60)

    for event in result.events:
        tick = event.tick
        fields = event.fields

        victim = fields.get("victim_userid", "?")
        killer = fields.get("killer1_userid", "?")

        # Collect assisters
        assisters = []
        for i in range(2, 6):
            a = fields.get(f"killer{i}_userid")
            if a:
                assisters.append(str(a))

        # Format output
        assist_str = f" + {', '.join(assisters)}" if assisters else ""
        print(f"[Tick {tick:>7}] Player {killer}{assist_str} killed Player {victim}")

    print(f"\nTotal kills: {len(result.events)}")

# Usage
build_kill_timeline("match.dem")
```

---

## Item Build Tracker

Track item purchases for each player throughout the match using combat log.

```python
from python_manta import MantaParser, CombatLogType
from collections import defaultdict

def track_item_builds(demo_path: str):
    parser = MantaParser()

    # Item purchases are in combat log PURCHASE type
    result = parser.parse_combat_log(
        demo_path,
        types=[CombatLogType.PURCHASE],
        max_entries=2000
    )

    # Group by hero
    hero_items = defaultdict(list)

    for entry in result.entries:
        hero = entry.target_name.replace("npc_dota_hero_", "")
        item = entry.value_name.replace("item_", "")

        # Calculate game time
        mins = int(abs(entry.game_time) // 60)
        secs = int(abs(entry.game_time)) % 60
        sign = "-" if entry.game_time < 0 else ""

        hero_items[hero].append({
            "time": f"{sign}{mins:02d}:{secs:02d}",
            "item": item,
            "game_time": entry.game_time
        })

    print("Item Build Order by Hero")
    print("=" * 60)

    for hero in sorted(hero_items.keys()):
        items = hero_items[hero]
        print(f"\n{hero}: ({len(items)} items)")
        print("-" * 50)

        for i, item in enumerate(items, 1):
            print(f"  {i:>3}. [{item['time']}] {item['item']}")

# Usage
track_item_builds("match.dem")
```

**Expected Output (TI 2025 Grand Finals - Ame's Juggernaut build):**
```
Item Build Order by Hero
============================================================

juggernaut: (54 items)
--------------------------------------------------
    1. [01:04] recipe_wraith_band
    2. [01:54] wraith_band
    3. [02:06] boots_of_elves
    4. [03:35] gloves
    5. [04:53] boots
    6. [05:32] power_treads          # Power Treads at 5:32
    7. [08:05] cornucopia
    8. [09:36] broadsword
    9. [12:01] broadsword
   10. [13:17] recipe_bfury
   11. [13:44] bfury                 # Battle Fury at 13:44
   12. [14:18] blade_of_alacrity
   13. [15:14] boots_of_elves
   14. [15:31] recipe_yasha
   15. [16:11] yasha
   16. [16:56] diadem
   17. [19:20] recipe_manta
   18. [19:44] manta                 # Manta Style at 19:44
   19. [22:56] eagle
   20. [24:19] claymore
   21. [25:56] talisman_of_evasion
   22. [26:40] butterfly             # Butterfly at 26:40
   ...
```

---

## Ward Placement Analyzer

Analyze ward placement patterns from pings and events.

```python
from python_manta import MantaParser
from collections import defaultdict

def analyze_wards(demo_path: str):
    parser = MantaParser()

    # Get ward-related entities at end of game
    wards = parser.query_entities(
        demo_path,
        class_filter="Ward",
        property_filter=["m_vecOrigin", "m_iTeamNum", "m_iHealth"],
        max_entities=100
    )

    print("Ward Analysis")
    print("=" * 50)

    radiant_wards = []
    dire_wards = []

    for ward in wards.entities:
        pos = ward.properties.get("m_vecOrigin", [0, 0, 0])
        team = ward.properties.get("m_iTeamNum", 0)
        alive = ward.properties.get("m_iHealth", 0) > 0

        ward_info = {
            "class": ward.class_name,
            "position": (pos[0], pos[1]),
            "alive": alive
        }

        if team == 2:
            radiant_wards.append(ward_info)
        elif team == 3:
            dire_wards.append(ward_info)

    print(f"\nRadiant wards (end of game): {len(radiant_wards)}")
    for w in radiant_wards:
        status = "ALIVE" if w["alive"] else "dead"
        print(f"  {w['class']}: ({w['position'][0]:.0f}, {w['position'][1]:.0f}) [{status}]")

    print(f"\nDire wards (end of game): {len(dire_wards)}")
    for w in dire_wards:
        status = "ALIVE" if w["alive"] else "dead"
        print(f"  {w['class']}: ({w['position'][0]:.0f}, {w['position'][1]:.0f}) [{status}]")

# Usage
analyze_wards("match.dem")
```

---

## Damage Report

Generate a damage breakdown by hero and ability.

```python
from python_manta import MantaParser
from collections import defaultdict

def generate_damage_report(demo_path: str):
    parser = MantaParser()

    result = parser.parse_combat_log(
        demo_path,
        types=[0],  # Damage only
        heroes_only=True,
        max_entries=10000
    )

    # Aggregate damage by attacker
    damage_dealt = defaultdict(int)
    damage_taken = defaultdict(int)
    ability_damage = defaultdict(lambda: defaultdict(int))

    for entry in result.entries:
        if entry.is_attacker_hero:
            damage_dealt[entry.attacker_name] += entry.value

            if entry.inflictor_name:
                ability_damage[entry.attacker_name][entry.inflictor_name] += entry.value

        if entry.is_target_hero:
            damage_taken[entry.target_name] += entry.value

    print("Damage Report")
    print("=" * 60)

    print("\nTotal Damage Dealt:")
    print("-" * 40)
    for hero, dmg in sorted(damage_dealt.items(), key=lambda x: -x[1]):
        print(f"  {hero:<35}: {dmg:>10,}")

    print("\nTotal Damage Taken:")
    print("-" * 40)
    for hero, dmg in sorted(damage_taken.items(), key=lambda x: -x[1]):
        print(f"  {hero:<35}: {dmg:>10,}")

    print("\nTop Damage Sources by Hero:")
    print("-" * 60)
    for hero in sorted(ability_damage.keys()):
        abilities = ability_damage[hero]
        top_abilities = sorted(abilities.items(), key=lambda x: -x[1])[:5]

        print(f"\n{hero}:")
        for ability, dmg in top_abilities:
            print(f"    {ability:<30}: {dmg:>8,}")

# Usage
generate_damage_report("match.dem")
```

**Expected Output (TI 2025 Grand Finals):**
```
Damage Report
============================================================

Total Hero vs Hero Damage:
----------------------------------------
  medusa                              :    157,175
  juggernaut                          :    120,374
  earthshaker                         :    120,136
  nevermore                           :     78,853
  pugna                               :     46,453
  disruptor                           :     27,317
  magnataur                           :     24,803
  shadow_demon                        :     22,983
  pangolier                           :     22,755
  naga_siren                          :     20,433
```

Note: skiter's Medusa dealt the most hero damage (157k), while Ame's Juggernaut (120k) and Xxs's Earthshaker (120k) were the top damage dealers for XG.

---

## Team Fight Detector

Detect team fights by analyzing death clusters.

```python
from python_manta import MantaParser
from collections import defaultdict

def detect_team_fights(demo_path: str, tick_window: int = 600):
    parser = MantaParser()

    # Get deaths from combat log
    result = parser.parse_combat_log(
        demo_path,
        types=[4],  # Deaths
        heroes_only=True,
        max_entries=500
    )

    if not result.entries:
        print("No hero deaths found")
        return

    # Group deaths by time window
    fights = []
    current_fight = []

    for entry in sorted(result.entries, key=lambda e: e.tick):
        if not current_fight:
            current_fight.append(entry)
        elif entry.tick - current_fight[-1].tick <= tick_window:
            current_fight.append(entry)
        else:
            if len(current_fight) >= 3:  # At least 3 deaths = team fight
                fights.append(current_fight)
            current_fight = [entry]

    # Don't forget last fight
    if len(current_fight) >= 3:
        fights.append(current_fight)

    print("Team Fight Detection")
    print("=" * 60)
    print(f"Found {len(fights)} team fights (3+ deaths within {tick_window} ticks)")

    for i, fight in enumerate(fights, 1):
        start_tick = fight[0].tick
        end_tick = fight[-1].tick
        duration = end_tick - start_tick

        radiant_deaths = sum(1 for e in fight if e.target_team == 2)
        dire_deaths = sum(1 for e in fight if e.target_team == 3)

        print(f"\nFight #{i}: Tick {start_tick} - {end_tick} ({duration} ticks)")
        print(f"  Deaths: Radiant {radiant_deaths}, Dire {dire_deaths}")
        print(f"  Outcome: {'Radiant' if dire_deaths > radiant_deaths else 'Dire'} won")

        print(f"  Deaths:")
        for entry in fight:
            team = "R" if entry.target_team == 2 else "D"
            print(f"    [{team}] {entry.target_name} killed by {entry.attacker_name}")

# Usage
detect_team_fights("match.dem")
```

---

## Chat Log Extractor

Extract and format all chat messages.

```python
from python_manta import MantaParser

def extract_chat_log(demo_path: str):
    parser = MantaParser()

    result = parser.parse_universal(
        demo_path,
        "CDOTAUserMsg_ChatMessage",
        max_messages=1000
    )

    # Get string tables for player names (if available)
    userinfo = parser.get_string_tables(
        demo_path,
        table_names=["userinfo"],
        max_entries=20
    )

    print("Chat Log")
    print("=" * 60)

    chat_types = {1: "ALL", 2: "TEAM", 3: "SPEC"}

    for msg in result.messages:
        player_id = msg.data.get("source_player_id", "?")
        text = msg.data.get("message_text", "")
        chat_type = msg.data.get("chat_type", 0)

        if not text:
            continue

        type_str = chat_types.get(chat_type, "???")
        tick = msg.tick

        print(f"[{tick:>7}] [{type_str:>4}] Player {player_id}: {text}")

# Usage
extract_chat_log("match.dem")
```

**Expected Output (TI 2025 Grand Finals):**
```
Chat Log
============================================================
[ 27298] [ ALL] Player 0: gl hf
[ 27330] [ ALL] Player 5: hf
[ 27338] [ ALL] Player 1: gl
[ 27346] [ ALL] Player 6: glhf
[ 28882] [ ALL] Player 3: the lights are too much
[ 29194] [ ALL] Player 7: its fine
[ 29330] [ ALL] Player 0: g
[ 29378] [ ALL] Player 7: g
[ 29394] [ ALL] Player 9: G
[ 65954] [ ALL] Player 5: teamspeak delay
[ 66538] [ ALL] Player 0: g
[ 66618] [ ALL] Player 5: g
[ 66858] [ ALL] Player 9: g
[139170] [ ALL] Player 5: gg
[139250] [ ALL] Player 3: gg
```

Note: The TI Grand Finals captured the pre-game "gl hf" exchanges, a technical pause for "teamspeak delay", and the final "gg" at match end.

---

## Rune Tracking

Track rune pickups throughout the match using combat log modifiers.

```python
from python_manta import MantaParser, RuneType
from collections import defaultdict

def track_runes(demo_path: str):
    parser = MantaParser()

    # Rune pickups are tracked via combat log modifiers
    # When a hero picks up a rune, they receive a modifier_rune_* buff
    result = parser.parse_combat_log(
        demo_path,
        types=[2],  # MODIFIER_ADD only
        heroes_only=True,
        max_entries=50000
    )

    # Filter for rune modifiers using the RuneType enum
    rune_pickups = [
        e for e in result.entries
        if RuneType.is_rune_modifier(e.inflictor_name)
    ]

    print("Rune Tracking")
    print("=" * 50)
    print(f"\nTotal Rune Pickups: {len(rune_pickups)}")
    print("-" * 40)

    # Group by hero
    hero_runes = defaultdict(list)
    for pickup in rune_pickups:
        hero = pickup.target_name.replace("npc_dota_hero_", "")
        rune = RuneType.from_modifier(pickup.inflictor_name)
        rune_name = rune.display_name if rune else pickup.inflictor_name
        hero_runes[hero].append({
            "time": pickup.timestamp,
            "rune": rune_name
        })

    # Print timeline
    print("\nRune Pickup Timeline:")
    print("-" * 60)
    for pickup in rune_pickups:
        hero = pickup.target_name.replace("npc_dota_hero_", "")
        rune = RuneType.from_modifier(pickup.inflictor_name)
        rune_name = rune.display_name if rune else pickup.inflictor_name
        minutes = int(pickup.timestamp // 60)
        seconds = int(pickup.timestamp % 60)
        print(f"[{minutes:02d}:{seconds:02d}] {hero:<20} picked up {rune_name}")

    # Print summary by hero
    print("\nRunes by Hero:")
    print("-" * 40)
    for hero, runes in sorted(hero_runes.items()):
        rune_summary = ", ".join(r["rune"] for r in runes)
        print(f"  {hero}: {len(runes)} runes ({rune_summary})")

# Usage
track_runes("match.dem")
```

**Expected Output (TI 2025 Grand Finals):**
```
Rune Tracking
==================================================

Total Rune Pickups: 19
----------------------------------------

Rune Pickup Timeline:
------------------------------------------------------------
[23:30] naga_siren           picked up Arcane
[26:05] pangolier            picked up Invisibility
[28:44] pangolier            picked up Haste
[30:45] pangolier            picked up Double Damage
[35:56] pangolier            picked up Regeneration
[37:17] naga_siren           picked up Double Damage
[40:29] pangolier            picked up Invisibility
[41:24] pugna                picked up Shield
[44:55] pangolier            picked up Regeneration
[45:57] naga_siren           picked up Haste

Runes by Hero:
----------------------------------------
  naga_siren: 4 runes (Arcane, Double Damage, Haste, Arcane)
  pangolier: 8 runes (Invisibility, Haste, Double Damage, ...)
  pugna: 3 runes (Shield, Shield, Shield)
  ...
```

---

## Item Usage Tracker

Track when heroes use active items (smoke, wards, BKB, etc.).

```python
from python_manta import MantaParser, CombatLogType
from collections import defaultdict

def track_item_usage(demo_path: str):
    parser = MantaParser()

    # Item usage is in combat log ITEM type
    result = parser.parse_combat_log(
        demo_path,
        types=[CombatLogType.ITEM],
        heroes_only=True,
        max_entries=2000
    )

    print("Item Usage Tracking")
    print("=" * 60)
    print(f"Total item activations: {result.total_entries}\n")

    # Group by hero
    hero_usage = defaultdict(lambda: defaultdict(int))

    for entry in result.entries:
        hero = entry.attacker_name.replace("npc_dota_hero_", "")
        item = entry.inflictor_name.replace("item_", "")
        hero_usage[hero][item] += 1

    # Print usage by hero
    for hero in sorted(hero_usage.keys()):
        items = hero_usage[hero]
        print(f"\n{hero}:")
        for item, count in sorted(items.items(), key=lambda x: -x[1]):
            print(f"  {item}: {count}x")

# Usage
track_item_usage("match.dem")
```

---

## Lotus Orb Detection

Detect Lotus Orb spell reflections using ability triggers.

```python
from python_manta import MantaParser, CombatLogType

def detect_lotus_orb(demo_path: str):
    parser = MantaParser()

    # Ability triggers include Lotus Orb reflections
    result = parser.parse_combat_log(
        demo_path,
        types=[CombatLogType.ABILITY_TRIGGER],
        max_entries=500
    )

    print("Lotus Orb / Ability Trigger Detection")
    print("=" * 60)

    lotus_events = []
    other_triggers = []

    for entry in result.entries:
        hero = entry.attacker_name.replace("npc_dota_hero_", "")
        target = entry.target_name.replace("npc_dota_hero_", "")
        item = entry.inflictor_name

        # Calculate time
        mins = int(entry.game_time // 60)
        secs = int(entry.game_time % 60)

        event = {
            "time": f"{mins:02d}:{secs:02d}",
            "hero": hero,
            "target": target,
            "item": item
        }

        if "lotus_orb" in item:
            lotus_events.append(event)
        else:
            other_triggers.append(event)

    if lotus_events:
        print(f"\nLotus Orb Reflections ({len(lotus_events)} total):")
        print("-" * 50)
        for e in lotus_events:
            print(f"[{e['time']}] {e['hero']} reflected spell to {e['target']}")

    if other_triggers:
        print(f"\nOther Ability Triggers ({len(other_triggers)} total):")
        print("-" * 50)
        for e in other_triggers[:10]:  # Show first 10
            print(f"[{e['time']}] {e['hero']} -> {e['target']} ({e['item']})")

# Usage
detect_lotus_orb("match.dem")
```

---

## Neutral Item Tracker

Track neutral item drops, pickups, and usage throughout the game.

```python
from python_manta import MantaParser, NeutralItem, NeutralItemTier, CombatLogType

def track_neutral_items(demo_path: str):
    parser = MantaParser()

    print("Neutral Item Analysis")
    print("=" * 60)

    # 1. Track neutral item pickups via CDOTAUserMsg_FoundNeutralItem
    found_result = parser.parse_universal(demo_path, "FoundNeutralItem", max_messages=100)

    print(f"\nNeutral Items Found: {len(found_result.messages)}")
    print("-" * 40)

    items_by_tier = {t: [] for t in NeutralItemTier}

    for msg in found_result.messages:
        player_id = msg.data.get('player_id')
        item_tier_value = msg.data.get('item_tier', 0)
        tier = NeutralItemTier.from_value(item_tier_value)

        if tier:
            mins = int(msg.tick / 30 / 60)  # Approximate game time
            items_by_tier[tier].append({
                "player": player_id,
                "time_approx": f"~{mins}m",
                "tick": msg.tick
            })

    for tier in NeutralItemTier:
        items = items_by_tier[tier]
        if items:
            print(f"\n{tier.display_name} (unlocks at {tier.unlock_time_minutes}min): {len(items)} drops")
            for item in items[:5]:  # Show first 5
                print(f"  Player {item['player']} at {item['time_approx']}")

    # 2. Track neutral item USAGE via combat log
    result = parser.parse_combat_log(
        demo_path,
        types=[CombatLogType.ITEM],
        max_entries=1000
    )

    print(f"\n\nNeutral Item Active Usage")
    print("-" * 40)

    usage_count = {}
    for entry in result.entries:
        if NeutralItem.is_neutral_item(entry.inflictor_name):
            item = NeutralItem.from_item_name(entry.inflictor_name)
            if item:
                key = (entry.attacker_name, item.display_name)
                usage_count[key] = usage_count.get(key, 0) + 1

    # Sort by usage count
    sorted_usage = sorted(usage_count.items(), key=lambda x: x[1], reverse=True)
    for (hero, item_name), count in sorted_usage[:15]:
        hero_short = hero.replace("npc_dota_hero_", "")
        print(f"  {hero_short}: {item_name} x{count}")

    # 3. Track neutral item modifiers/buffs
    mod_result = parser.parse_combat_log(
        demo_path,
        types=[CombatLogType.MODIFIER_ADD],
        max_entries=2000
    )

    print(f"\n\nNeutral Item Buffs Applied")
    print("-" * 40)

    buff_count = {}
    for entry in mod_result.entries:
        inflictor = entry.inflictor_name
        # Check if it's a neutral item modifier
        if inflictor and inflictor.startswith("modifier_item_"):
            # Extract item name from modifier
            item_name = inflictor.replace("modifier_", "")
            if NeutralItem.is_neutral_item(item_name):
                buff_count[inflictor] = buff_count.get(inflictor, 0) + 1

    for mod, count in sorted(buff_count.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {mod}: {count} applications")

# Usage
track_neutral_items("match.dem")
```

---

## Defensive Item vs Ultimate Analysis

Analyze how defensive items counter ultimates. This example shows how skiter's Outworld Staff nullified Ame's Omnislash in a crucial teamfight at 64:08.

```python
from python_manta import MantaParser, CombatLogType, NeutralItem

def analyze_defensive_counter(demo_path: str, start_time: float, end_time: float):
    """Analyze a specific window for ability vs defensive item interactions."""
    parser = MantaParser()

    print("Defensive Item Analysis")
    print("=" * 60)
    print(f"Window: {start_time/60:.0f}:{start_time%60:02.0f} - {end_time/60:.0f}:{end_time%60:02.0f}")

    # Get abilities cast in window
    abilities = parser.parse_combat_log(demo_path, types=[CombatLogType.ABILITY], max_entries=100000)
    items = parser.parse_combat_log(demo_path, types=[CombatLogType.ITEM], max_entries=100000)
    damage = parser.parse_combat_log(demo_path, types=[CombatLogType.DAMAGE], max_entries=500000)
    mods = parser.parse_combat_log(demo_path, types=[CombatLogType.MODIFIER_ADD], max_entries=100000)

    window_abilities = [e for e in abilities.entries if start_time <= e.timestamp <= end_time]
    window_items = [e for e in items.entries if start_time <= e.timestamp <= end_time]
    window_damage = [e for e in damage.entries if start_time <= e.timestamp <= end_time]
    window_mods = [e for e in mods.entries if start_time <= e.timestamp <= end_time]

    print("\n--- Abilities Cast ---")
    for e in window_abilities:
        mins = int(e.timestamp // 60)
        secs = int(e.timestamp % 60)
        caster = e.attacker_name.replace('npc_dota_hero_', '')
        ability = e.inflictor_name
        target = e.target_name.replace('npc_dota_hero_', '')
        print(f"  [{mins:02d}:{secs:02d}] {caster} -> {ability} on {target}")

    print("\n--- Items Used ---")
    for e in window_items:
        mins = int(e.timestamp // 60)
        secs = int(e.timestamp % 60)
        user = e.attacker_name.replace('npc_dota_hero_', '')
        item = e.inflictor_name
        print(f"  [{mins:02d}:{secs:02d}] {user} -> {item}")

    print("\n--- Key Modifiers ---")
    defensive_mods = [e for e in window_mods
                      if 'ethereal' in e.inflictor_name.lower()
                      or 'invulnerable' in e.inflictor_name.lower()
                      or 'outworld' in e.inflictor_name.lower()
                      or 'aeon' in e.inflictor_name.lower()]
    for e in defensive_mods:
        mins = int(e.timestamp // 60)
        secs = int(e.timestamp % 60)
        target = e.target_name.replace('npc_dota_hero_', '')
        mod = e.inflictor_name
        print(f"  [{mins:02d}:{secs:02d}] {mod} on {target}")

    # Check for Omnislash damage specifically
    omni_damage = [e for e in window_damage
                   if 'omni' in e.inflictor_name.lower() or 'swift' in e.inflictor_name.lower()]
    print(f"\n--- Omnislash Damage: {len(omni_damage)} hits ---")
    for e in omni_damage[:5]:
        mins = int(e.timestamp // 60)
        secs = int(e.timestamp % 60)
        target = e.target_name.replace('npc_dota_hero_', '')
        dmg = e.value
        print(f"  [{mins:02d}:{secs:02d}] Hit {target} for {dmg}")

# Usage - Analyze the 64:08 Omnislash vs Outworld Staff moment
# At 64:08, Ame Omnislashes Medusa, but she uses Outworld Staff at 64:09
# The ethereal form nullifies the Omnislash, leading to Juggernaut's death at 64:13
analyze_defensive_counter("match.dem", start_time=3848, end_time=3855)
```

**Expected Output (TI 2025 Grand Finals - 64:08 fight):**
```
Defensive Item Analysis
============================================================
Window: 64:08 - 64:15

--- Abilities Cast ---
  [64:08] juggernaut -> juggernaut_omni_slash on medusa
  [64:10] juggernaut -> juggernaut_blade_fury on dota_unknown
  [64:10] shadow_demon -> shadow_demon_demonic_cleanse on juggernaut
  [64:11] pangolier -> pangolier_gyroshell on dota_unknown

--- Items Used ---
  [64:09] medusa -> item_outworld_staff

--- Key Modifiers ---
  [64:09] modifier_item_outworld_staff on medusa

--- Omnislash Damage: 0 hits ---
```

**Analysis:** Ame's Omnislash targeted Medusa at 64:08, but skiter immediately used Outworld Staff at 64:09. The `modifier_item_outworld_staff` made Medusa ethereal (untargetable by physical attacks), causing Omnislash to deal **zero damage** and end prematurely. This forced Juggernaut into Blade Fury defensively, and he was killed at 64:13.

This demonstrates how:
1. **Ability casts** are tracked via `CombatLogType.ABILITY`
2. **Defensive items** are tracked via `CombatLogType.ITEM`
3. **Buff effects** are tracked via `CombatLogType.MODIFIER_ADD`
4. **Missing damage** indicates the counter was successful

---

## Complete Analysis Pipeline

Combine multiple analyses into a single comprehensive report.

```python
from python_manta import MantaParser, CombatLogType

def full_analysis(demo_path: str):
    parser = MantaParser()

    print("=" * 70)
    print("COMPREHENSIVE MATCH ANALYSIS")
    print("=" * 70)

    # 1. Basic Info
    header = parser.parse_header(demo_path)
    info = parser.get_parser_info(demo_path)

    print(f"\n[1] Match Information")
    print(f"    Build: {header.build_num}")
    print(f"    Duration: {info.tick} ticks")
    print(f"    Entities: {info.entity_count}")

    # 2. Draft
    game_info = parser.parse_game_info(demo_path)
    picks = [e for e in game_info.picks_bans if e.is_pick]
    bans = [e for e in game_info.picks_bans if not e.is_pick]

    print(f"\n[2] Draft")
    print(f"    Picks: {len(picks)}")
    print(f"    Bans: {len(bans)}")

    # 3. Kill Summary
    kills = parser.parse_game_events(demo_path, event_filter="dota_player_kill", max_events=500)
    print(f"\n[3] Kills")
    print(f"    Total: {len(kills.events)}")

    # 4. Combat Log Stats
    combat = parser.parse_combat_log(demo_path, heroes_only=True, max_entries=5000)
    damage_entries = [e for e in combat.entries if e.type == 0]
    death_entries = [e for e in combat.entries if e.type == 4]

    print(f"\n[4] Combat Log")
    print(f"    Damage events: {len(damage_entries)}")
    print(f"    Death events: {len(death_entries)}")

    # 5. Chat Activity
    chat = parser.parse_universal(demo_path, "CDOTAUserMsg_ChatMessage", max_messages=500)
    print(f"\n[5] Communication")
    print(f"    Chat messages: {chat.count}")

    # 6. Item Economy (via combat log)
    items = parser.parse_combat_log(demo_path, types=[CombatLogType.PURCHASE], max_entries=2000)
    print(f"\n[6] Economy")
    print(f"    Item purchases: {items.total_entries}")

    print("\n" + "=" * 70)
    print("Analysis complete")

# Usage
full_analysis("match.dem")
```
