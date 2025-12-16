"""
Test model classes with REAL VALUES from actual demo file.
Golden Master approach: Test against verified expected values.
Uses v2 Parser API exclusively.

Note: Fixtures from conftest.py provide cached parsed results to avoid
redundant parsing and improve test performance significantly.
"""

import pytest

pytestmark = pytest.mark.fast
from python_manta import (
    ParseResult,
    HeaderInfo,
    DraftEvent,
    PlayerInfo,
    GameInfo,
    MessageEvent,
    MessagesResult,
    Hero,
    AbilitySnapshot,
    TalentChoice,
    HeroSnapshot,
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


class TestAbilitySnapshotModel:
    """Test AbilitySnapshot model properties."""

    def test_ability_snapshot_defaults(self):
        """Test AbilitySnapshot has correct default values."""
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
        # Not maxed
        ult = AbilitySnapshot(level=2, is_ultimate=True)
        assert ult.is_maxed is False

        # Maxed
        maxed_ult = AbilitySnapshot(level=3, is_ultimate=True)
        assert maxed_ult.is_maxed is True

    def test_ability_snapshot_is_on_cooldown(self):
        """Test is_on_cooldown property."""
        # Not on cooldown
        ready = AbilitySnapshot(cooldown=0.0)
        assert ready.is_on_cooldown is False

        # On cooldown
        on_cd = AbilitySnapshot(cooldown=5.5)
        assert on_cd.is_on_cooldown is True

    def test_ability_snapshot_serialization(self):
        """Test AbilitySnapshot serializes and deserializes correctly."""
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
        talent = TalentChoice()
        assert talent.tier == 0
        assert talent.slot == 0
        assert talent.is_left is True
        assert talent.name == ""

    def test_talent_choice_side_property_left(self):
        """Test side property returns 'left' when is_left is True."""
        talent = TalentChoice(tier=10, is_left=True)
        assert talent.side == "left"

    def test_talent_choice_side_property_right(self):
        """Test side property returns 'right' when is_left is False."""
        talent = TalentChoice(tier=15, is_left=False)
        assert talent.side == "right"

    def test_talent_choice_valid_tiers(self):
        """Test TalentChoice accepts valid tier values."""
        for tier in [10, 15, 20, 25]:
            talent = TalentChoice(tier=tier)
            assert talent.tier == tier

    def test_talent_choice_serialization(self):
        """Test TalentChoice serializes and deserializes correctly."""
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
        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, level=1, is_ultimate=False),
                AbilitySnapshot(slot=5, level=0, is_ultimate=True),  # Unlearned ult
            ]
        )
        assert hero.has_ultimate is False

    def test_hero_snapshot_has_ultimate_true(self):
        """Test has_ultimate is True when ultimate is learned."""
        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, level=1, is_ultimate=False),
                AbilitySnapshot(slot=5, level=1, is_ultimate=True),  # Learned ult
            ]
        )
        assert hero.has_ultimate is True

    def test_hero_snapshot_talents_chosen(self):
        """Test talents_chosen returns correct count."""
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
        hero = HeroSnapshot(
            abilities=[
                AbilitySnapshot(slot=0, name="CDOTA_Ability_Juggernaut_BladeFury", level=4),
            ]
        )

        not_found = hero.get_ability("Omnislash")
        assert not_found is None

    def test_hero_snapshot_get_talent_at_tier_found(self):
        """Test get_talent_at_tier finds talent at specified tier."""
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
        hero = HeroSnapshot(
            talents=[
                TalentChoice(tier=10, is_left=True),
            ]
        )

        not_found = hero.get_talent_at_tier(15)
        assert not_found is None


class TestNormalizeHeroName:
    """Test normalize_hero_name utility function."""

    def test_double_underscore_normalized(self):
        """Test double underscores are replaced with single."""
        from python_manta import normalize_hero_name

        assert normalize_hero_name("shadow__demon") == "shadow_demon"
        assert normalize_hero_name("npc_dota_hero_shadow__demon") == "npc_dota_hero_shadow_demon"

    def test_triple_underscore_normalized(self):
        """Test triple underscores are also normalized."""
        from python_manta import normalize_hero_name

        assert normalize_hero_name("test___name") == "test_name"

    def test_single_underscore_unchanged(self):
        """Test single underscores are not modified."""
        from python_manta import normalize_hero_name

        assert normalize_hero_name("shadow_demon") == "shadow_demon"
        assert normalize_hero_name("npc_dota_hero_troll_warlord") == "npc_dota_hero_troll_warlord"

    def test_no_underscore_unchanged(self):
        """Test names without underscores are not modified."""
        from python_manta import normalize_hero_name

        assert normalize_hero_name("axe") == "axe"
        assert normalize_hero_name("juggernaut") == "juggernaut"

    def test_empty_string(self):
        """Test empty string returns empty string."""
        from python_manta import normalize_hero_name

        assert normalize_hero_name("") == ""


class TestTimeUtilities:
    """Test time utility functions."""

    def test_format_game_time_positive(self):
        """Test format_game_time with positive values."""
        from python_manta import format_game_time

        assert format_game_time(0) == "0:00"
        assert format_game_time(30) == "0:30"
        assert format_game_time(60) == "1:00"
        assert format_game_time(187) == "3:07"
        assert format_game_time(3600) == "60:00"

    def test_format_game_time_negative(self):
        """Test format_game_time with negative values (pre-horn)."""
        from python_manta import format_game_time

        assert format_game_time(-40) == "-0:40"
        assert format_game_time(-90) == "-1:30"

    def test_game_time_to_tick(self):
        """Test game_time_to_tick conversion."""
        from python_manta import game_time_to_tick, TICKS_PER_SECOND

        game_start_tick = 27000
        # 300 seconds = 5:00 = 9000 ticks after game start
        assert game_time_to_tick(300, game_start_tick) == 27000 + 300 * int(TICKS_PER_SECOND)
        # 0 seconds = game start
        assert game_time_to_tick(0, game_start_tick) == 27000
        # Negative = pre-horn
        assert game_time_to_tick(-30, game_start_tick) == 27000 - 30 * int(TICKS_PER_SECOND)

    def test_tick_to_game_time(self):
        """Test tick_to_game_time conversion."""
        from python_manta import tick_to_game_time, TICKS_PER_SECOND

        game_start_tick = 27000
        # At game start tick, game_time = 0
        assert tick_to_game_time(27000, game_start_tick) == 0.0
        # 9000 ticks after = 300 seconds
        assert tick_to_game_time(36000, game_start_tick) == 300.0
        # Before game start = negative
        assert tick_to_game_time(26100, game_start_tick) == -30.0
