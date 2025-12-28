"""MCP Replay Dota 2 Server Use-Case Validation Tests.

Validates python-manta can extract all data required by MCP server use-cases:
https://deepbluecoding.github.io/mcp_replay_dota2/latest/examples/use-cases/

Match: 8447659831 - Team Spirit vs Tundra (Captains Mode)
Winner: Radiant (Team Spirit)

Radiant (Team Spirit):
  - Yatoro: Troll Warlord (carry)
  - Collapse: Bristleback (offlane)
  - Larl: Monkey King (mid)
  - Miposhka: Chen (support)
  - rue: Hoodwink (support)

Dire (Tundra):
  - Crystallis: Faceless Void (carry)
  - 33: Lycan (offlane)
  - bzm: Storm Spirit (mid)
  - Saksa: Shadow Shaman (support)
  - Tobi: Pugna (support)

Key Events:
  - First kill: 03:07 - Pugna kills Hoodwink (nether ward)
  - First Roshan: 19:17 - Radiant (Troll Warlord)
  - Second Roshan: 28:57 - Radiant (Troll Warlord)
  - First tower: 11:15 - Dire bot T1 destroyed
"""

import pytest
from python_manta import (
    CombatLogType,
    DamageType,
    Team,
    Hero,
)

pytestmark = [pytest.mark.integration]

# Expected values from match 8447659831
MATCH_ID = 8447659831
RADIANT_TEAM_TAG = "TSpirit"
DIRE_TEAM_TAG = "Tundra"
WINNER = Team.RADIANT

# Yatoro's key item timings (game_time in seconds from tick-based calculation)
YATORO_ITEMS = {
    "item_phase_boots": 365.13333,
    "item_bfury": 756.9667,
    "item_sange_and_yasha": 1043.6666,
    "item_black_king_bar": 1556.8667,
    "item_satanic": 1811.0,
    "item_butterfly": 2227.6,
}

# First real kill (after laning starts)
FIRST_KILL = {
    "victim": "npc_dota_hero_hoodwink",
    "killer": "npc_dota_hero_pugna",
    "game_time": 216.73334,  # 03:37 (tick-based)
    "victim_team": Team.RADIANT,
}

# Roshan kills (tick-based game_time)
ROSHAN_KILLS = [
    {"game_time": 1186.8667, "killer": "npc_dota_hero_troll_warlord", "team": Team.RADIANT},
    {"game_time": 1766.3334, "killer": "npc_dota_hero_troll_warlord", "team": Team.RADIANT},
]

# Tower kills (first 3, tick-based game_time)
TOWER_KILLS = [
    {"game_time": 704.7, "target": "npc_dota_badguys_tower1_bot"},
    {"game_time": 765.2, "target": "npc_dota_badguys_tower1_top"},
    {"game_time": 817.4, "target": "npc_dota_goodguys_tower1_bot"},
]


# Use parser fixture from conftest.py (CachingParser)


@pytest.fixture(scope="module")
def combat_log(parser):
    result = parser.parse(combat_log={"max_entries": 0})
    assert result.success
    return result.combat_log


@pytest.fixture(scope="module")
def game_info(parser):
    result = parser.parse(game_info=True)
    assert result.success
    return result.game_info


class TestMatchContext:
    """Validate match metadata matches expected values."""

    def test_match_id(self, game_info):
        assert game_info.match_id == MATCH_ID

    def test_winner(self, game_info):
        assert game_info.game_winner == WINNER.value

    def test_team_tags(self, game_info):
        assert game_info.radiant_team_tag == RADIANT_TEAM_TAG
        assert game_info.dire_team_tag == DIRE_TEAM_TAG

    def test_player_count(self, game_info):
        assert len(game_info.players) == 10
        radiant = [p for p in game_info.players if p.team == Team.RADIANT.value]
        dire = [p for p in game_info.players if p.team == Team.DIRE.value]
        assert len(radiant) == 5
        assert len(dire) == 5

    def test_yatoro_on_troll_warlord(self, game_info):
        yatoro = next((p for p in game_info.players if p.player_name == "Yatoro"), None)
        assert yatoro is not None
        assert yatoro.hero_name == "npc_dota_hero_troll_warlord"
        assert yatoro.team == Team.RADIANT.value


