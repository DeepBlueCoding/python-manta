"""Comprehensive tests for attacks collector.

Tests ranged (TE_Projectile) and melee (combat log) attack tracking.
Uses match 8447659831 (Team Spirit vs Tundra) as reference.

Verifies exact values from real replay data, not just existence.
"""

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]


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

# First Troll Warlord melee attack (with all combat log fields)
FIRST_TROLL_MELEE = {
    "tick": 28228,
    "game_time_str": "15:40",
    "source_index": 1322,
    "attacker_name": "npc_dota_hero_troll_warlord",
    "target_name": "npc_dota_neutral_polar_furbolg_champion",
    "damage": 50,
    "target_health": 62,
    "attacker_team": 2,  # Radiant
    "target_team": 2,    # Neutral creeps show as Radiant in combat log
    "is_melee": True,
    "is_attacker_hero": True,
    "is_target_hero": False,
    "is_attacker_illusion": False,
    "is_target_illusion": False,
    "is_target_building": False,
    "damage_type": 1,  # Physical
}

# First hero vs hero melee attack (Faceless Void vs Hoodwink)
FIRST_HERO_VS_HERO_MELEE = {
    "tick": 29552,
    "game_time_str": "16:25",
    "attacker_name": "npc_dota_hero_faceless_void",
    "target_name": "npc_dota_hero_hoodwink",
    "damage": 51,
    "target_health": 515,
    "attacker_team": 3,  # Dire
    "target_team": 2,    # Radiant
    "is_attacker_hero": True,
    "is_target_hero": True,
    "damage_type": 1,  # Physical
}

# First Troll Warlord last hit (target_health=0)
FIRST_TROLL_LAST_HIT = {
    "tick": 30950,
    "game_time_str": "17:11",
    "attacker_name": "npc_dota_hero_troll_warlord",
    "target_name": "npc_dota_creep_badguys_melee",
    "damage": 60,
    "target_health": 0,
    "attacker_team": 2,  # Radiant
    "target_team": 3,    # Dire
}

# First hero building attack (Troll hitting tower)
FIRST_HERO_BUILDING_ATTACK = {
    "tick": 43040,
    "game_time_str": "23:54",
    "attacker_name": "npc_dota_hero_troll_warlord",
    "target_name": "npc_dota_badguys_tower1_bot",
    "damage": 23,
    "target_health": 1481,
    "attacker_team": 2,  # Radiant
    "target_team": 3,    # Dire
    "is_attacker_hero": True,
    "is_target_building": True,
}

# First illusion melee attack
FIRST_ILLUSION_ATTACK = {
    "tick": 61469,
    "game_time_str": "34:08",
    "attacker_name": "npc_dota_hero_storm_spirit",
    "target_name": "npc_dota_hero_bristleback",
    "is_attacker_illusion": True,
    "damage": 6,
}

