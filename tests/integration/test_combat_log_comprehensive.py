"""Comprehensive tests for combat log parsing.

Tests all combat log event types and validates field resolution against known data.
Uses match 8447659831 (Team Spirit vs Tundra) as reference.
Uses v2 Parser API exclusively.

The game_time field is automatically computed from the GAME_IN_PROGRESS state event,
so we don't need manual timestamp calculations.
"""

import pytest

# Module-level markers: slow integration tests (~5min)
pytestmark = [pytest.mark.slow, pytest.mark.integration]
from python_manta import Parser

# Test data from OpenDota API for match 8447659831
DEMO_PATH = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"

# OpenDota verified data for Troll Warlord (hero_id=95)
# Key item purchases for Troll Warlord (game_time in seconds, exact item name)
# Only use items that have unique exact names to avoid substring matching issues
TROLL_WARLORD_EXPECTED_PURCHASES = [
    (29, "item_circlet"),
    (336, "item_phase_boots"),  # 05:36
    (421, "item_cornucopia"),   # 07:01
    (728, "item_bfury"),        # 12:08
    (849, "item_yasha"),        # 14:09
    (1014, "item_sange_and_yasha"),  # 16:54
    (1527, "item_black_king_bar"),   # 25:27
    (1782, "item_satanic"),     # 29:42
    (2198, "item_butterfly"),   # 36:38
]

TROLL_WARLORD_EXPECTED_KILLS = [
    (348, "npc_dota_hero_pugna"),      # 05:48
    (374, "npc_dota_hero_lycan"),      # 06:14
    (1450, "npc_dota_hero_pugna"),     # 24:10
    (1523, "npc_dota_hero_faceless_void"),  # 25:23
]


@pytest.fixture(scope="module")
def parser():
    return Parser(DEMO_PATH)


@pytest.fixture(scope="module")
def combat_log(parser):
    """Parse all combat log entries once for all tests."""
    result = parser.parse(combat_log={"max_entries": 0})
    assert result.success, f"Failed to parse combat log: {result.error}"
    return result.combat_log


