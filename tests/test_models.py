"""
Test models with REAL VALUES from actual demo file.
Golden Master approach: Test against verified expected values.
Uses v2 Parser API exclusively.
"""

import pytest

# Module-level marker: fast tests (~10s)
pytestmark = pytest.mark.fast
from python_manta import (
    Parser,
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

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


class TestHeaderInfoRealValues:
    """Test HeaderInfo contains EXACT values from real demo file."""

    def test_header_exact_values(self):
        """Test header parsing produces exact expected values from real file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)

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

    def test_header_serialization_roundtrip(self):
        """Test HeaderInfo JSON serialization preserves exact values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(header=True)
        original = result.header

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = HeaderInfo.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert restored.map_name == "start"
        assert restored.build_num == 10512


class TestDraftEventRealValues:
    """Test DraftEvent with EXACT values from real draft."""

    def test_draft_exact_structure(self):
        """Test draft contains exact pick/ban structure from real game."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
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

    def test_picks_exact_values(self):
        """Test picks contain exact hero IDs from real game."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        game_info = result.game_info

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

    def test_bans_exact_values(self):
        """Test bans contain exact hero IDs from real game."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        game_info = result.game_info

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

    def test_game_info_exact_structure(self):
        """Test game info contains exact structure from real file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)

        assert result.success is True
        assert len(result.game_info.picks_bans) == 24
        assert result.error is None

        # Test team distribution is correct
        team_2_events = [e for e in result.game_info.picks_bans if e.team == 2]  # Radiant
        team_3_events = [e for e in result.game_info.picks_bans if e.team == 3]  # Dire

        assert len(team_2_events) == 12  # Radiant events (5 picks + 7 bans)
        assert len(team_3_events) == 12  # Dire events (5 picks + 7 bans)

    def test_game_info_serialization_roundtrip(self):
        """Test GameInfo JSON serialization preserves exact values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(game_info=True)
        original = result.game_info

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = GameInfo.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert len(restored.picks_bans) == 24


class TestMessageEventRealValues:
    """Test MessageEvent with EXACT values from real demo file."""

    def test_messages_exact_values(self):
        """Test messages parsing produces exact message sequence."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 10})

        assert result.success is True
        assert len(result.messages.messages) == 10
        assert result.error is None

        # Test exact message types from real file (specific Manta callback names)
        message_types = [msg.type for msg in result.messages.messages]
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

    def test_first_message_exact_values(self):
        """Test first message contains exact expected values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 5})

        first_message = result.messages.messages[0]
        assert first_message.type == "CDemoFileHeader"
        assert first_message.tick == 0
        assert first_message.net_tick == 0
        assert first_message.data is not None

    def test_tick_progression_exact_sequence(self):
        """Test tick progression follows exact sequence from real file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 10})

        ticks = [msg.tick for msg in result.messages.messages]
        # First 10 messages are all at tick 0 (header and string table setup)
        expected_ticks = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert ticks == expected_ticks

        # Ticks must be in non-decreasing order
        assert ticks == sorted(ticks)


class TestMessagesResultRealValues:
    """Test MessagesResult with EXACT values from real demo file."""

    def test_messages_result_exact_structure(self):
        """Test messages result contains exact structure from real file."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 5})

        assert result.success is True
        assert len(result.messages.messages) == 5
        assert result.error is None

    def test_messages_result_serialization_roundtrip(self):
        """Test MessagesResult JSON serialization preserves exact values."""
        parser = Parser(DEMO_FILE)
        result = parser.parse(messages={"max_messages": 3})
        original = result.messages

        # Serialize and deserialize
        json_str = original.model_dump_json()
        restored = MessagesResult.model_validate_json(json_str)

        # Must be identical to original
        assert restored == original
        assert len(restored.messages) == 3
        assert restored.messages[0].type == "CDemoFileHeader"

    def test_filtered_messages_exact_results(self):
        """Test message filtering produces exact expected results."""
        parser = Parser(DEMO_FILE)
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