# First deny (same team last hit)
FIRST_DENY = {
    "tick": 30458,
    "game_time_str": "16:55",
    "attacker_name": "npc_dota_hero_storm_spirit",
    "target_name": "npc_dota_creep_badguys_melee",
    "damage": 49,
    "target_health": 0,
    "attacker_team": 3,  # Dire
    "target_team": 3,    # Dire (same team = deny)
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

# Expected counts for combat log fields
EXPECTED_HERO_VS_HERO_COUNT = 1133
EXPECTED_BUILDING_ATTACKS_COUNT = 2349
EXPECTED_HERO_LAST_HITS_COUNT = 1328
EXPECTED_ILLUSION_ATTACKS_COUNT = 182
EXPECTED_TROLL_LAST_HITS_COUNT = 342


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


class TestMeleeCombatLogFields:
    """Test combat log fields populated for melee attacks."""

    def test_melee_has_target_health(self, melee_attacks):
        """Melee attacks should have target_health field."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name]
        with_health = [a for a in hero_melee if a.target_health >= 0]
        assert len(with_health) > 1000, f"Expected >1k melee with target_health, got {len(with_health)}"

    def test_melee_target_health_zero_on_kill(self, melee_attacks):
        """Some melee attacks should result in target_health=0 (last hits)."""
        kills = [a for a in melee_attacks if a.target_health == 0]
        assert len(kills) > 100, f"Expected >100 last hits (health=0), got {len(kills)}"

    def test_melee_has_team_info(self, melee_attacks):
        """Melee attacks should have attacker_team and target_team."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name]
        with_team = [a for a in hero_melee if a.attacker_team in (2, 3)]
        assert len(with_team) > 1000, f"Expected >1k melee with valid attacker_team, got {len(with_team)}"

    def test_melee_team_values(self, melee_attacks):
        """Team values should be 2 (Radiant) or 3 (Dire)."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name][:100]
        for attack in hero_melee:
            if attack.attacker_team != 0:
                assert attack.attacker_team in (2, 3), f"Invalid attacker_team: {attack.attacker_team}"
            if attack.target_team != 0:
                assert attack.target_team in (2, 3), f"Invalid target_team: {attack.target_team}"

    def test_melee_has_is_attacker_hero(self, melee_attacks):
        """Melee attacks from heroes should have is_attacker_hero=True."""
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name]
        hero_flagged = [a for a in hero_melee if a.is_attacker_hero]
        assert len(hero_flagged) > 5000, f"Expected >5k hero melee with is_attacker_hero=True, got {len(hero_flagged)}"

    def test_melee_has_is_target_hero(self, melee_attacks):
        """Some melee attacks should have is_target_hero=True (hero vs hero)."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert len(hero_vs_hero) > 100, f"Expected >100 hero vs hero melee, got {len(hero_vs_hero)}"

    def test_melee_is_target_building(self, melee_attacks):
        """Some melee attacks should target buildings (towers/barracks)."""
        building_attacks = [a for a in melee_attacks if a.is_target_building]
        assert len(building_attacks) > 50, f"Expected >50 building attacks, got {len(building_attacks)}"

    def test_melee_damage_type_is_physical(self, melee_attacks):
        """Auto-attack damage should be physical (damage_type=1 in combat log)."""
        # Combat log damage types: 0=none, 1=physical, 2=magical, 4=pure
        hero_melee = [a for a in melee_attacks if "npc_dota_hero" in a.attacker_name][:100]
        for attack in hero_melee:
            assert attack.damage_type == 1, f"Expected physical damage (1), got {attack.damage_type}"

    def test_troll_melee_has_all_combat_fields(self, melee_attacks):
        """Troll Warlord melee attacks should have all combat log fields."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert len(troll_melee) > 0, "No Troll Warlord melee attacks"
        first = troll_melee[0]
        assert first.damage > 0
        assert first.target_health >= 0
        assert first.attacker_team in (2, 3)
        assert first.is_attacker_hero is True
        assert first.damage_type == 1  # Physical (combat log: 1=physical, 2=magical, 4=pure)

    def test_creep_attacks_have_combat_fields(self, melee_attacks):
        """Creep melee attacks should also have combat log fields."""
        creep_melee = [a for a in melee_attacks if "creep" in a.attacker_name]
        assert len(creep_melee) > 1000, f"Expected >1k creep melee attacks, got {len(creep_melee)}"
        sample = creep_melee[0]
        assert sample.damage > 0
        assert sample.is_attacker_hero is False


class TestCombatLogFieldsExactValues:
    """Test combat log fields have exact values from real replay data."""

    def test_first_troll_melee_target_health(self, melee_attacks):
        """First Troll melee attack has exact target_health value."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].target_health == FIRST_TROLL_MELEE["target_health"]

    def test_first_troll_melee_attacker_team(self, melee_attacks):
        """First Troll melee attack has exact attacker_team value (Radiant=2)."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].attacker_team == FIRST_TROLL_MELEE["attacker_team"]

    def test_first_troll_melee_target_team(self, melee_attacks):
        """First Troll melee attack has exact target_team value."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].target_team == FIRST_TROLL_MELEE["target_team"]

    def test_first_troll_melee_is_attacker_hero(self, melee_attacks):
        """First Troll melee attack has is_attacker_hero=True."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].is_attacker_hero == FIRST_TROLL_MELEE["is_attacker_hero"]

    def test_first_troll_melee_is_target_hero(self, melee_attacks):
        """First Troll melee attack has is_target_hero=False (attacking neutral)."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].is_target_hero == FIRST_TROLL_MELEE["is_target_hero"]

    def test_first_troll_melee_is_attacker_illusion(self, melee_attacks):
        """First Troll melee attack has is_attacker_illusion=False."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].is_attacker_illusion == FIRST_TROLL_MELEE["is_attacker_illusion"]

    def test_first_troll_melee_damage_type(self, melee_attacks):
        """First Troll melee attack has damage_type=1 (physical)."""
        troll_melee = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord"]
        assert troll_melee[0].damage_type == FIRST_TROLL_MELEE["damage_type"]


class TestHeroVsHeroExactValues:
    """Test hero vs hero melee attacks have exact values."""

    def test_first_hero_vs_hero_tick(self, melee_attacks):
        """First hero vs hero melee attack has exact tick."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].tick == FIRST_HERO_VS_HERO_MELEE["tick"]

    def test_first_hero_vs_hero_game_time(self, melee_attacks):
        """First hero vs hero melee attack has exact game time."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].game_time_str == FIRST_HERO_VS_HERO_MELEE["game_time_str"]

    def test_first_hero_vs_hero_attacker(self, melee_attacks):
        """First hero vs hero melee attack is Faceless Void."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].attacker_name == FIRST_HERO_VS_HERO_MELEE["attacker_name"]

    def test_first_hero_vs_hero_target(self, melee_attacks):
        """First hero vs hero melee attack target is Hoodwink."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].target_name == FIRST_HERO_VS_HERO_MELEE["target_name"]

    def test_first_hero_vs_hero_damage(self, melee_attacks):
        """First hero vs hero melee attack has exact damage value."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].damage == FIRST_HERO_VS_HERO_MELEE["damage"]

    def test_first_hero_vs_hero_target_health(self, melee_attacks):
        """First hero vs hero melee attack has exact target health."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].target_health == FIRST_HERO_VS_HERO_MELEE["target_health"]

    def test_first_hero_vs_hero_teams(self, melee_attacks):
        """First hero vs hero melee attack has correct team values (Dire vs Radiant)."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert hero_vs_hero[0].attacker_team == FIRST_HERO_VS_HERO_MELEE["attacker_team"]
        assert hero_vs_hero[0].target_team == FIRST_HERO_VS_HERO_MELEE["target_team"]

    def test_hero_vs_hero_count(self, melee_attacks):
        """Match has exact number of hero vs hero melee attacks."""
        hero_vs_hero = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_hero]
        assert len(hero_vs_hero) == EXPECTED_HERO_VS_HERO_COUNT


