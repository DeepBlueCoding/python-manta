"""
Test enum classes with REAL VALUES.
Tests ChatWheelMessage, GameActivity, NeutralCampType, and other enums.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.unit
from python_manta import (
    ChatWheelMessage,
    GameActivity,
    NeutralCampType,
    Team,
)


class TestChatWheelMessageEnum:
    """Test ChatWheelMessage enum with real values."""

    def test_standard_message_values(self):
        """Test standard chat wheel message IDs map correctly."""
        assert ChatWheelMessage.HELP.value == 5
        assert ChatWheelMessage.MY_BAD.value == 68
        assert ChatWheelMessage.SPACE_CREATED.value == 71
        assert ChatWheelMessage.BRUTAL_SAVAGE_REKT.value == 230

    def test_display_name_exact_values(self):
        """Test display names are exact expected text."""
        assert ChatWheelMessage.HELP.display_name == "Help!"
        assert ChatWheelMessage.MY_BAD.display_name == "My bad"
        assert ChatWheelMessage.SPACE_CREATED.display_name == "> Space created"
        assert ChatWheelMessage.WELL_PLAYED.display_name == "Well played!"

    def test_from_id_returns_enum(self):
        """Test from_id returns correct enum for known IDs."""
        assert ChatWheelMessage.from_id(5) == ChatWheelMessage.HELP
        assert ChatWheelMessage.from_id(71) == ChatWheelMessage.SPACE_CREATED
        assert ChatWheelMessage.from_id(68) == ChatWheelMessage.MY_BAD

    def test_from_id_returns_none_for_unknown(self):
        """Test from_id returns None for unmapped IDs."""
        assert ChatWheelMessage.from_id(99999) is None
        assert ChatWheelMessage.from_id(120009) is None  # TI voice line

    def test_describe_id_known_message(self):
        """Test describe_id returns display name for known IDs."""
        assert ChatWheelMessage.describe_id(5) == "Help!"
        assert ChatWheelMessage.describe_id(71) == "> Space created"

    def test_describe_id_dota_plus_range(self):
        """Test describe_id identifies Dota Plus voice lines."""
        result = ChatWheelMessage.describe_id(11005)
        assert "Dota Plus Hero Voice Line" in result

    def test_describe_id_ti_battle_pass_range(self):
        """Test describe_id identifies TI Battle Pass voice lines."""
        result = ChatWheelMessage.describe_id(120009)
        assert "TI Battle Pass Voice Line" in result

    def test_describe_id_ti_talent_range(self):
        """Test describe_id identifies TI talent/team voice lines."""
        result = ChatWheelMessage.describe_id(401500)
        assert "TI Talent/Team Voice Line" in result


class TestGameActivityEnum:
    """Test GameActivity enum with real values."""

    def test_basic_activity_values(self):
        """Test basic activity codes have correct values."""
        assert GameActivity.IDLE.value == 1500
        assert GameActivity.RUN.value == 1502
        assert GameActivity.ATTACK.value == 1503
        assert GameActivity.DIE.value == 1506

    def test_taunt_activity_values(self):
        """Test taunt activity codes have correct values."""
        assert GameActivity.TAUNT.value == 1536
        assert GameActivity.KILLTAUNT.value == 1535
        assert GameActivity.TAUNT_SNIPER.value == 1641
        assert GameActivity.TAUNT_SPECIAL.value == 1752

    def test_ability_cast_values(self):
        """Test ability cast activity codes are sequential."""
        assert GameActivity.CAST_ABILITY_1.value == 1510
        assert GameActivity.CAST_ABILITY_2.value == 1511
        assert GameActivity.CAST_ABILITY_3.value == 1512
        assert GameActivity.CAST_ABILITY_4.value == 1513

    def test_is_taunt_property(self):
        """Test is_taunt correctly identifies taunt activities."""
        assert GameActivity.TAUNT.is_taunt is True
        assert GameActivity.KILLTAUNT.is_taunt is True
        assert GameActivity.TAUNT_SNIPER.is_taunt is True
        assert GameActivity.ATTACK.is_taunt is False
        assert GameActivity.RUN.is_taunt is False

    def test_is_attack_property(self):
        """Test is_attack correctly identifies attack activities."""
        assert GameActivity.ATTACK.is_attack is True
        assert GameActivity.ATTACK2.is_attack is True
        assert GameActivity.ATTACK_EVENT.is_attack is True
        assert GameActivity.TAUNT.is_attack is False
        assert GameActivity.RUN.is_attack is False

    def test_is_ability_cast_property(self):
        """Test is_ability_cast correctly identifies ability casts."""
        assert GameActivity.CAST_ABILITY_1.is_ability_cast is True
        assert GameActivity.CAST_ABILITY_6.is_ability_cast is True
        assert GameActivity.ATTACK.is_ability_cast is False
        assert GameActivity.TAUNT.is_ability_cast is False

    def test_is_channeling_property(self):
        """Test is_channeling correctly identifies channeling activities."""
        assert GameActivity.CHANNEL_ABILITY_1.is_channeling is True
        assert GameActivity.CHANNEL_ABILITY_5.is_channeling is True
        assert GameActivity.CAST_ABILITY_1.is_channeling is False

    def test_from_value_returns_enum(self):
        """Test from_value returns correct enum for known values."""
        assert GameActivity.from_value(1500) == GameActivity.IDLE
        assert GameActivity.from_value(1536) == GameActivity.TAUNT
        assert GameActivity.from_value(1503) == GameActivity.ATTACK

    def test_from_value_returns_none_for_unknown(self):
        """Test from_value returns None for unmapped values."""
        assert GameActivity.from_value(9999) is None
        assert GameActivity.from_value(0) is None

    def test_get_taunt_activities(self):
        """Test get_taunt_activities returns all taunt activities."""
        taunts = GameActivity.get_taunt_activities()
        assert GameActivity.TAUNT in taunts
        assert GameActivity.KILLTAUNT in taunts
        assert GameActivity.TAUNT_SNIPER in taunts
        assert GameActivity.ATTACK not in taunts
        assert len(taunts) == 5  # TAUNT, KILLTAUNT, TAUNT_SNIPER, TAUNT_SPECIAL, CUSTOM_TOWER_TAUNT

    def test_display_name_format(self):
        """Test display_name produces readable names."""
        assert GameActivity.CAST_ABILITY_1.display_name == "Cast Ability 1"
        assert GameActivity.TAUNT.display_name == "Taunt"
        assert GameActivity.RUN.display_name == "Run"


class TestNeutralCampTypeEnum:
    """Test NeutralCampType enum with real values from replays."""

    def test_camp_type_values(self):
        """Test camp type enum has correct integer values."""
        assert NeutralCampType.SMALL.value == 0
        assert NeutralCampType.MEDIUM.value == 1
        assert NeutralCampType.HARD.value == 2
        assert NeutralCampType.ANCIENT.value == 3

    def test_display_name_exact_values(self):
        """Test display names are exact expected text."""
        assert NeutralCampType.SMALL.display_name == "Small Camp"
        assert NeutralCampType.MEDIUM.display_name == "Medium Camp"
        assert NeutralCampType.HARD.display_name == "Hard Camp"
        assert NeutralCampType.ANCIENT.display_name == "Ancient Camp"

    def test_is_ancient_property(self):
        """Test is_ancient correctly identifies ancient camps."""
        assert NeutralCampType.ANCIENT.is_ancient is True
        assert NeutralCampType.HARD.is_ancient is False
        assert NeutralCampType.MEDIUM.is_ancient is False
        assert NeutralCampType.SMALL.is_ancient is False

    def test_from_value_returns_enum(self):
        """Test from_value returns correct enum for known values."""
        assert NeutralCampType.from_value(0) == NeutralCampType.SMALL
        assert NeutralCampType.from_value(1) == NeutralCampType.MEDIUM
        assert NeutralCampType.from_value(2) == NeutralCampType.HARD
        assert NeutralCampType.from_value(3) == NeutralCampType.ANCIENT

    def test_from_value_returns_small_for_unknown(self):
        """Test from_value returns SMALL for unmapped values (as fallback)."""
        assert NeutralCampType.from_value(99) == NeutralCampType.SMALL
        assert NeutralCampType.from_value(-1) == NeutralCampType.SMALL


class TestNeutralCampTypeIntegration:
    """Integration tests for NeutralCampType with real demo data.

    Uses combat_log_result_secondary fixture from conftest.py for cached parsing.
    """

    def test_neutral_deaths_have_camp_type(self, combat_log_result_secondary):
        """Test neutral creep deaths have valid camp_type values."""
        result = combat_log_result_secondary
        neutral_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and "npc_dota_neutral" in e.target_name
            and e.neutral_camp_type > 0
        ]

        assert len(neutral_deaths) > 0
        for death in neutral_deaths:
            camp_type = NeutralCampType.from_value(death.neutral_camp_type)
            assert camp_type in [NeutralCampType.MEDIUM, NeutralCampType.HARD, NeutralCampType.ANCIENT]

    def test_ancient_camp_contains_ancient_creeps(self, combat_log_result_secondary):
        """Test ANCIENT camp type (value 3) has neutral creep deaths."""
        result = combat_log_result_secondary
        ancient_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and e.neutral_camp_type == NeutralCampType.ANCIENT.value
            and "npc_dota_neutral" in e.target_name
        ]

        assert len(ancient_deaths) > 0
        for death in ancient_deaths:
            assert "npc_dota_neutral" in death.target_name

    def test_medium_camp_contains_medium_creeps(self, combat_log_result_secondary):
        """Test MEDIUM camp type contains wolves/ogres/mud golems."""
        result = combat_log_result_secondary
        medium_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and e.neutral_camp_type == NeutralCampType.MEDIUM.value
            and "npc_dota_neutral" in e.target_name
        ]

        assert len(medium_deaths) > 0
        creep_names = set(e.target_name.replace("npc_dota_neutral_", "") for e in medium_deaths)
        medium_creep_keywords = ["wolf", "ogre", "mud_golem", "satyr", "frog"]
        found_medium = any(any(k in n for k in medium_creep_keywords) for n in creep_names)
        assert found_medium, f"Expected medium creeps, got: {creep_names}"

    def test_hard_camp_contains_hard_creeps(self, combat_log_result_secondary):
        """Test HARD camp type contains hellbears/trolls/centaurs."""
        result = combat_log_result_secondary
        hard_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and e.neutral_camp_type == NeutralCampType.HARD.value
            and "npc_dota_neutral" in e.target_name
        ]

        assert len(hard_deaths) > 0
        creep_names = set(e.target_name.replace("npc_dota_neutral_", "") for e in hard_deaths)
        hard_creep_keywords = ["furbolg", "dark_troll", "centaur", "wildkin", "satyr_hellcaller", "warpine"]
        found_hard = any(any(k in n for k in hard_creep_keywords) for n in creep_names)
        assert found_hard, f"Expected hard creeps, got: {creep_names}"

    def test_neutral_camp_team_matches_team_enum(self, combat_log_result_secondary):
        """Test neutral_camp_team uses Team enum values (2=Radiant, 3=Dire)."""
        result = combat_log_result_secondary
        neutral_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and "npc_dota_neutral" in e.target_name
            and e.neutral_camp_type > 0
        ]

        camp_teams = set(e.neutral_camp_team for e in neutral_deaths)
        assert camp_teams.issubset({Team.RADIANT.value, Team.DIRE.value})