class TestTeamfightAnalysis:
    """Use Case 1: Analyzing a Lost Teamfight.

    Required: get_hero_deaths(), get_fight_combat_log()
    Fields: game_time, victim, killer, ability, fight events
    """

    def test_hero_death_events_exist(self, combat_log):
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "hero" in e.target_name.lower()]
        # Match has multiple hero deaths
        assert len(deaths) > 20

    def test_death_has_victim_and_killer(self, combat_log):
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "hero" in e.target_name.lower()
                  and e.game_time > 60]

        first = deaths[0]
        assert first.target_name == FIRST_KILL["victim"]
        assert first.attacker_name == FIRST_KILL["killer"]
        assert first.game_time == FIRST_KILL["game_time"]

    def test_damage_events_for_fight_reconstruction(self, combat_log):
        damage = [e for e in combat_log.entries if e.type == CombatLogType.DAMAGE.value]
        assert len(damage) > 30000  # Match has extensive combat

        # Damage events have required fields
        sample = damage[100]
        assert sample.attacker_name
        assert sample.target_name
        assert sample.value >= 0
        assert sample.damage_type in [d.value for d in DamageType]

    def test_ability_cast_events(self, combat_log):
        abilities = [e for e in combat_log.entries if e.type == CombatLogType.ABILITY.value]
        assert len(abilities) > 3000

        sample = abilities[0]
        assert sample.attacker_name  # Caster
        assert sample.inflictor_name  # Ability name
        assert sample.game_time is not None

    def test_fight_window_has_clustered_events(self, combat_log):
        """Around first Roshan (19:17), there should be combat activity."""
        roshan_time = ROSHAN_KILLS[0]["game_time"]
        window_start = roshan_time - 30
        window_end = roshan_time + 10

        fight_events = [
            e for e in combat_log.entries
            if window_start <= e.game_time <= window_end
            and e.type in [CombatLogType.DAMAGE.value, CombatLogType.ABILITY.value]
        ]
        assert len(fight_events) > 50  # Active combat around Roshan


class TestCarryFarmTracking:
    """Use Case 2: Tracking Carry Farm.

    Required: get_item_purchases(), get_stats_at_minute()
    Fields: game_time, item name, last_hits, net_worth
    """

    def test_yatoro_phase_boots_timing(self, combat_log):
        purchases = [e for e in combat_log.entries
                     if e.type == CombatLogType.PURCHASE.value
                     and e.target_name == "npc_dota_hero_troll_warlord"
                     and e.value_name == "item_phase_boots"]
        assert len(purchases) >= 1
        assert purchases[-1].game_time == YATORO_ITEMS["item_phase_boots"]

    def test_yatoro_battlefury_timing(self, combat_log):
        purchases = [e for e in combat_log.entries
                     if e.type == CombatLogType.PURCHASE.value
                     and e.target_name == "npc_dota_hero_troll_warlord"
                     and e.value_name == "item_bfury"]
        assert len(purchases) >= 1
        assert purchases[-1].game_time == YATORO_ITEMS["item_bfury"]

    def test_yatoro_sny_timing(self, combat_log):
        purchases = [e for e in combat_log.entries
                     if e.type == CombatLogType.PURCHASE.value
                     and e.target_name == "npc_dota_hero_troll_warlord"
                     and e.value_name == "item_sange_and_yasha"]
        assert len(purchases) >= 1
        assert purchases[-1].game_time == YATORO_ITEMS["item_sange_and_yasha"]

    def test_yatoro_bkb_timing(self, combat_log):
        purchases = [e for e in combat_log.entries
                     if e.type == CombatLogType.PURCHASE.value
                     and e.target_name == "npc_dota_hero_troll_warlord"
                     and e.value_name == "item_black_king_bar"]
        assert len(purchases) >= 1
        assert purchases[-1].game_time == YATORO_ITEMS["item_black_king_bar"]

    def test_gold_events_track_income(self, combat_log):
        gold = [e for e in combat_log.entries
                if e.type == CombatLogType.GOLD.value
                and e.target_name == "npc_dota_hero_troll_warlord"]
        assert len(gold) > 200  # Carry gets lots of gold

        # Verify gold values are positive
        total_gold = sum(e.value for e in gold)
        assert total_gold > 20000  # Carry farms a lot

    def test_xp_events_track_levels(self, combat_log):
        xp = [e for e in combat_log.entries
              if e.type == CombatLogType.XP.value
              and e.target_name == "npc_dota_hero_troll_warlord"]
        assert len(xp) > 100


