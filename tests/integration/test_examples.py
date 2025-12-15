"""
Integration tests for all documentation examples.

Tests are run against TI 2025 Grand Finals Game 5 (Match ID: 8461956309).
These tests verify the examples work and capture real output for documentation.
Uses v2 Parser API exclusively.

Run with: uv run pytest tests/integration/test_examples.py -v -s
"""
import pytest

# Module-level markers: slow integration tests (~8min)
pytestmark = [pytest.mark.slow, pytest.mark.integration]
from collections import defaultdict
from caching_parser import Parser
from python_manta import (
    Hero, CombatLogType, RuneType,
    NeutralItem, NeutralItemTier
)
from tests.conftest import DEMO_FILE_SECONDARY

# TI 2025 Grand Finals Game 5
DEMO_PATH = DEMO_FILE_SECONDARY


@pytest.fixture(scope="module")
def parser():
    return Parser(DEMO_PATH)


class TestMatchSummary:
    """Test Match Summary example."""

    def test_header_info(self, parser):
        """Verify header parsing returns expected data."""
        result = parser.parse(header=True)
        header = result.header

        assert result.success
        assert header.map_name == "start"
        assert header.build_num > 0
        assert "Valve" in header.server_name or "TI" in header.server_name

        print(f"\n=== Header Info ===")
        print(f"Map: {header.map_name}")
        print(f"Build: {header.build_num}")
        print(f"Server: {header.server_name}")

    def test_game_info_draft(self, parser):
        """Verify draft picks with Hero enum."""
        result = parser.parse(game_info=True)
        game_info = result.game_info

        assert result.success
        assert game_info.match_id == 8461956309

        radiant_picks = []
        dire_picks = []
        for event in game_info.picks_bans:
            if event.is_pick:
                hero = Hero.from_id(event.hero_id)
                hero_name = hero.display_name if hero else f"Unknown({event.hero_id})"
                if event.team == 2:
                    radiant_picks.append(hero_name)
                else:
                    dire_picks.append(hero_name)

        # Verify expected heroes
        assert "Juggernaut" in radiant_picks
        assert "Shadow Fiend" in radiant_picks
        assert "Medusa" in dire_picks
        assert "Pangolier" in dire_picks

        print(f"\n=== Draft ===")
        print(f"Radiant picks: {radiant_picks}")
        print(f"Dire picks: {dire_picks}")


