"""
Python interface for Manta Dota 2 replay parser using ctypes.
Provides basic file header reading functionality through Go CGO wrapper.
"""
from __future__ import annotations

import bz2
import ctypes
import json
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator
from pydantic import BaseModel, Field

# ============================================================================
# TIME UTILITIES
# ============================================================================

TICKS_PER_SECOND = 30.0


def format_game_time(seconds: float) -> str:
    """Format game time as '-0:40' or '3:07'.

    Args:
        seconds: Game time in seconds (negative = pre-horn)

    Returns:
        Formatted time string like '-0:40' or '3:07'
    """
    negative = seconds < 0
    abs_seconds = abs(int(seconds))
    mins = abs_seconds // 60
    secs = abs_seconds % 60
    sign = "-" if negative else ""
    return f"{sign}{mins}:{secs:02d}"


def game_time_to_tick(game_time: float, game_start_tick: int) -> int:
    """Convert game_time (seconds from horn) to tick.

    Args:
        game_time: Seconds from horn (negative = pre-horn)
        game_start_tick: Tick when horn sounded

    Returns:
        Tick number
    """
    return game_start_tick + int(game_time * TICKS_PER_SECOND)


def tick_to_game_time(tick: int, game_start_tick: int) -> float:
    """Convert tick to game_time (seconds from horn).

    Args:
        tick: Tick number
        game_start_tick: Tick when horn sounded

    Returns:
        Seconds from horn (negative = pre-horn)
    """
    return (tick - game_start_tick) / TICKS_PER_SECOND


def normalize_hero_name(name: str) -> str:
    """Normalize hero names by replacing double underscores with single.

    Entity snapshots may use double underscores (npc_dota_hero_shadow__demon)
    while combat log uses single (npc_dota_hero_shadow_demon). This ensures
    consistency for matching.

    Args:
        name: Hero name (e.g., "npc_dota_hero_shadow__demon" or "shadow__demon")

    Returns:
        Normalized name with single underscores (e.g., "npc_dota_hero_shadow_demon")
    """
    while "__" in name:
        name = name.replace("__", "_")
    return name


class RuneType(str, Enum):
    """Dota 2 rune types with their modifier names.

    Usage:
        # Check if a combat log entry is a rune pickup
        if RuneType.from_modifier(entry.inflictor_name):
            rune = RuneType.from_modifier(entry.inflictor_name)
            print(f"Picked up {rune.display_name}")

        # Get all rune modifiers for filtering
        rune_modifiers = RuneType.all_modifiers()
    """
    DOUBLE_DAMAGE = "modifier_rune_doubledamage"
    HASTE = "modifier_rune_haste"
    ILLUSION = "modifier_rune_illusion"
    INVISIBILITY = "modifier_rune_invis"
    REGENERATION = "modifier_rune_regen"
    ARCANE = "modifier_rune_arcane"
    SHIELD = "modifier_rune_shield"
    WATER = "modifier_rune_water"

    @property
    def display_name(self) -> str:
        """Human-readable rune name."""
        names = {
            RuneType.DOUBLE_DAMAGE: "Double Damage",
            RuneType.HASTE: "Haste",
            RuneType.ILLUSION: "Illusion",
            RuneType.INVISIBILITY: "Invisibility",
            RuneType.REGENERATION: "Regeneration",
            RuneType.ARCANE: "Arcane",
            RuneType.SHIELD: "Shield",
            RuneType.WATER: "Water",
        }
        return names[self]

    @property
    def modifier_name(self) -> str:
        """Combat log modifier name for this rune."""
        return self.value

    @classmethod
    def from_modifier(cls, modifier_name: str) -> Optional["RuneType"]:
        """Get RuneType from a combat log modifier name.

        Returns None if the modifier is not a rune modifier.
        """
        for rune in cls:
            if rune.value == modifier_name:
                return rune
        return None

    @classmethod
    def all_modifiers(cls) -> List[str]:
        """Get list of all rune modifier names for filtering."""
        return [rune.value for rune in cls]

    @classmethod
    def is_rune_modifier(cls, modifier_name: str) -> bool:
        """Check if a modifier name is a rune modifier."""
        return modifier_name.startswith("modifier_rune_")


_SUMMON_PATTERNS = (
    "lycan_wolf", "lone_druid_bear", "beastmaster_boar", "beastmaster_hawk",
    "enigma_eidolon", "nature_prophet_treant", "undying_zombie", "venomancer_plague_ward",
    "witch_doctor_death_ward", "shadow_shaman_ward", "pugna_nether_ward",
    "templar_assassin_psionic_trap", "techies_mine", "invoker_forge_spirit",
    "warlock_golem", "visage_familiar", "brewmaster_", "phoenix_sun",
    "grimstroke_ink_creature", "hoodwink_sharpshooter",
)


class EntityType(str, Enum):
    """Dota 2 entity types identified from entity names.

    Usage:
        # Identify entity type from combat log
        attacker_type = EntityType.from_name(entry.attacker_name)
        if attacker_type == EntityType.HERO:
            print("Hero attacked")

        # Check if target is a creep
        if EntityType.from_name(entry.target_name).is_creep:
            print("Creep was targeted")
    """
    HERO = "hero"
    LANE_CREEP = "lane_creep"
    NEUTRAL_CREEP = "neutral_creep"
    SUMMON = "summon"
    BUILDING = "building"
    WARD = "ward"
    COURIER = "courier"
    ROSHAN = "roshan"
    UNKNOWN = "unknown"

    @classmethod
    def from_name(cls, entity_name: str) -> "EntityType":
        """Get EntityType from an entity name string.

        Args:
            entity_name: Raw entity name from combat log (e.g., "npc_dota_hero_axe")

        Returns:
            EntityType enum value
        """
        if not entity_name:
            return cls.UNKNOWN

        name = entity_name.lower()

        if "npc_dota_hero_" in name:
            return cls.HERO
        if "npc_dota_roshan" in name:
            return cls.ROSHAN
        if "npc_dota_creep_goodguys" in name or "npc_dota_creep_badguys" in name:
            return cls.LANE_CREEP
        if "npc_dota_neutral_" in name:
            return cls.NEUTRAL_CREEP
        if any(x in name for x in ["tower", "barracks", "fort", "filler", "effigy"]):
            return cls.BUILDING
        if "ward" in name and "reward" not in name:
            return cls.WARD
        if "courier" in name:
            return cls.COURIER
        if any(pattern in name for pattern in _SUMMON_PATTERNS):
            return cls.SUMMON

        return cls.UNKNOWN

    @property
    def is_hero(self) -> bool:
        """True if this is a hero."""
        return self == EntityType.HERO

    @property
    def is_creep(self) -> bool:
        """True if this is any type of creep (lane or neutral)."""
        return self in (EntityType.LANE_CREEP, EntityType.NEUTRAL_CREEP)

    @property
    def is_unit(self) -> bool:
        """True if this is a controllable unit (not building/ward)."""
        return self in (
            EntityType.HERO, EntityType.LANE_CREEP, EntityType.NEUTRAL_CREEP,
            EntityType.SUMMON, EntityType.COURIER, EntityType.ROSHAN
        )

    @property
    def is_structure(self) -> bool:
        """True if this is a building or ward."""
        return self in (EntityType.BUILDING, EntityType.WARD)

    @property
    def display_name(self) -> str:
        """Human-readable entity type name."""
        return self.name.replace("_", " ").title()


class CombatLogType(int, Enum):
    """Dota 2 combat log event types.

    Usage:
        # Check combat log entry type
        if entry.type == CombatLogType.DAMAGE:
            print(f"{entry.attacker_name} dealt {entry.value} damage")

        # Filter by type
        result = parser.parse_combat_log(demo_path, types=[CombatLogType.PURCHASE])
    """
    DAMAGE = 0
    HEAL = 1
    MODIFIER_ADD = 2
    MODIFIER_REMOVE = 3
    DEATH = 4
    ABILITY = 5
    ITEM = 6
    LOCATION = 7
    GOLD = 8
    GAME_STATE = 9
    XP = 10
    PURCHASE = 11
    BUYBACK = 12
    ABILITY_TRIGGER = 13
    PLAYERSTATS = 14
    MULTIKILL = 15
    KILLSTREAK = 16
    TEAM_BUILDING_KILL = 17
    FIRST_BLOOD = 18
    MODIFIER_REFRESH = 19
    NEUTRAL_CAMP_STACK = 20
    PICKUP_RUNE = 21
    REVEALED_INVISIBLE = 22
    HERO_SAVED = 23
    MANA_RESTORED = 24
    HERO_LEVELUP = 25
    BOTTLE_HEAL_ALLY = 26
    ENDGAME_STATS = 27
    INTERRUPT_CHANNEL = 28
    ALLIED_GOLD = 29
    AEGIS_TAKEN = 30
    MANA_DAMAGE = 31
    PHYSICAL_DAMAGE_PREVENTED = 32
    UNIT_SUMMONED = 33
    ATTACK_EVADE = 34
    TREE_CUT = 35
    SUCCESSFUL_SCAN = 36
    END_KILLSTREAK = 37
    BLOODSTONE_CHARGE = 38
    CRITICAL_DAMAGE = 39
    SPELL_ABSORB = 40
    UNIT_TELEPORTED = 41
    KILL_EATER_EVENT = 42
    NEUTRAL_ITEM_EARNED = 43
    TELEPORT_INTERRUPTED = 44
    MODIFIER_STACK_EVENT = 45

    @property
    def display_name(self) -> str:
        """Human-readable combat log type name."""
        return self.name.replace("_", " ").title()

    @classmethod
    def from_value(cls, value: int) -> Optional["CombatLogType"]:
        """Get CombatLogType from integer value."""
        for t in cls:
            if t.value == value:
                return t
        return None

    @property
    def is_damage_related(self) -> bool:
        """True if this type is related to damage/healing."""
        return self in (
            CombatLogType.DAMAGE, CombatLogType.HEAL, CombatLogType.CRITICAL_DAMAGE,
            CombatLogType.MANA_DAMAGE, CombatLogType.PHYSICAL_DAMAGE_PREVENTED
        )

    @property
    def is_modifier_related(self) -> bool:
        """True if this type is related to buffs/debuffs."""
        return self in (
            CombatLogType.MODIFIER_ADD, CombatLogType.MODIFIER_REMOVE,
            CombatLogType.MODIFIER_REFRESH, CombatLogType.MODIFIER_STACK_EVENT
        )

    @property
    def is_economy_related(self) -> bool:
        """True if this type is related to gold/XP/items."""
        return self in (
            CombatLogType.GOLD, CombatLogType.XP, CombatLogType.PURCHASE,
            CombatLogType.ALLIED_GOLD, CombatLogType.NEUTRAL_ITEM_EARNED
        )

    @property
    def is_shield_related(self) -> bool:
        """True if this type is related to shields, barriers, or damage absorption.

        Note: These events may be rare or not generated in all replays.
        - PHYSICAL_DAMAGE_PREVENTED: Damage block (Vanguard, Crimson Guard, etc.)
        - SPELL_ABSORB: Spell blocked (Linken's Sphere, Lotus Orb, etc.)
        - AEGIS_TAKEN: Aegis of the Immortal picked up
        """
        return self in (
            CombatLogType.PHYSICAL_DAMAGE_PREVENTED,
            CombatLogType.SPELL_ABSORB,
            CombatLogType.AEGIS_TAKEN,
        )

    @property
    def is_death_related(self) -> bool:
        """True if this type is related to death, kills, or reincarnation.

        Note: Check `will_reincarnate` field on DEATH events for Aegis/WK respawns.
        """
        return self in (
            CombatLogType.DEATH,
            CombatLogType.FIRST_BLOOD,
            CombatLogType.MULTIKILL,
            CombatLogType.KILLSTREAK,
            CombatLogType.END_KILLSTREAK,
            CombatLogType.TEAM_BUILDING_KILL,
            CombatLogType.BUYBACK,
        )

    @property
    def is_defensive_related(self) -> bool:
        """True if this type is related to defensive actions or evasion.

        Includes damage prevention, spell absorption, saves, and evasion.
        """
        return self in (
            CombatLogType.PHYSICAL_DAMAGE_PREVENTED,
            CombatLogType.SPELL_ABSORB,
            CombatLogType.ATTACK_EVADE,
            CombatLogType.HERO_SAVED,
            CombatLogType.REVEALED_INVISIBLE,
        )

    @property
    def is_ability_related(self) -> bool:
        """True if this type is related to ability usage."""
        return self in (
            CombatLogType.ABILITY,
            CombatLogType.ABILITY_TRIGGER,
            CombatLogType.INTERRUPT_CHANNEL,
        )

    @property
    def is_movement_related(self) -> bool:
        """True if this type is related to movement or teleportation."""
        return self in (
            CombatLogType.UNIT_TELEPORTED,
            CombatLogType.TELEPORT_INTERRUPTED,
        )

    @property
    def is_resource_related(self) -> bool:
        """True if this type is related to health/mana resources."""
        return self in (
            CombatLogType.HEAL,
            CombatLogType.MANA_RESTORED,
            CombatLogType.MANA_DAMAGE,
            CombatLogType.BOTTLE_HEAL_ALLY,
            CombatLogType.BLOODSTONE_CHARGE,
        )

    @property
    def is_unit_related(self) -> bool:
        """True if this type is related to unit spawning or summoning."""
        return self in (
            CombatLogType.UNIT_SUMMONED,
            CombatLogType.NEUTRAL_CAMP_STACK,
        )

    @classmethod
    def shield_types(cls) -> list["CombatLogType"]:
        """Get all combat log types related to shields/absorption."""
        return [
            cls.PHYSICAL_DAMAGE_PREVENTED,
            cls.SPELL_ABSORB,
            cls.AEGIS_TAKEN,
        ]

    @classmethod
    def death_types(cls) -> list["CombatLogType"]:
        """Get all combat log types related to death/kills."""
        return [
            cls.DEATH,
            cls.FIRST_BLOOD,
            cls.MULTIKILL,
            cls.KILLSTREAK,
            cls.END_KILLSTREAK,
            cls.TEAM_BUILDING_KILL,
            cls.BUYBACK,
        ]


class DamageType(int, Enum):
    """Dota 2 damage types.

    Usage:
        if entry.damage_type == DamageType.PURE:
            print("Pure damage - ignores armor and magic resistance")
    """
    PHYSICAL = 0
    MAGICAL = 1
    PURE = 2
    COMPOSITE = 3  # Legacy: removed from Dota 2, was reduced by both armor and magic resistance
    HP_REMOVAL = 4

    @property
    def display_name(self) -> str:
        """Human-readable damage type name."""
        return self.name.title()

    @classmethod
    def from_value(cls, value: int) -> Optional["DamageType"]:
        """Get DamageType from integer value."""
        for t in cls:
            if t.value == value:
                return t
        return None


class Team(int, Enum):
    """Dota 2 team identifiers.

    Usage:
        if entry.attacker_team == Team.RADIANT:
            print("Radiant team attacked")
    """
    SPECTATOR = 0
    UNASSIGNED = 1
    RADIANT = 2
    DIRE = 3
    NEUTRAL = 4

    @property
    def display_name(self) -> str:
        """Human-readable team name."""
        return self.name.title()

    @property
    def is_playing(self) -> bool:
        """True if this is an actual playing team (not spectator/unassigned)."""
        return self in (Team.RADIANT, Team.DIRE)

    @property
    def is_neutral(self) -> bool:
        """True if this is a neutral unit (creeps, Roshan, etc.)."""
        return self == Team.NEUTRAL

    @classmethod
    def from_value(cls, value: int) -> Optional["Team"]:
        """Get Team from integer value."""
        for t in cls:
            if t.value == value:
                return t
        return None

    @property
    def opposite(self) -> Optional["Team"]:
        """Get the opposing team. Returns None for non-playing teams."""
        if self == Team.RADIANT:
            return Team.DIRE
        elif self == Team.DIRE:
            return Team.RADIANT
        return None


class NeutralCampType(int, Enum):
    """Neutral creep camp types.

    Used in combat log events (DEATH, MODIFIER_ADD, etc.) to identify
    which type of neutral camp a creep belongs to.

    Note: SMALL (0) is also used for non-neutral units (lane creeps, wards).
    Filter by target_name containing "neutral" to get only neutral creeps.

    Usage:
        if entry.neutral_camp_type == NeutralCampType.ANCIENT:
            print("Ancient camp creep killed")

        # Detect multi-camp farming (filter for neutrals first)
        neutral_deaths = [e for e in deaths if "neutral" in e.target_name]
        camp_types = {e.neutral_camp_type for e in neutral_deaths}
        if len(camp_types) >= 2:
            print("Multi-camp farming detected!")
    """
    SMALL = 0      # Small camps: kobolds, harpies, ghosts, forest trolls, gnolls (also default for non-neutrals)
    MEDIUM = 1     # Medium camps: wolves, ogres, mud golems
    HARD = 2       # Hard/Large camps: hellbears, dark trolls, wildkin, satyr hellcaller, centaurs
    ANCIENT = 3    # Ancient camps: dragons, thunderhides, prowlers, rock golems

    @property
    def display_name(self) -> str:
        """Human-readable camp type name."""
        names = {
            0: "Small Camp",
            1: "Medium Camp",
            2: "Hard Camp",
            3: "Ancient Camp",
        }
        return names.get(self.value, "Unknown")

    @property
    def is_ancient(self) -> bool:
        """True if this is an ancient camp."""
        return self == NeutralCampType.ANCIENT

    @classmethod
    def from_value(cls, value: int) -> "NeutralCampType":
        """Get NeutralCampType from integer value."""
        for t in cls:
            if t.value == value:
                return t
        return cls.SMALL