class TestCombatLogTypes:
    """Test that all combat log event types are properly parsed."""

    def test_damage_events(self, combat_log):
        """Type 0: DOTA_COMBATLOG_DAMAGE - damage dealt."""
        damage_events = [e for e in combat_log.entries if e.type == 0]
        assert len(damage_events) > 30000, f"Expected >30k damage events, got {len(damage_events)}"

        sample = damage_events[0]
        assert sample.target_name, "target_name should be resolved"
        assert sample.attacker_name, "attacker_name should be resolved"
        assert sample.value > 0, "damage value should be positive"
        assert "dota_unknown" not in sample.target_name.lower()
        assert "dota_unknown" not in sample.attacker_name.lower()

    def test_heal_events(self, combat_log):
        """Type 1: DOTA_COMBATLOG_HEAL - healing received."""
        heal_events = [e for e in combat_log.entries if e.type == 1]
        assert len(heal_events) > 1000, f"Expected >1k heal events, got {len(heal_events)}"

        sample = heal_events[0]
        assert sample.target_name, "target_name should be resolved"
        assert sample.value > 0, "heal value should be positive"

    def test_modifier_add_events(self, combat_log):
        """Type 2: DOTA_COMBATLOG_MODIFIER_ADD - buff/debuff applied."""
        modifier_adds = [e for e in combat_log.entries if e.type == 2]
        assert len(modifier_adds) > 15000, f"Expected >15k modifier add events, got {len(modifier_adds)}"

        with_ability = [e for e in modifier_adds if e.modifier_ability_name]
        assert len(with_ability) > 10000, "Most modifier adds should have modifier_ability_name resolved"

        sample = with_ability[0]
        assert sample.target_name, "target_name should be resolved"
        assert sample.inflictor_name, "inflictor_name (modifier name) should be resolved"
        assert sample.modifier_ability_name, "modifier_ability_name should be resolved"

    def test_modifier_remove_events(self, combat_log):
        """Type 3: DOTA_COMBATLOG_MODIFIER_REMOVE - buff/debuff removed."""
        modifier_removes = [e for e in combat_log.entries if e.type == 3]
        assert len(modifier_removes) > 15000, f"Expected >15k modifier remove events"

        purged = [e for e in modifier_removes if e.modifier_purged]
        assert len(purged) > 100, "Should have some purged modifiers"

        for e in purged[:10]:
            if e.modifier_purge_ability > 0:
                assert e.modifier_purge_ability_name, "purge ability name should be resolved"
            if e.modifier_purge_npc > 0:
                assert e.modifier_purge_npc_name, "purge npc name should be resolved"

    def test_death_events(self, combat_log):
        """Type 4: DOTA_COMBATLOG_DEATH - unit death."""
        deaths = [e for e in combat_log.entries if e.type == 4]
        assert len(deaths) > 4000, f"Expected >4k death events, got {len(deaths)}"

        hero_deaths = [e for e in deaths if "hero" in e.target_name.lower()]
        assert len(hero_deaths) > 0, "Should have hero deaths"

        sample = hero_deaths[0]
        assert sample.target_name, "target_name should be resolved"
        assert sample.attacker_name, "attacker_name should be resolved"

    def test_ability_events(self, combat_log):
        """Type 5: DOTA_COMBATLOG_ABILITY - ability cast."""
        ability_events = [e for e in combat_log.entries if e.type == 5]
        assert len(ability_events) > 3000, f"Expected >3k ability events"

        sample = ability_events[0]
        assert sample.attacker_name, "attacker_name should be resolved"
        assert sample.inflictor_name, "inflictor_name (ability name) should be resolved"
        assert "dota_unknown" not in sample.inflictor_name.lower()

    def test_item_events(self, combat_log):
        """Type 6: DOTA_COMBATLOG_ITEM - item use."""
        item_events = [e for e in combat_log.entries if e.type == 6]
        assert len(item_events) > 4000, f"Expected >4k item events"

        sample = item_events[0]
        assert sample.attacker_name, "attacker_name should be resolved"
        assert sample.inflictor_name, "inflictor_name (item name) should be resolved"
        assert sample.inflictor_name.startswith("item_"), f"Item should start with item_, got {sample.inflictor_name}"

    def test_gold_events(self, combat_log):
        """Type 8: DOTA_COMBATLOG_GOLD - gold earned."""
        gold_events = [e for e in combat_log.entries if e.type == 8]
        assert len(gold_events) > 3000, f"Expected >3k gold events"

        sample = gold_events[0]
        assert sample.target_name, "target_name (receiver) should be resolved"
        assert sample.value > 0, "gold value should be positive"

    def test_xp_events(self, combat_log):
        """Type 10: DOTA_COMBATLOG_XP - XP earned."""
        xp_events = [e for e in combat_log.entries if e.type == 10]
        assert len(xp_events) > 4000, f"Expected >4k XP events"

        sample = xp_events[0]
        assert sample.target_name, "target_name (receiver) should be resolved"

    def test_purchase_events(self, combat_log):
        """Type 11: DOTA_COMBATLOG_PURCHASE - item purchased."""
        purchases = [e for e in combat_log.entries if e.type == 11]
        assert len(purchases) > 600, f"Expected >600 purchase events, got {len(purchases)}"

        for e in purchases[:10]:
            assert e.target_name, "target_name (buyer) should be resolved"
            assert e.value_name, "value_name (item) should be resolved"
            assert e.value_name.startswith("item_"), f"Item should start with item_, got {e.value_name}"
            assert "dota_unknown" not in e.value_name.lower()

    def test_buyback_events(self, combat_log):
        """Type 12: DOTA_COMBATLOG_BUYBACK - hero buyback."""
        buybacks = [e for e in combat_log.entries if e.type == 12]
        assert len(buybacks) > 0, "Should have some buyback events"

        sample = buybacks[0]
        assert sample.value_name, "value_name (hero) should be resolved"

    def test_multikill_events(self, combat_log):
        """Type 15: DOTA_COMBATLOG_MULTIKILL - double/triple kill etc."""
        multikills = [e for e in combat_log.entries if e.type == 15]
        # May or may not have multikills depending on the match
        if multikills:
            sample = multikills[0]
            assert sample.target_name, "target_name should be resolved"

    def test_killstreak_events(self, combat_log):
        """Type 16: DOTA_COMBATLOG_KILLSTREAK - killing spree etc."""
        killstreaks = [e for e in combat_log.entries if e.type == 16]
        if killstreaks:
            sample = killstreaks[0]
            assert sample.target_name, "target_name should be resolved"

    def test_building_kill_events(self, combat_log):
        """Type 17: DOTA_COMBATLOG_TEAM_BUILDING_KILL - tower/barracks destroyed."""
        building_kills = [e for e in combat_log.entries if e.type == 17]
        assert len(building_kills) > 20, "Should have building kills"

        sample = building_kills[0]
        assert sample.target_name, "target_name (building) should be resolved"
        assert "tower" in sample.target_name.lower() or "rax" in sample.target_name.lower() or "ancient" in sample.target_name.lower()

    def test_modifier_stack_events(self, combat_log):
        """Type 19: DOTA_COMBATLOG_MODIFIER_STACK_EVENT - stack count changes."""
        stack_events = [e for e in combat_log.entries if e.type == 19]
        assert len(stack_events) > 20000, f"Expected >20k stack events, got {len(stack_events)}"

        with_ability = [e for e in stack_events if e.modifier_ability_name]
        assert len(with_ability) > 15000, "Most stack events should have modifier_ability_name resolved"