class TestKillTimeline:
    """Test Kill Timeline example.

    Use combat log DEATH type and filter for hero targets.
    """

    def test_kill_events(self, parser):
        """Verify hero kills are captured via combat log deaths."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.DEATH], "max_entries": 5000}
        )

        assert result.success

        # Filter for hero deaths only
        hero_deaths = [e for e in result.combat_log.entries if "npc_dota_hero_" in e.target_name]
        assert len(hero_deaths) > 0

        print(f"\n=== Kill Timeline ({len(hero_deaths)} hero deaths) ===")
        for entry in hero_deaths:
            mins = int(entry.game_time // 60)
            secs = int(entry.game_time % 60)
            victim = entry.target_name.replace("npc_dota_hero_", "")
            killer = entry.attacker_name.replace("npc_dota_hero_", "")
            print(f"[{mins:02d}:{secs:02d}] {killer} killed {victim}")


class TestItemBuildTracker:
    """Test Item Build Tracker example."""

    def test_item_purchases(self, parser):
        """Verify item purchases are tracked."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.PURCHASE], "max_entries": 2000}
        )

        assert result.success
        assert len(result.combat_log.entries) > 0

        hero_items = defaultdict(list)
        for entry in result.combat_log.entries:
            hero = entry.target_name.replace("npc_dota_hero_", "")
            item = entry.value_name.replace("item_", "")
            mins = int(abs(entry.game_time) // 60)
            secs = int(abs(entry.game_time) % 60)
            sign = "-" if entry.game_time < 0 else ""

            hero_items[hero].append({
                "time": f"{sign}{mins:02d}:{secs:02d}",
                "item": item
            })

        # Verify Juggernaut has items
        assert "juggernaut" in hero_items
        assert len(hero_items["juggernaut"]) > 10

        print(f"\n=== Item Builds (Juggernaut first 25) ===")
        jug_items = hero_items["juggernaut"]
        for i, item in enumerate(jug_items[:25], 1):
            print(f"  {i:>3}. [{item['time']}] {item['item']}")


class TestDamageReport:
    """Test Damage Report example."""

    def test_damage_dealt(self, parser):
        """Verify damage tracking."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.DAMAGE], "heroes_only": True, "max_entries": 50000}
        )

        assert result.success

        damage_dealt = defaultdict(int)
        for entry in result.combat_log.entries:
            if entry.is_attacker_hero:
                hero = entry.attacker_name.replace("npc_dota_hero_", "")
                damage_dealt[hero] += entry.value

        print(f"\n=== Damage Report (Hero vs Hero) ===")
        for hero, dmg in sorted(damage_dealt.items(), key=lambda x: -x[1]):
            print(f"  {hero:<25}: {dmg:>10,}")


class TestChatLog:
    """Test Chat Log example."""

    def test_chat_messages(self, parser):
        """Verify chat messages are captured."""
        result = parser.parse(
            messages={"filter": "CDOTAUserMsg_ChatMessage", "max_messages": 1000}
        )

        assert result.success

        chat_types = {1: "ALL", 2: "TEAM", 3: "SPEC"}

        print(f"\n=== Chat Log ===")
        for msg in result.messages.messages:
            player_id = msg.data.get("source_player_id", "?")
            text = msg.data.get("message_text", "")
            chat_type = msg.data.get("chat_type", 0)

            if not text:
                continue

            type_str = chat_types.get(chat_type, "???")
            tick = msg.tick
            print(f"[{tick:>7}] [{type_str:>4}] Player {player_id}: {text}")

        print(f"\nTotal chat messages: {len(result.messages.messages)}")


class TestRuneTracking:
    """Test Rune Tracking example."""

    def test_rune_pickups(self, parser):
        """Verify rune pickups via modifier tracking."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.MODIFIER_ADD], "heroes_only": True, "max_entries": 50000}
        )

        assert result.success

        rune_pickups = [
            e for e in result.combat_log.entries
            if RuneType.is_rune_modifier(e.inflictor_name)
        ]

        print(f"\n=== Rune Tracking ===")
        print(f"Total Rune Pickups: {len(rune_pickups)}")
        print("-" * 60)

        for pickup in rune_pickups:
            hero = pickup.target_name.replace("npc_dota_hero_", "")
            rune = RuneType.from_modifier(pickup.inflictor_name)
            rune_name = rune.display_name if rune else pickup.inflictor_name
            print(f"[{pickup.game_time_str}] {hero:<20} picked up {rune_name}")

        # Summary by hero
        hero_runes = defaultdict(list)
        for pickup in rune_pickups:
            hero = pickup.target_name.replace("npc_dota_hero_", "")
            rune = RuneType.from_modifier(pickup.inflictor_name)
            rune_name = rune.display_name if rune else pickup.inflictor_name
            hero_runes[hero].append(rune_name)

        print("\nRunes by Hero:")
        for hero, runes in sorted(hero_runes.items()):
            print(f"  {hero}: {len(runes)} runes ({', '.join(runes)})")


class TestItemUsage:
    """Test Item Usage Tracker example."""

    def test_item_activations(self, parser):
        """Verify item usage tracking."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.ITEM], "heroes_only": True, "max_entries": 5000}
        )

        assert result.success

        hero_usage = defaultdict(lambda: defaultdict(int))
        for entry in result.combat_log.entries:
            hero = entry.attacker_name.replace("npc_dota_hero_", "")
            item = entry.inflictor_name.replace("item_", "")
            hero_usage[hero][item] += 1

        print(f"\n=== Item Usage ===")
        print(f"Total activations: {result.combat_log.total_entries}")

        for hero in sorted(hero_usage.keys()):
            items = hero_usage[hero]
            print(f"\n{hero}:")
            for item, count in sorted(items.items(), key=lambda x: -x[1])[:5]:
                print(f"  {item}: {count}x")


class TestTeamFightDetector:
    """Test Team Fight Detector example."""

    def test_team_fights(self, parser):
        """Verify team fight detection via death clustering."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.DEATH], "heroes_only": True, "max_entries": 500}
        )

        assert result.success

        tick_window = 600
        fights = []
        current_fight = []

        for entry in sorted(result.combat_log.entries, key=lambda e: e.tick):
            if not current_fight:
                current_fight.append(entry)
            elif entry.tick - current_fight[-1].tick <= tick_window:
                current_fight.append(entry)
            else:
                if len(current_fight) >= 3:
                    fights.append(current_fight)
                current_fight = [entry]

        if len(current_fight) >= 3:
            fights.append(current_fight)

        print(f"\n=== Team Fights (3+ deaths within {tick_window} ticks) ===")
        print(f"Found {len(fights)} team fights")

        for i, fight in enumerate(fights[:5], 1):
            start_tick = fight[0].tick
            end_tick = fight[-1].tick
            radiant_deaths = sum(1 for e in fight if e.target_team == 2)
            dire_deaths = sum(1 for e in fight if e.target_team == 3)

            print(f"\nFight #{i}: Tick {start_tick} - {end_tick}")
            print(f"  Deaths: Radiant {radiant_deaths}, Dire {dire_deaths}")
            print(f"  Outcome: {'Radiant' if dire_deaths > radiant_deaths else 'Dire'} won")