class TestLastHitExactValues:
    """Test last hit (target_health=0) exact values."""

    def test_first_troll_last_hit_tick(self, melee_attacks):
        """First Troll last hit has exact tick."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert troll_last_hits[0].tick == FIRST_TROLL_LAST_HIT["tick"]

    def test_first_troll_last_hit_game_time(self, melee_attacks):
        """First Troll last hit has exact game time."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert troll_last_hits[0].game_time_str == FIRST_TROLL_LAST_HIT["game_time_str"]

    def test_first_troll_last_hit_target(self, melee_attacks):
        """First Troll last hit target is enemy melee creep."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert troll_last_hits[0].target_name == FIRST_TROLL_LAST_HIT["target_name"]

    def test_first_troll_last_hit_damage(self, melee_attacks):
        """First Troll last hit has exact damage value."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert troll_last_hits[0].damage == FIRST_TROLL_LAST_HIT["damage"]

    def test_first_troll_last_hit_teams(self, melee_attacks):
        """First Troll last hit has correct team values (Radiant vs Dire)."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert troll_last_hits[0].attacker_team == FIRST_TROLL_LAST_HIT["attacker_team"]
        assert troll_last_hits[0].target_team == FIRST_TROLL_LAST_HIT["target_team"]

    def test_troll_last_hits_count(self, melee_attacks):
        """Troll Warlord has exact number of last hits."""
        troll_last_hits = [a for a in melee_attacks if a.attacker_name == "npc_dota_hero_troll_warlord" and a.target_health == 0]
        assert len(troll_last_hits) == EXPECTED_TROLL_LAST_HITS_COUNT

    def test_hero_last_hits_count(self, melee_attacks):
        """Match has exact number of hero last hits."""
        hero_last_hits = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0]
        assert len(hero_last_hits) == EXPECTED_HERO_LAST_HITS_COUNT


class TestBuildingAttackExactValues:
    """Test building attack exact values."""

    def test_first_hero_building_attack_tick(self, melee_attacks):
        """First hero building attack has exact tick."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].tick == FIRST_HERO_BUILDING_ATTACK["tick"]

    def test_first_hero_building_attack_game_time(self, melee_attacks):
        """First hero building attack has exact game time."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].game_time_str == FIRST_HERO_BUILDING_ATTACK["game_time_str"]

    def test_first_hero_building_attack_attacker(self, melee_attacks):
        """First hero building attack is by Troll Warlord."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].attacker_name == FIRST_HERO_BUILDING_ATTACK["attacker_name"]

    def test_first_hero_building_attack_target(self, melee_attacks):
        """First hero building attack target is T1 bot tower."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].target_name == FIRST_HERO_BUILDING_ATTACK["target_name"]

    def test_first_hero_building_attack_damage(self, melee_attacks):
        """First hero building attack has exact damage value."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].damage == FIRST_HERO_BUILDING_ATTACK["damage"]

    def test_first_hero_building_attack_target_health(self, melee_attacks):
        """First hero building attack has exact target health."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].target_health == FIRST_HERO_BUILDING_ATTACK["target_health"]

    def test_first_hero_building_attack_teams(self, melee_attacks):
        """First hero building attack has correct team values."""
        hero_building = [a for a in melee_attacks if a.is_attacker_hero and a.is_target_building]
        assert hero_building[0].attacker_team == FIRST_HERO_BUILDING_ATTACK["attacker_team"]
        assert hero_building[0].target_team == FIRST_HERO_BUILDING_ATTACK["target_team"]

    def test_building_attacks_count(self, melee_attacks):
        """Match has exact number of building attacks."""
        building_attacks = [a for a in melee_attacks if a.is_target_building]
        assert len(building_attacks) == EXPECTED_BUILDING_ATTACKS_COUNT


class TestIllusionAttackExactValues:
    """Test illusion attack exact values."""

    def test_first_illusion_attack_tick(self, melee_attacks):
        """First illusion attack has exact tick."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert illusion_attacks[0].tick == FIRST_ILLUSION_ATTACK["tick"]

    def test_first_illusion_attack_game_time(self, melee_attacks):
        """First illusion attack has exact game time."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert illusion_attacks[0].game_time_str == FIRST_ILLUSION_ATTACK["game_time_str"]

    def test_first_illusion_attack_attacker(self, melee_attacks):
        """First illusion attack is by Storm Spirit illusion."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert illusion_attacks[0].attacker_name == FIRST_ILLUSION_ATTACK["attacker_name"]

    def test_first_illusion_attack_target(self, melee_attacks):
        """First illusion attack target is Bristleback."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert illusion_attacks[0].target_name == FIRST_ILLUSION_ATTACK["target_name"]

    def test_first_illusion_attack_damage(self, melee_attacks):
        """First illusion attack has exact damage value (reduced)."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert illusion_attacks[0].damage == FIRST_ILLUSION_ATTACK["damage"]

    def test_illusion_attacks_count(self, melee_attacks):
        """Match has exact number of illusion attacks."""
        illusion_attacks = [a for a in melee_attacks if a.is_attacker_illusion]
        assert len(illusion_attacks) == EXPECTED_ILLUSION_ATTACKS_COUNT