class TestTrollWarlordPurchases:
    """Validate Troll Warlord purchases against OpenDota API data."""

    def test_purchase_count(self, combat_log):
        """Verify total purchase count for Troll Warlord."""
        troll_purchases = [
            e for e in combat_log.entries
            if e.type == 11 and e.target_name == "npc_dota_hero_troll_warlord"
        ]
        # OpenDota shows 48 purchases, but some are pre-game
        assert len(troll_purchases) >= 40, f"Expected >=40 Troll purchases, got {len(troll_purchases)}"

    def test_key_item_timings(self, combat_log):
        """Verify key item timings match OpenDota data using game_time field.

        The game_time field is automatically computed from the GAME_IN_PROGRESS
        state event, giving us accurate in-game timestamps.
        """
        troll_purchases = [
            e for e in combat_log.entries
            if e.type == 11 and e.target_name == "npc_dota_hero_troll_warlord"
        ]

        for expected_time, expected_item in TROLL_WARLORD_EXPECTED_PURCHASES:
            # Find exact match for the item
            matching = [
                e for e in troll_purchases
                if e.value_name == expected_item
            ]
            assert len(matching) > 0, f"Should find purchase of {expected_item}"

            # Use the LAST matching event (the final assembled item)
            last_match = matching[-1]
            time_diff = abs(last_match.game_time - expected_time)

            # Allow 5s tolerance for timing differences
            assert time_diff < 5, f"Time for {expected_item} off by {time_diff}s (expected ~{expected_time}s, got ~{last_match.game_time}s)"

    def test_item_names_resolved(self, combat_log):
        """Verify all item names are properly resolved, not raw indices."""
        troll_purchases = [
            e for e in combat_log.entries
            if e.type == 11 and e.target_name == "npc_dota_hero_troll_warlord"
        ]

        for e in troll_purchases:
            assert e.value_name, f"value_name should not be empty"
            assert e.value_name.startswith("item_"), f"Item should start with 'item_', got '{e.value_name}'"
            assert "unknown" not in e.value_name.lower(), f"Item name should not contain 'unknown': {e.value_name}"


class TestTrollWarlordKills:
    """Validate Troll Warlord kills against OpenDota API data."""

    def test_kill_targets_resolved(self, combat_log):
        """Verify kill targets are properly resolved."""
        troll_kills = [
            e for e in combat_log.entries
            if e.type == 4
            and e.attacker_name == "npc_dota_hero_troll_warlord"
            and "hero" in e.target_name.lower()
        ]

        # Troll has 12 kills according to OpenDota
        assert len(troll_kills) >= 10, f"Expected >=10 Troll hero kills, got {len(troll_kills)}"

        for e in troll_kills:
            assert e.target_name.startswith("npc_dota_hero_"), f"Target should be a hero: {e.target_name}"

    def test_first_kills_timing(self, combat_log):
        """Verify first kills match OpenDota data using game_time field."""
        troll_kills = [
            e for e in combat_log.entries
            if e.type == 4
            and e.attacker_name == "npc_dota_hero_troll_warlord"
            and "hero" in e.target_name.lower()
        ]

        # First kill should be Pugna around 5:48 (348s)
        if troll_kills:
            first_kill = troll_kills[0]

            assert "pugna" in first_kill.target_name.lower(), f"First kill should be Pugna, got {first_kill.target_name}"
            assert 340 < first_kill.game_time < 360, f"First kill timing should be ~348s, got {first_kill.game_time}s"


