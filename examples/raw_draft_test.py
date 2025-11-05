#!/usr/bin/env python3
"""
Raw draft data test - shows exactly what the library returns without formatting.
This should match Manta's native output exactly.
"""
import sys
import json
from pathlib import Path

# Add the src directory to Python path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from python_manta import parse_demo_draft

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 raw_draft_test.py <demo_file.dem>")
        sys.exit(1)

    demo_file = sys.argv[1]
    
    try:
        # Get raw draft data from library
        draft_info = parse_demo_draft(demo_file)
        
        # Print the raw Pydantic model as JSON (this should match Manta exactly)
        print("RAW LIBRARY OUTPUT:")
        print("=" * 50)
        print(json.dumps(draft_info.model_dump(), indent=2))
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()