class TestGankAnalysis:
    """Use Case 3: Understanding a Gank.

    Required: get_hero_deaths() with position, get_fight_combat_log()
    Fields: game_time, position (x, y), killer, ability sequence
    """

    def test_first_kill_victim_and_killer(self, combat_log):
        """First real kill: Pugna kills Hoodwink at 03:07."""
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "hero" in e.target_name.lower()
                  and e.game_time > 60]

        first = deaths[0]
        assert first.target_name == "npc_dota_hero_hoodwink"
        assert first.attacker_name == "npc_dota_hero_pugna"

    def test_first_kill_timing(self, combat_log):
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and e.target_name == "npc_dota_hero_hoodwink"
                  and e.game_time > 60]

        first = deaths[0]
        assert first.game_time == FIRST_KILL["game_time"]

    def test_damage_sequence_before_kill(self, combat_log):
        """Damage events leading to first kill."""
        kill_time = FIRST_KILL["game_time"]
        victim = FIRST_KILL["victim"]

        damage = [e for e in combat_log.entries
                  if e.type == CombatLogType.DAMAGE.value
                  and e.target_name == victim
                  and kill_time - 5 <= e.game_time <= kill_time]

        assert len(damage) >= 3  # Multiple damage instances
        # Pugna nether ward was involved
        attackers = {e.attacker_name for e in damage}
        assert any("pugna" in a.lower() for a in attackers)

    def test_death_has_location_fields(self, combat_log):
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "hero" in e.target_name.lower()]

        for death in deaths[:10]:
            assert hasattr(death, "location_x")
            assert hasattr(death, "location_y")

    def test_assist_tracking(self, combat_log):
        deaths = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "hero" in e.target_name.lower()]

        # Some kills have assists
        with_assists = [d for d in deaths if d.assist_players or d.assist_player0 > 0]
        assert len(with_assists) > 0