# Hero name aliases - maps internal replay names to canonical enum member names
_HERO_ALIASES: Dict[str, str] = {
    "nevermore": "shadow_fiend",
    "zuus": "zeus",
    "furion": "natures_prophet",
    "wisp": "io",
    "skeleton_king": "wraith_king",
    "obsidian_destroyer": "outworld_destroyer",
    "rattletrap": "clockwerk",
    "shredder": "timbersaw",
    "windrunner": "windranger",
    "necrolyte": "necrophos",
    "magnataur": "magnus",
    "abyssal_underlord": "underlord",
}


class Hero(int, Enum):
    """Dota 2 hero IDs."""
    ANTI_MAGE = 1
    AXE = 2
    BANE = 3
    BLOODSEEKER = 4
    CRYSTAL_MAIDEN = 5
    DROW_RANGER = 6
    EARTHSHAKER = 7
    JUGGERNAUT = 8
    MIRANA = 9
    MORPHLING = 10
    SHADOW_FIEND = 11
    PHANTOM_LANCER = 12
    PUCK = 13
    PUDGE = 14
    RAZOR = 15
    SAND_KING = 16
    STORM_SPIRIT = 17
    SVEN = 18
    TINY = 19
    VENGEFUL_SPIRIT = 20
    WINDRANGER = 21
    ZEUS = 22
    KUNKKA = 23
    LINA = 25
    LION = 26
    SHADOW_SHAMAN = 27
    SLARDAR = 28
    TIDEHUNTER = 29
    WITCH_DOCTOR = 30
    LICH = 31
    RIKI = 32
    ENIGMA = 33
    TINKER = 34
    SNIPER = 35
    NECROPHOS = 36
    WARLOCK = 37
    BEASTMASTER = 38
    QUEEN_OF_PAIN = 39
    VENOMANCER = 40
    FACELESS_VOID = 41
    WRAITH_KING = 42
    DEATH_PROPHET = 43
    PHANTOM_ASSASSIN = 44
    PUGNA = 45
    TEMPLAR_ASSASSIN = 46
    VIPER = 47
    LUNA = 48
    DRAGON_KNIGHT = 49
    DAZZLE = 50
    CLOCKWERK = 51
    LESHRAC = 52
    NATURES_PROPHET = 53
    LIFESTEALER = 54
    DARK_SEER = 55
    CLINKZ = 56
    OMNIKNIGHT = 57
    ENCHANTRESS = 58
    HUSKAR = 59
    NIGHT_STALKER = 60
    BROODMOTHER = 61
    BOUNTY_HUNTER = 62
    WEAVER = 63
    JAKIRO = 64
    BATRIDER = 65
    CHEN = 66
    SPECTRE = 67
    ANCIENT_APPARITION = 68
    DOOM = 69
    URSA = 70
    SPIRIT_BREAKER = 71
    GYROCOPTER = 72
    ALCHEMIST = 73
    INVOKER = 74
    SILENCER = 75
    OUTWORLD_DESTROYER = 76
    LYCAN = 77
    BREWMASTER = 78
    SHADOW_DEMON = 79
    LONE_DRUID = 80
    CHAOS_KNIGHT = 81
    MEEPO = 82
    TREANT_PROTECTOR = 83
    OGRE_MAGI = 84
    UNDYING = 85
    RUBICK = 86
    DISRUPTOR = 87
    NYX_ASSASSIN = 88
    NAGA_SIREN = 89
    KEEPER_OF_THE_LIGHT = 90
    IO = 91
    VISAGE = 92
    SLARK = 93
    MEDUSA = 94
    TROLL_WARLORD = 95
    CENTAUR_WARRUNNER = 96
    MAGNUS = 97
    TIMBERSAW = 98
    BRISTLEBACK = 99
    TUSK = 100
    SKYWRATH_MAGE = 101
    ABADDON = 102
    ELDER_TITAN = 103
    LEGION_COMMANDER = 104
    TECHIES = 105
    EMBER_SPIRIT = 106
    EARTH_SPIRIT = 107
    UNDERLORD = 108
    TERRORBLADE = 109
    PHOENIX = 110
    ORACLE = 111
    WINTER_WYVERN = 112
    ARC_WARDEN = 113
    MONKEY_KING = 114
    DARK_WILLOW = 119
    PANGOLIER = 120
    GRIMSTROKE = 121
    HOODWINK = 123
    VOID_SPIRIT = 126
    SNAPFIRE = 128
    MARS = 129
    RINGMASTER = 131
    DAWNBREAKER = 135
    MARCI = 136
    PRIMAL_BEAST = 137
    MUERTA = 138
    KEZ = 145
    LARGO = 155  # Added in 7.40

    @classmethod
    def from_id(cls, hero_id: int) -> Optional["Hero"]:
        """Get Hero from integer ID."""
        for hero in cls:
            if hero.value == hero_id:
                return hero
        return None

    @classmethod
    def from_hero_name(cls, hero_name: str) -> Optional["Hero"]:
        """Get Hero from internal hero name (handles aliases).

        Args:
            hero_name: Internal name like "npc_dota_hero_nevermore" or "nevermore"

        Returns:
            Hero enum or None if not found
        """
        if not hero_name:
            return None
        # Strip prefix if present
        name = hero_name.lower()
        if name.startswith("npc_dota_hero_"):
            name = name[14:]  # len("npc_dota_hero_")
        # Resolve alias to canonical name
        canonical = _HERO_ALIASES.get(name, name)
        # Find matching enum member
        for hero in cls:
            if hero.name.lower() == canonical:
                return hero
        return None

    @property
    def display_name(self) -> str:
        """Human-readable hero name."""
        return self.name.replace("_", " ").title()


# Category constants for item classification
class ItemCategory(str, Enum):
    """Item category classification."""
    CONSUMABLE = "consumable"
    ATTRIBUTE = "attribute"
    EQUIPMENT = "equipment"
    SECRET_SHOP = "secret_shop"
    SUPPORT = "support"
    MAGICAL = "magical"
    ARMOR = "armor"
    WEAPON = "weapon"
    ARTIFACT = "artifact"
    ACCESSORY = "accessory"

    @property
    def display_name(self) -> str:
        """Human-readable category name."""
        return self.name.replace("_", " ").title()


