"""
Test advanced parser features (respawn, pre-horn positions, creeps, camps_stacked, hero_level_injection).
Tests real data values from actual demo files.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.unit
from caching_parser import Parser
from tests.conftest import DEMO_FILE


class TestRespawnEvents:
    """Test hero respawn event derivation."""

    def test_derive_respawn_events(self, parser):
        """Test deriving respawn events from death entries."""
        from python_manta import derive_respawn_events, HeroRespawnEvent, CombatLogType

        result = parser.parse(combat_log={
            "types": [CombatLogType.DEATH],
            "heroes_only": True,
            "max_entries": 1000
        })
        assert result.success is True

        respawns = derive_respawn_events(result.combat_log)
        assert len(respawns) > 0

        for event in respawns:
            assert isinstance(event, HeroRespawnEvent)
            assert "npc_dota_hero_" in event.hero_name
            assert len(event.hero_display_name) > 0
            assert event.death_tick > 0
            assert event.respawn_duration >= 0
            assert event.respawn_tick >= event.death_tick

    def test_respawn_event_uses_combat_log_level(self, parser):
        """Test respawn uses target_hero_level from combat log when available."""
        from python_manta import derive_respawn_events, CombatLogType

        result = parser.parse(combat_log={
            "types": [CombatLogType.DEATH],
            "heroes_only": True,
            "max_entries": 1000
        })
        respawns = derive_respawn_events(result.combat_log)

        # Find a respawn with known level from combat log
        deaths_with_level = [e for e in result.combat_log.entries if e.target_hero_level > 0]
        if len(deaths_with_level) > 0 and len(respawns) > 0:
            # The respawn should use the combat log level, not default level 1
            # and custom levels should NOT override combat log levels
            hero_name = respawns[0].hero_name
            hero_key = hero_name.replace("npc_dota_hero_", "")
            hero_levels = {hero_key: 99}  # Try to override with level 99
            respawns_custom = derive_respawn_events(result.combat_log, hero_levels)

            # Combat log level should take precedence over custom level
            assert respawns_custom[0].hero_level == respawns[0].hero_level
            assert respawns_custom[0].hero_level != 99  # Custom level was NOT used


class TestPreHornPositions:
    """Test pre-horn entity snapshots (FEATURE #12).

    Pre-horn snapshots should have negative game_time values,
    indicating time before the horn sounded (0:00 mark).
    """

    def test_prehorn_snapshots_have_negative_game_time(self, entities_with_prehord):
        """Test that early snapshots have negative game_time (before horn)."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) > 0

        prehorn_snapshots = [s for s in result.entities.snapshots if s.game_time < 0]
        assert len(prehorn_snapshots) > 0, "Should have pre-horn snapshots with negative game_time"

        for snap in prehorn_snapshots:
            assert snap.game_time < 0
            assert snap.tick > 0

    def test_game_start_tick_is_populated(self, entities_with_prehord):
        """Test that game_start_tick is returned and non-zero."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert result.entities.game_start_tick > 0, "game_start_tick should be positive"
        # For typical Dota 2 replays, game starts around tick 20000-40000
        assert result.entities.game_start_tick > 10000

    def test_game_time_str_formats_negative_times(self, entities_with_prehord):
        """Test game_time_str property formats negative times with minus sign."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None

        prehorn_snapshots = [s for s in result.entities.snapshots if s.game_time < 0]
        assert len(prehorn_snapshots) > 0

        for snap in prehorn_snapshots:
            time_str = snap.game_time_str
            assert time_str.startswith("-"), f"Pre-horn time should start with '-': {time_str}"
            assert ":" in time_str, f"Time should contain colon: {time_str}"

    def test_posthorn_snapshots_have_positive_game_time(self, entities_with_prehord):
        """Test that snapshots after horn have positive game_time."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None

        posthorn_snapshots = [s for s in result.entities.snapshots if s.game_time >= 0]
        assert len(posthorn_snapshots) > 0, "Should have post-horn snapshots"

        for snap in posthorn_snapshots:
            assert snap.game_time >= 0

    def test_game_time_increases_with_tick(self, entities_with_prehord):
        """Test that game_time increases as tick increases."""
        result = entities_with_prehord
        assert result.success is True
        assert result.entities is not None
        assert len(result.entities.snapshots) >= 2

        snapshots = sorted(result.entities.snapshots, key=lambda s: s.tick)
        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            assert curr.tick > prev.tick
            assert curr.game_time > prev.game_time, \
                f"game_time should increase: {prev.game_time} -> {curr.game_time}"


class TestCreepPositions:
    """Test creep entity positions (FEATURE #9).

    When include_creeps=True, snapshots should include lane and neutral creep positions.
    """

    def test_include_creeps_populates_creeps_list(self, entities_with_creeps):
        """Test that include_creeps=True populates creeps in snapshots."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        snapshots_with_creeps = [s for s in result.entities.snapshots if len(s.creeps) > 0]
        assert len(snapshots_with_creeps) > 0, "Should have snapshots with creeps"

    def test_creep_snapshot_has_expected_fields(self, entities_with_creeps):
        """Test CreepSnapshot model has all expected fields."""
        from python_manta import CreepSnapshot

        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        for snap in result.entities.snapshots:
            for creep in snap.creeps:
                assert isinstance(creep, CreepSnapshot)
                assert hasattr(creep, 'entity_id')
                assert hasattr(creep, 'class_name')
                assert hasattr(creep, 'name')
                assert hasattr(creep, 'team')
                assert hasattr(creep, 'x')
                assert hasattr(creep, 'y')
                assert hasattr(creep, 'health')
                assert hasattr(creep, 'max_health')
                assert hasattr(creep, 'is_neutral')
                assert hasattr(creep, 'is_lane')
                break  # Just need to verify one
            if snap.creeps:
                break

    def test_creeps_have_valid_team_values(self, entities_with_creeps):
        """Test creeps have valid team values (2=Radiant, 3=Dire, 4=Neutral)."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        valid_teams = {0, 2, 3, 4}  # 0=unknown, 2=Radiant, 3=Dire, 4=Neutral
        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        for creep in all_creeps:
            assert creep.team in valid_teams, f"Invalid team: {creep.team}"

    def test_lane_creeps_have_is_lane_flag(self, entities_with_creeps):
        """Test lane creeps have is_lane=True flag."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        lane_creeps = [c for c in all_creeps if c.is_lane]
        # Lane creeps should exist in any normal game
        assert len(lane_creeps) > 0, "Should have lane creeps with is_lane=True"

        for creep in lane_creeps:
            assert "Lane" in creep.class_name or "creep" in creep.name.lower()
            assert creep.team in {2, 3}, f"Lane creeps should be Radiant(2) or Dire(3), got {creep.team}"

    def test_neutral_creeps_have_is_neutral_flag(self, entities_with_creeps):
        """Test neutral creeps have is_neutral=True flag."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        neutral_creeps = [c for c in all_creeps if c.is_neutral]
        # Neutral creeps should exist in any normal game
        assert len(neutral_creeps) > 0, "Should have neutral creeps with is_neutral=True"

        for creep in neutral_creeps:
            assert "Neutral" in creep.class_name

    def test_creeps_have_valid_positions(self, entities_with_creeps):
        """Test creeps have positions within valid map bounds."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        # Dota 2 map is roughly -8192 to +8192 world units
        for creep in all_creeps:
            assert -10000 < creep.x < 10000, f"X position out of bounds: {creep.x}"
            assert -10000 < creep.y < 10000, f"Y position out of bounds: {creep.y}"

    def test_creeps_have_positive_health(self, entities_with_creeps):
        """Test creeps have positive health values."""
        result = entities_with_creeps
        assert result.success is True
        assert result.entities is not None

        all_creeps = []
        for snap in result.entities.snapshots:
            all_creeps.extend(snap.creeps)

        assert len(all_creeps) > 0, "Should have creeps to test"
        for creep in all_creeps:
            assert creep.health >= 0, f"Health should be non-negative: {creep.health}"
            assert creep.max_health > 0, f"Max health should be positive: {creep.max_health}"

    def test_creeps_not_included_by_default(self, entities_result):
        """Test that creeps are NOT included when include_creeps is not set."""
        result = entities_result
        assert result.success is True
        assert result.entities is not None

        for snap in result.entities.snapshots:
            assert len(snap.creeps) == 0, "Creeps should not be included by default"


class TestCampsStacked:
    """Test camps_stacked field extraction from entity properties (FEATURE #11).

    The camps_stacked stat is extracted from CDOTA_DataRadiant/CDOTA_DataDire
    entities via the m_vecDataTeam.%04d.m_iCampsStacked property.
    """

    def test_camps_stacked_field_exists(self, snapshot_30k):
        """Test HeroSnapshot has camps_stacked field."""
        snap = snapshot_30k
        assert snap is not None
        assert len(snap.heroes) > 0

        for hero in snap.heroes:
            assert hasattr(hero, 'camps_stacked'), "HeroSnapshot should have camps_stacked field"
            assert isinstance(hero.camps_stacked, int)

    def test_camps_stacked_non_negative(self, snapshot_lategame):
        """Test camps_stacked values are non-negative."""
        snap = snapshot_lategame
        assert snap is not None
        assert len(snap.heroes) > 0

        for hero in snap.heroes:
            assert hero.camps_stacked >= 0, f"camps_stacked should be >= 0, got {hero.camps_stacked}"

    def test_camps_stacked_increases_over_time(self, snapshot_30k, snapshot_lategame):
        """Test camps_stacked generally increases over time in a match."""
        early_snap = snapshot_30k
        late_snap = snapshot_lategame
        assert early_snap is not None and late_snap is not None

        early_total = sum(h.camps_stacked for h in early_snap.heroes)
        late_total = sum(h.camps_stacked for h in late_snap.heroes)

        assert late_total >= early_total, \
            f"Total camps_stacked should increase over time: {early_total} -> {late_total}"

    def test_camps_stacked_supports_have_stacks(self, snapshot_lategame):
        """Test that at least some heroes have camps_stacked > 0 in late game.

        In a typical pro match, supports stack camps for carries.
        """
        snap = snapshot_lategame
        assert snap is not None
        assert len(snap.heroes) == 10

        heroes_with_stacks = [h for h in snap.heroes if h.camps_stacked > 0]
        assert len(heroes_with_stacks) > 0, \
            "At least one hero should have camps_stacked > 0 in late game"

    def test_camps_stacked_reasonable_values(self, snapshot_lategame):
        """Test camps_stacked values are within reasonable range.

        Even in a long game, individual player stacks rarely exceed 30.
        """
        snap = snapshot_lategame
        assert snap is not None

        for hero in snap.heroes:
            assert hero.camps_stacked < 50, \
                f"camps_stacked unusually high for {hero.hero_name}: {hero.camps_stacked}"


class TestHeroLevelInjection:
    """Test hero level injection from entity state into combat log.

    Previously, target_hero_level and attacker_hero_level were always 0
    because Dota 2 doesn't populate these protobuf fields. Now we inject
    hero levels from entity state (m_iCurrentLevel) during parsing.

    Real data from match 8447659831 (Team Spirit vs Tundra):
    - Total hero deaths: 48
    - Deaths with target_hero_level > 0: 48 (100%)
    - Deaths with attacker_hero_level > 0: 45 (94%)
    """

    def test_hero_deaths_have_target_levels(self, combat_log_hero_deaths):
        """Test that all hero deaths now have target_hero_level populated.

        This was 0% before the fix, now should be 100%.
        """
        result = combat_log_hero_deaths
        assert result.success is True
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        assert len(hero_deaths) == 48  # Real value from match

        deaths_with_level = sum(1 for d in hero_deaths if d.target_hero_level > 0)
        assert deaths_with_level == 48  # 100% now have levels

    def test_hero_deaths_have_attacker_levels(self, combat_log_hero_deaths):
        """Test that most hero deaths have attacker_hero_level populated.

        Non-hero attackers (summons, neutrals, wards) will have 0.
        Real data: 45/48 = 94% have attacker levels.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        deaths_with_attacker_level = sum(1 for d in hero_deaths if d.attacker_hero_level > 0)

        # 45 of 48 deaths had hero attackers
        assert deaths_with_attacker_level == 45

    def test_nonhero_attackers_have_zero_level(self, combat_log_hero_deaths):
        """Test that non-hero attackers correctly have level 0.

        Real data shows 3 deaths from non-heroes:
        - npc_dota_lycan_wolf4 (summon)
        - npc_dota_neutral_black_dragon (neutral creep)
        - npc_dota_shadow_shaman_ward_2 (ward)
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        nonhero_attacker_deaths = [d for d in hero_deaths if not d.is_attacker_hero]

        # All non-hero attackers should have level 0
        for death in nonhero_attacker_deaths:
            assert death.attacker_hero_level == 0

        # Should be exactly 3 non-hero attacker deaths
        assert len(nonhero_attacker_deaths) == 3

    def test_hero_levels_are_realistic(self, combat_log_hero_deaths):
        """Test that hero levels are within valid Dota 2 range (1-30)."""
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        for entry in result.combat_log.entries:
            if entry.target_hero_level > 0:
                assert 1 <= entry.target_hero_level <= 30
            if entry.attacker_hero_level > 0:
                assert 1 <= entry.attacker_hero_level <= 30

    def test_hero_levels_increase_over_game(self, combat_log_hero_deaths):
        """Test that hero levels generally increase as game progresses.

        Sample early vs late deaths to verify levels grow over time.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        # Get first and last few deaths with levels
        early_deaths = [d for d in hero_deaths[:10] if d.target_hero_level > 0]
        late_deaths = [d for d in hero_deaths[-10:] if d.target_hero_level > 0]

        early_avg = sum(d.target_hero_level for d in early_deaths) / len(early_deaths)
        late_avg = sum(d.target_hero_level for d in late_deaths) / len(late_deaths)

        # Late game levels should be higher than early game
        assert late_avg > early_avg

    def test_first_death_level_is_low(self, combat_log_hero_deaths):
        """Test that the first hero death has a low level (early game).

        First death at 00:10 - should be level 1.
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]
        first_death = hero_deaths[0]

        # First death at 00:10 game time
        assert first_death.game_time < 60  # Within first minute
        assert first_death.target_hero_level == 1  # Level 1 at game start

    def test_specific_death_levels_match_real_data(self, combat_log_hero_deaths):
        """Test specific death events match verified real data.

        Sample verified deaths from manual inspection:
        - [03:36] hoodwink (lvl 2) killed by pugna (lvl 2)
        - [05:09] pugna (lvl 3) killed by bristleback (lvl 3)
        - [10:24] hoodwink (lvl 5) killed by faceless_void (lvl 7)
        """
        result = combat_log_hero_deaths
        assert result.combat_log is not None

        hero_deaths = [e for e in result.combat_log.entries if e.is_target_hero]

        # Find death around 03:36 (216 seconds)
        hoodwink_death = next(
            (d for d in hero_deaths
             if "hoodwink" in d.target_name and 210 < d.game_time < 220),
            None
        )
        assert hoodwink_death is not None
        assert hoodwink_death.target_hero_level == 2
        assert hoodwink_death.attacker_hero_level == 2

        # Find bristleback kill around 05:09 (309 seconds)
        pugna_death = next(
            (d for d in hero_deaths
             if "pugna" in d.target_name and 305 < d.game_time < 315),
            None
        )
        assert pugna_death is not None
        assert pugna_death.target_hero_level == 3
        assert pugna_death.attacker_hero_level == 3


class TestHeroInventory:
    """Test hero inventory extraction from entity state.

    Inventory slots:
        - 0-5: Main inventory (6 slots)
        - 6-8: Backpack (3 slots)
        - 9: TP scroll slot
        - 10-15: Stash (6 slots)
        - 16: Neutral item slot

    Real data from match 8447659831 (Team Spirit vs Tundra).
    All values are exact from replay parsing.
    """

    def test_troll_warlord_inventory_tick_30000(self, snapshot_30k):
        """Test Troll Warlord exact inventory at tick 30000 (game_time=11.87s).

        Exact inventory: 6 items total.
        """
        snap = snapshot_30k
        assert snap.game_time == pytest.approx(11.866667, abs=0.01)

        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")
        assert len(troll.inventory) == 6

        # Exact items with slot, name, charges
        expected = [
            (0, "item_tango", 3),
            (1, "item_magicstick", 1),
            (3, "item_ironwoodbranch", 0),
            (4, "item_ironwoodbranch", 0),
            (5, "item_quellingblade", 0),
            (15, "item_teleportscroll", 2),
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(troll.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_chen_inventory_tick_30000(self, snapshot_30k):
        """Test Chen exact inventory at tick 30000.

        Exact inventory: 7 items total.
        """
        snap = snapshot_30k
        chen = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_chen")
        assert len(chen.inventory) == 7

        expected = [
            (0, "item_tango", 3),
            (1, "item_circlet", 0),
            (2, "item_sentryward", 2),
            (3, "item_ironwoodbranch", 0),
            (4, "item_faerie_fire", 1),
            (5, "item_blood_grenade", 1),
            (15, "item_teleportscroll", 1),
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(chen.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_hoodwink_inventory_tick_30000(self, snapshot_30k):
        """Test Hoodwink exact inventory at tick 30000.

        Has backpack item in slot 6.
        """
        snap = snapshot_30k
        hoodwink = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_hoodwink")
        assert len(hoodwink.inventory) == 8

        expected = [
            (0, "item_tango", 3),
            (1, "item_sentryward", 1),
            (2, "item_faerie_fire", 1),
            (3, "item_blood_grenade", 1),
            (4, "item_magicstick", 1),
            (5, "item_ironwoodbranch", 0),
            (6, "item_ironwoodbranch", 0),  # Backpack
            (15, "item_teleportscroll", 1),
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(hoodwink.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_shadow_shaman_inventory_tick_30000(self, snapshot_30k):
        """Test Shadow Shaman exact inventory at tick 30000.

        Has backpack item in slot 6.
        """
        snap = snapshot_30k
        shaman = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_shadow_shaman")
        assert len(shaman.inventory) == 7

        expected = [
            (0, "item_tango", 3),
            (2, "item_magicstick", 3),
            (3, "item_ironwoodbranch", 0),
            (4, "item_ironwoodbranch", 0),
            (5, "item_faerie_fire", 1),
            (6, "item_sentryward", 1),  # Backpack
            (15, "item_teleportscroll", 1),
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(shaman.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_troll_warlord_inventory_tick_60000(self, snapshot_60k):
        """Test Troll Warlord exact inventory at tick 60000 (game_time=1011.87s).

        Has neutral item, backpack item, and TP slot item.
        """
        snap = snapshot_60k
        assert snap.game_time == pytest.approx(1011.866667, abs=0.01)

        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")
        assert len(troll.inventory) == 9

        expected = [
            (0, "item_circlet", 0),
            (1, "item_phaseboots", 0),
            (2, "item_magicstick", 5),
            (3, "item_ogreaxe", 0),
            (4, "item_yasha", 0),
            (5, "item_battlefury", 0),
            (6, "item_ironwoodbranch", 0),  # Backpack
            (9, "item_beltofstrength", 0),  # TP slot
            (16, "item_poormansshield", 0),  # Neutral
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(troll.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_chen_inventory_tick_60000(self, snapshot_60k):
        """Test Chen exact inventory at tick 60000.

        Magic wand with 20 charges.
        """
        snap = snapshot_60k
        chen = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_chen")
        assert len(chen.inventory) == 9

        expected = [
            (0, "item_sentryward", 1),
            (1, "item_circlet", 0),
            (2, "item_magicwand", 20),
            (3, "item_ancient_janggo", 0),
            (4, "item_ring_of_basilius", 0),
            (5, "item_clarity", 2),
            (6, "item_windlace", 0),  # Backpack
            (15, "item_teleportscroll", 1),  # Stash
            (16, "item_dormant_curio", 0),  # Neutral
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(chen.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_bristleback_inventory_tick_60000(self, snapshot_60k):
        """Test Bristleback exact inventory at tick 60000.

        Full main inventory, backpack items, neutral item.
        """
        snap = snapshot_60k
        bristle = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_bristleback")
        assert len(bristle.inventory) == 10

        expected = [
            (0, "item_powertreads", 0),
            (1, "item_magicwand", 20),
            (2, "item_blade_mail", 0),
            (3, "item_nulltalisman", 0),
            (4, "item_platemail", 0),
            (5, "item_bracer", 0),
            (6, "item_perseverance", 0),  # Backpack
            (7, "item_recipe_lotus_orb", 0),  # Backpack
            (15, "item_teleportscroll", 1),  # Stash
            (16, "item_occult_bracelet", 0),  # Neutral
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(bristle.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_hoodwink_inventory_tick_60000(self, snapshot_60k):
        """Test Hoodwink exact inventory at tick 60000.

        Full backpack (slots 6, 7, 8).
        """
        snap = snapshot_60k
        hoodwink = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_hoodwink")
        assert len(hoodwink.inventory) == 10

        expected = [
            (0, "item_arcane_boots", 0),
            (1, "item_ward_dispenser", 1),
            (2, "item_flask", 1),
            (4, "item_magicwand", 9),
            (5, "item_infused_raindrop", 3),
            (6, "item_smoke_of_deceit", 1),  # Backpack
            (7, "item_famango", 1),  # Backpack
            (8, "item_ward_dispenser", 1),  # Backpack
            (15, "item_teleportscroll", 1),  # Stash
            (16, "item_kobold_cup", 0),  # Neutral
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(hoodwink.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_pugna_inventory_tick_60000(self, snapshot_60k):
        """Test Pugna exact inventory at tick 60000.

        No stash items, neutral item present.
        """
        snap = snapshot_60k
        pugna = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_pugna")
        assert len(pugna.inventory) == 5

        expected = [
            (2, "item_arcane_boots", 0),
            (3, "item_magicwand", 13),
            (4, "item_sentryward", 2),
            (5, "item_pavise", 0),
            (16, "item_dormant_curio", 0),  # Neutral
        ]
        actual = [(i.slot, i.name, i.charges) for i in sorted(pugna.inventory, key=lambda x: x.slot)]
        assert actual == expected

    def test_all_heroes_neutral_items_tick_60000(self, snapshot_60k):
        """Test exact neutral items for all 10 heroes at tick 60000."""
        snap = snapshot_60k

        expected_neutrals = {
            "npc_dota_hero_troll_warlord": "item_poormansshield",
            "npc_dota_hero_chen": "item_dormant_curio",
            "npc_dota_hero_monkey_king": "item_spark_of_courage",
            "npc_dota_hero_hoodwink": "item_kobold_cup",
            "npc_dota_hero_bristleback": "item_occult_bracelet",
            "npc_dota_hero_lycan": "item_ripperslash",
            "npc_dota_hero_pugna": "item_dormant_curio",
            "npc_dota_hero_faceless_void": "item_ripperslash",
            "npc_dota_hero_storm_spirit": "item_dormant_curio",
            "npc_dota_hero_shadow_shaman": "item_kobold_cup",
        }

        for hero in snap.heroes:
            expected = expected_neutrals[hero.hero_name]
            assert hero.neutral_item is not None, f"{hero.hero_name} should have neutral item"
            assert hero.neutral_item.name == expected, \
                f"{hero.hero_name}: expected {expected}, got {hero.neutral_item.name}"

    def test_main_inventory_property(self, snapshot_60k):
        """Test main_inventory property returns only slots 0-5."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        main = troll.main_inventory
        assert len(main) == 6
        assert [i.slot for i in main] == [0, 1, 2, 3, 4, 5]

    def test_backpack_property(self, snapshot_60k):
        """Test backpack property returns only slots 6-8."""
        snap = snapshot_60k
        hoodwink = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_hoodwink")

        backpack = hoodwink.backpack
        assert len(backpack) == 3
        assert [i.slot for i in backpack] == [6, 7, 8]

    def test_stash_property(self, snapshot_60k):
        """Test stash property returns only slots 10-15."""
        snap = snapshot_60k
        chen = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_chen")

        stash = chen.stash
        assert len(stash) == 1
        assert stash[0].slot == 15
        assert stash[0].name == "item_teleportscroll"

    def test_neutral_item_property(self, snapshot_60k):
        """Test neutral_item property returns slot 16."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        neutral = troll.neutral_item
        assert neutral is not None
        assert neutral.slot == 16
        assert neutral.name == "item_poormansshield"

    def test_tp_scroll_property(self, snapshot_60k):
        """Test tp_scroll property returns slot 9."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        tp = troll.tp_scroll
        assert tp is not None
        assert tp.slot == 9
        assert tp.name == "item_beltofstrength"

    def test_get_item_method(self, snapshot_60k):
        """Test get_item returns correct item by partial name match."""
        snap = snapshot_60k
        bristle = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_bristleback")

        treads = bristle.get_item("treads")
        assert treads is not None
        assert treads.name == "item_powertreads"
        assert treads.slot == 0

        wand = bristle.get_item("magicwand")
        assert wand is not None
        assert wand.charges == 20

        assert bristle.get_item("radiance") is None

    def test_has_item_method(self, snapshot_60k):
        """Test has_item returns True/False correctly."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        assert troll.has_item("battlefury") is True
        assert troll.has_item("phaseboots") is True
        assert troll.has_item("radiance") is False

    def test_item_short_name_property(self, snapshot_60k):
        """Test ItemSnapshot.short_name removes item_ prefix."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        bf = troll.get_item("battlefury")
        assert bf.name == "item_battlefury"
        assert bf.short_name == "battlefury"

    def test_item_slot_classification_properties(self, snapshot_60k):
        """Test is_main_inventory, is_backpack, is_stash, is_neutral_slot properties."""
        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        for item in troll.inventory:
            if item.slot <= 5:
                assert item.is_main_inventory is True
                assert item.is_backpack is False
            elif item.slot <= 8:
                assert item.is_backpack is True
                assert item.is_main_inventory is False
            elif item.slot == 9:
                assert item.is_tp_slot is True
            elif item.slot <= 15:
                assert item.is_stash is True
            elif item.slot == 16:
                assert item.is_neutral_slot is True

    def test_neutral_item_enum_property(self, snapshot_60k):
        """Test neutral_item_enum returns NeutralItem enum for neutral items."""
        from python_manta import NeutralItem

        snap = snapshot_60k
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")

        # Troll has item_poormansshield in neutral slot
        neutral = troll.neutral_item
        assert neutral is not None
        assert neutral.name == "item_poormansshield"
        assert neutral.neutral_item_enum == NeutralItem.POOR_MANS_SHIELD
        assert neutral.is_neutral_item is True

        # Regular item should return None for neutral_item_enum
        bf = troll.get_item("battlefury")
        assert bf is not None
        assert bf.neutral_item_enum is None
        assert bf.is_neutral_item is False

    def test_item_display_name_property(self, snapshot_60k):
        """Test display_name returns human-readable names."""
        snap = snapshot_60k

        # Neutral item uses NeutralItem.display_name
        troll = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord")
        neutral = troll.neutral_item
        assert neutral.display_name == "Poor Man's Shield"

        # Regular item uses title case
        bf = troll.get_item("battlefury")
        assert bf.display_name == "Battlefury"

        # Item with underscores
        chen = next(h for h in snap.heroes if h.hero_name == "npc_dota_hero_chen")
        janggo = chen.get_item("ancient_janggo")
        assert janggo.display_name == "Ancient Janggo"
