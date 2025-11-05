#!/usr/bin/env python3
"""
Universal parsing test - demonstrates ALL Manta interfaces working together.
Tests the comprehensive callback system with filtering and message limits.
"""
import sys
from pathlib import Path

# Add the src directory to Python path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from python_manta import parse_demo_universal

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 universal_test.py <demo_file.dem>")
        sys.exit(1)

    demo_file = sys.argv[1]
    
    try:
        print(f"🧪 Testing Universal Parsing with: {demo_file}")
        print("=" * 80)
        
        # Test 1: Parse first 10 messages of any type
        print("\n🔍 TEST 1: First 10 messages of ANY type")
        print("-" * 50)
        result = parse_demo_universal(demo_file, "", 10)
        print(f"✅ Success: {result.success}")
        print(f"📊 Total Messages: {result.count}")
        for i, msg in enumerate(result.messages[:3], 1):  # Show first 3
            print(f"  {i}. {msg.type} (tick: {msg.tick})")
        if len(result.messages) > 3:
            print(f"  ... and {len(result.messages) - 3} more")
        
        # Test 2: Filter for DOTA chat events only
        print("\n💬 TEST 2: Filter for DOTA chat events only")
        print("-" * 50)
        chat_result = parse_demo_universal(demo_file, "CDOTAUserMsg_ChatEvent", 0)
        print(f"✅ Success: {chat_result.success}")
        print(f"💭 Chat Messages Found: {chat_result.count}")
        for i, msg in enumerate(chat_result.messages[:5], 1):  # Show first 5
            print(f"  {i}. {msg.type} at tick {msg.tick}")
        
        # Test 3: Filter for file header only  
        print("\n📄 TEST 3: Filter for demo file header")
        print("-" * 50)
        header_result = parse_demo_universal(demo_file, "CDemoFileHeader", 1)
        print(f"✅ Success: {header_result.success}")
        print(f"📋 Header Messages: {header_result.count}")
        if header_result.messages:
            msg = header_result.messages[0]
            print(f"  Header Type: {msg.type}")
            print(f"  Data Available: {bool(msg.data)}")
        
        # Test 4: Filter for combat log data
        print("\n⚔️ TEST 4: Filter for combat log data")
        print("-" * 50)
        combat_result = parse_demo_universal(demo_file, "CDOTAUserMsg_CombatLogBulkData", 5)
        print(f"✅ Success: {combat_result.success}")
        print(f"⚔️ Combat Messages: {combat_result.count}")
        for i, msg in enumerate(combat_result.messages, 1):
            print(f"  {i}. {msg.type} at tick {msg.tick}")
        
        # Test 5: Filter for hero position data
        print("\n🎯 TEST 5: Filter for hero position data")
        print("-" * 50)
        pos_result = parse_demo_universal(demo_file, "CDOTAUserMsg_CombatHeroPositions", 3)
        print(f"✅ Success: {pos_result.success}")
        print(f"🎯 Position Messages: {pos_result.count}")
        for i, msg in enumerate(pos_result.messages, 1):
            print(f"  {i}. {msg.type} at tick {msg.tick} (net_tick: {msg.net_tick})")
        
        # Test 6: Get a sample of ALL message types  
        print("\n🌐 TEST 6: Sample of ALL message types (first 20 messages)")
        print("-" * 50)
        sample_result = parse_demo_universal(demo_file, "", 20)
        print(f"✅ Success: {sample_result.success}")
        print(f"📦 Sample Messages: {sample_result.count}")
        
        # Show unique message types found
        unique_types = list(set(msg.type for msg in sample_result.messages))
        unique_types.sort()
        print(f"🎪 Unique Message Types Found: {len(unique_types)}")
        for msg_type in unique_types:
            print(f"   • {msg_type}")
        
        print(f"\n🎉 Universal parsing test completed successfully!")
        print(f"🔥 This demonstrates ALL {len(unique_types)} different Manta message types working!")
        
    except Exception as e:
        print(f"❌ Error during universal parsing test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()