class TestObjectiveControl:
    """Use Case 4: Objective Control Analysis.

    Required: get_objective_kills()
    Fields: roshan_kills, tower_kills with game_time, killer, team
    """

    def test_first_roshan_kill(self, combat_log):
        """First Roshan at 19:17 by Troll Warlord (Radiant)."""
        roshan = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "roshan" in e.target_name.lower()]

        assert len(roshan) >= 2  # Two Roshan kills in this match

        first = roshan[0]
        assert first.attacker_name == ROSHAN_KILLS[0]["killer"]
        assert first.attacker_team == ROSHAN_KILLS[0]["team"].value
        assert first.game_time == ROSHAN_KILLS[0]["game_time"]

    def test_second_roshan_kill(self, combat_log):
        """Second Roshan at 28:57 by Troll Warlord (Radiant)."""
        roshan = [e for e in combat_log.entries
                  if e.type == CombatLogType.DEATH.value
                  and "roshan" in e.target_name.lower()]

        second = roshan[1]
        assert second.attacker_name == ROSHAN_KILLS[1]["killer"]
        assert second.attacker_team == ROSHAN_KILLS[1]["team"].value
        assert second.game_time == ROSHAN_KILLS[1]["game_time"]

    def test_first_tower_kill(self, combat_log):
        """First tower: Dire bot T1 at 11:15."""
        towers = [e for e in combat_log.entries
                  if e.type == CombatLogType.TEAM_BUILDING_KILL.value
                  and "tower" in e.target_name.lower()]

        assert len(towers) >= 3

        first = towers[0]
        assert TOWER_KILLS[0]["target"] in first.target_name
        assert first.target_team == Team.DIRE.value
        assert first.game_time == TOWER_KILLS[0]["game_time"]

    def test_tower_kill_sequence(self, combat_log):
        """Verify tower kill order matches expected."""
        towers = [e for e in combat_log.entries
                  if e.type == CombatLogType.TEAM_BUILDING_KILL.value
                  and "tower" in e.target_name.lower()]

        # First 3 towers in order
        assert "badguys_tower1_bot" in towers[0].target_name  # Dire bot T1
        assert "badguys_tower1_top" in towers[1].target_name  # Dire top T1
        assert "goodguys_tower1_bot" in towers[2].target_name  # Radiant bot T1


class TestLaningPhaseComparison:
    """Use Case 5: Comparing Laning Phase.

    Required: get_stats_at_minute()
    Fields: last_hits, denies, net_worth, level at specific minutes
    """

    def test_snapshot_at_10_minutes(self, parser):
        """Hero stats at 10 minutes."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        assert snapshot.success
        assert len(snapshot.heroes) == 10

    def test_troll_warlord_level_at_10min(self, parser):
        """Yatoro (Troll Warlord) should be level 6 at 10 min."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        troll = next((h for h in snapshot.heroes if "troll_warlord" in h.hero_name), None)
        assert troll is not None
        assert troll.level == 6
        assert troll.team == Team.RADIANT.value

    def test_bristleback_level_at_10min(self, parser):
        """Collapse (Bristleback) should be level 8 at 10 min."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        bb = next((h for h in snapshot.heroes if "bristleback" in h.hero_name), None)
        assert bb is not None
        assert bb.level == 8

    def test_hero_health_at_10min(self, parser):
        """Heroes have valid health values at 10 min snapshot."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        for hero in snapshot.heroes:
            assert hero.max_health > 0
            assert 0 <= hero.health <= hero.max_health

    def test_team_distribution_at_snapshot(self, parser):
        """5 Radiant and 5 Dire heroes at snapshot."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        radiant = [h for h in snapshot.heroes if h.team == Team.RADIANT.value]
        dire = [h for h in snapshot.heroes if h.team == Team.DIRE.value]

        assert len(radiant) == 5
        assert len(dire) == 5

    def test_hero_positions_valid(self, parser):
        """Hero positions within map bounds."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_10min)

        for hero in snapshot.heroes:
            assert -10000 < hero.x < 10000
            assert -10000 < hero.y < 10000


