
# Examples

??? info "AI Summary"
    Complete working examples for common Dota 2 replay analysis tasks. Includes: match summary generator (header + draft + final stats), kill timeline builder, item build tracker, ward placement analyzer, damage report generator, and team fight detector. Each example demonstrates combining multiple API methods for real analysis workflows.

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

Track item purchases for each player throughout the match.

```python
from python_manta import MantaParser
from collections import defaultdict

def track_item_builds(demo_path: str):
    parser = MantaParser()

    result = parser.parse_universal(
        demo_path,
        "CDOTAUserMsg_ItemPurchased",
        max_messages=2000
    )

    # Group by player
    player_items = defaultdict(list)

    for msg in result.messages:
        player_id = msg.data.get("player_id")
        item_id = msg.data.get("item_ability")

        player_items[player_id].append({
            "tick": msg.tick,
            "item_id": item_id
        })

    print("Item Build Order by Player")
    print("=" * 50)

    for player_id in sorted(player_items.keys()):
        items = player_items[player_id]
        print(f"\nPlayer {player_id}: ({len(items)} items)")
        print("-" * 40)

        for i, item in enumerate(items, 1):
            print(f"  {i:>3}. Item ID {item['item_id']:>5} at tick {item['tick']:>7}")

# Usage
track_item_builds("match.dem")
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

---

## Complete Analysis Pipeline

Combine multiple analyses into a single comprehensive report.

```python
from python_manta import MantaParser

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

    # 6. Item Economy
    items = parser.parse_universal(demo_path, "CDOTAUserMsg_ItemPurchased", max_messages=2000)
    print(f"\n[6] Economy")
    print(f"    Item purchases: {items.count}")

    print("\n" + "=" * 70)
    print("Analysis complete")

# Usage
full_analysis("match.dem")
```
