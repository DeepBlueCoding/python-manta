"""
Test convenience functions with REAL workflows and data processing.
Focus on end-to-end workflows and data extraction scenarios.
"""

import pytest
from python_manta import (
    parse_demo_header,
    parse_demo_draft,
    parse_demo_universal,
    MantaParser
)

# Real demo file path
DEMO_FILE = "/home/juanma/projects/equilibrium_coach/.data/replays/8447659831.dem"


@pytest.mark.unit
class TestConvenienceFunctionWorkflows:
    """Test convenience functions in real workflow scenarios."""

    def test_complete_match_analysis_workflow(self):
        """Test complete match analysis workflow with real data extraction."""
        # Step 1: Extract match metadata
        header = parse_demo_header(DEMO_FILE)
        assert header.success is True
        
        # Step 2: Extract draft information  
        draft = parse_demo_draft(DEMO_FILE)
        assert draft.success is True
        
        # Step 3: Extract early game messages
        messages = parse_demo_universal(DEMO_FILE, max_messages=20)
        assert messages.success is True
        
        # Workflow result: Complete match summary
        match_summary = {
            "map": header.map_name,
            "build": header.build_num,
            "server": header.server_name,
            "radiant_picks": [e.hero_id for e in draft.picks_bans if e.is_pick and e.team == 2],
            "dire_picks": [e.hero_id for e in draft.picks_bans if e.is_pick and e.team == 3],
            "total_events": len(draft.picks_bans),
            "message_count": len(messages.messages)
        }
        
        # Verify workflow produced correct real data
        assert match_summary["map"] == "start"
        assert match_summary["build"] == 10512
        assert match_summary["radiant_picks"] == [99, 123, 66, 114, 95]
        assert match_summary["dire_picks"] == [77, 45, 27, 17, 41]
        assert match_summary["total_events"] == 24
        assert match_summary["message_count"] == 20

    def test_draft_analysis_workflow(self):
        """Test draft analysis workflow with real pick/ban data."""
        draft = parse_demo_draft(DEMO_FILE)
        
        # Workflow: Analyze draft phase
        picks = [e for e in draft.picks_bans if e.is_pick]
        bans = [e for e in draft.picks_bans if not e.is_pick]
        
        # Extract team compositions
        radiant_composition = {
            "picks": [e.hero_id for e in picks if e.team == 2],
            "bans": [e.hero_id for e in bans if e.team == 2],
            "pick_count": len([e for e in picks if e.team == 2]),
            "ban_count": len([e for e in bans if e.team == 2])
        }
        
        dire_composition = {
            "picks": [e.hero_id for e in picks if e.team == 3], 
            "bans": [e.hero_id for e in bans if e.team == 3],
            "pick_count": len([e for e in picks if e.team == 3]),
            "ban_count": len([e for e in bans if e.team == 3])
        }
        
        # Verify real draft analysis results
        assert radiant_composition["picks"] == [99, 123, 66, 114, 95]
        assert dire_composition["picks"] == [77, 45, 27, 17, 41]
        assert radiant_composition["pick_count"] == 5
        assert dire_composition["pick_count"] == 5
        assert radiant_composition["ban_count"] == 7
        assert dire_composition["ban_count"] == 7

    def test_message_stream_analysis_workflow(self):
        """Test message stream analysis workflow with real message data."""
        messages = parse_demo_universal(DEMO_FILE, max_messages=15)
        
        # Workflow: Analyze message stream
        message_analysis = {
            "total_messages": len(messages.messages),
            "message_types": list(set(msg.type for msg in messages.messages)),
            "tick_range": {
                "start": messages.messages[0].tick,
                "end": messages.messages[-1].tick
            },
            "demo_packets": len([msg for msg in messages.messages if msg.type == "CDemoPacket"]),
            "file_headers": len([msg for msg in messages.messages if msg.type == "CDemoFileHeader"])
        }
        
        # Verify real message analysis results
        assert message_analysis["total_messages"] == 15
        assert "CDemoFileHeader" in message_analysis["message_types"]
        assert "CDemoPacket" in message_analysis["message_types"]
        assert message_analysis["tick_range"]["start"] == 0
        assert message_analysis["tick_range"]["end"] > 0
        assert message_analysis["file_headers"] == 1  # Should have exactly one file header

    def test_batch_processing_simulation_workflow(self):
        """Test batch processing simulation with real file processing."""
        demo_files = [DEMO_FILE]  # In real scenario would be multiple files
        
        # Workflow: Batch process multiple demo files
        batch_results = []
        
        for demo_path in demo_files:
            try:
                # Process each file
                header = parse_demo_header(demo_path)
                draft = parse_demo_draft(demo_path)
                
                batch_results.append({
                    "file": demo_path,
                    "success": header.success and draft.success,
                    "map": header.map_name,
                    "build": header.build_num,
                    "pick_count": len([e for e in draft.picks_bans if e.is_pick]),
                    "ban_count": len([e for e in draft.picks_bans if not e.is_pick])
                })
            except Exception as e:
                batch_results.append({
                    "file": demo_path,
                    "success": False,
                    "error": str(e)
                })
        
        # Verify batch processing results
        assert len(batch_results) == 1
        assert batch_results[0]["success"] is True
        assert batch_results[0]["map"] == "start"
        assert batch_results[0]["build"] == 10512
        assert batch_results[0]["pick_count"] == 10
        assert batch_results[0]["ban_count"] == 14


