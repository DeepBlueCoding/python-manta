#!/usr/bin/env python3
"""
Basic usage example for Python Manta library.

This example demonstrates how to parse Dota 2 replay file headers
using the Python Manta library.
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from python_manta import MantaParser, parse_demo_header
except ImportError as e:
    print(f"❌ Failed to import python_manta: {e}")
    print("Make sure you've built the library with ./build.sh")
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 basic_usage.py <demo_file.dem>")
        print("\nExample:")
        print("  python3 basic_usage.py /path/to/match.dem")
        sys.exit(1)

    demo_file = sys.argv[1]
    
    if not os.path.exists(demo_file):
        print(f"❌ Demo file not found: {demo_file}")
        sys.exit(1)

    print(f"🎮 Parsing Dota 2 replay: {demo_file}")
    print("=" * 50)
    
    try:
        # Method 1: Quick parsing with convenience function
        print("📊 Using quick parse function...")
        header = parse_demo_header(demo_file)
        
        print(f"✅ Successfully parsed demo file!")
        print(f"📍 Map: {header.map_name}")
        print(f"🖥️  Server: {header.server_name}")
        print(f"📺 Client: {header.client_name}")
        print(f"🏗️  Build: {header.build_num}")
        print(f"🔗 Protocol: {header.network_protocol}")
        print(f"🎯 Start Tick: {header.server_start_tick}")
        
        # Method 2: Advanced usage with parser instance
        print("\n🔧 Using parser instance...")
        parser = MantaParser()
        header2 = parser.parse_header(demo_file)
        
        # Verify both methods return identical results
        if (header.map_name == header2.map_name and 
            header.build_num == header2.build_num):
            print("✅ Both parsing methods returned identical results")
        else:
            print("⚠️  Warning: Parsing methods returned different results")
            
        print("\n🎉 Demo parsing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error parsing demo file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()