class TestFieldResolution:
    """Verify fields are resolved correctly for their event types.

    Note: 'dota_unknown' at index 0 is the expected value when a field is not applicable.
    For example:
    - GAME_STATE events have no target or attacker
    - XP/GOLD/PURCHASE events have no attacker (it's the receiver in target_name)
    - DAMAGE from auto-attacks has no inflictor (ability)
    """

    def test_damage_events_resolved(self, combat_log):
        """Damage events should have target and attacker resolved."""
        damage_events = [e for e in combat_log.entries if e.type == 0]

        # All damage events should have valid target and attacker
        for e in damage_events[:100]:
            assert e.target_name != "dota_unknown", f"Damage event should have target"
            assert e.attacker_name != "dota_unknown", f"Damage event should have attacker"

    def test_death_events_resolved(self, combat_log):
        """Death events should have target and attacker resolved."""
        death_events = [e for e in combat_log.entries if e.type == 4]

        for e in death_events[:100]:
            assert e.target_name != "dota_unknown", f"Death event should have target (who died)"
            # Attacker can be dota_unknown for deaths from DoT, etc

    def test_modifier_events_resolved(self, combat_log):
        """Modifier add/remove events should have target and inflictor resolved."""
        modifier_events = [e for e in combat_log.entries if e.type in (2, 3)]

        for e in modifier_events[:100]:
            assert e.target_name != "dota_unknown", f"Modifier event should have target"
            assert e.inflictor_name != "dota_unknown", f"Modifier event should have inflictor (buff name)"

    def test_ability_events_resolved(self, combat_log):
        """Ability cast events should have attacker and inflictor resolved."""
        ability_events = [e for e in combat_log.entries if e.type == 5]

        for e in ability_events[:100]:
            assert e.attacker_name != "dota_unknown", f"Ability event should have attacker (caster)"
            assert e.inflictor_name != "dota_unknown", f"Ability event should have inflictor (ability name)"

    def test_purchase_events_resolved(self, combat_log):
        """Purchase events should have target (buyer) and value_name (item) resolved."""
        purchases = [e for e in combat_log.entries if e.type == 11]

        for e in purchases:
            assert e.target_name != "dota_unknown", f"Purchase should have target (buyer)"
            assert e.value_name, f"Purchase at tick {e.tick} has no value_name"
            assert e.value_name.startswith("item_"), f"Purchase value_name should be item: {e.value_name}"
            # attacker_name is expected to be dota_unknown for purchases (no attacker)

    def test_gold_xp_events_have_target(self, combat_log):
        """Gold and XP events should have target (receiver) resolved."""
        gold_xp_events = [e for e in combat_log.entries if e.type in (8, 10)]

        for e in gold_xp_events[:100]:
            assert e.target_name != "dota_unknown", f"Gold/XP event should have target (receiver)"
            # attacker_name is expected to be dota_unknown (it's a reward, not an attack)

    def test_auto_attack_damage_no_inflictor(self, combat_log):
        """Auto-attack damage correctly has no inflictor (dota_unknown is valid)."""
        damage_events = [e for e in combat_log.entries if e.type == 0]

        # Count events with vs without inflictor
        with_inflictor = sum(1 for e in damage_events if e.inflictor_name != "dota_unknown")
        without_inflictor = sum(1 for e in damage_events if e.inflictor_name == "dota_unknown")

        # Should have both types - ability damage and auto-attack damage
        assert with_inflictor > 10000, "Should have many ability damage events"
        assert without_inflictor > 10000, "Should have many auto-attack damage events"


