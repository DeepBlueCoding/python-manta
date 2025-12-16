"""
Test advanced parser features (respawn, pre-horn positions, creeps, camps_stacked, hero_level_injection).
Tests real data values from actual demo files.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.integration
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