@pytest.mark.unit
class TestConvenienceFunctionConsistency:
    """Test convenience functions produce consistent results."""

    def test_convenience_vs_parser_consistency(self):
        """Test convenience functions produce same results as parser methods."""
        # Using convenience functions
        conv_header = parse_demo_header(DEMO_FILE)
        conv_draft = parse_demo_draft(DEMO_FILE)
        conv_universal = parse_demo_universal(DEMO_FILE, max_messages=10)
        
        # Using parser methods
        parser = MantaParser()
        parser_header = parser.parse_header(DEMO_FILE)
        parser_draft = parser.parse_draft(DEMO_FILE)
        parser_universal = parser.parse_universal(DEMO_FILE, max_messages=10)
        
        # Results must be identical
        assert conv_header.map_name == parser_header.map_name == "start"
        assert conv_header.build_num == parser_header.build_num == 10512
        assert len(conv_draft.picks_bans) == len(parser_draft.picks_bans) == 24
        assert len(conv_universal.messages) == len(parser_universal.messages) == 10
        
        # Message types must match
        conv_types = [msg.type for msg in conv_universal.messages]
        parser_types = [msg.type for msg in parser_universal.messages]
        assert conv_types == parser_types

    def test_repeated_convenience_calls_consistency(self):
        """Test repeated convenience function calls produce identical results."""
        # Call multiple times
        headers = [parse_demo_header(DEMO_FILE) for _ in range(3)]
        drafts = [parse_demo_draft(DEMO_FILE) for _ in range(3)]
        
        # All headers must be identical
        for header in headers[1:]:
            assert header.map_name == headers[0].map_name == "start"
            assert header.build_num == headers[0].build_num == 10512
            assert header.server_name == headers[0].server_name
        
        # All drafts must be identical  
        for draft in drafts[1:]:
            assert len(draft.picks_bans) == len(drafts[0].picks_bans) == 24
            
            # Pick sequences must match
            picks1 = [e.hero_id for e in draft.picks_bans if e.is_pick and e.team == 2]
            picks0 = [e.hero_id for e in drafts[0].picks_bans if e.is_pick and e.team == 2]
            assert picks1 == picks0 == [99, 123, 66, 114, 95]

    def test_universal_parsing_parameter_consistency(self):
        """Test universal parsing produces consistent results with different parameters."""
        # Test with different max_messages values
        result_5 = parse_demo_universal(DEMO_FILE, max_messages=5)
        result_10 = parse_demo_universal(DEMO_FILE, max_messages=10)
        result_20 = parse_demo_universal(DEMO_FILE, max_messages=20)
        
        # All should succeed
        assert result_5.success is True
        assert result_10.success is True  
        assert result_20.success is True
        
        # Message counts should respect limits
        assert len(result_5.messages) == 5
        assert len(result_10.messages) == 10
        assert len(result_20.messages) == 20
        
        # First messages should be identical (CDemoFileHeader)
        assert result_5.messages[0].type == result_10.messages[0].type == result_20.messages[0].type == "CDemoFileHeader"
        assert result_5.messages[0].tick == result_10.messages[0].tick == result_20.messages[0].tick == 0
        
        # Overlapping messages should be identical
        for i in range(5):
            assert result_5.messages[i].type == result_10.messages[i].type == result_20.messages[i].type
            assert result_5.messages[i].tick == result_10.messages[i].tick == result_20.messages[i].tick


