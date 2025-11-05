#!/usr/bin/env python3
"""
Draft parsing example for Python Manta library.

This example demonstrates how to parse Dota 2 replay draft phase 
(picks and bans) using the Python Manta library.
"""
import sys
import os
from pathlib import Path

# Add the src directory to Python path for local development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from python_manta import parse_demo_draft, MantaParser, CHeroSelectEvent
except ImportError as e:
    print(f"❌ Failed to import python_manta: {e}")
    print("Make sure you've built the library with ./build.sh")
    sys.exit(1)


# Hero ID to name mapping (partial - common heroes)
HERO_NAMES = {
    1: "Anti-Mage", 2: "Axe", 3: "Bane", 4: "Bloodseeker", 5: "Crystal Maiden",
    6: "Drow Ranger", 7: "Earthshaker", 8: "Juggernaut", 9: "Mirana", 10: "Morphling",
    11: "Shadow Fiend", 12: "Phantom Lancer", 13: "Puck", 14: "Pudge", 15: "Razor",
    16: "Sand King", 17: "Storm Spirit", 18: "Sven", 19: "Tiny", 20: "Vengeful Spirit",
    21: "Windranger", 22: "Zeus", 23: "Kunkka", 25: "Lina", 26: "Lion",
    27: "Shadow Shaman", 28: "Slardar", 29: "Tidehunter", 30: "Witch Doctor", 31: "Lich",
    32: "Riki", 33: "Enigma", 34: "Tinker", 35: "Sniper", 36: "Necrophos",
    37: "Warlock", 38: "Beastmaster", 39: "Queen of Pain", 40: "Venomancer", 41: "Faceless Void",
    42: "Wraith King", 43: "Death Prophet", 44: "Phantom Assassin", 45: "Pugna", 46: "Templar Assassin",
    47: "Viper", 48: "Luna", 49: "Dragon Knight", 50: "Dazzle", 51: "Clockwerk",
    52: "Leshrac", 53: "Nature's Prophet", 54: "Lifestealer", 55: "Dark Seer", 56: "Clinkz",
    57: "Omniknight", 58: "Enchantress", 59: "Huskar", 60: "Night Stalker", 61: "Broodmother",
    62: "Bounty Hunter", 63: "Weaver", 64: "Jakiro", 65: "Batrider", 66: "Chen",
    67: "Spectre", 68: "Ancient Apparition", 69: "Doom", 70: "Ursa", 71: "Spirit Breaker",
    72: "Gyrocopter", 73: "Alchemist", 74: "Invoker", 75: "Silencer", 76: "Outworld Destroyer",
    77: "Lycan", 78: "Brewmaster", 79: "Shadow Demon", 80: "Lone Druid", 81: "Chaos Knight",
    82: "Meepo", 83: "Treant Protector", 84: "Ogre Magi", 85: "Undying", 86: "Rubick",
    87: "Disruptor", 88: "Nyx Assassin", 89: "Naga Siren", 90: "Keeper of the Light",
    91: "Io", 92: "Visage", 93: "Slark", 94: "Medusa", 95: "Troll Warlord",
    96: "Centaur Warrunner", 97: "Magnus", 98: "Timbersaw", 99: "Bristleback", 100: "Tusk",
    101: "Skywrath Mage", 102: "Abaddon", 103: "Elder Titan", 104: "Legion Commander", 105: "Techies",
    106: "Ember Spirit", 107: "Earth Spirit", 108: "Underlord", 109: "Terrorblade", 110: "Phoenix",
    111: "Oracle", 112: "Winter Wyvern", 113: "Arc Warden", 114: "Monkey King", 119: "Dark Willow",
    120: "Pangolier", 121: "Grimstroke", 123: "Hoodwink", 126: "Void Spirit", 128: "Snapfire",
    129: "Mars", 131: "Dawnbreaker", 135: "Marci", 136: "Primal Beast", 137: "Muerta"
}


def get_hero_name(hero_id: int) -> str:
    """Get hero name from ID, with fallback."""
    return HERO_NAMES.get(hero_id, f"Hero_{hero_id}")


def get_team_name(team_id: int) -> str:
    """Get team name from ID."""
    if team_id == 2:
        return "Radiant"
    elif team_id == 3:
        return "Dire"
    else:
        return f"Team_{team_id}"


def format_draft_phase(picks_bans: list[CHeroSelectEvent]) -> str:
    """Format draft phase for display."""
    if not picks_bans:
        return "No draft data found"
    
    result = []
    result.append("🎭 DRAFT PHASE")
    result.append("=" * 50)
    
    for i, event in enumerate(picks_bans, 1):
        action = "🛡️ PICK" if event.is_pick else "❌ BAN"
        team = get_team_name(event.team)
        hero = get_hero_name(event.hero_id)
        
        result.append(f"{i:2d}. {action} - {team:7s} - {hero}")
    
    return "\n".join(result)


def analyze_draft(picks_bans: list[CHeroSelectEvent]) -> str:
    """Analyze the draft for interesting statistics."""
    if not picks_bans:
        return "No draft data to analyze"
    
    picks = [e for e in picks_bans if e.is_pick]
    bans = [e for e in picks_bans if not e.is_pick]
    
    radiant_picks = [e for e in picks if e.team == 2]
    dire_picks = [e for e in picks if e.team == 3]
    radiant_bans = [e for e in bans if e.team == 2]
    dire_bans = [e for e in bans if e.team == 3]
    
    result = []
    result.append("📊 DRAFT ANALYSIS")
    result.append("=" * 30)
    result.append(f"Total Events: {len(picks_bans)}")
    result.append(f"Picks: {len(picks)}, Bans: {len(bans)}")
    result.append("")
    result.append("By Team:")
    result.append(f"  Radiant: {len(radiant_picks)} picks, {len(radiant_bans)} bans")
    result.append(f"  Dire:    {len(dire_picks)} picks, {len(dire_bans)} bans")
    
    if radiant_picks:
        result.append("")
        result.append("🌟 Radiant Picks:")
        for pick in radiant_picks:
            result.append(f"   • {get_hero_name(pick.hero_id)}")
    
    if dire_picks:
        result.append("")
        result.append("🔥 Dire Picks:")
        for pick in dire_picks:
            result.append(f"   • {get_hero_name(pick.hero_id)}")
    
    return "\n".join(result)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 draft_example.py <demo_file.dem>")
        print("\nExample:")
        print("  python3 draft_example.py /path/to/match.dem")
        sys.exit(1)

    demo_file = sys.argv[1]
    
    if not os.path.exists(demo_file):
        print(f"❌ Demo file not found: {demo_file}")
        sys.exit(1)

    print(f"🎮 Parsing Dota 2 replay draft: {demo_file}")
    print("=" * 60)
    
    try:
        # Parse draft information
        print("📊 Parsing draft phase...")
        draft_info = parse_demo_draft(demo_file)
        
        print(f"✅ Successfully parsed draft data!")
        print(f"📝 Found {len(draft_info.picks_bans)} draft events")
        print()
        
        # Display formatted draft
        print(format_draft_phase(draft_info.picks_bans))
        print()
        
        # Display analysis
        print(analyze_draft(draft_info.picks_bans))
        
        print("\n🎉 Draft parsing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error parsing draft: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()