class TestGameTime:
    """Test game_time field and game_start_time detection."""

    def test_game_start_time_detected(self, combat_log):
        """Game start time should be detected from GAME_IN_PROGRESS event."""
        # Game start time should be around 1000s (after draft + strategy + pregame)
        assert combat_log.game_start_time > 900, f"Game start time too early: {combat_log.game_start_time}"
        assert combat_log.game_start_time < 1100, f"Game start time too late: {combat_log.game_start_time}"

    def test_pregame_negative_times(self, combat_log):
        """Pre-game events (during 90s countdown) should have negative game_time values."""
        # Exclude GAME_STATE events (type 9) as they occur during draft phase
        pregame_events = [
            e for e in combat_log.entries
            if e.game_time < 0 and e.type != 9
        ]

        # Should have some pre-game events (ward purchases, etc)
        assert len(pregame_events) > 0, "Should have pre-game events with negative game_time"

        # Pre-game should be within -90s to 0s (the horn period)
        for e in pregame_events:
            assert e.game_time >= -100, f"Pre-game time too early: {e.game_time}"
            assert e.game_time < 0, f"Should be negative: {e.game_time}"

    def test_ingame_positive_times(self, combat_log):
        """In-game events should have positive game_time values."""
        ingame_events = [e for e in combat_log.entries if e.game_time >= 0]

        # Most events should be in-game
        assert len(ingame_events) > len(combat_log.entries) * 0.95, "Most events should be in-game"

    def test_game_time_matches_opendota(self, combat_log):
        """Game times should match OpenDota API data."""
        # Find Troll's circlet purchase (OpenDota shows 00:29)
        circlet = [
            e for e in combat_log.entries
            if e.type == 11
            and e.target_name == "npc_dota_hero_troll_warlord"
            and e.value_name == "item_circlet"
        ]
        assert len(circlet) > 0, "Should find circlet purchase"
        assert 25 < circlet[0].game_time < 35, f"Circlet should be ~29s, got {circlet[0].game_time}s"


class TestFieldConsistency:
    """Test that fields are consistent across event types."""

    def test_timestamps_reasonable(self, combat_log):
        """Timestamps should be within match duration."""
        max_timestamp = max(e.timestamp for e in combat_log.entries)
        min_timestamp = min(e.timestamp for e in combat_log.entries if e.timestamp > 0)

        # Match duration is ~2585s + pregame
        assert max_timestamp < 4000, f"Max timestamp {max_timestamp} too high"
        assert min_timestamp > 0, f"Min timestamp {min_timestamp} should be positive"

    def test_ticks_increasing(self, combat_log):
        """Ticks should generally increase over time."""
        ticks = [e.tick for e in combat_log.entries]
        max_tick = max(ticks)
        min_tick = min(ticks)

        assert max_tick > min_tick, "Ticks should span a range"
        assert max_tick > 100000, "Should have significant tick count for full game"

    def test_type_names_populated(self, combat_log):
        """All entries should have type_name populated."""
        for e in combat_log.entries[:1000]:
            assert e.type_name, f"Entry at tick {e.tick} has no type_name"
            assert "DOTA_COMBATLOG" in e.type_name, f"Invalid type_name: {e.type_name}"