# All purchasable items with their category and display name
_ITEMS_DATA: Dict[str, Tuple[str, str]] = {
    # === CONSUMABLES ===
    "item_clarity": ("consumable", "Clarity"),
    "item_tango": ("consumable", "Tango"),
    "item_tango_single": ("consumable", "Tango (Shared)"),
    "item_flask": ("consumable", "Healing Salve"),
    "item_faerie_fire": ("consumable", "Faerie Fire"),
    "item_enchanted_mango": ("consumable", "Enchanted Mango"),
    "item_famango": ("consumable", "Enchanted Mango"),  # Alt name in replays
    "item_blood_grenade": ("consumable", "Blood Grenade"),
    "item_smoke_of_deceit": ("consumable", "Smoke of Deceit"),
    "item_ward_observer": ("consumable", "Observer Ward"),
    "item_ward_sentry": ("consumable", "Sentry Ward"),
    "item_dust": ("consumable", "Dust of Appearance"),
    "item_tome_of_knowledge": ("consumable", "Tome of Knowledge"),
    "item_aghanims_shard": ("consumable", "Aghanim's Shard"),
    "item_cheese": ("consumable", "Cheese"),
    "item_refresher_shard": ("consumable", "Refresher Shard"),
    "item_roshan_banner": ("consumable", "Roshan Banner"),
    "item_gem": ("consumable", "Gem of True Sight"),
    "item_courier": ("consumable", "Animal Courier"),
    "item_flying_courier": ("consumable", "Flying Courier"),
    "item_bottle": ("consumable", "Bottle"),
    "item_ward_dispenser": ("consumable", "Observer and Sentry Wards"),

    # === ATTRIBUTES ===
    "item_branches": ("attribute", "Iron Branch"),
    "item_ironwoodbranch": ("attribute", "Iron Branch"),  # Alt name
    "item_gauntlets": ("attribute", "Gauntlets of Strength"),
    "item_slippers": ("attribute", "Slippers of Agility"),
    "item_mantle": ("attribute", "Mantle of Intelligence"),
    "item_circlet": ("attribute", "Circlet"),
    "item_belt_of_strength": ("attribute", "Belt of Strength"),
    "item_boots_of_elves": ("attribute", "Band of Elvenskin"),
    "item_robe": ("attribute", "Robe of the Magi"),
    "item_ogre_axe": ("attribute", "Ogre Axe"),
    "item_blade_of_alacrity": ("attribute", "Blade of Alacrity"),
    "item_staff_of_wizardry": ("attribute", "Staff of Wizardry"),
    "item_crown": ("attribute", "Crown"),
    "item_diadem": ("attribute", "Diadem"),
    "item_tiara_of_selemene": ("attribute", "Tiara of Selemene"),

    # === EQUIPMENT ===
    "item_quelling_blade": ("equipment", "Quelling Blade"),
    "item_quellingblade": ("equipment", "Quelling Blade"),  # Alt name
    "item_blight_stone": ("equipment", "Blight Stone"),
    "item_orb_of_venom": ("equipment", "Orb of Venom"),
    "item_orb_of_corrosion": ("equipment", "Orb of Corrosion"),
    "item_ring_of_protection": ("equipment", "Ring of Protection"),
    "item_stout_shield": ("equipment", "Stout Shield"),
    "item_blades_of_attack": ("equipment", "Blades of Attack"),
    "item_chainmail": ("equipment", "Chainmail"),
    "item_quarterstaff": ("equipment", "Quarterstaff"),
    "item_helm_of_iron_will": ("equipment", "Helm of Iron Will"),
    "item_javelin": ("equipment", "Javelin"),
    "item_broadsword": ("equipment", "Broadsword"),
    "item_claymore": ("equipment", "Claymore"),
    "item_mithril_hammer": ("equipment", "Mithril Hammer"),

    # === BOOTS ===
    "item_boots": ("equipment", "Boots of Speed"),
    "item_power_treads": ("equipment", "Power Treads"),
    "item_phase_boots": ("equipment", "Phase Boots"),
    "item_arcane_boots": ("equipment", "Arcane Boots"),
    "item_tranquil_boots": ("equipment", "Tranquil Boots"),
    "item_guardian_greaves": ("equipment", "Guardian Greaves"),
    "item_travel_boots": ("equipment", "Boots of Travel"),
    "item_travel_boots_2": ("equipment", "Boots of Travel 2"),

    # === SECRET SHOP ===
    "item_ring_of_health": ("secret_shop", "Ring of Health"),
    "item_void_stone": ("secret_shop", "Void Stone"),
    "item_energy_booster": ("secret_shop", "Energy Booster"),
    "item_vitality_booster": ("secret_shop", "Vitality Booster"),
    "item_point_booster": ("secret_shop", "Point Booster"),
    "item_platemail": ("secret_shop", "Platemail"),
    "item_talisman_of_evasion": ("secret_shop", "Talisman of Evasion"),
    "item_ultimate_orb": ("secret_shop", "Ultimate Orb"),
    "item_hyperstone": ("secret_shop", "Hyperstone"),
    "item_demon_edge": ("secret_shop", "Demon Edge"),
    "item_mystic_staff": ("secret_shop", "Mystic Staff"),
    "item_reaver": ("secret_shop", "Reaver"),
    "item_eaglesong": ("secret_shop", "Eaglesong"),
    "item_relic": ("secret_shop", "Sacred Relic"),
    "item_cornucopia": ("secret_shop", "Cornucopia"),
    "item_blitz_knuckles": ("secret_shop", "Blitz Knuckles"),

    # === MAGICAL ===
    "item_magic_stick": ("magical", "Magic Stick"),
    "item_magicstick": ("magical", "Magic Stick"),  # Alt name
    "item_magic_wand": ("magical", "Magic Wand"),
    "item_null_talisman": ("magical", "Null Talisman"),
    "item_wraith_band": ("magical", "Wraith Band"),
    "item_bracer": ("magical", "Bracer"),
    "item_soul_ring": ("magical", "Soul Ring"),
    "item_ring_of_basilius": ("magical", "Ring of Basilius"),
    "item_headdress": ("magical", "Headdress"),
    "item_buckler": ("magical", "Buckler"),
    "item_urn_of_shadows": ("magical", "Urn of Shadows"),
    "item_spirit_vessel": ("magical", "Spirit Vessel"),
    "item_medallion_of_courage": ("magical", "Medallion of Courage"),
    "item_solar_crest": ("magical", "Solar Crest"),
    "item_ring_of_tarrasque": ("magical", "Ring of Tarrasque"),
    "item_infused_raindrop": ("magical", "Infused Raindrop"),
    "item_wind_lace": ("magical", "Wind Lace"),
    "item_cloak": ("magical", "Cloak"),
    "item_glimmer_cape": ("magical", "Glimmer Cape"),
    "item_ghost": ("magical", "Ghost Scepter"),
    "item_ethereal_blade": ("magical", "Ethereal Blade"),
    "item_veil_of_discord": ("magical", "Veil of Discord"),
    "item_aether_lens": ("magical", "Aether Lens"),
    "item_octarine_core": ("magical", "Octarine Core"),
    "item_rod_of_atos": ("magical", "Rod of Atos"),
    "item_gungir": ("magical", "Gleipnir"),
    "item_cyclone": ("magical", "Eul's Scepter of Divinity"),
    "item_wind_waker": ("magical", "Wind Waker"),
    "item_force_staff": ("magical", "Force Staff"),
    "item_hurricane_pike": ("magical", "Hurricane Pike"),
    "item_dagon": ("magical", "Dagon"),
    "item_dagon_2": ("magical", "Dagon 2"),
    "item_dagon_3": ("magical", "Dagon 3"),
    "item_dagon_4": ("magical", "Dagon 4"),
    "item_dagon_5": ("magical", "Dagon 5"),
    "item_necronomicon": ("magical", "Necronomicon"),
    "item_necronomicon_2": ("magical", "Necronomicon 2"),
    "item_necronomicon_3": ("magical", "Necronomicon 3"),
    "item_ultimate_scepter": ("magical", "Aghanim's Scepter"),
    "item_ultimate_scepter_2": ("magical", "Aghanim's Blessing"),
    "item_refresher": ("magical", "Refresher Orb"),
    "item_sheepstick": ("magical", "Scythe of Vyse"),
    "item_kaya": ("magical", "Kaya"),
    "item_yasha": ("magical", "Yasha"),
    "item_sange": ("magical", "Sange"),
    "item_kaya_and_sange": ("magical", "Kaya and Sange"),
    "item_yasha_and_kaya": ("magical", "Yasha and Kaya"),
    "item_sange_and_yasha": ("magical", "Sange and Yasha"),
    "item_phylactery": ("magical", "Phylactery"),
    "item_mage_slayer": ("magical", "Mage Slayer"),
    "item_witch_blade": ("magical", "Witch Blade"),
    "item_parasma": ("magical", "Parasma"),

    # === SUPPORT ===
    "item_mekansm": ("support", "Mekansm"),
    "item_pipe": ("support", "Pipe of Insight"),
    "item_holy_locket": ("support", "Holy Locket"),
    "item_vladmir": ("support", "Vladmir's Offering"),
    "item_crimson_guard": ("support", "Crimson Guard"),
    "item_lotus_orb": ("support", "Lotus Orb"),
    "item_solar_crest": ("support", "Solar Crest"),
    "item_ancient_janggo": ("support", "Drum of Endurance"),
    "item_boots_of_bearing": ("support", "Boots of Bearing"),
    "item_pavise": ("support", "Pavise"),
    "item_vanguard": ("support", "Vanguard"),
    "item_ring_of_regen": ("support", "Ring of Regen"),
    "item_sobi_mask": ("support", "Sage's Mask"),

    # === ARMOR ===
    "item_blade_mail": ("armor", "Blade Mail"),
    "item_assault": ("armor", "Assault Cuirass"),
    "item_shivas_guard": ("armor", "Shiva's Guard"),
    "item_heart": ("armor", "Heart of Tarrasque"),
    "item_eternal_shroud": ("armor", "Eternal Shroud"),
    "item_hood_of_defiance": ("armor", "Hood of Defiance"),
    "item_aeon_disk": ("armor", "Aeon Disk"),
    "item_sphere": ("armor", "Linken's Sphere"),
    "item_manta": ("armor", "Manta Style"),
    "item_black_king_bar": ("armor", "Black King Bar"),
    "item_platemail": ("armor", "Platemail"),
    "item_heavens_halberd": ("armor", "Heaven's Halberd"),
    "item_harpoon": ("armor", "Harpoon"),
    "item_lotus_orb": ("armor", "Lotus Orb"),

    # === WEAPONS ===
    "item_bfury": ("weapon", "Battle Fury"),
    "item_battlefury": ("weapon", "Battle Fury"),  # Alt name in replays
    "item_mask_of_madness": ("weapon", "Mask of Madness"),
    "item_moon_shard": ("weapon", "Moon Shard"),
    "item_greater_crit": ("weapon", "Daedalus"),
    "item_lesser_crit": ("weapon", "Crystalys"),
    "item_maelstrom": ("weapon", "Maelstrom"),
    "item_mjollnir": ("weapon", "Mjollnir"),
    "item_desolator": ("weapon", "Desolator"),
    "item_desolator_2": ("weapon", "Stygian Desolator"),
    "item_monkey_king_bar": ("weapon", "Monkey King Bar"),
    "item_diffusal_blade": ("weapon", "Diffusal Blade"),
    "item_basher": ("weapon", "Skull Basher"),
    "item_abyssal_blade": ("weapon", "Abyssal Blade"),
    "item_butterfly": ("weapon", "Butterfly"),
    "item_rapier": ("weapon", "Divine Rapier"),
    "item_radiance": ("weapon", "Radiance"),
    "item_armlet": ("weapon", "Armlet of Mordiggian"),
    "item_echo_sabre": ("weapon", "Echo Sabre"),
    "item_silver_edge": ("weapon", "Silver Edge"),
    "item_invis_sword": ("weapon", "Shadow Blade"),
    "item_nullifier": ("weapon", "Nullifier"),
    "item_bloodthorn": ("weapon", "Bloodthorn"),
    "item_orchid": ("weapon", "Orchid Malevolence"),
    "item_meteor_hammer": ("weapon", "Meteor Hammer"),
    "item_dragon_lance": ("weapon", "Dragon Lance"),
    "item_falcon_blade": ("weapon", "Falcon Blade"),
    "item_oblivion_staff": ("weapon", "Oblivion Staff"),
    "item_perseverance": ("weapon", "Perseverance"),
    "item_hand_of_midas": ("weapon", "Hand of Midas"),
    "item_aghs_shard": ("weapon", "Aghanim's Shard"),

    # === ARTIFACTS ===
    "item_blink": ("artifact", "Blink Dagger"),
    "item_overwhelming_blink": ("artifact", "Overwhelming Blink"),
    "item_swift_blink": ("artifact", "Swift Blink"),
    "item_arcane_blink": ("artifact", "Arcane Blink"),
    "item_satanic": ("artifact", "Satanic"),
    "item_skadi": ("artifact", "Eye of Skadi"),
    "item_disperser": ("artifact", "Disperser"),
    "item_bloodstone": ("artifact", "Bloodstone"),
    "item_khanda": ("artifact", "Khanda"),
    "item_angels_demise": ("artifact", "Revenant's Brooch"),
    "item_revenants_brooch": ("artifact", "Revenant's Brooch"),
    "item_devastator": ("artifact", "Devastator"),
    "item_samurai_tabi": ("artifact", "Samurai Tabi"),

    # === ACCESSORIES ===
    "item_teleportscroll": ("accessory", "Town Portal Scroll"),
    "item_tpscroll": ("accessory", "Town Portal Scroll"),  # Alt name
    "item_lifesteal": ("accessory", "Morbid Mask"),
    "item_mask_of_death": ("accessory", "Morbid Mask"),  # Alt name
    "item_helm_of_the_dominator": ("accessory", "Helm of the Dominator"),
    "item_helm_of_the_overlord": ("accessory", "Helm of the Overlord"),
    "item_soul_booster": ("accessory", "Soul Booster"),
    "item_voodoo_mask": ("accessory", "Voodoo Mask"),
    "item_fluffy_hat": ("accessory", "Fluffy Hat"),

    # === RECIPES ===
    "item_recipe_magic_wand": ("recipe", "Magic Wand Recipe"),
    "item_recipe_null_talisman": ("recipe", "Null Talisman Recipe"),
    "item_recipe_wraith_band": ("recipe", "Wraith Band Recipe"),
    "item_recipe_bracer": ("recipe", "Bracer Recipe"),
    "item_recipe_soul_ring": ("recipe", "Soul Ring Recipe"),
    "item_recipe_phase_boots": ("recipe", "Phase Boots Recipe"),
    "item_recipe_power_treads": ("recipe", "Power Treads Recipe"),
    "item_recipe_hand_of_midas": ("recipe", "Hand of Midas Recipe"),
    "item_recipe_mekansm": ("recipe", "Mekansm Recipe"),
    "item_recipe_vladmir": ("recipe", "Vladmir's Offering Recipe"),
    "item_recipe_buckler": ("recipe", "Buckler Recipe"),
    "item_recipe_ring_of_basilius": ("recipe", "Ring of Basilius Recipe"),
    "item_recipe_pipe": ("recipe", "Pipe of Insight Recipe"),
    "item_recipe_urn_of_shadows": ("recipe", "Urn of Shadows Recipe"),
    "item_recipe_headdress": ("recipe", "Headdress Recipe"),
    "item_recipe_sheepstick": ("recipe", "Scythe of Vyse Recipe"),
    "item_recipe_orchid": ("recipe", "Orchid Malevolence Recipe"),
    "item_recipe_cyclone": ("recipe", "Eul's Scepter Recipe"),
    "item_recipe_force_staff": ("recipe", "Force Staff Recipe"),
    "item_recipe_dagon": ("recipe", "Dagon Recipe"),
    "item_recipe_dagon_2": ("recipe", "Dagon 2 Recipe"),
    "item_recipe_dagon_3": ("recipe", "Dagon 3 Recipe"),
    "item_recipe_dagon_4": ("recipe", "Dagon 4 Recipe"),
    "item_recipe_dagon_5": ("recipe", "Dagon 5 Recipe"),
    "item_recipe_necronomicon": ("recipe", "Necronomicon Recipe"),
    "item_recipe_necronomicon_2": ("recipe", "Necronomicon 2 Recipe"),
    "item_recipe_necronomicon_3": ("recipe", "Necronomicon 3 Recipe"),
    "item_recipe_ultimate_scepter": ("recipe", "Aghanim's Scepter Recipe"),
    "item_recipe_refresher": ("recipe", "Refresher Orb Recipe"),
    "item_recipe_assault": ("recipe", "Assault Cuirass Recipe"),
    "item_recipe_heart": ("recipe", "Heart of Tarrasque Recipe"),
    "item_recipe_black_king_bar": ("recipe", "Black King Bar Recipe"),
    "item_recipe_shivas_guard": ("recipe", "Shiva's Guard Recipe"),
    "item_recipe_bloodstone": ("recipe", "Bloodstone Recipe"),
    "item_recipe_sphere": ("recipe", "Linken's Sphere Recipe"),
    "item_recipe_vanguard": ("recipe", "Vanguard Recipe"),
    "item_recipe_crimson_guard": ("recipe", "Crimson Guard Recipe"),
    "item_recipe_blade_mail": ("recipe", "Blade Mail Recipe"),
    "item_recipe_hood_of_defiance": ("recipe", "Hood of Defiance Recipe"),
    "item_recipe_manta": ("recipe", "Manta Style Recipe"),
    "item_recipe_diffusal_blade": ("recipe", "Diffusal Blade Recipe"),
    "item_recipe_basher": ("recipe", "Skull Basher Recipe"),
    "item_recipe_bfury": ("recipe", "Battle Fury Recipe"),
    "item_recipe_butterfly": ("recipe", "Butterfly Recipe"),
    "item_recipe_greater_crit": ("recipe", "Daedalus Recipe"),
    "item_recipe_armlet": ("recipe", "Armlet Recipe"),
    "item_recipe_invis_sword": ("recipe", "Shadow Blade Recipe"),
    "item_recipe_silver_edge": ("recipe", "Silver Edge Recipe"),
    "item_recipe_desolator": ("recipe", "Desolator Recipe"),
    "item_recipe_mask_of_madness": ("recipe", "Mask of Madness Recipe"),
    "item_recipe_satanic": ("recipe", "Satanic Recipe"),
    "item_recipe_mjollnir": ("recipe", "Mjollnir Recipe"),
    "item_recipe_maelstrom": ("recipe", "Maelstrom Recipe"),
    "item_recipe_skadi": ("recipe", "Eye of Skadi Recipe"),
    "item_recipe_sange": ("recipe", "Sange Recipe"),
    "item_recipe_yasha": ("recipe", "Yasha Recipe"),
    "item_recipe_kaya": ("recipe", "Kaya Recipe"),
    "item_recipe_radiance": ("recipe", "Radiance Recipe"),
    "item_recipe_travel_boots": ("recipe", "Boots of Travel Recipe"),
    "item_recipe_travel_boots_2": ("recipe", "Boots of Travel 2 Recipe"),
    "item_recipe_ancient_janggo": ("recipe", "Drum of Endurance Recipe"),
    "item_recipe_medallion_of_courage": ("recipe", "Medallion of Courage Recipe"),
    "item_recipe_solar_crest": ("recipe", "Solar Crest Recipe"),
    "item_recipe_glimmer_cape": ("recipe", "Glimmer Cape Recipe"),
    "item_recipe_aether_lens": ("recipe", "Aether Lens Recipe"),
    "item_recipe_octarine_core": ("recipe", "Octarine Core Recipe"),
    "item_recipe_dragon_lance": ("recipe", "Dragon Lance Recipe"),
    "item_recipe_echo_sabre": ("recipe", "Echo Sabre Recipe"),
    "item_recipe_lotus_orb": ("recipe", "Lotus Orb Recipe"),
    "item_recipe_meteor_hammer": ("recipe", "Meteor Hammer Recipe"),
    "item_recipe_nullifier": ("recipe", "Nullifier Recipe"),
    "item_recipe_aeon_disk": ("recipe", "Aeon Disk Recipe"),
    "item_recipe_spirit_vessel": ("recipe", "Spirit Vessel Recipe"),
    "item_recipe_holy_locket": ("recipe", "Holy Locket Recipe"),
    "item_recipe_guardian_greaves": ("recipe", "Guardian Greaves Recipe"),
    "item_recipe_rod_of_atos": ("recipe", "Rod of Atos Recipe"),
    "item_recipe_abyssal_blade": ("recipe", "Abyssal Blade Recipe"),
    "item_recipe_bloodthorn": ("recipe", "Bloodthorn Recipe"),
    "item_recipe_hurricane_pike": ("recipe", "Hurricane Pike Recipe"),
    "item_recipe_monkey_king_bar": ("recipe", "Monkey King Bar Recipe"),
    "item_recipe_helm_of_the_dominator": ("recipe", "Helm of the Dominator Recipe"),
    "item_recipe_helm_of_the_overlord": ("recipe", "Helm of the Overlord Recipe"),
    "item_recipe_tranquil_boots": ("recipe", "Tranquil Boots Recipe"),
    "item_recipe_ethereal_blade": ("recipe", "Ethereal Blade Recipe"),
    "item_recipe_veil_of_discord": ("recipe", "Veil of Discord Recipe"),
    "item_recipe_boots_of_bearing": ("recipe", "Boots of Bearing Recipe"),
    "item_recipe_wind_waker": ("recipe", "Wind Waker Recipe"),
    "item_recipe_eternal_shroud": ("recipe", "Eternal Shroud Recipe"),
    "item_recipe_gungir": ("recipe", "Gleipnir Recipe"),
    "item_recipe_overwhelming_blink": ("recipe", "Overwhelming Blink Recipe"),
    "item_recipe_swift_blink": ("recipe", "Swift Blink Recipe"),
    "item_recipe_arcane_blink": ("recipe", "Arcane Blink Recipe"),
    "item_recipe_witch_blade": ("recipe", "Witch Blade Recipe"),
    "item_recipe_falcon_blade": ("recipe", "Falcon Blade Recipe"),
    "item_recipe_orb_of_corrosion": ("recipe", "Orb of Corrosion Recipe"),
    "item_recipe_mage_slayer": ("recipe", "Mage Slayer Recipe"),
    "item_recipe_harpoon": ("recipe", "Harpoon Recipe"),
    "item_recipe_pavise": ("recipe", "Pavise Recipe"),
    "item_recipe_phylactery": ("recipe", "Phylactery Recipe"),
    "item_recipe_disperser": ("recipe", "Disperser Recipe"),
    "item_recipe_heavens_halberd": ("recipe", "Heaven's Halberd Recipe"),
    "item_recipe_khanda": ("recipe", "Khanda Recipe"),
    "item_recipe_parasma": ("recipe", "Parasma Recipe"),
}

# Alias mapping: alternate internal names -> canonical names
_ITEM_ALIASES: Dict[str, str] = {
    "item_famango": "item_enchanted_mango",
    "item_ironwoodbranch": "item_branches",
    "item_quellingblade": "item_quelling_blade",
    "item_magicstick": "item_magic_stick",
    "item_tpscroll": "item_teleportscroll",
    "item_mask_of_death": "item_lifesteal",
    "item_battlefury": "item_bfury",
    "item_angels_demise": "item_revenants_brooch",
}


