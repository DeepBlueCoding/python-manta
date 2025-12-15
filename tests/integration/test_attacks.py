"""Comprehensive tests for attacks collector.

Tests ranged (TE_Projectile) and melee (combat log) attack tracking.
Uses match 8447659831 (Team Spirit vs Tundra) as reference.

Verifies exact values from real replay data, not just existence.
"""

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

from tests.conftest import DEMO_FILE
from caching_parser import Parser


# Expected values from match 8447659831
EXPECTED_TOTAL_ATTACKS = 32895
EXPECTED_MELEE_ATTACKS = 17000
EXPECTED_RANGED_ATTACKS = 15895

# First ranged attack with hero attacker (Troll Warlord in ranged form)
FIRST_TROLL_RANGED = {
    "tick": 28220,
    "game_time_str": "15:40",
    "source_index": 1322,
    "target_index": 1673,
    "attacker_name": "npc_dota_hero_troll_warlord",
    "projectile_speed": 1200,
    "dodgeable": True,
    "is_melee": False,
}

# First Troll Warlord melee attack
FIRST_TROLL_MELEE = {
    "tick": 28228,
    "game_time_str": "15:40",
    "source_index": 1322,
    "attacker_name": "npc_dota_hero_troll_warlord",
    "target_name": "npc_dota_neutral_polar_furbolg_champion",
    "damage": 50,
    "is_melee": True,
}

# First Pugna ranged attack (attacking Troll Warlord)
FIRST_PUGNA_RANGED = {
    "tick": 29610,
    "game_time_str": "16:27",
    "source_index": 469,
    "target_index": 1322,
    "attacker_name": "npc_dota_hero_pugna",
    "target_name": "npc_dota_hero_troll_warlord",
    "projectile_speed": 900,
    "is_melee": False,
}

# Hero entity IDs for verification
HERO_ENTITY_IDS = {
    "npc_dota_hero_troll_warlord": 1322,
    "npc_dota_hero_pugna": 469,
    "npc_dota_hero_chen": 1372,
    "npc_dota_hero_monkey_king": 1422,
    "npc_dota_hero_faceless_void": 521,
}


@pytest.fixture(scope="module")
def parser():
    return Parser(DEMO_FILE)


@pytest.fixture(scope="module")
def attacks_result(parser):
    """Parse all attack events."""
    result = parser.parse(attacks={"max_events": 0})
    assert result.success, f"Failed to parse attacks: {result.error}"
    return result.attacks


@pytest.fixture(scope="module")
def melee_attacks(attacks_result):
    """Filter melee attacks."""
    return [a for a in attacks_result.events if a.is_melee]


@pytest.fixture(scope="module")
def ranged_attacks(attacks_result):
    """Filter ranged attacks."""
    return [a for a in attacks_result.events if not a.is_melee]


class TestAttackCounts:
    """Test attack counts match expected values."""

    def test_total_attacks(self, attacks_result):
        """Total attacks should match expected count."""
        assert attacks_result.total_events == EXPECTED_TOTAL_ATTACKS

    def test_melee_count(self, melee_attacks):
        """Melee attack count should match expected."""
        assert len(melee_attacks) == EXPECTED_MELEE_ATTACKS

    def test_ranged_count(self, ranged_attacks):
        """Ranged attack count should match expected."""
        assert len(ranged_attacks) == EXPECTED_RANGED_ATTACKS