class TestHeroSnapshotEconomy:
    """Test HeroSnapshot economy fields (gold, net_worth, last_hits, etc.)."""

    def test_hero_has_economy_fields(self, parser):
        """All heroes should have economy fields populated."""
        index = parser.build_index(interval_ticks=1800)
        tick_15min = index.game_started + (15 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_15min)

        assert snapshot.success
        for hero in snapshot.heroes:
            # Economy fields should be populated (may be 0 for some)
            assert hasattr(hero, "gold")
            assert hasattr(hero, "net_worth")
            assert hasattr(hero, "last_hits")
            assert hasattr(hero, "denies")
            assert hasattr(hero, "xp")

    def test_troll_warlord_farm_at_15min(self, parser):
        """Yatoro (Troll Warlord) farming stats at 15 min."""
        index = parser.build_index(interval_ticks=1800)
        tick_15min = index.game_started + (15 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_15min)

        troll = next((h for h in snapshot.heroes if "troll_warlord" in h.hero_name), None)
        assert troll is not None

        # Carry should have significant farm by 15 min
        assert troll.last_hits > 80
        assert troll.net_worth > 5000
        assert troll.xp > 0

    def test_kda_property(self, parser):
        """Test KDA property returns correct format."""
        index = parser.build_index(interval_ticks=1800)
        tick_20min = index.game_started + (20 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_20min)

        for hero in snapshot.heroes:
            # KDA should be "kills/deaths/assists" format
            assert "/" in hero.kda
            parts = hero.kda.split("/")
            assert len(parts) == 3
            assert all(p.isdigit() for p in parts)

    def test_hero_kda_fields(self, parser):
        """Test kills/deaths/assists are populated."""
        index = parser.build_index(interval_ticks=1800)
        tick_20min = index.game_started + (20 * 60 * 30)
        snapshot = parser.snapshot(target_tick=tick_20min)

        total_kills = sum(h.kills for h in snapshot.heroes)
        total_deaths = sum(h.deaths for h in snapshot.heroes)

        # By 20 min there should be some kills
        assert total_kills > 0
        # Kills and deaths should roughly match (assists don't count)
        assert total_deaths > 0

    def test_team_net_worth_comparison(self, parser):
        """Compare team net worth at different intervals."""
        index = parser.build_index(interval_ticks=1800)
        tick_10min = index.game_started + (10 * 60 * 30)
        tick_20min = index.game_started + (20 * 60 * 30)

        snap_10 = parser.snapshot(target_tick=tick_10min)
        snap_20 = parser.snapshot(target_tick=tick_20min)

        # Net worth at 20 min should be higher than 10 min
        nw_10 = sum(h.net_worth for h in snap_10.heroes)
        nw_20 = sum(h.net_worth for h in snap_20.heroes)
        assert nw_20 > nw_10


class TestSnapshotWithIllusions:
    """Test snapshot API with illusions/clones (Monkey King in this match)."""

    def test_snapshot_includes_monkey_king_clones(self, parser):
        """Match has Monkey King - snapshot should include clones."""
        snapshot = parser.snapshot(target_tick=50000, include_illusions=True)

        assert snapshot.success
        # With illusions, should have more than 10 heroes
        assert len(snapshot.heroes) > 10

        real = [h for h in snapshot.heroes if not h.is_clone and not h.is_illusion]
        clones = [h for h in snapshot.heroes if h.is_clone]

        assert len(real) == 10
        assert len(clones) > 0  # MK clones


class TestDraftAnalysis:
    """Validate draft picks/bans for analysis."""

    def test_draft_has_24_events(self, game_info):
        """CM draft: 10 picks + 14 bans = 24 events."""
        assert len(game_info.picks_bans) == 24

    def test_radiant_picks(self, game_info):
        """Radiant picked: Bristleback, Hoodwink, Chen, Monkey King, Troll Warlord."""
        picks = [e.hero_id for e in game_info.picks_bans if e.is_pick and e.team == Team.RADIANT.value]
        assert picks == [
            Hero.BRISTLEBACK.value,
            Hero.HOODWINK.value,
            Hero.CHEN.value,
            Hero.MONKEY_KING.value,
            Hero.TROLL_WARLORD.value,
        ]

    def test_dire_picks(self, game_info):
        """Dire picked: Lycan, Pugna, Shadow Shaman, Storm Spirit, Faceless Void."""
        picks = [e.hero_id for e in game_info.picks_bans if e.is_pick and e.team == Team.DIRE.value]
        assert picks == [
            Hero.LYCAN.value,
            Hero.PUGNA.value,
            Hero.SHADOW_SHAMAN.value,
            Hero.STORM_SPIRIT.value,
            Hero.FACELESS_VOID.value,
        ]