class Item(str, Enum):
    """All Dota 2 purchasable items.

    Usage:
        # Get item from internal name
        item = Item.from_item_name("item_blink")
        print(f"Item: {item.display_name}")  # "Blink Dagger"

        # Check if an item name is a known purchasable item
        if Item.is_purchasable_item("item_butterfly"):
            item = Item.from_item_name("item_butterfly")
            print(f"Category: {item.category}")  # "weapon"

        # Get all items in a category
        weapons = Item.items_by_category("weapon")
    """
    # === CONSUMABLES ===
    CLARITY = "item_clarity"
    TANGO = "item_tango"
    TANGO_SINGLE = "item_tango_single"
    HEALING_SALVE = "item_flask"
    FAERIE_FIRE = "item_faerie_fire"
    ENCHANTED_MANGO = "item_enchanted_mango"
    BLOOD_GRENADE = "item_blood_grenade"
    SMOKE_OF_DECEIT = "item_smoke_of_deceit"
    OBSERVER_WARD = "item_ward_observer"
    SENTRY_WARD = "item_ward_sentry"
    DUST = "item_dust"
    TOME_OF_KNOWLEDGE = "item_tome_of_knowledge"
    AGHANIMS_SHARD = "item_aghanims_shard"
    CHEESE = "item_cheese"
    REFRESHER_SHARD = "item_refresher_shard"
    ROSHAN_BANNER = "item_roshan_banner"
    GEM = "item_gem"
    COURIER = "item_courier"
    FLYING_COURIER = "item_flying_courier"
    BOTTLE = "item_bottle"
    WARD_DISPENSER = "item_ward_dispenser"

    # === ATTRIBUTES ===
    IRON_BRANCH = "item_branches"
    GAUNTLETS = "item_gauntlets"
    SLIPPERS = "item_slippers"
    MANTLE = "item_mantle"
    CIRCLET = "item_circlet"
    BELT_OF_STRENGTH = "item_belt_of_strength"
    BAND_OF_ELVENSKIN = "item_boots_of_elves"
    ROBE_OF_THE_MAGI = "item_robe"
    OGRE_AXE = "item_ogre_axe"
    BLADE_OF_ALACRITY = "item_blade_of_alacrity"
    STAFF_OF_WIZARDRY = "item_staff_of_wizardry"
    CROWN = "item_crown"
    DIADEM = "item_diadem"
    TIARA_OF_SELEMENE = "item_tiara_of_selemene"

    # === EQUIPMENT ===
    QUELLING_BLADE = "item_quelling_blade"
    BLIGHT_STONE = "item_blight_stone"
    ORB_OF_VENOM = "item_orb_of_venom"
    ORB_OF_CORROSION = "item_orb_of_corrosion"
    RING_OF_PROTECTION = "item_ring_of_protection"
    STOUT_SHIELD = "item_stout_shield"
    BLADES_OF_ATTACK = "item_blades_of_attack"
    CHAINMAIL = "item_chainmail"
    QUARTERSTAFF = "item_quarterstaff"
    HELM_OF_IRON_WILL = "item_helm_of_iron_will"
    JAVELIN = "item_javelin"
    BROADSWORD = "item_broadsword"
    CLAYMORE = "item_claymore"
    MITHRIL_HAMMER = "item_mithril_hammer"

    # === BOOTS ===
    BOOTS = "item_boots"
    POWER_TREADS = "item_power_treads"
    PHASE_BOOTS = "item_phase_boots"
    ARCANE_BOOTS = "item_arcane_boots"
    TRANQUIL_BOOTS = "item_tranquil_boots"
    GUARDIAN_GREAVES = "item_guardian_greaves"
    BOOTS_OF_TRAVEL = "item_travel_boots"
    BOOTS_OF_TRAVEL_2 = "item_travel_boots_2"

    # === SECRET SHOP ===
    RING_OF_HEALTH = "item_ring_of_health"
    VOID_STONE = "item_void_stone"
    ENERGY_BOOSTER = "item_energy_booster"
    VITALITY_BOOSTER = "item_vitality_booster"
    POINT_BOOSTER = "item_point_booster"
    PLATEMAIL = "item_platemail"
    TALISMAN_OF_EVASION = "item_talisman_of_evasion"
    ULTIMATE_ORB = "item_ultimate_orb"
    HYPERSTONE = "item_hyperstone"
    DEMON_EDGE = "item_demon_edge"
    MYSTIC_STAFF = "item_mystic_staff"
    REAVER = "item_reaver"
    EAGLESONG = "item_eaglesong"
    SACRED_RELIC = "item_relic"
    CORNUCOPIA = "item_cornucopia"
    BLITZ_KNUCKLES = "item_blitz_knuckles"

    # === MAGICAL ===
    MAGIC_STICK = "item_magic_stick"
    MAGIC_WAND = "item_magic_wand"
    NULL_TALISMAN = "item_null_talisman"
    WRAITH_BAND = "item_wraith_band"
    BRACER = "item_bracer"
    SOUL_RING = "item_soul_ring"
    RING_OF_BASILIUS = "item_ring_of_basilius"
    HEADDRESS = "item_headdress"
    BUCKLER = "item_buckler"
    URN_OF_SHADOWS = "item_urn_of_shadows"
    SPIRIT_VESSEL = "item_spirit_vessel"
    MEDALLION_OF_COURAGE = "item_medallion_of_courage"
    SOLAR_CREST = "item_solar_crest"
    RING_OF_TARRASQUE = "item_ring_of_tarrasque"
    INFUSED_RAINDROP = "item_infused_raindrop"
    WIND_LACE = "item_wind_lace"
    CLOAK = "item_cloak"
    GLIMMER_CAPE = "item_glimmer_cape"
    GHOST_SCEPTER = "item_ghost"
    ETHEREAL_BLADE = "item_ethereal_blade"
    VEIL_OF_DISCORD = "item_veil_of_discord"
    AETHER_LENS = "item_aether_lens"
    OCTARINE_CORE = "item_octarine_core"
    ROD_OF_ATOS = "item_rod_of_atos"
    GLEIPNIR = "item_gungir"
    EULS_SCEPTER = "item_cyclone"
    WIND_WAKER = "item_wind_waker"
    FORCE_STAFF = "item_force_staff"
    HURRICANE_PIKE = "item_hurricane_pike"
    DAGON = "item_dagon"
    DAGON_2 = "item_dagon_2"
    DAGON_3 = "item_dagon_3"
    DAGON_4 = "item_dagon_4"
    DAGON_5 = "item_dagon_5"
    NECRONOMICON = "item_necronomicon"
    NECRONOMICON_2 = "item_necronomicon_2"
    NECRONOMICON_3 = "item_necronomicon_3"
    AGHANIMS_SCEPTER = "item_ultimate_scepter"
    AGHANIMS_BLESSING = "item_ultimate_scepter_2"
    REFRESHER_ORB = "item_refresher"
    SCYTHE_OF_VYSE = "item_sheepstick"
    KAYA = "item_kaya"
    YASHA = "item_yasha"
    SANGE = "item_sange"
    KAYA_AND_SANGE = "item_kaya_and_sange"
    YASHA_AND_KAYA = "item_yasha_and_kaya"
    SANGE_AND_YASHA = "item_sange_and_yasha"
    PHYLACTERY = "item_phylactery"
    MAGE_SLAYER = "item_mage_slayer"
    WITCH_BLADE = "item_witch_blade"
    PARASMA = "item_parasma"

    # === SUPPORT ===
    MEKANSM = "item_mekansm"
    PIPE = "item_pipe"
    HOLY_LOCKET = "item_holy_locket"
    VLADMIRS = "item_vladmir"
    CRIMSON_GUARD = "item_crimson_guard"
    LOTUS_ORB = "item_lotus_orb"
    DRUM_OF_ENDURANCE = "item_ancient_janggo"
    BOOTS_OF_BEARING = "item_boots_of_bearing"
    PAVISE = "item_pavise"
    VANGUARD = "item_vanguard"
    RING_OF_REGEN = "item_ring_of_regen"
    SAGES_MASK = "item_sobi_mask"

    # === ARMOR ===
    BLADE_MAIL = "item_blade_mail"
    ASSAULT_CUIRASS = "item_assault"
    SHIVAS_GUARD = "item_shivas_guard"
    HEART = "item_heart"
    ETERNAL_SHROUD = "item_eternal_shroud"
    HOOD_OF_DEFIANCE = "item_hood_of_defiance"
    AEON_DISK = "item_aeon_disk"
    LINKENS_SPHERE = "item_sphere"
    MANTA_STYLE = "item_manta"
    BLACK_KING_BAR = "item_black_king_bar"
    HEAVENS_HALBERD = "item_heavens_halberd"
    HARPOON = "item_harpoon"

    # === WEAPONS ===
    BATTLE_FURY = "item_bfury"
    MASK_OF_MADNESS = "item_mask_of_madness"
    MOON_SHARD = "item_moon_shard"
    DAEDALUS = "item_greater_crit"
    CRYSTALYS = "item_lesser_crit"
    MAELSTROM = "item_maelstrom"
    MJOLLNIR = "item_mjollnir"
    DESOLATOR = "item_desolator"
    STYGIAN_DESOLATOR = "item_desolator_2"
    MONKEY_KING_BAR = "item_monkey_king_bar"
    DIFFUSAL_BLADE = "item_diffusal_blade"
    SKULL_BASHER = "item_basher"
    ABYSSAL_BLADE = "item_abyssal_blade"
    BUTTERFLY = "item_butterfly"
    DIVINE_RAPIER = "item_rapier"
    RADIANCE = "item_radiance"
    ARMLET = "item_armlet"
    ECHO_SABRE = "item_echo_sabre"
    SILVER_EDGE = "item_silver_edge"
    SHADOW_BLADE = "item_invis_sword"
    NULLIFIER = "item_nullifier"
    BLOODTHORN = "item_bloodthorn"
    ORCHID = "item_orchid"
    METEOR_HAMMER = "item_meteor_hammer"
    DRAGON_LANCE = "item_dragon_lance"
    FALCON_BLADE = "item_falcon_blade"
    OBLIVION_STAFF = "item_oblivion_staff"
    PERSEVERANCE = "item_perseverance"
    HAND_OF_MIDAS = "item_hand_of_midas"

    # === ARTIFACTS ===
    BLINK_DAGGER = "item_blink"
    OVERWHELMING_BLINK = "item_overwhelming_blink"
    SWIFT_BLINK = "item_swift_blink"
    ARCANE_BLINK = "item_arcane_blink"
    SATANIC = "item_satanic"
    EYE_OF_SKADI = "item_skadi"
    DISPERSER = "item_disperser"
    BLOODSTONE = "item_bloodstone"
    KHANDA = "item_khanda"
    REVENANTS_BROOCH = "item_revenants_brooch"
    DEVASTATOR = "item_devastator"
    SAMURAI_TABI = "item_samurai_tabi"

    # === ACCESSORIES ===
    TP_SCROLL = "item_teleportscroll"
    MORBID_MASK = "item_lifesteal"
    HELM_OF_THE_DOMINATOR = "item_helm_of_the_dominator"
    HELM_OF_THE_OVERLORD = "item_helm_of_the_overlord"
    SOUL_BOOSTER = "item_soul_booster"
    VOODOO_MASK = "item_voodoo_mask"
    FLUFFY_HAT = "item_fluffy_hat"

    @property
    def item_name(self) -> str:
        """Internal item name (e.g., 'item_blink')."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable item name."""
        data = _ITEMS_DATA.get(self.value)
        return data[1] if data else self.name.replace("_", " ").title()

    @property
    def category(self) -> Optional[str]:
        """Item category (consumable, weapon, armor, etc.)."""
        data = _ITEMS_DATA.get(self.value)
        return data[0] if data else None

    @classmethod
    def from_item_name(cls, item_name: str) -> Optional["Item"]:
        """Get Item from internal item name (handles aliases)."""
        # Resolve alias to canonical name
        canonical = _ITEM_ALIASES.get(item_name, item_name)
        for item in cls:
            if item.value == canonical:
                return item
        return None

    @classmethod
    def is_purchasable_item(cls, item_name: str) -> bool:
        """Check if an item name is a purchasable item (handles aliases)."""
        canonical = _ITEM_ALIASES.get(item_name, item_name)
        return canonical in _ITEMS_DATA or item_name in _ITEMS_DATA

    @classmethod
    def items_by_category(cls, category: str) -> List["Item"]:
        """Get all items of a specific category."""
        return [
            item for item in cls
            if _ITEMS_DATA.get(item.value, (None,))[0] == category
        ]

    @classmethod
    def all_item_names(cls) -> List[str]:
        """Get all purchasable item internal names."""
        return list(_ITEMS_DATA.keys())


class NeutralItemTier(int, Enum):
    """Neutral item tier classification.

    Tiers unlock at specific game times:
    - Tier 1: 5:00 (was 7:00 before 7.39d)
    - Tier 2: 15:00 (was 17:00)
    - Tier 3: 25:00 (was 27:00)
    - Tier 4: 35:00 (was 37:00)
    - Tier 5: 55:00 (was 60:00)
    """
    TIER_1 = 0
    TIER_2 = 1
    TIER_3 = 2
    TIER_4 = 3
    TIER_5 = 4

    @property
    def display_name(self) -> str:
        """Human-readable tier name."""
        return f"Tier {self.value + 1}"

    @property
    def unlock_time_minutes(self) -> int:
        """Game time in minutes when this tier unlocks (patch 7.39d+)."""
        times = {0: 5, 1: 15, 2: 25, 3: 35, 4: 55}
        return times[self.value]

    @classmethod
    def from_value(cls, value: int) -> Optional["NeutralItemTier"]:
        """Get NeutralItemTier from integer value (0-4)."""
        for t in cls:
            if t.value == value:
                return t
        return None


# All neutral items with their internal names and tiers
# Includes both active items and retired/rotated items from previous patches
_NEUTRAL_ITEMS_DATA = {
    # === TIER 1 (Current 7.38+) ===
    "item_chipped_vest": (0, "Chipped Vest"),
    "item_dormant_curio": (0, "Dormant Curio"),
    "item_kobold_cup": (0, "Kobold Cup"),
    "item_occult_bracelet": (0, "Occult Bracelet"),
    "item_pollywog_charm": (0, "Pollywog Charm"),
    "item_rippers_lash": (0, "Ripper's Lash"),
    "item_sisters_shroud": (0, "Sister's Shroud"),
    "item_spark_of_courage": (0, "Spark of Courage"),
    # Tier 1 - Retired/Rotated
    "item_arcane_ring": (0, "Arcane Ring"),
    "item_broom_handle": (0, "Broom Handle"),
    "item_duelist_gloves": (0, "Duelist Gloves"),
    "item_faded_broach": (0, "Faded Broach"),
    "item_fairys_trinket": (0, "Fairy's Trinket"),
    "item_ironwood_tree": (0, "Ironwood Tree"),
    "item_keen_optic": (0, "Keen Optic"),
    "item_lance_of_pursuit": (0, "Lance of Pursuit"),
    "item_mango_tree": (0, "Mango Tree"),
    "item_ocean_heart": (0, "Ocean Heart"),
    "item_pig_pole": (0, "Pig Pole"),
    "item_possessed_mask": (0, "Possessed Mask"),
    "item_royal_jelly": (0, "Royal Jelly"),
    "item_safety_bubble": (0, "Safety Bubble"),
    "item_seeds_of_serenity": (0, "Seeds of Serenity"),
    "item_trusty_shovel": (0, "Trusty Shovel"),

    # === TIER 2 (Current 7.38+) ===
    "item_brigands_blade": (1, "Brigand's Blade"),
    "item_essence_ring": (1, "Essence Ring"),
    "item_mana_draught": (1, "Mana Draught"),
    "item_poor_mans_shield": (1, "Poor Man's Shield"),
    "item_poormansshield": (1, "Poor Man's Shield"),  # Alt name in replays
    "item_searing_signet": (1, "Searing Signet"),
    "item_tumblers_toy": (1, "Tumbler's Toy"),
    # Tier 2 - Retired/Rotated
    "item_bullwhip": (1, "Bullwhip"),
    "item_clumsy_net": (1, "Clumsy Net"),
    "item_dagger_of_ristul": (1, "Dagger of Ristul"),
    "item_dragon_scale": (1, "Dragon Scale"),
    "item_eye_of_the_vizier": (1, "Eye of the Vizier"),
    "item_fae_grenade": (1, "Fae Grenade"),
    "item_gossamer_cape": (1, "Gossamer Cape"),
    "item_grove_bow": (1, "Grove Bow"),
    "item_imp_claw": (1, "Imp Claw"),
    "item_iron_talon": (1, "Iron Talon"),
    "item_light_collector": (1, "Light Collector"),
    "item_nether_shawl": (1, "Nether Shawl"),
    "item_orb_of_destruction": (1, "Orb of Destruction"),
    "item_philosophers_stone": (1, "Philosopher's Stone"),
    "item_pupils_gift": (1, "Pupil's Gift"),
    "item_quicksilver_amulet": (1, "Quicksilver Amulet"),
    "item_ring_of_aquila": (1, "Ring of Aquila"),
    "item_specialists_array": (1, "Specialist's Array"),
    "item_vambrace": (1, "Vambrace"),
    "item_vampire_fangs": (1, "Vampire Fangs"),

    # === TIER 3 (Current 7.38+) ===
    "item_gale_guard": (2, "Gale Guard"),
    "item_gunpowder_gauntlet": (2, "Gunpowder Gauntlet"),
    "item_jidi_pollen_bag": (2, "Jidi Pollen Bag"),
    "item_psychic_headband": (2, "Psychic Headband"),
    "item_serrated_shiv": (2, "Serrated Shiv"),
    "item_whisper_of_the_dread": (2, "Whisper of the Dread"),
    # Tier 3 - Retired/Rotated
    "item_ceremonial_robe": (2, "Ceremonial Robe"),
    "item_cloak_of_flames": (2, "Cloak of Flames"),
    "item_craggy_coat": (2, "Craggy Coat"),
    "item_dandelion_amulet": (2, "Dandelion Amulet"),
    "item_defiant_shell": (2, "Defiant Shell"),
    "item_doubloon": (2, "Doubloon"),
    "item_elven_tunic": (2, "Elven Tunic"),
    "item_enchanted_quiver": (2, "Enchanted Quiver"),
    "item_nemesis_curse": (2, "Nemesis Curse"),
    "item_ogre_seal_totem": (2, "Ogre Seal Totem"),
    "item_paladin_sword": (2, "Paladin Sword"),
    "item_quickening_charm": (2, "Quickening Charm"),
    "item_spider_legs": (2, "Spider Legs"),
    "item_titan_sliver": (2, "Titan Sliver"),
    "item_tome_of_aghanim": (2, "Tome of Aghanim"),
    "item_vindicators_axe": (2, "Vindicator's Axe"),

    # === TIER 4 (Current 7.38+) ===
    "item_crippling_crossbow": (3, "Crippling Crossbow"),
    "item_dezun_bloodrite": (3, "Dezun Bloodrite"),
    "item_giants_maul": (3, "Giant's Maul"),
    "item_magnifying_monocle": (3, "Magnifying Monocle"),
    "item_outworld_staff": (3, "Outworld Staff"),
    "item_pyrrhic_cloak": (3, "Pyrrhic Cloak"),
    # Tier 4 - Retired/Rotated
    "item_ancient_guardian": (3, "Ancient Guardian"),
    "item_ascetics_cap": (3, "Ascetic's Cap"),
    "item_avianas_feather": (3, "Aviana's Feather"),
    "item_flicker": (3, "Flicker"),
    "item_havoc_hammer": (3, "Havoc Hammer"),
    "item_illusionists_cape": (3, "Illusionist's Cape"),
    "item_martyrs_plate": (3, "Martyr's Plate"),
    "item_mind_breaker": (3, "Mind Breaker"),
    "item_ninja_gear": (3, "Ninja Gear"),
    "item_penta_edged_sword": (3, "Penta-edged Sword"),
    "item_princes_knife": (3, "Prince's Knife"),
    "item_rattlecage": (3, "Rattlecage"),
    "item_spell_prism": (3, "Spell Prism"),
    "item_stormcrafter": (3, "Stormcrafter"),
    "item_telescope": (3, "Telescope"),
    "item_timeless_relic": (3, "Timeless Relic"),
    "item_trickster_cloak": (3, "Trickster Cloak"),
    "item_witchbane": (3, "Witchbane"),

    # === TIER 5 (Current 7.38+) ===
    "item_book_of_the_dead": (4, "Book of the Dead"),
    "item_divine_regalia": (4, "Divine Regalia"),
    "item_fallen_sky": (4, "Fallen Sky"),
    "item_helm_of_the_undying": (4, "Helm of the Undying"),
    "item_minotaur_horn": (4, "Minotaur Horn"),
    "item_spider_legs_tier5": (4, "Spider Legs"),
    "item_stygian_desolator": (4, "Stygian Desolator"),
    "item_unrelenting_eye": (4, "Unrelenting Eye"),
    # Tier 5 - Retired/Rotated
    "item_apex": (4, "Apex"),
    "item_arcanists_armor": (4, "Arcanist's Armor"),
    "item_ballista": (4, "Ballista"),
    "item_book_of_shadows": (4, "Book of Shadows"),
    "item_demonicon": (4, "Demonicon"),
    "item_ex_machina": (4, "Ex Machina"),
    "item_force_boots": (4, "Force Boots"),
    "item_fusion_rune": (4, "Fusion Rune"),
    "item_giants_ring": (4, "Giant's Ring"),
    "item_magic_lamp": (4, "Magic Lamp"),
    "item_mirror_shield": (4, "Mirror Shield"),
    "item_phoenix_ash": (4, "Phoenix Ash"),
    "item_pirate_hat": (4, "Pirate Hat"),
    "item_seer_stone": (4, "Seer Stone"),
    "item_the_leveller": (4, "The Leveller"),
    "item_trident": (4, "Trident"),
    "item_unwavering_condition": (4, "Unwavering Condition"),
    "item_witless_shako": (4, "Witless Shako"),
    "item_woodland_striders": (4, "Woodland Striders"),

    # === SPECIAL / CRAFTING SYSTEM ===
    "item_madstone_bundle": (None, "Madstone Bundle"),  # Crafting currency
}