class TestRangedAttacks:
    """Test ranged attack (TE_Projectile) fields have exact values."""

    def test_first_troll_ranged_tick(self, ranged_attacks):
        """First Troll ranged attack has correct tick."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert len(troll_ranged) > 0, "No Troll Warlord ranged attacks found"
        assert troll_ranged[0].tick == FIRST_TROLL_RANGED["tick"]

    def test_first_troll_ranged_game_time(self, ranged_attacks):
        """First Troll ranged attack has correct game time."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].game_time_str == FIRST_TROLL_RANGED["game_time_str"]

    def test_first_troll_ranged_source_index(self, ranged_attacks):
        """First Troll ranged attack has correct entity index."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].source_index == FIRST_TROLL_RANGED["source_index"]

    def test_first_troll_ranged_target_index(self, ranged_attacks):
        """First Troll ranged attack has correct target entity index."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].target_index == FIRST_TROLL_RANGED["target_index"]

    def test_first_troll_ranged_projectile_speed(self, ranged_attacks):
        """First Troll ranged attack has correct projectile speed."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].projectile_speed == FIRST_TROLL_RANGED["projectile_speed"]

    def test_first_troll_ranged_dodgeable(self, ranged_attacks):
        """First Troll ranged attack is dodgeable."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].dodgeable == FIRST_TROLL_RANGED["dodgeable"]

    def test_first_troll_ranged_is_not_melee(self, ranged_attacks):
        """First Troll ranged attack is not melee."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_ranged[0].is_melee == FIRST_TROLL_RANGED["is_melee"]

    def test_pugna_ranged_exact_values(self, ranged_attacks):
        """Pugna's first ranged attack has all exact values."""
        pugna_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_pugna"]
        assert len(pugna_ranged) > 0, "No Pugna ranged attacks found"

        first = pugna_ranged[0]
        assert first.tick == FIRST_PUGNA_RANGED["tick"]
        assert first.game_time_str == FIRST_PUGNA_RANGED["game_time_str"]
        assert first.source_index == FIRST_PUGNA_RANGED["source_index"]
        assert first.target_index == FIRST_PUGNA_RANGED["target_index"]
        assert first.attacker_name == FIRST_PUGNA_RANGED["attacker_name"]
        assert first.target_name == FIRST_PUGNA_RANGED["target_name"]
        assert first.projectile_speed == FIRST_PUGNA_RANGED["projectile_speed"]
        assert first.is_melee == FIRST_PUGNA_RANGED["is_melee"]

    def test_ranged_attacks_have_location(self, ranged_attacks):
        """Ranged attacks should have non-zero location."""
        with_location = [a for a in ranged_attacks if a.location_x != 0 or a.location_y != 0]
        assert len(with_location) > 10000, f"Expected >10k ranged with location, got {len(with_location)}"