@pytest.mark.unit
class TestConvenienceFunctionRealDataExtraction:
    """Test convenience functions for real data extraction scenarios."""

    def test_hero_id_extraction_accuracy(self):
        """Test accurate hero ID extraction from real draft data."""
        draft = parse_demo_draft(DEMO_FILE)
        
        # Extract all unique hero IDs involved in draft
        all_hero_ids = set(e.hero_id for e in draft.picks_bans)
        picked_hero_ids = set(e.hero_id for e in draft.picks_bans if e.is_pick)
        banned_hero_ids = set(e.hero_id for e in draft.picks_bans if not e.is_pick)
        
        # Verify real hero ID data
        expected_picked = {99, 123, 66, 114, 95, 77, 45, 27, 17, 41}
        expected_banned = {74, 38, 89, 136, 102, 70, 8, 53, 11, 7, 16, 110, 13, 1}
        
        assert picked_hero_ids == expected_picked
        assert banned_hero_ids == expected_banned
        assert len(picked_hero_ids & banned_hero_ids) == 0  # No overlap between picks and bans
        assert all_hero_ids == picked_hero_ids | banned_hero_ids

    def test_team_balance_validation(self):
        """Test team balance validation with real draft data."""
        draft = parse_demo_draft(DEMO_FILE)
        
        # Count events by team
        radiant_events = [e for e in draft.picks_bans if e.team == 2]
        dire_events = [e for e in draft.picks_bans if e.team == 3]
        
        # In this specific game, teams should have equal total events
        assert len(radiant_events) == len(dire_events) == 12
        
        # Each team should have exactly 5 picks
        radiant_picks = [e for e in radiant_events if e.is_pick]
        dire_picks = [e for e in dire_events if e.is_pick]
        assert len(radiant_picks) == len(dire_picks) == 5
        
        # Each team should have exactly 7 bans
        radiant_bans = [e for e in radiant_events if not e.is_pick]
        dire_bans = [e for e in dire_events if not e.is_pick]
        assert len(radiant_bans) == len(dire_bans) == 7

    def test_message_filtering_accuracy(self):
        """Test message filtering produces accurate filtered results."""
        # Get all messages first
        all_messages = parse_demo_universal(DEMO_FILE, max_messages=50)
        
        # Filter for specific message type
        header_messages = parse_demo_universal(DEMO_FILE, message_filter="CDemoFileHeader", max_messages=10)
        packet_messages = parse_demo_universal(DEMO_FILE, message_filter="CDemoPacket", max_messages=20)
        
        # Verify filtering accuracy
        assert header_messages.success is True
        assert packet_messages.success is True
        
        # All filtered messages must match the filter
        for msg in header_messages.messages:
            assert "CDemoFileHeader" in msg.type
            
        for msg in packet_messages.messages:
            assert "CDemoPacket" in msg.type
        
        # Should have at least one header message
        assert len(header_messages.messages) >= 1
        # Should have multiple packet messages
        assert len(packet_messages.messages) > 1