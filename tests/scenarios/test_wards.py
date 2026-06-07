"""Tests for wards collector.

Tests ward placement, expiration, and dewarding lifecycle tracking.
Uses match 8447659831 (Team Spirit vs Tundra) as reference.
"""

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]


EXPECTED_TOTAL_WARDS = 105
EXPECTED_OBSERVER_WARDS = 38
EXPECTED_SENTRY_WARDS = 67
EXPECTED_DEWARDS = 33


class TestWardsBasic:

    def test_total_ward_count(self, wards_result):
        assert wards_result.total_events == EXPECTED_TOTAL_WARDS

    def test_observer_count(self, wards_result):
        obs = [w for w in wards_result.events if w.ward_type == "observer"]
        assert len(obs) == EXPECTED_OBSERVER_WARDS

    def test_sentry_count(self, wards_result):
        sen = [w for w in wards_result.events if w.ward_type == "sentry"]
        assert len(sen) == EXPECTED_SENTRY_WARDS

    def test_ward_types_valid(self, wards_result):
        for ward in wards_result.events:
            assert ward.ward_type in ("observer", "sentry")

    def test_wards_have_positions(self, wards_result):
        for ward in wards_result.events:
            assert ward.x != 0 or ward.y != 0

    def test_wards_have_ticks(self, wards_result):
        for ward in wards_result.events:
            assert ward.tick > 0


class TestWardTeams:

    def test_most_wards_have_team(self, wards_result):
        with_team = [w for w in wards_result.events if w.team in (2, 3)]
        assert len(with_team) >= 90

    def test_team_balance(self, wards_result):
        rad = [w for w in wards_result.events if w.team == 2]
        dire = [w for w in wards_result.events if w.team == 3]
        assert len(rad) == len(dire) == 48


class TestDewards:

    def test_deward_count(self, wards_result):
        killed = [w for w in wards_result.events if w.was_killed]
        assert len(killed) == EXPECTED_DEWARDS

    def test_dewards_have_killer(self, wards_result):
        killed = [w for w in wards_result.events if w.was_killed]
        for ward in killed:
            assert ward.killed_by != ""
            assert "npc_dota_hero_" in ward.killed_by

    def test_dewards_have_killer_team(self, wards_result):
        killed = [w for w in wards_result.events if w.was_killed]
        for ward in killed:
            assert ward.killer_team in (2, 3)

    def test_dewards_have_gold_bounty(self, wards_result):
        killed = [w for w in wards_result.events if w.was_killed]
        for ward in killed:
            assert ward.gold_bounty > 0

    def test_killer_team_differs_from_ward_team(self, wards_result):
        killed = [w for w in wards_result.events if w.was_killed and w.team > 0]
        for ward in killed:
            assert ward.killer_team != ward.team


class TestWardLifecycle:

    def test_dead_wards_have_death_tick(self, wards_result):
        dead = [w for w in wards_result.events if w.death_tick > 0]
        assert len(dead) >= 90
        for ward in dead:
            assert ward.death_tick > ward.tick

    def test_dead_wards_have_death_game_time(self, wards_result):
        dead = [w for w in wards_result.events if w.death_tick > 0]
        for ward in dead:
            assert ward.death_game_time_str != ""

    def test_some_wards_placed_by_hero(self, wards_result):
        placed = [w for w in wards_result.events if w.placed_by != ""]
        assert len(placed) > 0
        for ward in placed:
            assert "npc_dota_hero_" in ward.placed_by


class TestWardGameTime:

    def test_game_time_str_format(self, wards_result):
        for ward in wards_result.events:
            assert ward.game_time_str != ""
            assert ":" in ward.game_time_str


class TestGameStartClockWithoutCombatLog:
    """Regression: ward game_time must use the horn offset even when the
    combat_log collector is disabled.

    gameStartTick used to be set ONLY inside the combat log callback, so a
    wards-only parse (exactly what the wards_result fixture does) silently
    degraded TickToGameTime to tick/30: the first ward of this match showed
    game_time ~929s ("15:29") instead of -58.6s ("-0:58"). The fix adds an
    always-on gamerules (m_pGameRules.m_flGameStartTime) fallback detector.
    """

    def test_first_ward_is_pre_horn(self, wards_result):
        first = min(wards_result.events, key=lambda e: e.tick)
        assert first.tick == 27886
        assert first.game_time == pytest.approx(-58.6, abs=0.1)
        assert first.game_time_str == "-0:58"

    def test_pre_horn_ward_count(self, wards_result):
        pre_horn = [e for e in wards_result.events if e.game_time < 0]
        assert len(pre_horn) == 5

    def test_clock_matches_combat_log_detector(self, parser):
        """The gamerules fallback and the GAME_STATE=5 detector must agree."""
        result = parser.parse(wards={}, combat_log={"types": [4], "max_entries": 5})
        assert result.success
        first = min(result.wards.events, key=lambda e: e.tick)
        assert first.game_time == pytest.approx(-58.6, abs=0.1)