# Neutral item alias mapping: alternate internal names -> canonical names
_NEUTRAL_ITEM_ALIASES: Dict[str, str] = {
    "item_poormansshield": "item_poor_mans_shield",
    "item_ripperslash": "item_rippers_lash",
}


class NeutralItem(str, Enum):
    """All Dota 2 neutral items (active and retired).

    Usage:
        # Check if an item is a neutral item
        if NeutralItem.is_neutral_item(entry.inflictor_name):
            item = NeutralItem.from_item_name(entry.inflictor_name)
            print(f"Neutral item: {item.display_name} (Tier {item.tier + 1})")

        # Get all tier 1 items
        tier1 = NeutralItem.items_by_tier(0)
    """
    # Tier 1 - Current (7.40)
    ASH_LEGION_SHIELD = "item_ash_legion_shield"  # New in 7.40
    CHIPPED_VEST = "item_chipped_vest"
    DORMANT_CURIO = "item_dormant_curio"
    DUELIST_GLOVES = "item_duelist_gloves"  # Returned in 7.40
    KOBOLD_CUP = "item_kobold_cup"
    OCCULT_BRACELET = "item_occult_bracelet"
    POLLYWOG_CHARM = "item_pollywog_charm"
    WEIGHTED_DICE = "item_weighted_dice"  # New in 7.40
    # Tier 1 - Retired/Cycled out
    ARCANE_RING = "item_arcane_ring"
    BROOM_HANDLE = "item_broom_handle"
    RIPPERS_LASH = "item_rippers_lash"  # Cycled out in 7.40
    SISTERS_SHROUD = "item_sisters_shroud"  # Cycled out in 7.40
    SPARK_OF_COURAGE = "item_spark_of_courage"  # Cycled out in 7.40
    FADED_BROACH = "item_faded_broach"
    FAIRYS_TRINKET = "item_fairys_trinket"
    IRONWOOD_TREE = "item_ironwood_tree"
    KEEN_OPTIC = "item_keen_optic"
    LANCE_OF_PURSUIT = "item_lance_of_pursuit"
    MANGO_TREE = "item_mango_tree"
    OCEAN_HEART = "item_ocean_heart"
    PIG_POLE = "item_pig_pole"
    POSSESSED_MASK = "item_possessed_mask"
    ROYAL_JELLY = "item_royal_jelly"
    SAFETY_BUBBLE = "item_safety_bubble"
    SEEDS_OF_SERENITY = "item_seeds_of_serenity"
    TRUSTY_SHOVEL = "item_trusty_shovel"

    # Tier 2 - Current (7.40)
    DEFIANT_SHELL = "item_defiant_shell"  # Returned in 7.40
    ESSENCE_RING = "item_essence_ring"
    MANA_DRAUGHT = "item_mana_draught"
    POOR_MANS_SHIELD = "item_poor_mans_shield"
    SEARING_SIGNET = "item_searing_signet"
    TUMBLERS_TOY = "item_tumblers_toy"
    # Tier 2 - Retired/Cycled out
    BRIGANDS_BLADE = "item_brigands_blade"  # Cycled out in 7.40
    BULLWHIP = "item_bullwhip"
    CLUMSY_NET = "item_clumsy_net"
    DAGGER_OF_RISTUL = "item_dagger_of_ristul"
    DRAGON_SCALE = "item_dragon_scale"
    EYE_OF_THE_VIZIER = "item_eye_of_the_vizier"
    FAE_GRENADE = "item_fae_grenade"
    GOSSAMER_CAPE = "item_gossamer_cape"
    GROVE_BOW = "item_grove_bow"
    IMP_CLAW = "item_imp_claw"
    IRON_TALON = "item_iron_talon"
    LIGHT_COLLECTOR = "item_light_collector"
    NETHER_SHAWL = "item_nether_shawl"
    ORB_OF_DESTRUCTION = "item_orb_of_destruction"
    PHILOSOPHERS_STONE = "item_philosophers_stone"
    PUPILS_GIFT = "item_pupils_gift"
    QUICKSILVER_AMULET = "item_quicksilver_amulet"
    RING_OF_AQUILA = "item_ring_of_aquila"
    SPECIALISTS_ARRAY = "item_specialists_array"
    VAMBRACE = "item_vambrace"
    VAMPIRE_FANGS = "item_vampire_fangs"

    # Tier 3 - Current
    GALE_GUARD = "item_gale_guard"
    GUNPOWDER_GAUNTLET = "item_gunpowder_gauntlet"
    JIDI_POLLEN_BAG = "item_jidi_pollen_bag"
    PSYCHIC_HEADBAND = "item_psychic_headband"
    SERRATED_SHIV = "item_serrated_shiv"
    WHISPER_OF_THE_DREAD = "item_whisper_of_the_dread"
    # Tier 3 - Retired
    CEREMONIAL_ROBE = "item_ceremonial_robe"
    CLOAK_OF_FLAMES = "item_cloak_of_flames"
    CRAGGY_COAT = "item_craggy_coat"
    DANDELION_AMULET = "item_dandelion_amulet"
    DOUBLOON = "item_doubloon"
    ELVEN_TUNIC = "item_elven_tunic"
    ENCHANTED_QUIVER = "item_enchanted_quiver"
    NEMESIS_CURSE = "item_nemesis_curse"
    OGRE_SEAL_TOTEM = "item_ogre_seal_totem"
    PALADIN_SWORD = "item_paladin_sword"
    QUICKENING_CHARM = "item_quickening_charm"
    SPIDER_LEGS = "item_spider_legs"
    TITAN_SLIVER = "item_titan_sliver"
    TOME_OF_AGHANIM = "item_tome_of_aghanim"
    VINDICATORS_AXE = "item_vindicators_axe"

    # Tier 4 - Current
    CRIPPLING_CROSSBOW = "item_crippling_crossbow"
    DEZUN_BLOODRITE = "item_dezun_bloodrite"
    GIANTS_MAUL = "item_giants_maul"
    MAGNIFYING_MONOCLE = "item_magnifying_monocle"
    OUTWORLD_STAFF = "item_outworld_staff"
    PYRRHIC_CLOAK = "item_pyrrhic_cloak"
    # Tier 4 - Retired
    ANCIENT_GUARDIAN = "item_ancient_guardian"
    ASCETICS_CAP = "item_ascetics_cap"
    AVIANAS_FEATHER = "item_avianas_feather"
    FLICKER = "item_flicker"
    HAVOC_HAMMER = "item_havoc_hammer"
    ILLUSIONISTS_CAPE = "item_illusionists_cape"
    MARTYRS_PLATE = "item_martyrs_plate"
    MIND_BREAKER = "item_mind_breaker"
    NINJA_GEAR = "item_ninja_gear"
    PENTA_EDGED_SWORD = "item_penta_edged_sword"
    PRINCES_KNIFE = "item_princes_knife"
    RATTLECAGE = "item_rattlecage"
    SPELL_PRISM = "item_spell_prism"
    STORMCRAFTER = "item_stormcrafter"
    TELESCOPE = "item_telescope"
    TIMELESS_RELIC = "item_timeless_relic"
    TRICKSTER_CLOAK = "item_trickster_cloak"
    WITCHBANE = "item_witchbane"

    # Tier 5 - Current
    BOOK_OF_THE_DEAD = "item_book_of_the_dead"
    DIVINE_REGALIA = "item_divine_regalia"
    FALLEN_SKY = "item_fallen_sky"
    HELM_OF_THE_UNDYING = "item_helm_of_the_undying"
    MINOTAUR_HORN = "item_minotaur_horn"
    SPIDER_LEGS_T5 = "item_spider_legs_tier5"
    STYGIAN_DESOLATOR = "item_stygian_desolator"
    UNRELENTING_EYE = "item_unrelenting_eye"
    # Tier 5 - Retired
    APEX = "item_apex"
    ARCANISTS_ARMOR = "item_arcanists_armor"
    BALLISTA = "item_ballista"
    BOOK_OF_SHADOWS = "item_book_of_shadows"
    DEMONICON = "item_demonicon"
    EX_MACHINA = "item_ex_machina"
    FORCE_BOOTS = "item_force_boots"
    FUSION_RUNE = "item_fusion_rune"
    GIANTS_RING = "item_giants_ring"
    MAGIC_LAMP = "item_magic_lamp"
    MIRROR_SHIELD = "item_mirror_shield"
    PHOENIX_ASH = "item_phoenix_ash"
    PIRATE_HAT = "item_pirate_hat"
    SEER_STONE = "item_seer_stone"
    THE_LEVELLER = "item_the_leveller"
    TRIDENT = "item_trident"
    UNWAVERING_CONDITION = "item_unwavering_condition"
    WITLESS_SHAKO = "item_witless_shako"
    WOODLAND_STRIDERS = "item_woodland_striders"

    # Special
    MADSTONE_BUNDLE = "item_madstone_bundle"

    @property
    def item_name(self) -> str:
        """Internal item name (e.g., 'item_kobold_cup')."""
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable item name."""
        data = _NEUTRAL_ITEMS_DATA.get(self.value)
        return data[1] if data else self.name.replace("_", " ").title()

    @property
    def tier(self) -> Optional[int]:
        """Item tier (0-4) or None for special items like Madstone."""
        data = _NEUTRAL_ITEMS_DATA.get(self.value)
        return data[0] if data else None

    @property
    def tier_enum(self) -> Optional[NeutralItemTier]:
        """Item tier as NeutralItemTier enum."""
        t = self.tier
        return NeutralItemTier.from_value(t) if t is not None else None

    @classmethod
    def from_item_name(cls, item_name: str) -> Optional["NeutralItem"]:
        """Get NeutralItem from internal item name (handles aliases)."""
        # Resolve alias to canonical name
        canonical = _NEUTRAL_ITEM_ALIASES.get(item_name, item_name)
        for item in cls:
            if item.value == canonical:
                return item
        return None

    @classmethod
    def is_neutral_item(cls, item_name: str) -> bool:
        """Check if an item name is a neutral item (handles aliases)."""
        canonical = _NEUTRAL_ITEM_ALIASES.get(item_name, item_name)
        return canonical in _NEUTRAL_ITEMS_DATA or item_name in _NEUTRAL_ITEMS_DATA

    @classmethod
    def items_by_tier(cls, tier: int) -> List["NeutralItem"]:
        """Get all neutral items of a specific tier."""
        return [
            item for item in cls
            if _NEUTRAL_ITEMS_DATA.get(item.value, (None,))[0] == tier
        ]

    @classmethod
    def all_item_names(cls) -> List[str]:
        """Get all neutral item internal names."""
        return list(_NEUTRAL_ITEMS_DATA.keys())


class ChatWheelMessage(int, Enum):
    """Dota 2 chat wheel message IDs.

    Standard phrases (IDs 0-232) are available to all players.
    IDs 11000+ are Dota Plus hero voice lines.
    IDs 120000+ are TI Battle Pass voice lines.
    IDs 401000+ are TI talent/team voice lines.

    Usage:
        msg = ChatWheelMessage.from_id(chat_message_id)
        if msg:
            print(f"Voice line: {msg.display_name}")
    """
    # Basic phrases
    OK = 0
    CAREFUL = 1
    GET_BACK = 2
    NEED_WARDS = 3
    STUN_NOW = 4
    HELP = 5
    PUSH_NOW = 6
    WELL_PLAYED = 7
    MISSING = 8
    MISSING_TOP = 9
    MISSING_MID = 10
    MISSING_BOTTOM = 11
    GO = 12
    INITIATE = 13
    FOLLOW_ME = 14
    GROUP_UP = 15
    SPREAD_OUT = 16
    SPLIT_FARM = 17
    ATTACK_NOW = 18
    # Combat/Cooldowns
    ON_MY_WAY = 22
    HEAL = 24
    MANA = 25
    OUT_OF_MANA = 26
    COOLDOWN = 27
    # Enemy/Lane info
    ENEMY_RETURNED = 30
    ALL_MISSING = 31
    ENEMY_INCOMING = 32
    ENEMY_INVIS = 33
    # Items/Neutral
    CHECK_RUNES = 40
    ROSHAN = 41
    AFFIRMATIVE = 54
    WAIT = 55
    DIVE = 56
    ENEMY_HAS_RUNE = 57
    SPLIT_PUSH = 58
    COMING_TO_GANK = 59
    REQUESTING_GANK = 60
    # Misc
    THANKS = 62
    SORRY = 63
    DONT_GIVE_UP = 64
    THAT_JUST_HAPPENED = 65
    NICE = 66
    NEW_META = 67
    MY_BAD = 68
    REGRET = 69
    RELAX = 70
    SPACE_CREATED = 71
    GGWP = 72
    GAME_IS_HARD = 73
    # Additional
    IM_RETREATING = 78
    GOOD_LUCK = 79
    UH_OH = 82
    WOW = 86
    PATIENCE = 224
    CRYBABY = 229
    BRUTAL_SAVAGE_REKT = 230
    NOT_YET = 232

    @property
    def display_name(self) -> str:
        """Human-readable message text."""
        names = {
            0: "Okay", 1: "Careful!", 2: "Get Back!", 3: "We need wards",
            4: "Stun now!", 5: "Help!", 6: "Push now", 7: "Well played!",
            8: "Missing!", 9: "Missing top!", 10: "Missing mid!", 11: "Missing bottom!",
            12: "Go!", 13: "Initiate!", 14: "Follow me", 15: "Group up",
            16: "Spread out", 17: "Split up and farm", 18: "Attack now!",
            22: "On my way", 24: "Heal", 25: "Mana", 26: "Out of mana",
            27: "Cooldown", 30: "Enemy returned", 31: "All enemy heroes missing!",
            32: "Enemy incoming!", 33: "Invisible enemy nearby!",
            40: "Check runes", 41: "Roshan", 54: "Affirmative", 55: "Wait",
            56: "Dive!", 57: "Enemy has rune", 58: "Split push",
            59: "Coming to gank", 60: "Requesting a gank", 62: "Thanks!",
            63: "Sorry", 64: "Don't give up!", 65: "That just happened",
            66: "Nice", 67: "New Meta", 68: "My bad", 69: "I immediately regret my decision",
            70: "Relax, you're doing fine", 71: "> Space created",
            72: "GG, well played", 73: "Game is hard", 78: "I'm retreating",
            79: "Good luck, have fun", 82: "Uh oh", 86: "Wow",
            224: "Patience from Zhou", 229: "Crybaby", 230: "Brutal. Savage. Rekt.",
            232: "Not yet"
        }
        return names.get(self.value, f"Voice Line #{self.value}")

    @classmethod
    def from_id(cls, message_id: int) -> Optional["ChatWheelMessage"]:
        """Get ChatWheelMessage from message ID. Returns None for unmapped IDs."""
        for msg in cls:
            if msg.value == message_id:
                return msg
        return None

    @classmethod
    def describe_id(cls, message_id: int) -> str:
        """Get description for any message ID, including unmapped ones."""
        msg = cls.from_id(message_id)
        if msg:
            return msg.display_name
        if 11000 <= message_id < 12000:
            return f"Dota Plus Hero Voice Line #{message_id}"
        if 120000 <= message_id < 130000:
            return f"TI Battle Pass Voice Line #{message_id}"
        if 401000 <= message_id < 402000:
            return f"TI Talent/Team Voice Line #{message_id}"
        return f"Voice Line #{message_id}"


class GameActivity(int, Enum):
    """Dota 2 unit animation activity codes.

    These are used in CDOTAUserMsg_TE_UnitAnimation messages to identify
    what animation a unit is playing. Useful for detecting taunts.

    Usage:
        if animation_data['activity'] == GameActivity.TAUNT:
            print("Unit is taunting!")

    Source: https://docs.moddota.com/lua_server_enums/
    """
    # Basic states
    IDLE = 1500
    IDLE_RARE = 1501
    RUN = 1502
    ATTACK = 1503
    ATTACK2 = 1504
    ATTACK_EVENT = 1505
    DIE = 1506
    FLINCH = 1507
    FLAIL = 1508
    DISABLED = 1509
    # Ability casting
    CAST_ABILITY_1 = 1510
    CAST_ABILITY_2 = 1511
    CAST_ABILITY_3 = 1512
    CAST_ABILITY_4 = 1513
    CAST_ABILITY_5 = 1514
    CAST_ABILITY_6 = 1515
    # Override abilities
    OVERRIDE_ABILITY_1 = 1516
    OVERRIDE_ABILITY_2 = 1517
    OVERRIDE_ABILITY_3 = 1518
    OVERRIDE_ABILITY_4 = 1519
    # Channeling
    CHANNEL_ABILITY_1 = 1520
    CHANNEL_ABILITY_2 = 1521
    CHANNEL_ABILITY_3 = 1522
    CHANNEL_ABILITY_4 = 1523
    CHANNEL_ABILITY_5 = 1524
    CHANNEL_ABILITY_6 = 1525
    CHANNEL_END_ABILITY_1 = 1526
    CHANNEL_END_ABILITY_2 = 1527
    CHANNEL_END_ABILITY_3 = 1528
    CHANNEL_END_ABILITY_4 = 1529
    CHANNEL_END_ABILITY_5 = 1530
    # Victory/Defeat
    CONSTANT_LAYER = 1531
    CAPTURE = 1532
    SPAWN = 1533
    KILLTAUNT = 1535
    TAUNT = 1536
    # Generic abilities
    CAST_ABILITY_ROT = 1537
    CAST_ABILITY_2_ES_ROLL_START = 1538
    CAST_ABILITY_2_ES_ROLL = 1539
    CAST_ABILITY_2_ES_ROLL_END = 1540
    RUN_ANIM = 1541
    CAST_ABILITY_4_END = 1543
    LOADOUT = 1559
    FORCESTAFF_END = 1560
    LOADOUT_RARE = 1561
    # Teleport
    TELEPORT = 1563
    TELEPORT_END = 1564
    # Special taunts
    TAUNT_SNIPER = 1641
    TAUNT_SPECIAL = 1752
    CUSTOM_TOWER_TAUNT = 1756

    @property
    def display_name(self) -> str:
        """Human-readable activity name."""
        return self.name.replace("_", " ").title()

    @property
    def is_taunt(self) -> bool:
        """True if this activity is a taunt animation."""
        return self in (
            GameActivity.TAUNT, GameActivity.KILLTAUNT,
            GameActivity.TAUNT_SNIPER, GameActivity.TAUNT_SPECIAL,
            GameActivity.CUSTOM_TOWER_TAUNT
        )

    @property
    def is_attack(self) -> bool:
        """True if this activity is an attack animation."""
        return self in (GameActivity.ATTACK, GameActivity.ATTACK2, GameActivity.ATTACK_EVENT)

    @property
    def is_ability_cast(self) -> bool:
        """True if this activity is an ability cast."""
        return 1510 <= self.value <= 1519

    @property
    def is_channeling(self) -> bool:
        """True if this activity is a channeling animation."""
        return 1520 <= self.value <= 1530

    @classmethod
    def from_value(cls, value: int) -> Optional["GameActivity"]:
        """Get GameActivity from integer value."""
        for activity in cls:
            if activity.value == value:
                return activity
        return None

    @classmethod
    def get_taunt_activities(cls) -> List["GameActivity"]:
        """Get all taunt-related activities."""
        return [a for a in cls if a.is_taunt]


class HeaderInfo(BaseModel):
    """Pydantic model for demo file header information."""
    map_name: str
    server_name: str
    client_name: str
    game_directory: str
    network_protocol: int
    demo_file_stamp: str
    build_num: int
    game_build: int = 0  # Extracted from game_directory (e.g., 6559 from /dota_v6559/)
    game: str
    server_start_tick: int
    success: bool
    error: Optional[str] = None


class DraftEvent(BaseModel):
    """A single pick or ban event during the draft phase.

    Maps to Manta's CGameInfo.CDotaGameInfo.CHeroSelectEvent protobuf.
    """
    is_pick: bool   # True for pick, False for ban
    team: int       # 2=Radiant, 3=Dire
    hero_id: int


class PlayerInfo(BaseModel):
    """Player information from match metadata.

    Maps to Manta's CGameInfo.CDotaGameInfo.CPlayerInfo protobuf.
    """
    model_config = {"populate_by_name": True}

    hero_name: str = ""
    player_name: str = ""
    is_fake_client: bool = False
    steam_id: int = Field(default=0, alias="steamid")
    team: int = Field(default=0, alias="game_team")  # 2=Radiant, 3=Dire


class GameInfo(BaseModel):
    """Complete game information extracted from replay.

    Contains match metadata, draft picks/bans, player info, and team data.
    For pro matches, includes team IDs, team tags, and league ID.
    For pub matches, team fields will be 0/empty.

    Maps to Manta's CGameInfo.CDotaGameInfo protobuf.
    """
    model_config = {"populate_by_name": True}

    match_id: int
    game_mode: int
    game_winner: int  # 2=Radiant, 3=Dire
    league_id: int = 0
    end_time: int = 0

    # Team info (pro matches only - 0/empty for pubs)
    radiant_team_id: int = 0
    dire_team_id: int = 0
    radiant_team_tag: str = ""
    dire_team_tag: str = ""

    # Players (Go returns as "player_info")
    players: List[PlayerInfo] = Field(default=[], alias="player_info")

    # Draft (None for pub matches without CM/CD)
    picks_bans: Optional[List[DraftEvent]] = None

    # Playback info
    playback_time: float = 0.0
    playback_ticks: int = 0
    playback_frames: int = 0

    success: bool
    error: Optional[str] = None

    def is_pro_match(self) -> bool:
        """Check if this is a pro/league match."""
        return self.league_id > 0 or self.radiant_team_id > 0 or self.dire_team_id > 0


# Universal Message Event for ALL Manta callbacks
class MessageEvent(BaseModel):
    """Universal message event that can capture ANY Manta message type."""
    type: str          # Message type name (e.g., "CDemoFileHeader", "CDOTAUserMsg_ChatEvent")
    tick: int          # Tick when message occurred
    net_tick: int      # Net tick when message occurred  
    data: Any          # Raw message data (varies by message type)
    timestamp: Optional[int] = None  # Unix timestamp (if available)


class UniversalParseResult(BaseModel):
    """Result from universal parsing - captures ALL message types."""
    messages: List[MessageEvent] = []
    success: bool = True
    error: Optional[str] = None
    count: int = 0


class TeamState(BaseModel):
    """Team state at a specific tick."""
    team_id: int
    score: int = 0
    tower_kills: int = 0


class CreepSnapshot(BaseModel):
    """Creep position and state snapshot.

    Only populated when include_creeps=True in EntityParseConfig.
    """
    entity_id: int
    class_name: str  # e.g., "CDOTA_BaseNPC_Creep_Lane"
    name: str = ""   # e.g., "npc_dota_creep_goodguys_melee"
    team: int = 0    # 2=Radiant, 3=Dire, 0=Neutral
    x: float = 0.0
    y: float = 0.0
    health: int = 0
    max_health: int = 0
    is_neutral: bool = False  # true for neutral creeps
    is_lane: bool = False     # true for lane creeps


class EntitySnapshot(BaseModel):
    """Entity state snapshot at a specific tick.

    Contains complete hero state including economy, abilities, talents, combat stats,
    and attributes. All hero data is consolidated in the heroes field.
    Optionally includes creep positions when include_creeps=True.
    """
    tick: int
    game_time: float
    heroes: List["HeroSnapshot"] = []
    creeps: List[CreepSnapshot] = []  # Only populated when include_creeps=True
    teams: List[TeamState] = []
    raw_entities: Optional[Dict[str, Any]] = None

    @property
    def game_time_str(self) -> str:
        """Formatted game time like '-0:40' or '3:07'."""
        return format_game_time(self.game_time)


class EntityParseConfig(BaseModel):
    """Configuration for entity parsing."""
    interval_ticks: int = 1800  # ~1 minute at 30 ticks/sec
    max_snapshots: int = 0      # 0 = unlimited
    target_ticks: List[int] = []  # Specific ticks to capture (overrides interval if set)
    target_heroes: List[str] = []  # Filter by hero name (npc_dota_hero_* format)
    entity_classes: List[str] = []  # Empty = default set
    include_raw: bool = False
    include_creeps: bool = False  # Include lane and neutral creep positions


class EntityParseResult(BaseModel):
    """Result from entity state parsing."""
    snapshots: List[EntitySnapshot] = []
    success: bool = True
    error: Optional[str] = None
    total_ticks: int = 0
    snapshot_count: int = 0
    game_start_tick: int = 0  # Tick when horn sounded (for game_time calculation)


# ============================================================================
# GAME EVENTS MODELS
# ============================================================================

class GameEventData(BaseModel):
    """Parsed game event with typed fields."""
    name: str
    tick: int
    net_tick: int
    fields: Dict[str, Any] = {}


class GameEventsConfig(BaseModel):
    """Configuration for game event parsing."""
    event_filter: str = ""           # Filter by event name (substring)
    event_names: List[str] = []      # Specific events to capture
    max_events: int = 0              # Max events (0 = unlimited)
    capture_types: bool = True       # Capture event type definitions


class GameEventsResult(BaseModel):
    """Result from game events parsing."""
    events: List[GameEventData] = []
    event_types: List[str] = []
    success: bool = True
    error: Optional[str] = None
    total_events: int = 0


# ============================================================================
# MODIFIER/BUFF MODELS
# ============================================================================

class ModifierEntry(BaseModel):
    """Buff/debuff modifier entry."""
    tick: int
    net_tick: int
    parent: int           # Entity handle of unit with modifier
    caster: int           # Entity handle of caster
    ability: int          # Ability that created modifier
    modifier_class: int   # Modifier class ID
    serial_num: int       # Serial number
    index: int            # Modifier index
    creation_time: float  # When created
    duration: float       # Duration (-1 = permanent)
    stack_count: int      # Number of stacks
    is_aura: bool         # Is an aura
    is_debuff: bool       # Is a debuff


class ModifiersConfig(BaseModel):
    """Configuration for modifier parsing."""
    max_modifiers: int = 0    # Max modifiers (0 = unlimited)
    debuffs_only: bool = False
    auras_only: bool = False


class ModifiersResult(BaseModel):
    """Result from modifier parsing."""
    modifiers: List[ModifierEntry] = []
    success: bool = True
    error: Optional[str] = None
    total_modifiers: int = 0


# ============================================================================
# ENTITY QUERY MODELS
# ============================================================================

class EntityData(BaseModel):
    """Full entity state data."""
    index: int
    serial: int
    class_name: str
    properties: Dict[str, Any] = {}


class EntitiesConfig(BaseModel):
    """Configuration for entity querying."""
    class_filter: str = ""          # Filter by class name (substring)
    class_names: List[str] = []     # Specific classes to capture
    property_filter: List[str] = [] # Only include these properties
    at_tick: int = 0                # Capture at tick (0 = end)
    max_entities: int = 0           # Max entities (0 = unlimited)


class EntitiesResult(BaseModel):
    """Result from entity querying."""
    entities: List[EntityData] = []
    success: bool = True
    error: Optional[str] = None
    total_entities: int = 0
    tick: int = 0
    net_tick: int = 0


# ============================================================================
# STRING TABLE MODELS
# ============================================================================

class StringTableData(BaseModel):
    """String table entry."""
    table_name: str
    index: int
    key: str
    value: Optional[str] = None


class StringTablesConfig(BaseModel):
    """Configuration for string table extraction."""
    table_names: List[str] = []     # Tables to extract (empty = all)
    include_values: bool = False    # Include value data
    max_entries: int = 100          # Max entries per table


class StringTablesResult(BaseModel):
    """Result from string table extraction."""
    tables: Dict[str, List[StringTableData]] = {}
    table_names: List[str] = []
    success: bool = True
    error: Optional[str] = None
    total_entries: int = 0


# ============================================================================
# COMBAT LOG MODELS
# ============================================================================

class CombatLogEntry(BaseModel):
    """Structured combat log entry with ALL available fields for fight reconstruction."""
    tick: int
    net_tick: int
    type: int
    type_name: str
    target_name: str = ""
    target_source_name: str = ""
    attacker_name: str = ""
    damage_source_name: str = ""
    inflictor_name: str = ""
    is_attacker_illusion: bool = False
    is_attacker_hero: bool = False
    is_target_illusion: bool = False
    is_target_hero: bool = False
    is_visible_radiant: bool = False
    is_visible_dire: bool = False
    value: int = 0
    value_name: str = ""
    health: int = 0
    game_time: float = 0.0
    stun_duration: float = 0.0
    slow_duration: float = 0.0
    is_ability_toggle_on: bool = False
    is_ability_toggle_off: bool = False
    ability_level: int = 0
    xp: int = 0
    gold: int = 0
    last_hits: int = 0
    attacker_team: int = 0
    target_team: int = 0
    # Location data
    location_x: float = 0.0
    location_y: float = 0.0
    # Assist tracking
    assist_player0: int = 0
    assist_player1: int = 0
    assist_player2: int = 0
    assist_player3: int = 0
    assist_players: List[int] = []
    # Damage classification
    damage_type: int = 0
    damage_category: int = 0
    # Additional combat info
    is_target_building: bool = False
    is_ultimate_ability: bool = False
    is_heal_save: bool = False
    target_is_self: bool = False
    modifier_duration: float = 0.0
    stack_count: int = 0
    hidden_modifier: bool = False
    invisibility_modifier: bool = False
    # Hero levels
    attacker_hero_level: int = 0
    target_hero_level: int = 0
    # Economy stats
    xpm: int = 0
    gpm: int = 0
    event_location: int = 0
    networth: int = 0
    # Ward/rune/camp info
    obs_wards_placed: int = 0
    neutral_camp_type: int = 0
    neutral_camp_team: int = 0
    rune_type: int = 0
    # Building info
    building_type: int = 0
    # Modifier details
    modifier_elapsed_duration: float = 0.0
    silence_modifier: bool = False
    heal_from_lifesteal: bool = False
    modifier_purged: bool = False
    modifier_purge_ability: int = 0
    modifier_purge_ability_name: str = ""
    modifier_purge_npc: int = 0
    modifier_purge_npc_name: str = ""
    root_modifier: bool = False
    aura_modifier: bool = False
    armor_debuff_modifier: bool = False
    no_physical_damage_modifier: bool = False
    modifier_ability: int = 0
    modifier_ability_name: str = ""
    modifier_hidden: bool = False
    motion_controller_modifier: bool = False
    # Kill/death info
    spell_evaded: bool = False
    long_range_kill: bool = False
    total_unit_death_count: int = 0
    will_reincarnate: bool = False
    # Ability info
    inflictor_is_stolen_ability: bool = False
    spell_generated_attack: bool = False
    uses_charges: bool = False
    # Game state
    at_night_time: bool = False
    attacker_has_scepter: bool = False
    regenerated_health: float = 0.0
    # Tracking/events
    kill_eater_event: int = 0
    unit_status_label: int = 0
    tracked_stat_id: int = 0

    @property
    def game_time_str(self) -> str:
        """Formatted game time like '-0:40' or '3:07'."""
        return format_game_time(self.game_time)

    @property
    def is_pre_horn(self) -> bool:
        """True if event occurred before horn."""
        return self.game_time < 0


class CombatLogConfig(BaseModel):
    """Configuration for combat log parsing."""
    types: List[int] = []       # Filter by type (empty = all)
    max_entries: int = 0        # Max entries (0 = unlimited)
    heroes_only: bool = False   # Only hero-related


class CombatLogResult(BaseModel):
    """Result from combat log parsing."""
    entries: List[CombatLogEntry] = []
    success: bool = True
    error: Optional[str] = None
    total_entries: int = 0
    game_start_time: float = 0.0
    game_start_tick: int = 0  # Tick when horn sounds (game_time = 0)


# ============================================================================
# ATTACKS (from TE_Projectile)
# ============================================================================


class AttackEvent(BaseModel):
    """Represents a single attack (ranged projectile or melee).

    Ranged attacks come from TE_Projectile and have projectile data.
    Melee attacks come from combat log DAMAGE and have full combat data.
    Use is_melee to distinguish between them.
    """
    tick: int                        # Tick when attack was registered
    # Ranged attack fields (from TE_Projectile)
    source_index: int = 0            # Entity index of attacker
    target_index: int = 0            # Entity index of target
    source_handle: int = 0           # Raw entity handle (ranged only)
    target_handle: int = 0           # Raw entity handle (ranged only)
    projectile_speed: int = 0        # Projectile move speed (ranged only)
    dodgeable: bool = False          # Can be disjointed (ranged only)
    launch_tick: int = 0             # Tick when projectile was launched (ranged only)
    game_time: float = 0.0           # Game time in seconds
    game_time_str: str = ""          # Formatted game time (e.g., "12:34")
    # Common fields (populated for both ranged and melee)
    is_melee: bool = False           # True if melee attack (from combat log)
    attacker_name: str = ""          # Attacker name
    target_name: str = ""            # Target name
    location_x: float = 0.0          # Attack location X
    location_y: float = 0.0          # Attack location Y
    # Melee attack fields (from combat log DAMAGE events)
    damage: int = 0                  # Damage dealt (melee only, 0 for ranged)
    target_health: int = 0           # Target health AFTER attack (melee only)
    attacker_team: int = 0           # Attacker team: 2=Radiant, 3=Dire (melee only)
    target_team: int = 0             # Target team: 2=Radiant, 3=Dire (melee only)
    is_attacker_hero: bool = False   # Attacker is a hero (melee only)
    is_target_hero: bool = False     # Target is a hero (melee only)
    is_attacker_illusion: bool = False  # Attacker is an illusion (melee only)
    is_target_illusion: bool = False    # Target is an illusion (melee only)
    is_target_building: bool = False    # Target is a building (melee only)
    damage_type: int = 0             # 1=physical, 2=magical, 4=pure (melee only)


class AttacksResult(BaseModel):
    """Result from attacks parsing (ranged + optional melee)."""
    events: List[AttackEvent] = []
    total_events: int = 0


# ============================================================================
# ENTITY DEATHS (from entity lifecycle tracking)
# ============================================================================


class EntityDeath(BaseModel):
    """Represents an entity being removed from the game.

    This captures when entities are deleted, which typically means they died.
    Useful for tracking creep deaths with entity_id for correlation with attacks.
    """
    tick: int                        # Tick when entity was removed
    entity_id: int                   # Entity index (for correlation with attacks/snapshots)
    class_name: str                  # e.g., "CDOTA_BaseNPC_Creep_Lane"
    name: str = ""                   # e.g., "npc_dota_creep_goodguys_melee"
    team: int = 0                    # 2=Radiant, 3=Dire
    x: float = 0.0                   # Last known X position
    y: float = 0.0                   # Last known Y position
    health: int = 0                  # Health at removal (usually 0)
    max_health: int = 0              # Max health
    is_hero: bool = False            # Is a hero entity
    is_creep: bool = False           # Is a creep (lane or neutral)
    is_building: bool = False        # Is a building (tower, barracks)
    is_neutral: bool = False         # Is a neutral creep
    game_time: float = 0.0           # Game time in seconds
    game_time_str: str = ""          # Formatted game time (e.g., "12:34")


class EntityDeathsResult(BaseModel):
    """Result from entity deaths tracking."""
    events: List[EntityDeath] = []
    total_events: int = 0


# ============================================================================
# HERO RESPAWN EVENT MODEL AND UTILITY
# ============================================================================


class HeroRespawnEvent(BaseModel):
    """Represents a hero respawn event derived from death events.

    Note: Since target_hero_level is always 0 in replay data (Dota 2 limitation),
    respawn_time is estimated using a default formula unless hero_level is
    provided from entity snapshots.
    """
    hero_name: str                    # e.g., "npc_dota_hero_juggernaut"
    hero_display_name: str = ""       # e.g., "Juggernaut" (from Hero enum)
    death_tick: int                   # Tick when hero died
    death_game_time: float            # Game time when hero died (seconds from horn)
    death_game_time_str: str = ""     # Formatted game time (e.g., "12:34")
    respawn_tick: int = 0             # Estimated tick when hero respawns
    respawn_game_time: float = 0.0    # Estimated respawn game time
    respawn_game_time_str: str = ""   # Formatted respawn time
    respawn_duration: float = 0.0     # Respawn time in seconds
    killer_name: str = ""             # Who killed the hero
    hero_level: int = 0               # Hero level at death (if available)
    team: int = 0                     # 2=Radiant, 3=Dire
    will_reincarnate: bool = False    # Has Aegis/Reincarnation
    location_x: float = 0.0           # Death location X
    location_y: float = 0.0           # Death location Y


def calculate_respawn_time(level: int, game_time: float) -> float:
    """Calculate Dota 2 respawn time based on hero level.

    Formula: Base respawn is roughly 4 + (level * 2) seconds.
    This is simplified - actual respawn depends on talents, items, etc.

    Args:
        level: Hero level (1-30)
        game_time: Game time in seconds (for potential time-based modifiers)

    Returns:
        Estimated respawn time in seconds
    """
    if level <= 0:
        level = 1
    base_respawn = 4.0 + (level * 2.0)
    return min(base_respawn, 100.0)


def derive_respawn_events(
    combat_log_result: CombatLogResult,
    hero_levels: Optional[Dict[str, int]] = None,
) -> List[HeroRespawnEvent]:
    """Derive hero respawn events from combat log death entries.

    Processes DOTA_COMBATLOG_DEATH events where the target is a hero
    and creates HeroRespawnEvent instances with estimated respawn times.

    Args:
        combat_log_result: Parsed combat log with DEATH events
        hero_levels: Optional dict mapping hero names to levels for accurate
                     respawn calculation. If not provided, uses level 1 default.

    Returns:
        List of HeroRespawnEvent instances sorted by death time

    Example:
        >>> result = parser.parse(combat_log={"types": [CombatLogType.DEATH], "heroes_only": True})
        >>> respawns = derive_respawn_events(result.combat_log)
        >>> for r in respawns:
        ...     print(f"{r.hero_display_name} died at {r.death_game_time_str}, respawns at {r.respawn_game_time_str}")
    """
    if hero_levels is None:
        hero_levels = {}

    respawn_events = []

    for entry in combat_log_result.entries:
        if entry.type != 4:
            continue

        if "npc_dota_hero_" not in entry.target_name:
            continue

        hero_name = normalize_hero_name(entry.target_name)
        hero_key = hero_name.replace("npc_dota_hero_", "")

        level = hero_levels.get(hero_name, hero_levels.get(hero_key, 1))

        if entry.target_hero_level > 0:
            level = entry.target_hero_level

        respawn_duration = calculate_respawn_time(level, entry.game_time)

        if entry.will_reincarnate:
            respawn_duration = 0.0

        respawn_game_time = entry.game_time + respawn_duration
        respawn_tick = entry.tick + int(respawn_duration * TICKS_PER_SECOND)

        display_name = hero_key.replace("_", " ").title()
        for hero in Hero:
            if hero.name.lower() == hero_key.lower():
                display_name = hero.display_name
                break

        event = HeroRespawnEvent(
            hero_name=hero_name,
            hero_display_name=display_name,
            death_tick=entry.tick,
            death_game_time=entry.game_time,
            death_game_time_str=format_game_time(entry.game_time),
            respawn_tick=respawn_tick,
            respawn_game_time=respawn_game_time,
            respawn_game_time_str=format_game_time(respawn_game_time),
            respawn_duration=respawn_duration,
            killer_name=entry.attacker_name,
            hero_level=level,
            team=entry.target_team,
            will_reincarnate=entry.will_reincarnate,
            location_x=entry.location_x,
            location_y=entry.location_y,
        )
        respawn_events.append(event)

    return sorted(respawn_events, key=lambda e: e.death_game_time)


# ============================================================================
# PARSER INFO MODEL
# ============================================================================

class ParserInfo(BaseModel):
    """Parser state information."""
    game_build: int = 0
    tick: int = 0
    net_tick: int = 0
    string_tables: List[str] = []
    entity_count: int = 0
    success: bool = True
    error: Optional[str] = None


# ============================================================================
# V2 PARSER TYPES AND CLASS - UNIFIED SINGLE-PASS API
# ============================================================================


class HeaderCollectorConfig(BaseModel):
    """Config for header collection."""
    enabled: bool = True


class GameInfoCollectorConfig(BaseModel):
    """Config for game info collection."""
    enabled: bool = True


class MessagesCollectorConfig(BaseModel):
    """Config for universal messages collection."""
    filter: str = ""
    max_messages: int = 0


class ParserInfoCollectorConfig(BaseModel):
    """Config for parser info collection."""
    enabled: bool = True


class AttacksConfig(BaseModel):
    """Config for attacks collection (ranged projectiles + melee auto-attacks)."""
    max_events: int = 0  # Max events (0 = unlimited)


class EntityDeathsConfig(BaseModel):
    """Config for entity deaths tracking."""
    max_events: int = 0       # Max events (0 = unlimited)
    heroes_only: bool = False # Only track hero deaths
    creeps_only: bool = False # Only track creep deaths
    include_creeps: bool = False  # Include creeps (default False for performance)


class ParseConfig(BaseModel):
    """Configuration for single-pass parsing with multiple collectors."""
    header: Optional[HeaderCollectorConfig] = None
    game_info: Optional[GameInfoCollectorConfig] = None
    combat_log: Optional[CombatLogConfig] = None
    entities: Optional[EntityParseConfig] = None
    game_events: Optional[GameEventsConfig] = None
    modifiers: Optional[ModifiersConfig] = None
    string_tables: Optional[StringTablesConfig] = None
    messages: Optional[MessagesCollectorConfig] = None
    parser_info: Optional[ParserInfoCollectorConfig] = None
    attacks: Optional[AttacksConfig] = None
    entity_deaths: Optional[EntityDeathsConfig] = None


class MessagesResult(BaseModel):
    """Result from messages collector."""
    messages: List[MessageEvent] = []
    success: bool = True
    error: Optional[str] = None
    total_messages: int = 0
    filtered_count: int = 0
    callbacks_used: List[str] = []


class ParseResult(BaseModel):
    """Result from single-pass parsing with all collected data."""
    success: bool = True
    error: Optional[str] = None

    header: Optional[HeaderInfo] = None
    game_info: Optional[GameInfo] = None
    combat_log: Optional[CombatLogResult] = None
    entities: Optional[EntityParseResult] = None
    game_events: Optional[GameEventsResult] = None
    modifiers: Optional[ModifiersResult] = None
    string_tables: Optional[StringTablesResult] = None
    messages: Optional[MessagesResult] = None
    parser_info: Optional[ParserInfo] = None
    attacks: Optional[AttacksResult] = None
    entity_deaths: Optional[EntityDeathsResult] = None


class StreamConfig(BaseModel):
    """Configuration for streaming parse."""
    combat_log: bool = False
    messages: bool = False
    game_events: bool = False
    max_events: int = 1000


class StreamEvent(BaseModel):
    """A single event from streaming parse."""
    kind: str = ""
    tick: int = 0
    type: str = ""
    data: Dict[str, Any] = {}


class StreamResult(BaseModel):
    """Result from streaming parse open."""
    success: bool = True
    handle_id: int = 0
    error: Optional[str] = None


class Keyframe(BaseModel):
    """A seekable keyframe in the demo."""
    tick: int = 0
    offset: int = 0
    game_time: float = 0.0


class DemoIndex(BaseModel):
    """Index of keyframes for seeking."""
    keyframes: List[Keyframe] = []
    total_ticks: int = 0
    game_started: int = 0
    success: bool = True
    error: Optional[str] = None


class AbilitySnapshot(BaseModel):
    """State of a single ability at a specific tick.

    Abilities are tracked from hero entity's m_vecAbilities array. Each ability
    has a slot index (0-5 for regular abilities) and various state properties.
    """
    slot: int = 0
    name: str = ""
    level: int = 0
    cooldown: float = 0.0
    max_cooldown: float = 0.0
    mana_cost: int = 0
    charges: int = 0
    is_ultimate: bool = False

    @property
    def short_name(self) -> str:
        """Return ability name without CDOTA_Ability_ prefix."""
        return self.name.replace("CDOTA_Ability_", "")

    @property
    def is_maxed(self) -> bool:
        """True if ability is at max level (typically 4 for regular, 3 for ultimate)."""
        if self.is_ultimate:
            return self.level >= 3
        return self.level >= 4

    @property
    def is_on_cooldown(self) -> bool:
        """True if ability is currently on cooldown."""
        return self.cooldown > 0


class TalentChoice(BaseModel):
    """A talent choice made by a hero.

    Talents are selected at levels 10, 15, 20, and 25. Each tier offers two
    choices (left and right). This model captures which choice was made.
    """
    tier: int = 0
    slot: int = 0
    is_left: bool = True
    name: str = ""

    @property
    def side(self) -> str:
        """Return 'left' or 'right' based on talent choice."""
        return "left" if self.is_left else "right"


class ItemSnapshot(BaseModel):
    """State of a single item in inventory at a specific tick.

    Items are tracked from hero entity's m_hItems array. Dota 2 inventory slots:
        - 0-5: Main inventory (6 slots)
        - 6-8: Backpack (3 slots)
        - 9: TP scroll slot
        - 10-15: Stash (6 slots)
        - 16: Neutral item slot
    """
    slot: int = 0
    name: str = ""
    charges: int = 0
    cooldown: float = 0.0
    max_cooldown: float = 0.0

    @property
    def short_name(self) -> str:
        """Return item name without 'item_' prefix (e.g., 'blink' instead of 'item_blink')."""
        if self.name.startswith("item_"):
            return self.name[5:]
        return self.name

    @property
    def is_main_inventory(self) -> bool:
        """True if item is in main inventory (slots 0-5)."""
        return 0 <= self.slot <= 5

    @property
    def is_backpack(self) -> bool:
        """True if item is in backpack (slots 6-8)."""
        return 6 <= self.slot <= 8

    @property
    def is_tp_slot(self) -> bool:
        """True if item is in TP scroll slot (slot 9)."""
        return self.slot == 9

    @property
    def is_stash(self) -> bool:
        """True if item is in stash (slots 10-15)."""
        return 10 <= self.slot <= 15

    @property
    def is_neutral_slot(self) -> bool:
        """True if item is in neutral item slot (slot 16)."""
        return self.slot == 16

    @property
    def is_on_cooldown(self) -> bool:
        """True if item is currently on cooldown."""
        return self.cooldown > 0

    @property
    def item_enum(self) -> Optional["Item"]:
        """Get Item enum if this is a purchasable item, None otherwise."""
        return Item.from_item_name(self.name)

    @property
    def neutral_item_enum(self) -> Optional["NeutralItem"]:
        """Get NeutralItem enum if this is a neutral item, None otherwise."""
        return NeutralItem.from_item_name(self.name)

    @property
    def is_neutral_item(self) -> bool:
        """True if this item is a neutral item (regardless of slot)."""
        return self.neutral_item_enum is not None

    @property
    def is_purchasable_item(self) -> bool:
        """True if this item is a purchasable (shop) item."""
        return self.item_enum is not None

    @property
    def display_name(self) -> str:
        """Human-readable item name.

        For neutral items, returns the display name from NeutralItem enum.
        For purchasable items, returns the display name from Item enum.
        For unknown items, converts short_name to title case.
        """
        neutral = self.neutral_item_enum
        if neutral:
            return neutral.display_name
        item = self.item_enum
        if item:
            return item.display_name
        return self.short_name.replace("_", " ").title()


class HeroSnapshot(BaseModel):
    """Complete hero state at a specific tick.

    Consolidates all hero data: identity, position, vitals, economy, combat stats,
    attributes, abilities, and talents. This is the primary model for hero state
    in entity snapshots.
    """
    # Identity
    entity_id: int = 0
    hero_name: str = ""
    hero_id: int = 0
    player_id: int = 0
    team: int = 0
    index: int = 0  # Deprecated: use entity_id instead

    # Position
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # Vital stats
    health: int = 0
    max_health: int = 0
    mana: float = 0.0
    max_mana: float = 0.0
    level: int = 0
    is_alive: bool = True

    # Economy
    gold: int = 0
    net_worth: int = 0
    last_hits: int = 0
    denies: int = 0
    xp: int = 0
    camps_stacked: int = 0

    # KDA
    kills: int = 0
    deaths: int = 0
    assists: int = 0

    # Combat stats
    armor: float = 0.0
    magic_resistance: float = 0.0
    damage_min: int = 0
    damage_max: int = 0
    attack_range: int = 0

    # Attributes
    strength: float = 0.0
    agility: float = 0.0
    intellect: float = 0.0

    # Abilities and talents
    abilities: List[AbilitySnapshot] = []
    talents: List[TalentChoice] = []
    ability_points: int = 0

    # Inventory (slots 0-5: main, 6-8: backpack, 9: TP, 10-15: stash, 16: neutral)
    inventory: List[ItemSnapshot] = []

    # Clone/illusion flags
    is_illusion: bool = False
    is_clone: bool = False

    @property
    def kda(self) -> str:
        """Return KDA as a formatted string (e.g., '5/2/10')."""
        return f"{self.kills}/{self.deaths}/{self.assists}"

    @property
    def has_ultimate(self) -> bool:
        """True if hero has learned their ultimate ability."""
        for ability in self.abilities:
            if ability.is_ultimate and ability.level > 0:
                return True
        return False

    @property
    def talents_chosen(self) -> int:
        """Number of talents selected (0-4)."""
        return len(self.talents)

    def get_ability(self, name: str) -> Optional[AbilitySnapshot]:
        """Get ability by name (partial match supported)."""
        name_lower = name.lower()
        for ability in self.abilities:
            if name_lower in ability.name.lower():
                return ability
        return None

    def get_talent_at_tier(self, tier: int) -> Optional[TalentChoice]:
        """Get the talent chosen at a specific tier (10, 15, 20, or 25)."""
        for talent in self.talents:
            if talent.tier == tier:
                return talent
        return None

    @property
    def main_inventory(self) -> List[ItemSnapshot]:
        """Get items in main inventory (slots 0-5)."""
        return [item for item in self.inventory if item.is_main_inventory]

    @property
    def backpack(self) -> List[ItemSnapshot]:
        """Get items in backpack (slots 6-8)."""
        return [item for item in self.inventory if item.is_backpack]

    @property
    def stash(self) -> List[ItemSnapshot]:
        """Get items in stash (slots 10-15)."""
        return [item for item in self.inventory if item.is_stash]

    @property
    def neutral_item(self) -> Optional[ItemSnapshot]:
        """Get the neutral item (slot 16), or None if empty."""
        for item in self.inventory:
            if item.is_neutral_slot:
                return item
        return None

    @property
    def tp_scroll(self) -> Optional[ItemSnapshot]:
        """Get the TP scroll (slot 9), or None if empty."""
        for item in self.inventory:
            if item.is_tp_slot:
                return item
        return None

    def get_item(self, name: str) -> Optional[ItemSnapshot]:
        """Get item by name (partial match supported)."""
        name_lower = name.lower()
        for item in self.inventory:
            if name_lower in item.name.lower():
                return item
        return None

    def has_item(self, name: str) -> bool:
        """Check if hero has an item by name (partial match supported)."""
        return self.get_item(name) is not None


class EntityStateSnapshot(BaseModel):
    """Entity state snapshot at a specific tick."""
    tick: int = 0
    game_time: float = 0.0
    heroes: List[HeroSnapshot] = []
    success: bool = True
    error: Optional[str] = None


class RangeParseConfig(BaseModel):
    """Configuration for range parsing."""
    start_tick: int = 0
    end_tick: int = 0
    combat_log: bool = False
    messages: bool = False
    game_events: bool = False


class RangeParseResult(BaseModel):
    """Result from parsing a specific tick range."""
    start_tick: int = 0
    end_tick: int = 0
    actual_start: int = 0
    actual_end: int = 0
    combat_log: List[Dict[str, Any]] = []
    messages: List[Dict[str, Any]] = []
    success: bool = True
    error: Optional[str] = None


class KeyframeResult(BaseModel):
    """Result from finding a keyframe."""
    success: bool = True
    keyframe: Optional[Keyframe] = None
    exact: bool = False
    error: Optional[str] = None


class Parser:
    """V2 Parser with unified single-pass parsing.

    This is the recommended API that parses the file once and collects
    all requested data in a single pass.

    Usage:
        parser = Parser("match.dem")
        result = parser.parse(
            header=True,
            game_info=True,
            combat_log={"types": [4], "heroes_only": True},
            entities={"interval_ticks": 900},
        )

        print(result.header.map_name)
        print(result.game_info.match_id)
        print(len(result.combat_log.entries))
    """

    _BZ2_MAGIC = b'BZh'

    def __init__(self, demo_path: str, library_path: Optional[str] = None):
        """Initialize parser for a specific demo file."""
        self._demo_path = demo_path
        self._decompressed_cache: Dict[str, str] = {}
        self._game_start_tick: Optional[int] = None

        if library_path is None:
            library_path = Path(__file__).parent / "libmanta_wrapper.so"

        if not os.path.exists(library_path):
            raise FileNotFoundError(f"Shared library not found: {library_path}")

        self._lib = ctypes.CDLL(str(library_path))
        self._setup_function_signatures()

    def _setup_function_signatures(self):
        """Configure ctypes function signatures."""
        self._lib.Parse.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.Parse.restype = ctypes.c_char_p

        self._lib.FreeString.argtypes = [ctypes.c_char_p]
        self._lib.FreeString.restype = None

        self._lib.StreamOpen.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.StreamOpen.restype = ctypes.c_char_p

        self._lib.StreamNext.argtypes = [ctypes.c_longlong]
        self._lib.StreamNext.restype = ctypes.c_char_p

        self._lib.StreamClose.argtypes = [ctypes.c_longlong]
        self._lib.StreamClose.restype = ctypes.c_char_p

        self._lib.BuildIndex.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self._lib.BuildIndex.restype = ctypes.c_char_p

        self._lib.GetSnapshot.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.GetSnapshot.restype = ctypes.c_char_p

        self._lib.ParseRange.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self._lib.ParseRange.restype = ctypes.c_char_p

        self._lib.FindKeyframe.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self._lib.FindKeyframe.restype = ctypes.c_char_p

    def _prepare_demo_file(self, demo_file_path: str) -> str:
        """Prepare demo file, decompressing if needed."""
        if demo_file_path in self._decompressed_cache:
            cached_path = self._decompressed_cache[demo_file_path]
            if os.path.exists(cached_path):
                return cached_path

        if os.path.isdir(demo_file_path):
            raise ValueError(f"Parsing failed: '{demo_file_path}' is a directory, not a file")

        with open(demo_file_path, 'rb') as f:
            magic = f.read(3)

        if magic == self._BZ2_MAGIC:
            temp_fd, temp_path = tempfile.mkstemp(suffix='.dem')
            try:
                with bz2.open(demo_file_path, 'rb') as f_in:
                    with os.fdopen(temp_fd, 'wb') as f_out:
                        while True:
                            chunk = f_in.read(1024 * 1024)
                            if not chunk:
                                break
                            f_out.write(chunk)

                self._decompressed_cache[demo_file_path] = temp_path
                return temp_path
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise ValueError(f"Failed to decompress bz2 file: {e}")

        return demo_file_path

    def parse(
        self,
        header: bool = False,
        game_info: bool = False,
        combat_log: Optional[Dict[str, Any]] = None,
        entities: Optional[Dict[str, Any]] = None,
        game_events: Optional[Dict[str, Any]] = None,
        modifiers: Optional[Dict[str, Any]] = None,
        string_tables: Optional[Dict[str, Any]] = None,
        messages: Optional[Dict[str, Any]] = None,
        parser_info: bool = False,
        attacks: Optional[Dict[str, Any]] = None,
        entity_deaths: Optional[Dict[str, Any]] = None,
    ) -> ParseResult:
        """Parse the demo file with specified collectors.

        This method parses the file ONCE, collecting all requested data
        in a single pass. Much more efficient than multiple parse_* calls.

        Args:
            header: Collect header info
            game_info: Collect game info (match, players, draft)
            combat_log: Combat log config dict (types, max_entries, heroes_only)
            entities: Entity snapshot config (interval_ticks, max_snapshots, etc.)
            game_events: Game events config (event_filter, max_events, etc.)
            modifiers: Modifiers config (max_modifiers, auras_only, etc.)
            string_tables: String tables config (table_names, max_entries, etc.)
            messages: Universal messages config (filter, max_messages)
            parser_info: Collect parser state info
            attacks: Attacks config (max_events) - captures TE_Projectile attacks
            entity_deaths: Entity deaths config (include_creeps, heroes_only, etc.)

        Returns:
            ParseResult with all requested data
        """
        if not os.path.exists(self._demo_path):
            raise FileNotFoundError(f"Demo file not found: {self._demo_path}")

        actual_path = self._prepare_demo_file(self._demo_path)

        config = ParseConfig()

        if header:
            config.header = HeaderCollectorConfig(enabled=True)

        if game_info:
            config.game_info = GameInfoCollectorConfig(enabled=True)

        if combat_log is not None:
            config.combat_log = CombatLogConfig(**combat_log)

        if entities is not None:
            config.entities = EntityParseConfig(**entities)

        if game_events is not None:
            config.game_events = GameEventsConfig(**game_events)

        if modifiers is not None:
            config.modifiers = ModifiersConfig(**modifiers)

        if string_tables is not None:
            config.string_tables = StringTablesConfig(**string_tables)

        if messages is not None:
            config.messages = MessagesCollectorConfig(**messages)

        if parser_info:
            config.parser_info = ParserInfoCollectorConfig(enabled=True)

        if attacks is not None:
            config.attacks = AttacksConfig(**attacks)

        if entity_deaths is not None:
            config.entity_deaths = EntityDeathsConfig(**entity_deaths)

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json(exclude_none=True).encode('utf-8')

        result_ptr = self._lib.Parse(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("Parse returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = ParseResult(**result_dict)

            if not result.success:
                raise ValueError(f"Parsing failed: {result.error}")

            return result
        finally:
            pass

    def stream(
        self,
        combat_log: bool = False,
        messages: bool = False,
        game_events: bool = False,
        max_events: int = 1000,
    ) -> Iterator[StreamEvent]:
        """Stream events from the demo file."""
        if not os.path.exists(self._demo_path):
            raise FileNotFoundError(f"Demo file not found: {self._demo_path}")

        actual_path = self._prepare_demo_file(self._demo_path)

        config = StreamConfig(
            combat_log=combat_log,
            messages=messages,
            game_events=game_events,
            max_events=max_events,
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        open_result_ptr = self._lib.StreamOpen(path_bytes, config_json)
        if not open_result_ptr:
            raise ValueError("StreamOpen returned null pointer")

        open_result_json = ctypes.string_at(open_result_ptr).decode('utf-8')
        open_result = json.loads(open_result_json)

        if not open_result.get('success', False):
            raise ValueError(f"StreamOpen failed: {open_result.get('error', 'Unknown error')}")

        handle_id = open_result['handle_id']

        try:
            import time
            while True:
                next_result_ptr = self._lib.StreamNext(handle_id)
                if not next_result_ptr:
                    break

                next_result_json = ctypes.string_at(next_result_ptr).decode('utf-8')
                next_result = json.loads(next_result_json)

                if not next_result.get('success', False):
                    error = next_result.get('error', 'Unknown error')
                    if error:
                        raise ValueError(f"StreamNext failed: {error}")
                    break

                if next_result.get('done', False):
                    break

                if next_result.get('event'):
                    yield StreamEvent(**next_result['event'])
                else:
                    time.sleep(0.001)

        finally:
            self._lib.StreamClose(handle_id)

    def build_index(self, interval_ticks: int = 1800) -> DemoIndex:
        """Build an index of keyframes for seeking within the demo."""
        if not os.path.exists(self._demo_path):
            raise FileNotFoundError(f"Demo file not found: {self._demo_path}")

        actual_path = self._prepare_demo_file(self._demo_path)
        path_bytes = actual_path.encode('utf-8')

        result_ptr = self._lib.BuildIndex(path_bytes, interval_ticks)

        if not result_ptr:
            raise ValueError("BuildIndex returned null pointer")

        result_json = ctypes.string_at(result_ptr).decode('utf-8')
        result_dict = json.loads(result_json)
        result = DemoIndex(**result_dict)

        if not result.success:
            raise ValueError(f"Index building failed: {result.error}")

        # Cache game_start_tick for time conversions
        if result.game_started > 0:
            self._game_start_tick = result.game_started

        return result

    def _ensure_game_start_tick(self) -> int:
        """Ensure game_start_tick is cached, building index if needed."""
        if self._game_start_tick is None:
            # Build a lightweight index to get game_start_tick
            index = self.build_index(interval_ticks=36000)  # Large interval = fast
            if self._game_start_tick is None:
                raise ValueError("Could not determine game start tick from demo")
        return self._game_start_tick

    def _game_time_to_tick(self, game_time: float) -> int:
        """Convert game_time (seconds from horn) to tick."""
        game_start_tick = self._ensure_game_start_tick()
        return game_time_to_tick(game_time, game_start_tick)

    @property
    def game_start_tick(self) -> Optional[int]:
        """The tick when the horn sounds (game_time = 0). None if not yet determined."""
        return self._game_start_tick

    def snapshot(
        self,
        target_tick: Optional[int] = None,
        game_time: Optional[float] = None,
        include_illusions: bool = False
    ) -> EntityStateSnapshot:
        """Get entity state snapshot at a specific tick or game time.

        Args:
            target_tick: Tick number (preferred, faster)
            game_time: Seconds from horn (converted to tick internally)
            include_illusions: Include illusion/clone heroes

        Returns:
            EntityStateSnapshot with hero states at the specified time.

        Raises:
            ValueError: If neither target_tick nor game_time is provided
        """
        if target_tick is None and game_time is None:
            raise ValueError("Must provide either target_tick or game_time")

        if target_tick is None:
            target_tick = self._game_time_to_tick(game_time)

        if not os.path.exists(self._demo_path):
            raise FileNotFoundError(f"Demo file not found: {self._demo_path}")

        actual_path = self._prepare_demo_file(self._demo_path)
        path_bytes = actual_path.encode('utf-8')

        config = {"target_tick": target_tick, "include_illusions": include_illusions}
        config_json = json.dumps(config).encode('utf-8')

        result_ptr = self._lib.GetSnapshot(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("GetSnapshot returned null pointer")

        result_json = ctypes.string_at(result_ptr).decode('utf-8')
        result_dict = json.loads(result_json)
        result = EntityStateSnapshot(**result_dict)

        if not result.success:
            raise ValueError(f"Snapshot failed: {result.error}")

        return result

    def parse_range(
        self,
        start_tick: Optional[int] = None,
        end_tick: Optional[int] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        combat_log: bool = False,
        messages: bool = False,
        game_events: bool = False,
    ) -> RangeParseResult:
        """Parse events within a specific tick or time range.

        Args:
            start_tick: Start tick (preferred, faster)
            end_tick: End tick (preferred, faster)
            start_time: Start time in seconds from horn
            end_time: End time in seconds from horn
            combat_log: Collect combat log entries
            messages: Collect messages
            game_events: Collect game events

        You can mix tick and time parameters, e.g.:
            parse_range(start_time=60.0, end_tick=50000, combat_log=True)
        """
        # Convert times to ticks if provided
        if start_tick is None and start_time is not None:
            start_tick = self._game_time_to_tick(start_time)
        if end_tick is None and end_time is not None:
            end_tick = self._game_time_to_tick(end_time)

        if start_tick is None or end_tick is None:
            raise ValueError("Must provide start and end (either as tick or time)")

        if not os.path.exists(self._demo_path):
            raise FileNotFoundError(f"Demo file not found: {self._demo_path}")

        actual_path = self._prepare_demo_file(self._demo_path)

        config = RangeParseConfig(
            start_tick=start_tick,
            end_tick=end_tick,
            combat_log=combat_log,
            messages=messages,
            game_events=game_events,
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self._lib.ParseRange(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("ParseRange returned null pointer")

        result_json = ctypes.string_at(result_ptr).decode('utf-8')
        result_dict = json.loads(result_json)
        result = RangeParseResult(**result_dict)

        if not result.success:
            raise ValueError(f"Range parsing failed: {result.error}")

        return result

    def find_keyframe(self, index: DemoIndex, target_tick: int) -> KeyframeResult:
        """Find the nearest keyframe at or before a target tick."""
        index_json = index.model_dump_json().encode('utf-8')

        result_ptr = self._lib.FindKeyframe(index_json, target_tick)

        if not result_ptr:
            raise ValueError("FindKeyframe returned null pointer")

        result_json = ctypes.string_at(result_ptr).decode('utf-8')
        result_dict = json.loads(result_json)
        result = KeyframeResult(**result_dict)

        if not result.success:
            raise ValueError(f"Keyframe search failed: {result.error}")

        return result



def _run_cli(argv=None):
    """Run the CLI interface. Separated for testing."""
    import sys

    if argv is None:
        argv = sys.argv

    if len(argv) != 2:
        print("Usage: python manta_python.py <demo_file.dem>")
        sys.exit(1)

    demo_file = argv[1]

    try:
        parser = Parser(demo_file)
        result = parser.parse(header=True)
        header = result.header
        print(f"Success! Parsed header from: {demo_file}")
        print(f"  Map: {header.map_name}")
        print(f"  Server: {header.server_name}")
        print(f"  Client: {header.client_name}")
        print(f"  Game Directory: {header.game_directory}")
        print(f"  Network Protocol: {header.network_protocol}")
        print(f"  Demo File Stamp: {header.demo_file_stamp}")
        print(f"  Build Num: {header.build_num}")
        print(f"  Game: {header.game}")
        print(f"  Server Start Tick: {header.server_start_tick}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    _run_cli()