class TestMeleeAttacks:
    """Test melee attack (combat log) fields have exact values."""

    def test_first_troll_melee_tick(self, melee_attacks):
        """First Troll melee attack has correct tick."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert len(troll_melee) > 0, "No Troll Warlord melee attacks found"
        assert troll_melee[0].tick == FIRST_TROLL_MELEE["tick"]

    def test_first_troll_melee_game_time(self, melee_attacks):
        """First Troll melee attack has correct game time."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].game_time_str == FIRST_TROLL_MELEE["game_time_str"]

    def test_first_troll_melee_source_index(self, melee_attacks):
        """First Troll melee attack has correct entity index from name mapping."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].source_index == FIRST_TROLL_MELEE["source_index"]

    def test_first_troll_melee_attacker_name(self, melee_attacks):
        """First Troll melee attack has correct attacker name."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].attacker_name == FIRST_TROLL_MELEE["attacker_name"]

    def test_first_troll_melee_target_name(self, melee_attacks):
        """First Troll melee attack has correct target name."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].target_name == FIRST_TROLL_MELEE["target_name"]

    def test_first_troll_melee_damage(self, melee_attacks):
        """First Troll melee attack has correct damage value."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].damage == FIRST_TROLL_MELEE["damage"]

    def test_first_troll_melee_is_melee(self, melee_attacks):
        """First Troll melee attack is marked as melee."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].is_melee == FIRST_TROLL_MELEE["is_melee"]

    def test_melee_attacks_have_damage(self, melee_attacks):
        """Melee attacks should have non-zero damage."""
        with_damage = [a for a in melee_attacks if a.damage > 0]
        assert len(with_damage) == len(melee_attacks), "All melee attacks should have damage"

    def test_hero_melee_attacks_have_location(self, melee_attacks):
        """Hero melee attacks should have location from entity lookup."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name]
        with_location = [a for a in hero_melee if a.location_x != 0 or a.location_y != 0]
        # Most hero melee attacks should have location (entity was found)
        assert len(with_location) > 5000, f"Expected >5k hero melee with location, got {len(with_location)}"

    def test_troll_melee_has_location(self, melee_attacks):
        """Troll Warlord melee attacks should have location."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        first = troll_melee[0]
        assert first.location_x != 0, "Troll melee should have location_x"
        assert first.location_y != 0, "Troll melee should have location_y"
        # Verify approximate location (Roshan pit area at 15:40)
        assert 9000 < first.location_x < 10000, f"Expected x~9700, got {first.location_x}"
        assert 5000 < first.location_y < 6000, f"Expected y~5200, got {first.location_y}"


class TestHeroEntityIndexConsistency:
    """Test that hero entity indices are consistent between attacks and snapshots."""

    def test_troll_entity_id_matches_snapshot(self, parser, ranged_attacks):
        """Troll Warlord entity ID from attacks matches snapshot."""
        troll_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        troll_entity_id = troll_ranged[0].source_index

        snap = parser.snapshot(target_tick=30000)
        troll_snap = [h for h in snap.heroes if h.hero_name == "npc_dota_hero_troll_warlord"]
        assert len(troll_snap) == 1, "Troll Warlord should be in snapshot"
        assert troll_snap[0].entity_id == troll_entity_id

    def test_pugna_entity_id_matches_snapshot(self, parser, ranged_attacks):
        """Pugna entity ID from attacks matches snapshot."""
        pugna_ranged = [a for a in ranged_attacks if a.attacker_name == "npc_dota_hero_pugna"]
        pugna_entity_id = pugna_ranged[0].source_index

        snap = parser.snapshot(target_tick=30000)
        pugna_snap = [h for h in snap.heroes if h.hero_name == "npc_dota_hero_pugna"]
        assert len(pugna_snap) == 1, "Pugna should be in snapshot"
        assert pugna_snap[0].entity_id == pugna_entity_id


class TestHeroNameFormat:
    """Test hero names use correct underscore-separated format."""

    def test_troll_warlord_name_format(self, melee_attacks):
        """Troll Warlord uses correct underscore format."""
        troll = [a for a in melee_attacks if "troll" in a.attacker_name.lower()]
        assert len(troll) > 0
        assert troll[0].attacker_name == "npc_dota_hero_troll_warlord"

    def test_faceless_void_name_format(self, melee_attacks):
        """Faceless Void uses correct underscore format."""
        void = [a for a in melee_attacks if "faceless" in a.attacker_name.lower()]
        if len(void) > 0:
            assert void[0].attacker_name == "npc_dota_hero_faceless_void"

    def test_monkey_king_name_format(self, parser):
        """Monkey King uses correct underscore format."""
        snap = parser.snapshot(target_tick=30000)
        mk = [h for h in snap.heroes if "monkey" in h.hero_name.lower()]
        assert len(mk) > 0
        assert mk[0].hero_name == "npc_dota_hero_monkey_king"

    def test_shadow_shaman_name_format(self, parser):
        """Shadow Shaman uses correct underscore format."""
        snap = parser.snapshot(target_tick=30000)
        ss = [h for h in snap.heroes if "shadow" in h.hero_name.lower() and "shaman" in h.hero_name.lower()]
        if len(ss) > 0:
            assert ss[0].hero_name == "npc_dota_hero_shadow_shaman"


class TestAttackEventFields:
    """Test that all attack event fields are populated correctly."""

    def test_ranged_has_all_fields(self, ranged_attacks):
        """Ranged attacks should have all expected fields populated."""
        sample = ranged_attacks[100]  # Skip early events that might have empty names
        assert sample.tick > 0
        assert sample.game_time_str != ""
        assert sample.source_index > 0 or sample.attacker_name != ""
        assert sample.projectile_speed > 0
        assert sample.is_melee is False

    def test_melee_has_all_fields(self, melee_attacks):
        """Melee attacks should have all expected fields populated."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name]
        assert len(hero_melee) > 0
        sample = hero_melee[0]
        assert sample.tick > 0
        assert sample.game_time_str != ""
        assert sample.attacker_name != ""
        assert sample.target_name != ""
        assert sample.damage > 0
        assert sample.is_melee is True
        assert sample.source_index > 0  # Hero should have entity index
