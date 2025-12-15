"""
Test models with REAL VALUES from actual demo file.
Golden Master approach: Test against verified expected values.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

# Module-level marker: fast tests (~10s)
pytestmark = pytest.mark.fast
from python_manta import (
    ParseResult,
    HeaderInfo,
    DraftEvent,
    PlayerInfo,
    GameInfo,
    MessageEvent,
    MessagesResult,
    ChatWheelMessage,
    GameActivity,
    Hero,
)


class TestHeaderInfoRealValues:
    """Test HeaderInfo contains EXACT values from real demo file."""

    def test_header_exact_values(self, header_result):
        """Test header parsing produces exact expected values from real file."""
        result = header_result

        # EXACT values from the real demo file (verified manually)
        assert result.success is True
        assert result.header.map_name == "start"
        assert result.header.server_name == "Valve TI14 Server (srcds227-fra2.Hamburg.4)"
        assert result.header.client_name == "SourceTV Demo"
        assert result.header.game_directory == "/opt/srcds/dota/dota_v6536/dota"
        assert result.header.network_protocol == 48
        assert result.header.demo_file_stamp == "PBDEMS2\x00"
        assert result.header.build_num == 10512
        assert result.header.game == ""  # This specific demo file has empty game field
        assert result.header.server_start_tick == 381
        assert result.header.error is None

    def test_header_serialization_roundtrip(self, header_result):
        """Test HeaderInfo JSON serialization preserves exact values."""
        original = header_result.header

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = HeaderInfo.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert restored.map_name == "start"
        assert restored.build_num == 10512


class TestDraftEventRealValues:
    """Test DraftEvent with EXACT values from real draft."""

    def test_draft_exact_structure(self, game_info_result):
        """Test draft contains exact pick/ban structure from real game."""
        result = game_info_result
        game_info = result.game_info

        # EXACT values from real demo file
        assert result.success is True
        assert len(game_info.picks_bans) == 24  # Exact number of events
        assert result.error is None

        # Test first 5 events exact sequence using Hero enum
        first_5_events = [(e.is_pick, e.team, e.hero_id) for e in game_info.picks_bans[:5]]
        expected_first_5 = [
            (False, 3, Hero.NATURES_PROPHET.value),  # Dire ban
            (False, 2, Hero.INVOKER.value),          # Radiant ban
            (False, 2, Hero.BEASTMASTER.value),      # Radiant ban
            (False, 3, Hero.SHADOW_FIEND.value),     # Dire ban
            (False, 2, Hero.NAGA_SIREN.value),       # Radiant ban
        ]
        assert first_5_events == expected_first_5

    def test_picks_exact_values(self, game_info_result):
        """Test picks contain exact hero IDs from real game."""
        game_info = game_info_result.game_info

        picks = [e for e in game_info.picks_bans if e.is_pick]
        assert len(picks) == 10  # Standard 5v5 picks

        # Exact pick sequences by team using Hero enum
        radiant_picks = [e.hero_id for e in picks if e.team == 2]
        dire_picks = [e.hero_id for e in picks if e.team == 3]

        # Radiant: Bristleback, Hoodwink, Chen, Monkey King, Troll Warlord
        assert radiant_picks == [
            Hero.BRISTLEBACK.value,
            Hero.HOODWINK.value,
            Hero.CHEN.value,
            Hero.MONKEY_KING.value,
            Hero.TROLL_WARLORD.value,
        ]
        # Dire: Lycan, Pugna, Shadow Shaman, Storm Spirit, Faceless Void
        assert dire_picks == [
            Hero.LYCAN.value,
            Hero.PUGNA.value,
            Hero.SHADOW_SHAMAN.value,
            Hero.STORM_SPIRIT.value,
            Hero.FACELESS_VOID.value,
        ]

    def test_bans_exact_values(self, game_info_result):
        """Test bans contain exact hero IDs from real game."""
        game_info = game_info_result.game_info

        bans = [e for e in game_info.picks_bans if not e.is_pick]
        assert len(bans) == 14  # Exact number of bans in this game

        # Exact ban sequences by team using Hero enum
        radiant_bans = [e.hero_id for e in bans if e.team == 2]
        dire_bans = [e.hero_id for e in bans if e.team == 3]

        # Radiant bans: Invoker, Beastmaster, Naga Siren, Marci, Abaddon, Ursa, Juggernaut
        assert radiant_bans == [
            Hero.INVOKER.value,
            Hero.BEASTMASTER.value,
            Hero.NAGA_SIREN.value,
            Hero.MARCI.value,
            Hero.ABADDON.value,
            Hero.URSA.value,
            Hero.JUGGERNAUT.value,
        ]
        # Dire bans: Nature's Prophet, Shadow Fiend, Earthshaker, Sand King, Phoenix, Puck, Anti-Mage
        assert dire_bans == [
            Hero.NATURES_PROPHET.value,
            Hero.SHADOW_FIEND.value,
            Hero.EARTHSHAKER.value,
            Hero.SAND_KING.value,
            Hero.PHOENIX.value,
            Hero.PUCK.value,
            Hero.ANTI_MAGE.value,
        ]


class TestGameInfoRealValues:
    """Test GameInfo with EXACT values from real demo file."""

    def test_game_info_exact_structure(self, game_info_result):
        """Test game info contains exact structure from real file."""
        result = game_info_result

        assert result.success is True
        assert len(result.game_info.picks_bans) == 24
        assert result.error is None

        # Test team distribution is correct
        team_2_events = [e for e in result.game_info.picks_bans if e.team == 2]  # Radiant
        team_3_events = [e for e in result.game_info.picks_bans if e.team == 3]  # Dire

        assert len(team_2_events) == 12  # Radiant events (5 picks + 7 bans)
        assert len(team_3_events) == 12  # Dire events (5 picks + 7 bans)

    def test_game_info_serialization_roundtrip(self, game_info_result):
        """Test GameInfo JSON serialization preserves exact values."""
        original = game_info_result.game_info

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = GameInfo.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert len(restored.picks_bans) == 24


class TestMessageEventRealValues:
    """Test MessageEvent with EXACT values from real demo file."""

    def test_messages_exact_values(self, messages_result):
        """Test messages parsing produces exact message sequence."""
        result = messages_result

        assert result.success is True
        assert len(result.messages.messages) >= 10
        assert result.error is None

        # Test exact message types from real file (specific Manta callback names)
        message_types = [msg.type for msg in result.messages.messages[:10]]
        expected_types = [
            'CDemoFileHeader',
            'CNETMsg_Tick',
            'CSVCMsg_ClearAllStringTables',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
            'CSVCMsg_CreateStringTable',
        ]
        assert message_types == expected_types

    def test_first_message_exact_values(self, messages_result):
        """Test first message contains exact expected values."""
        first_message = messages_result.messages.messages[0]
        assert first_message.type == "CDemoFileHeader"
        assert first_message.tick == 0
        assert first_message.net_tick == 0
        assert first_message.data is not None

    def test_tick_progression_exact_sequence(self, messages_result):
        """Test tick progression follows exact sequence from real file."""
        ticks = [msg.tick for msg in messages_result.messages.messages[:10]]
        # First 10 messages are all at tick 0 (header and string table setup)
        expected_ticks = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert ticks == expected_ticks

        # Ticks must be in non-decreasing order
        assert ticks == sorted(ticks)


class TestMessagesResultRealValues:
    """Test MessagesResult with EXACT values from real demo file."""

    def test_messages_result_exact_structure(self, messages_result):
        """Test messages result contains exact structure from real file."""
        result = messages_result

        assert result.success is True
        assert len(result.messages.messages) >= 5
        assert result.error is None

    def test_messages_result_serialization_roundtrip(self, messages_result):
        """Test MessagesResult JSON serialization preserves exact values."""
        original = messages_result.messages

        # Create subset for testing serialization
        json_str = original.model_dump_json()
        restored = MessagesResult.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert len(restored.messages) >= 3
        assert restored.messages[0].type == "CDemoFileHeader"

    def test_filtered_messages_exact_results(self, parser):
        """Test message filtering produces exact expected results."""
        # This test needs a specific filter config, so it uses parser fixture
        result = parser.parse(messages={"filter": "CDemoFileHeader", "max_messages": 5})

        assert result.success is True
        assert len(result.messages.messages) >= 1

        # All messages must match the filter
        for message in result.messages.messages:
            assert "CDemoFileHeader" in message.type

        # First message should be the file header
        assert result.messages.messages[0].type == "CDemoFileHeader"
        assert result.messages.messages[0].tick == 0


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


class TestAbilitySnapshotModel:
    """Test AbilitySnapshot model properties."""

    def test_ability_snapshot_defaults(self):
        """Test AbilitySnapshot has correct default values."""
        from python_manta import AbilitySnapshot

        ability = AbilitySnapshot()
        assert ability.slot == 0
        assert ability.name == ""
        assert ability.level == 0
        assert ability.cooldown == 0.0
        assert ability.max_cooldown == 0.0
        assert ability.mana_cost == 0
        assert ability.charges == 0
        assert ability.is_ultimate is False

    def test_ability_snapshot_short_name_property(self):
        """Test short_name strips CDOTA_Ability_ prefix."""
        from python_manta import AbilitySnapshot

        ability = AbilitySnapshot(name="CDOTA_Ability_Juggernaut_BladeFury")
        assert ability.short_name == "Juggernaut_BladeFury"

        # Empty name case
        empty = AbilitySnapshot(name="")
        assert empty.short_name == ""

        # Name without prefix
        no_prefix = AbilitySnapshot(name="SomeOtherAbility")
        assert no_prefix.short_name == "SomeOtherAbility"

    def test_ability_snapshot_is_maxed_regular(self):
        """Test is_maxed for regular abilities (max level 4)."""
        from python_manta import AbilitySnapshot

        # Not maxed
        ability = AbilitySnapshot(level=3, is_ultimate=False)
        assert ability.is_maxed is False

        # Maxed
        maxed = AbilitySnapshot(level=4, is_ultimate=False)
        assert maxed.is_maxed is True

        # Over max (still maxed)
        over = AbilitySnapshot(level=5, is_ultimate=False)
        assert over.is_maxed is True

    def test_ability_snapshot_is_maxed_ultimate(self):
        """Test is_maxed for ultimate abilities (max level 3)."""
        from python_manta import AbilitySnapshot

        # Not maxed
        ult = AbilitySnapshot(level=2, is_ultimate=True)
        assert ult.is_maxed is False

        # Maxed
        maxed_ult = AbilitySnapshot(level=3, is_ultimate=True)
        assert maxed_ult.is_maxed is True

    def test_ability_snapshot_is_on_cooldown(self):
        """Test is_on_cooldown property."""
        from python_manta import AbilitySnapshot

        # Not on cooldown
        ready = AbilitySnapshot(cooldown=0.0)
        assert ready.is_on_cooldown is False

        # On cooldown
        on_cd = AbilitySnapshot(cooldown=5.5)
        assert on_cd.is_on_cooldown is True

    def test_ability_snapshot_serialization(self):
        """Test AbilitySnapshot serializes and deserializes correctly."""
        from python_manta import AbilitySnapshot

        ability = AbilitySnapshot(
            slot=2,
            name="CDOTA_Ability_Juggernaut_BladeDance",
            level=4,
            cooldown=0.0,
            max_cooldown=0.0,
            mana_cost=0,
            charges=0,
            is_ultimate=False,
        )

        # Serialize
        json_str = ability.model_dump_json()

        # Deserialize
        restored = AbilitySnapshot.model_validate_json(json_str)
        assert restored == ability
        assert restored.short_name == "Juggernaut_BladeDance"


class TestTalentChoiceModel:
    """Test TalentChoice model properties."""

    def test_talent_choice_defaults(self):
        """Test TalentChoice has correct default values."""
        from python_manta import TalentChoice

        talent = TalentChoice()
        assert talent.tier == 0
        assert talent.slot == 0
        assert talent.is_left is True
        assert talent.name == ""

    def test_talent_choice_side_property_left(self):
        """Test side property returns 'left' when is_left is True."""
        from python_manta import TalentChoice

        talent = TalentChoice(tier=10, is_left=True)
        assert talent.side == "left"

    def test_talent_choice_side_property_right(self):
        """Test side property returns 'right' when is_left is False."""
        from python_manta import TalentChoice

        talent = TalentChoice(tier=15, is_left=False)
        assert talent.side == "right"

    def test_talent_choice_valid_tiers(self):
        """Test TalentChoice accepts valid tier values."""
        from python_manta import TalentChoice

        for tier in [10, 15, 20, 25]:
            talent = TalentChoice(tier=tier)
            assert talent.tier == tier

    def test_talent_choice_serialization(self):
        """Test TalentChoice serializes and deserializes correctly."""
        from python_manta import TalentChoice

        talent = TalentChoice(
            tier=20,
            slot=10,
            is_left=False,
            name="CDOTA_Ability_Special_Bonus_Base",
        )

        # Serialize
        json_str = talent.model_dump_json()

        # Deserialize
        restored = TalentChoice.model_validate_json(json_str)
        assert restored == talent
        assert restored.side == "right"


class TestHeroSnapshotAbilityMethods:
    """Test HeroSnapshot ability-related methods."""

    def test_hero_snapshot_has_ultimate_false(self):
        """Test has_ultimate is False when no ultimate is learned."""
        from python_manta import HeroSnapshot, AbilitySnapshot

        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, level=1, is_ultimate=False),
                AbilitySnapshot(slot=5, level=0, is_ultimate=True),  # Unlearned ult
            ]
        )
        assert hero.has_ultimate is False

    def test_hero_snapshot_has_ultimate_true(self):
        """Test has_ultimate is True when ultimate is learned."""
        from python_manta import HeroSnapshot, AbilitySnapshot

        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, level=1, is_ultimate=False),
                AbilitySnapshot(slot=5, level=1, is_ultimate=True),  # Learned ult
            ]
        )
        assert hero.has_ultimate is True

    def test_hero_snapshot_talents_chosen(self):
        """Test talents_chosen returns correct count."""
        from python_manta import HeroSnapshot, TalentChoice

        # No talents
        hero_no_talents = HeroSnapshot(talents=[])
        assert hero_no_talents.talents_chosen == 0

        # Some talents
        hero_with_talents = HeroSnapshot(
            talents=[
                TalentChoice(tier=10, is_left=True),
                TalentChoice(tier=15, is_left=False),
            ]
        )
        assert hero_with_talents.talents_chosen == 2

    def test_hero_snapshot_get_ability_found(self):
        """Test get_ability finds ability by partial name match."""
        from python_manta import HeroSnapshot, AbilitySnapshot

        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, name="CDOTA_Ability_Juggernaut_BladeFury", level=4),
                AbilitySnapshot(slot=1, name="CDOTA_Ability_Juggernaut_HealingWard", level=2),
            ]
        )

        # Exact partial match
        found = hero.get_ability("BladeFury")
        assert found is not None
        assert found.level == 4

        # Case-insensitive match
        found_case = hero.get_ability("bladefury")
        assert found_case is not None

    def test_hero_snapshot_get_ability_not_found(self):
        """Test get_ability returns None when not found."""
        from python_manta import HeroSnapshot, AbilitySnapshot

        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, name="CDOTA_Ability_Juggernaut_BladeFury", level=4),
            ]
        )

        not_found = hero.get_ability("Omnislash")
        assert not_found is None

    def test_hero_snapshot_get_talent_at_tier_found(self):
        """Test get_talent_at_tier finds talent at specified tier."""
        from python_manta import HeroSnapshot, TalentChoice

        hero = HeroSnapshot(
            talents=[
                TalentChoice(tier=10, is_left=True, name="talent_10"),
                TalentChoice(tier=20, is_left=False, name="talent_20"),
            ]
        )

        found = hero.get_talent_at_tier(10)
        assert found is not None
        assert found.tier == 10
        assert found.is_left is True

        found_20 = hero.get_talent_at_tier(20)
        assert found_20 is not None
        assert found_20.tier == 20

    def test_hero_snapshot_get_talent_at_tier_not_found(self):
        """Test get_talent_at_tier returns None when not found."""
        from python_manta import HeroSnapshot, TalentChoice

        hero = HeroSnapshot(
            talents=[
                TalentChoice(tier=10, is_left=True),
            ]
        )

        not_found = hero.get_talent_at_tier(15)
        assert not_found is None


class TestNeutralCampTypeEnum:
    """Test NeutralCampType enum with real values from replays."""

    def test_camp_type_values(self):
        """Test camp type enum has correct integer values."""
        from python_manta import NeutralCampType

        assert NeutralCampType.SMALL.value == 0
        assert NeutralCampType.MEDIUM.value == 1
        assert NeutralCampType.HARD.value == 2
        assert NeutralCampType.ANCIENT.value == 3

    def test_display_name_exact_values(self):
        """Test display names are exact expected text."""
        from python_manta import NeutralCampType

        assert NeutralCampType.SMALL.display_name == "Small Camp"
        assert NeutralCampType.MEDIUM.display_name == "Medium Camp"
        assert NeutralCampType.HARD.display_name == "Hard Camp"
        assert NeutralCampType.ANCIENT.display_name == "Ancient Camp"

    def test_is_ancient_property(self):
        """Test is_ancient correctly identifies ancient camps."""
        from python_manta import NeutralCampType

        assert NeutralCampType.ANCIENT.is_ancient is True
        assert NeutralCampType.HARD.is_ancient is False
        assert NeutralCampType.MEDIUM.is_ancient is False
        assert NeutralCampType.SMALL.is_ancient is False

    def test_from_value_returns_enum(self):
        """Test from_value returns correct enum for known values."""
        from python_manta import NeutralCampType

        assert NeutralCampType.from_value(0) == NeutralCampType.SMALL
        assert NeutralCampType.from_value(1) == NeutralCampType.MEDIUM
        assert NeutralCampType.from_value(2) == NeutralCampType.HARD
        assert NeutralCampType.from_value(3) == NeutralCampType.ANCIENT

    def test_from_value_returns_small_for_unknown(self):
        """Test from_value returns SMALL for unmapped values (as fallback)."""
        from python_manta import NeutralCampType

        assert NeutralCampType.from_value(99) == NeutralCampType.SMALL
        assert NeutralCampType.from_value(-1) == NeutralCampType.SMALL


class TestNeutralCampTypeIntegration:
    """Integration tests for NeutralCampType with real demo data.

    Uses combat_log_result_secondary fixture from conftest.py for cached parsing.
    """

    def test_neutral_deaths_have_camp_type(self, combat_log_result_secondary):
        """Test neutral creep deaths have valid camp_type values."""
        from python_manta import NeutralCampType

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
        from python_manta import NeutralCampType

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
        from python_manta import NeutralCampType

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
        from python_manta import NeutralCampType

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
        from python_manta import Team

        result = combat_log_result_secondary
        neutral_deaths = [
            e for e in result.combat_log.entries
            if e.type_name == "DOTA_COMBATLOG_DEATH"
            and "npc_dota_neutral" in e.target_name
            and e.neutral_camp_type > 0
        ]

        camp_teams = set(e.neutral_camp_team for e in neutral_deaths)
        assert camp_teams.issubset({Team.RADIANT.value, Team.DIRE.value})