class TestNeutralItems:
    """Test Neutral Item Tracker example."""

    def test_neutral_item_drops(self, parser):
        """Verify neutral item tracking."""
        result = parser.parse(
            messages={"filter": "FoundNeutralItem", "max_messages": 100}
        )

        print(f"\n=== Neutral Item Drops ===")
        print(f"Items Found: {len(result.messages.messages)}")

        items_by_tier = {t: [] for t in NeutralItemTier}
        for msg in result.messages.messages:
            player_id = msg.data.get('player_id')
            item_tier_value = msg.data.get('item_tier', 0)
            tier = NeutralItemTier.from_value(item_tier_value)
            if tier:
                mins = int(msg.tick / 30 / 60)
                items_by_tier[tier].append({
                    "player": player_id,
                    "time_approx": f"~{mins}m"
                })

        for tier in NeutralItemTier:
            items = items_by_tier[tier]
            if items:
                print(f"\n{tier.display_name} (unlocks at {tier.unlock_time_minutes}min): {len(items)} drops")
                for item in items[:3]:
                    print(f"  Player {item['player']} at {item['time_approx']}")


class TestLotusOrbDetection:
    """Test Lotus Orb / Ability Trigger detection."""

    def test_ability_triggers(self, parser):
        """Verify ability trigger tracking."""
        result = parser.parse(
            combat_log={"types": [CombatLogType.ABILITY_TRIGGER], "max_entries": 500}
        )

        print(f"\n=== Ability Triggers ===")
        print(f"Total triggers: {len(result.combat_log.entries)}")

        for entry in result.combat_log.entries[:10]:
            hero = entry.attacker_name.replace("npc_dota_hero_", "")
            target = entry.target_name.replace("npc_dota_hero_", "")
            item = entry.inflictor_name
            mins = int(entry.game_time // 60)
            secs = int(entry.game_time % 60)
            print(f"[{mins:02d}:{secs:02d}] {hero} -> {target} ({item})")


class TestCompleteAnalysis:
    """Test Complete Analysis Pipeline example."""

    def test_full_pipeline(self, parser):
        """Verify complete analysis pipeline."""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE MATCH ANALYSIS")
        print("=" * 70)

        # 1. Basic Info + Parser Info + Game Info in single pass
        result = parser.parse(
            header=True,
            game_info=True,
            parser_info=True,
        )

        print(f"\n[1] Match Information")
        print(f"    Build: {result.header.build_num}")
        print(f"    Duration: {result.parser_info.tick} ticks")
        print(f"    Entities: {result.parser_info.entity_count}")

        # 2. Draft
        picks = [e for e in result.game_info.picks_bans if e.is_pick]
        bans = [e for e in result.game_info.picks_bans if not e.is_pick]

        print(f"\n[2] Draft")
        print(f"    Picks: {len(picks)}")
        print(f"    Bans: {len(bans)}")

        # 3. Kill Summary
        kills_result = parser.parse(game_events={"event_filter": "dota_player_kill", "max_events": 500})
        print(f"\n[3] Kills")
        print(f"    Total: {len(kills_result.game_events.events)}")

        # 4. Combat Log Stats
        combat_result = parser.parse(combat_log={"heroes_only": True, "max_entries": 5000})
        damage_entries = [e for e in combat_result.combat_log.entries if e.type == 0]
        death_entries = [e for e in combat_result.combat_log.entries if e.type == 4]

        print(f"\n[4] Combat Log")
        print(f"    Damage events: {len(damage_entries)}")
        print(f"    Death events: {len(death_entries)}")

        # 5. Chat Activity
        chat_result = parser.parse(messages={"filter": "CDOTAUserMsg_ChatMessage", "max_messages": 500})
        print(f"\n[5] Communication")
        print(f"    Chat messages: {len(chat_result.messages.messages)}")

        # 6. Item Economy
        items_result = parser.parse(combat_log={"types": [CombatLogType.PURCHASE], "max_entries": 2000})
        print(f"\n[6] Economy")
        print(f"    Item purchases: {items_result.combat_log.total_entries}")

        print("\n" + "=" * 70)
        print("Analysis complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