class TestDenyExactValues:
    """Test deny (same team last hit) exact values."""

    def test_first_deny_tick(self, melee_attacks):
        """First deny has exact tick."""
        denies = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0 and a.attacker_team == a.target_team]
        assert denies[0].tick == FIRST_DENY["tick"]

    def test_first_deny_game_time(self, melee_attacks):
        """First deny has exact game time."""
        denies = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0 and a.attacker_team == a.target_team]
        assert denies[0].game_time_str == FIRST_DENY["game_time_str"]

    def test_first_deny_attacker(self, melee_attacks):
        """First deny is by Storm Spirit."""
        denies = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0 and a.attacker_team == a.target_team]
        assert denies[0].attacker_name == FIRST_DENY["attacker_name"]

    def test_first_deny_target(self, melee_attacks):
        """First deny target is friendly creep."""
        denies = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0 and a.attacker_team == a.target_team]
        assert denies[0].target_name == FIRST_DENY["target_name"]

    def test_first_deny_same_team(self, melee_attacks):
        """First deny has attacker and target on same team (Dire)."""
        denies = [a for a in melee_attacks if a.is_attacker_hero and a.target_health == 0 and a.attacker_team == a.target_team]
        assert denies[0].attacker_team == FIRST_DENY["attacker_team"]
        assert denies[0].target_team == FIRST_DENY["target_team"]
        assert denies[0].attacker_team == denies[0].target_team  # Same team = deny