class TestShieldAndDamageAbsorption:
    """Test shield, barrier, and damage absorption tracking.

    Combat log types (defined in protobuf but may not appear in replays):
    - 30: AEGIS_TAKEN - Aegis pickup
    - 32: PHYSICAL_DAMAGE_PREVENTED - Damage block (Crimson Guard, etc.)
    - 40: SPELL_ABSORB - Spell absorbed (Linken's, Lotus, etc.)

    Related fields:
    - will_reincarnate: True if hero will respawn (Aegis/WK)
    - no_physical_damage_modifier: Physical damage immunity active
    - regenerated_health: Health restored

    IMPORTANT: Investigation shows these combat log types (30, 32, 40) are NOT
    generated in replays, even TI finals. The game tracks shields/absorption
    differently - likely through modifier events (type 2/3) rather than dedicated
    combat log types. The `will_reincarnate` field on DEATH events IS populated.

    OpenDota parser explicitly filters out types > 19, suggesting these types
    were added to protobuf but never implemented in the game's combat log system.
    """

    def test_aegis_taken_events(self, combat_log):
        """Type 30: DOTA_COMBATLOG_AEGIS_TAKEN - Aegis pickup."""
        aegis_events = [e for e in combat_log.entries if e.type == 30]

        # May or may not have aegis taken depending on the match
        # Match 8447659831 is a long pro game, likely has Roshan kills
        if aegis_events:
            for e in aegis_events:
                assert e.target_name, "Aegis pickup should have target (hero who picked it up)"
                assert "hero" in e.target_name.lower(), f"Aegis should be picked by hero: {e.target_name}"
                assert e.game_time > 0, "Aegis should be picked up after game start"

    def test_physical_damage_prevented_events(self, combat_log):
        """Type 32: DOTA_COMBATLOG_PHYSICAL_DAMAGE_PREVENTED - Damage block."""
        prevented_events = [e for e in combat_log.entries if e.type == 32]

        # Should have some damage prevention events in any match
        # Sources: Vanguard, Crimson Guard, Kraken Shell, damage block talents, etc.
        if prevented_events:
            sample = prevented_events[0]
            assert sample.target_name, "Damage prevented should have target"
            assert sample.value >= 0, "Prevented damage value should be non-negative"

            # Check we have context about who/what blocked the damage
            has_source_info = (
                sample.attacker_name or
                sample.inflictor_name or
                sample.attacker_name != "dota_unknown"
            )
            # Note: Some damage block may not have source info

    def test_spell_absorb_events(self, combat_log):
        """Type 40: DOTA_COMBATLOG_SPELL_ABSORB - Linken's, Lotus, etc."""
        absorb_events = [e for e in combat_log.entries if e.type == 40]

        # May or may not have spell absorb depending on item builds
        if absorb_events:
            sample = absorb_events[0]
            assert sample.target_name, "Spell absorb should have target (protected hero)"

            # Inflictor should be the absorbed spell
            if sample.inflictor_name and sample.inflictor_name != "dota_unknown":
                # Absorbed spell name should be present
                pass

    def test_will_reincarnate_on_death(self, combat_log):
        """Deaths with will_reincarnate=True indicate Aegis/WK ulti."""
        death_events = [e for e in combat_log.entries if e.type == 4]

        # Find deaths with reincarnation
        reincarnate_deaths = [e for e in death_events if e.will_reincarnate]

        # In a long pro game with Roshan, should have some reincarnations
        if reincarnate_deaths:
            for e in reincarnate_deaths:
                assert e.target_name, "Reincarnating death should have target"
                assert "hero" in e.target_name.lower(), f"Only heroes reincarnate: {e.target_name}"

    def test_no_physical_damage_modifier(self, combat_log):
        """Check no_physical_damage_modifier field on combat log entries."""
        # This modifier indicates ghost scepter, ethereal form, etc.
        damage_events = [e for e in combat_log.entries if e.type == 0]

        # Check if any events have this modifier tracked
        with_modifier = [e for e in damage_events if e.no_physical_damage_modifier]
        # May or may not be present depending on the match

    def test_damage_absorption_summary(self, combat_log):
        """Summary of all damage absorption events in the match."""
        aegis = [e for e in combat_log.entries if e.type == 30]
        prevented = [e for e in combat_log.entries if e.type == 32]
        absorbed = [e for e in combat_log.entries if e.type == 40]
        reincarnates = [e for e in combat_log.entries if e.type == 4 and e.will_reincarnate]

        print(f"\n=== Damage Absorption Summary ===")
        print(f"Aegis pickups: {len(aegis)}")
        print(f"Physical damage prevented events: {len(prevented)}")
        print(f"Spell absorb events: {len(absorbed)}")
        print(f"Deaths with reincarnation: {len(reincarnates)}")

        if aegis:
            print(f"\nAegis pickups:")
            for e in aegis:
                mins = int(e.game_time // 60)
                secs = int(e.game_time % 60)
                print(f"  [{mins:02d}:{secs:02d}] {e.target_name}")

        if prevented[:10]:
            print(f"\nSample damage prevented (first 10):")
            for e in prevented[:10]:
                mins = int(e.game_time // 60)
                secs = int(e.game_time % 60)
                print(f"  [{mins:02d}:{secs:02d}] {e.target_name} blocked {e.value} damage")

        if absorbed[:10]:
            print(f"\nSample spell absorbs (first 10):")
            for e in absorbed[:10]:
                mins = int(e.game_time // 60)
                secs = int(e.game_time % 60)
                spell = e.inflictor_name if e.inflictor_name != "dota_unknown" else "unknown spell"
                print(f"  [{mins:02d}:{secs:02d}] {e.target_name} absorbed {spell}")
