#!/usr/bin/env python3
"""
VERY SIMPLE Python Manta Example
Subscribe to callbacks and extract game data from Dota 2 replays
"""

import sys
import os
sys.path.append('src')

from python_manta.manta_python import MantaParser

def simple_callback_example():
    """
    Simple example showing how to subscribe to callbacks
    """
    print("🎮 SIMPLE PYTHON MANTA EXAMPLE")
    print("=" * 50)
    
    # 1. Initialize parser
    library_path = "go_wrapper/manta_wrapper.so"
    parser = MantaParser(library_path)
    print("✅ Parser ready")
    
    # 2. Specify demo file (replace with your demo file)
    demo_file = "path/to/your/demo.dem"  # Change this!
    
    if not os.path.exists(demo_file):
        print("❌ Demo file not found!")
        print("💡 Please update 'demo_file' path in this script")
        return
    
    print(f"📂 Using demo: {demo_file}")
    
    # 3. Subscribe to chat messages (most common use case)
    print("\n💬 EXTRACTING CHAT MESSAGES...")
    
    result = parser.parse_universal(demo_file, "CDOTAUserMsg_ChatMessage", 20)
    
    if result.success:
        print(f"Found {result.count} chat messages:")
        
        for msg in result.messages:
            player_id = msg.data['source_player_id']
            text = msg.data['message_text']
            tick = msg.tick
            print(f"  [Tick {tick}] Player {player_id}: '{text}'")
    else:
        print(f"❌ Error: {result.error}")
    
    # 4. Subscribe to location pings (second most common)
    print("\n📍 EXTRACTING LOCATION PINGS...")
    
    result = parser.parse_universal(demo_file, "CDOTAUserMsg_LocationPing", 10)
    
    if result.success:
        print(f"Found {result.count} location pings:")
        
        for msg in result.messages:
            player_id = msg.data['player_id']
            ping = msg.data['location_ping']
            x, y = ping['x'], ping['y']
            tick = msg.tick
            print(f"  [Tick {tick}] Player {player_id} pinged at ({x}, {y})")
    else:
        print(f"❌ Error: {result.error}")
    
    # 5. Get demo metadata
    print("\n📋 EXTRACTING DEMO INFO...")
    
    result = parser.parse_universal(demo_file, "CDemoFileHeader", 1)
    
    if result.success and result.messages:
        data = result.messages[0].data
        print(f"Map: {data.get('map_name', 'Unknown')}")
        print(f"Server: {data.get('server_name', 'Unknown')}")
        print(f"Build: {data.get('build_num', 'Unknown')}")
    
    print("\n✅ Done! That's all it takes!")

if __name__ == "__main__":
    simple_callback_example()