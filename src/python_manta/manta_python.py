"""
Python interface for Manta Dota 2 replay parser using ctypes.
Provides basic file header reading functionality through Go CGO wrapper.
"""
import bz2
import ctypes
import json
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


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


class HeaderInfo(BaseModel):
    """Pydantic model for demo file header information."""
    map_name: str
    server_name: str
    client_name: str
    game_directory: str
    network_protocol: int
    demo_file_stamp: str
    build_num: int
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
    hero_name: str
    player_name: str
    is_fake_client: bool = False
    steam_id: int
    team: int  # 2=Radiant, 3=Dire


class GameInfo(BaseModel):
    """Complete game information extracted from replay.

    Contains match metadata, draft picks/bans, player info, and team data.
    For pro matches, includes team IDs, team tags, and league ID.
    For pub matches, team fields will be 0/empty.

    Maps to Manta's CGameInfo.CDotaGameInfo protobuf.
    """
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

    # Players
    players: List[PlayerInfo] = []

    # Draft
    picks_bans: List[DraftEvent] = []

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


class PlayerState(BaseModel):
    """Player state at a specific tick."""
    player_id: int
    hero_id: int = 0
    hero_name: str = ""  # npc_dota_hero_* format (e.g., "npc_dota_hero_axe")
    team: int = 0
    last_hits: int = 0
    denies: int = 0
    gold: int = 0
    net_worth: int = 0
    xp: int = 0
    level: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    position_x: float = 0.0
    position_y: float = 0.0
    health: int = 0
    max_health: int = 0
    mana: float = 0.0
    max_mana: float = 0.0


class TeamState(BaseModel):
    """Team state at a specific tick."""
    team_id: int
    score: int = 0
    tower_kills: int = 0


class EntitySnapshot(BaseModel):
    """Entity state snapshot at a specific tick."""
    tick: int
    game_time: float
    players: List[PlayerState] = []
    teams: List[TeamState] = []
    raw_entities: Optional[Dict[str, Any]] = None


class EntityParseConfig(BaseModel):
    """Configuration for entity parsing."""
    interval_ticks: int = 1800  # ~1 minute at 30 ticks/sec
    max_snapshots: int = 0      # 0 = unlimited
    target_ticks: List[int] = []  # Specific ticks to capture (overrides interval if set)
    target_heroes: List[str] = []  # Filter by hero name (npc_dota_hero_* format)
    entity_classes: List[str] = []  # Empty = default set
    include_raw: bool = False


class EntityParseResult(BaseModel):
    """Result from entity state parsing."""
    snapshots: List[EntitySnapshot] = []
    success: bool = True
    error: Optional[str] = None
    total_ticks: int = 0
    snapshot_count: int = 0


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
    timestamp: float = 0.0
    timestamp_raw: float = 0.0
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


class MantaParser:
    """Python wrapper for Manta Dota 2 replay parser."""

    # BZ2 magic bytes
    _BZ2_MAGIC = b'BZh'

    def __init__(self, library_path: Optional[str] = None):
        """Initialize the Manta parser with the shared library."""
        if library_path is None:
            # Default to library in same directory
            library_path = Path(__file__).parent / "libmanta_wrapper.so"

        if not os.path.exists(library_path):
            raise FileNotFoundError(f"Shared library not found: {library_path}")

        # Load the shared library
        self.lib = ctypes.CDLL(str(library_path))

        # Configure function signatures
        self._setup_function_signatures()

        # Cache for decompressed files
        self._decompressed_cache: Dict[str, str] = {}

    def _prepare_demo_file(self, demo_file_path: str) -> str:
        """
        Prepare a demo file for parsing, decompressing if necessary.

        Supports:
        - Raw .dem files (PBDEMS2 format)
        - BZ2 compressed .dem files (downloaded from Valve servers)

        Args:
            demo_file_path: Path to the .dem file (possibly compressed)

        Returns:
            Path to the uncompressed demo file (may be a temp file)
        """
        # Check cache first
        if demo_file_path in self._decompressed_cache:
            cached_path = self._decompressed_cache[demo_file_path]
            if os.path.exists(cached_path):
                return cached_path

        # Check if file is bz2 compressed by reading magic bytes
        with open(demo_file_path, 'rb') as f:
            magic = f.read(3)

        if magic == self._BZ2_MAGIC:
            # Decompress to temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.dem')
            try:
                with bz2.open(demo_file_path, 'rb') as f_in:
                    with os.fdopen(temp_fd, 'wb') as f_out:
                        # Read and write in chunks to handle large files
                        while True:
                            chunk = f_in.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            f_out.write(chunk)

                # Cache the decompressed path
                self._decompressed_cache[demo_file_path] = temp_path
                return temp_path
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise ValueError(f"Failed to decompress bz2 file: {e}")

        # File is not compressed, use as-is
        return demo_file_path
    
    def _setup_function_signatures(self):
        """Configure ctypes function signatures for the shared library."""
        # ParseHeader function: takes char* filename, returns char* JSON
        self.lib.ParseHeader.argtypes = [ctypes.c_char_p]
        self.lib.ParseHeader.restype = ctypes.c_char_p

        # ParseMatchInfo function: takes char* filename, returns char* JSON (CDotaGameInfo)
        self.lib.ParseMatchInfo.argtypes = [ctypes.c_char_p]
        self.lib.ParseMatchInfo.restype = ctypes.c_char_p

        # ParseUniversal function: takes char* filename, char* filter, int maxMessages, returns char* JSON
        self.lib.ParseUniversal.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.ParseUniversal.restype = ctypes.c_char_p

        # ParseEntities function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.ParseEntities.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.ParseEntities.restype = ctypes.c_char_p

        # ParseGameEvents function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.ParseGameEvents.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.ParseGameEvents.restype = ctypes.c_char_p

        # ParseModifiers function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.ParseModifiers.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.ParseModifiers.restype = ctypes.c_char_p

        # QueryEntities function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.QueryEntities.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.QueryEntities.restype = ctypes.c_char_p

        # GetStringTables function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.GetStringTables.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.GetStringTables.restype = ctypes.c_char_p

        # ParseCombatLog function: takes char* filename, char* configJSON, returns char* JSON
        self.lib.ParseCombatLog.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.ParseCombatLog.restype = ctypes.c_char_p

        # GetParserInfo function: takes char* filename, returns char* JSON
        self.lib.GetParserInfo.argtypes = [ctypes.c_char_p]
        self.lib.GetParserInfo.restype = ctypes.c_char_p

        # ParseMatchInfo function: takes char* filename, returns char* JSON
        self.lib.ParseMatchInfo.argtypes = [ctypes.c_char_p]
        self.lib.ParseMatchInfo.restype = ctypes.c_char_p

        # FreeString function: takes char* to free
        self.lib.FreeString.argtypes = [ctypes.c_char_p]
        self.lib.FreeString.restype = None
    
    def parse_header(self, demo_file_path: str) -> HeaderInfo:
        """
        Parse the header of a Dota 2 demo file.

        Args:
            demo_file_path: Path to the .dem file (supports bz2 compressed)

        Returns:
            HeaderInfo object containing parsed header data

        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        # Convert path to bytes for C function
        path_bytes = actual_path.encode('utf-8')
        
        # Call the Go function
        result_ptr = self.lib.ParseHeader(path_bytes)
        
        if not result_ptr:
            raise ValueError("ParseHeader returned null pointer")
            
        try:
            # Convert C string result to Python string
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            
            # Parse JSON response
            result_dict = json.loads(result_json)
            
            # Convert to Pydantic model
            header_info = HeaderInfo(**result_dict)
            
            if not header_info.success:
                raise ValueError(f"Parsing failed: {header_info.error}")
            
            return header_info
            
        finally:
            # Note: Skipping FreeString call to avoid memory issues
            # Go's GC should handle this, but this creates a small memory leak
            # TODO: Fix memory management properly
            pass
    
    def parse_game_info(self, demo_file_path: str) -> GameInfo:
        """
        Parse game information from a Dota 2 demo file.

        Extracts match metadata including:
        - Match ID, game mode, winner
        - League ID (for pro matches)
        - Team IDs and tags (for pro matches)
        - All player information (names, heroes, Steam IDs, teams)
        - Draft picks and bans
        - Playback duration info

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            GameInfo object with match metadata.
            Use is_pro_match() to check if this is a league/pro match.

        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        actual_path = self._prepare_demo_file(demo_file_path)
        path_bytes = actual_path.encode('utf-8')

        result_ptr = self.lib.ParseMatchInfo(path_bytes)

        if not result_ptr:
            raise ValueError("ParseMatchInfo returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)

            # Map Go field names to Pythonic names
            players = [
                PlayerInfo(
                    hero_name=p["hero_name"],
                    player_name=p["player_name"],
                    is_fake_client=p.get("is_fake_client", False),
                    steam_id=p["steamid"],
                    team=p["game_team"]
                )
                for p in result_dict.get("player_info", [])
            ]

            picks_bans = [
                DraftEvent(
                    is_pick=pb["is_pick"],
                    team=pb["team"],
                    hero_id=pb["hero_id"]
                )
                for pb in result_dict.get("picks_bans", [])
            ]

            game_info = GameInfo(
                match_id=result_dict["match_id"],
                game_mode=result_dict["game_mode"],
                game_winner=result_dict["game_winner"],
                league_id=result_dict.get("leagueid", 0),
                end_time=result_dict.get("end_time", 0),
                radiant_team_id=result_dict.get("radiant_team_id", 0),
                dire_team_id=result_dict.get("dire_team_id", 0),
                radiant_team_tag=result_dict.get("radiant_team_tag", ""),
                dire_team_tag=result_dict.get("dire_team_tag", ""),
                players=players,
                picks_bans=picks_bans,
                playback_time=result_dict.get("playback_time", 0.0),
                playback_ticks=result_dict.get("playback_ticks", 0),
                playback_frames=result_dict.get("playback_frames", 0),
                success=result_dict["success"],
                error=result_dict.get("error")
            )

            if not game_info.success:
                raise ValueError(f"Game info parsing failed: {game_info.error}")

            return game_info

        finally:
            pass

    def parse_universal(self, demo_file_path: str, message_filter: str = "", max_messages: int = 0) -> UniversalParseResult:
        """
        Parse ALL Manta message types from a Dota 2 demo file universally.
        
        Args:
            demo_file_path: Path to the .dem file
            message_filter: Optional filter for specific message type (e.g., "CDOTAUserMsg_ChatEvent")
            max_messages: Maximum number of messages to return (0 = no limit)
            
        Returns:
            UniversalParseResult containing all captured messages
            
        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        # Convert parameters to bytes for C function
        path_bytes = actual_path.encode('utf-8')
        filter_bytes = message_filter.encode('utf-8')

        # Call the Go function
        result_ptr = self.lib.ParseUniversal(path_bytes, filter_bytes, max_messages)
        
        if not result_ptr:
            raise ValueError("ParseUniversal returned null pointer")
            
        try:
            # Convert C string result to Python string
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            
            # Parse JSON response
            result_dict = json.loads(result_json)
            
            # Convert to Pydantic model
            universal_result = UniversalParseResult(**result_dict)
            
            if not universal_result.success:
                raise ValueError(f"Universal parsing failed: {universal_result.error}")
            
            return universal_result
            
        finally:
            # Note: Skipping FreeString call to avoid memory issues
            # TODO: Fix memory management properly
            pass

    def parse_entities(
        self,
        demo_file_path: str,
        interval_ticks: int = 1800,
        max_snapshots: int = 0,
        target_ticks: Optional[List[int]] = None,
        target_heroes: Optional[List[str]] = None,
        entity_classes: Optional[List[str]] = None,
        include_raw: bool = False
    ) -> EntityParseResult:
        """
        Parse entity state snapshots from a Dota 2 demo file.

        This extracts player stats (last hits, denies, gold, etc.) and positions
        at regular intervals or at specific ticks throughout the game.

        Unlike combat log parsing, this captures data from the very start of
        the game, making it suitable for extracting per-minute statistics
        like lh_t and dn_t arrays, or hero positions at specific moments.

        Args:
            demo_file_path: Path to the .dem file
            interval_ticks: Capture snapshot every N ticks (default 1800 = ~1 min at 30 ticks/sec)
                           Ignored if target_ticks is provided.
            max_snapshots: Maximum snapshots to capture (0 = unlimited)
            target_ticks: Specific ticks to capture snapshots at. If provided, overrides
                         interval_ticks. Useful for getting hero positions at exact moments
                         (e.g., when a death occurred based on combat log tick).
            target_heroes: Filter to only include specific heroes. Use npc_dota_hero_* format
                          (e.g., ["npc_dota_hero_axe", "npc_dota_hero_lina"]). This is the
                          same format as combat log target_name/attacker_name fields.
            entity_classes: List of entity class names to include raw data for
            include_raw: Whether to include raw entity data in snapshots

        Returns:
            EntityParseResult containing player/team state snapshots over time

        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails

        Example:
            # Get position of a specific hero at death tick
            death = combat_log.entries[0]  # e.g., target_name = "npc_dota_hero_axe"
            result = parser.parse_entities(
                "match.dem",
                target_ticks=[death.tick],
                target_heroes=[death.target_name]
            )
            if result.snapshots and result.snapshots[0].players:
                hero = result.snapshots[0].players[0]
                print(f"{hero.hero_name} died at ({hero.position_x}, {hero.position_y})")
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        # Build config
        config = EntityParseConfig(
            interval_ticks=interval_ticks,
            max_snapshots=max_snapshots,
            target_ticks=target_ticks or [],
            target_heroes=target_heroes or [],
            entity_classes=entity_classes or [],
            include_raw=include_raw
        )

        # Convert parameters to bytes for C function
        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        # Call the Go function
        result_ptr = self.lib.ParseEntities(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("ParseEntities returned null pointer")

        try:
            # Convert C string result to Python string
            result_json = ctypes.string_at(result_ptr).decode('utf-8')

            # Parse JSON response
            result_dict = json.loads(result_json)

            # Convert to Pydantic model
            entity_result = EntityParseResult(**result_dict)

            if not entity_result.success:
                raise ValueError(f"Entity parsing failed: {entity_result.error}")

            return entity_result

        finally:
            # Note: Skipping FreeString call to avoid memory issues
            # TODO: Fix memory management properly
            pass

    def parse_game_events(
        self,
        demo_file_path: str,
        event_filter: str = "",
        event_names: Optional[List[str]] = None,
        max_events: int = 0,
        capture_types: bool = True
    ) -> GameEventsResult:
        """
        Parse game events from a Dota 2 demo file.

        Game events are named events like "dota_combatlog", "player_death",
        "dota_tower_kill", etc. There are 364+ event types available.

        Args:
            demo_file_path: Path to the .dem file
            event_filter: Filter events by name (substring match)
            event_names: List of specific event names to capture
            max_events: Max events to capture (0 = unlimited)
            capture_types: Whether to capture event type definitions

        Returns:
            GameEventsResult containing parsed game events
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        config = GameEventsConfig(
            event_filter=event_filter,
            event_names=event_names or [],
            max_events=max_events,
            capture_types=capture_types
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self.lib.ParseGameEvents(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("ParseGameEvents returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = GameEventsResult(**result_dict)

            if not result.success:
                raise ValueError(f"Game events parsing failed: {result.error}")

            return result
        finally:
            pass

    def parse_modifiers(
        self,
        demo_file_path: str,
        max_modifiers: int = 0,
        debuffs_only: bool = False,
        auras_only: bool = False
    ) -> ModifiersResult:
        """
        Parse modifier/buff entries from a Dota 2 demo file.

        Modifiers are buffs and debuffs applied to units. This tracks
        modifier creation, duration, stack counts, and more.

        Args:
            demo_file_path: Path to the .dem file
            max_modifiers: Max modifiers to capture (0 = unlimited)
            debuffs_only: Only capture debuffs
            auras_only: Only capture auras

        Returns:
            ModifiersResult containing modifier entries
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        config = ModifiersConfig(
            max_modifiers=max_modifiers,
            debuffs_only=debuffs_only,
            auras_only=auras_only
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self.lib.ParseModifiers(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("ParseModifiers returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = ModifiersResult(**result_dict)

            if not result.success:
                raise ValueError(f"Modifier parsing failed: {result.error}")

            return result
        finally:
            pass

    def query_entities(
        self,
        demo_file_path: str,
        class_filter: str = "",
        class_names: Optional[List[str]] = None,
        property_filter: Optional[List[str]] = None,
        at_tick: int = 0,
        max_entities: int = 0
    ) -> EntitiesResult:
        """
        Query entity states from a Dota 2 demo file.

        This provides full access to any entity in the game: heroes, buildings,
        wards, couriers, creeps, neutrals, etc.

        Args:
            demo_file_path: Path to the .dem file
            class_filter: Filter by class name (substring match)
            class_names: List of specific class names to capture
            property_filter: Only include these properties (empty = all)
            at_tick: Capture entities at this tick (0 = end of file)
            max_entities: Max entities to return (0 = unlimited)

        Returns:
            EntitiesResult containing entity data
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        config = EntitiesConfig(
            class_filter=class_filter,
            class_names=class_names or [],
            property_filter=property_filter or [],
            at_tick=at_tick,
            max_entities=max_entities
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self.lib.QueryEntities(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("QueryEntities returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = EntitiesResult(**result_dict)

            if not result.success:
                raise ValueError(f"Entity querying failed: {result.error}")

            return result
        finally:
            pass

    def get_string_tables(
        self,
        demo_file_path: str,
        table_names: Optional[List[str]] = None,
        include_values: bool = False,
        max_entries: int = 100
    ) -> StringTablesResult:
        """
        Extract string table data from a Dota 2 demo file.

        String tables contain mappings for hero names, ability names,
        item names, and other game data.

        Args:
            demo_file_path: Path to the .dem file
            table_names: Tables to extract (empty = all)
            include_values: Include value data (can be large)
            max_entries: Max entries per table

        Returns:
            StringTablesResult containing string table data
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        config = StringTablesConfig(
            table_names=table_names or [],
            include_values=include_values,
            max_entries=max_entries
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self.lib.GetStringTables(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("GetStringTables returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = StringTablesResult(**result_dict)

            if not result.success:
                raise ValueError(f"String table extraction failed: {result.error}")

            return result
        finally:
            pass

    def parse_combat_log(
        self,
        demo_file_path: str,
        types: Optional[List[int]] = None,
        max_entries: int = 0,
        heroes_only: bool = False
    ) -> CombatLogResult:
        """
        Parse structured combat log entries from a Dota 2 demo file.

        Combat log contains damage, healing, kills, ability usage, item
        purchases, and more. Note: Combat log data may be missing for the
        first ~12 minutes of SourceTV replays - use parse_entities() for
        early game stats.

        Args:
            demo_file_path: Path to the .dem file
            types: Filter by combat log type (empty = all)
            max_entries: Max entries (0 = unlimited)
            heroes_only: Only hero-related entries

        Returns:
            CombatLogResult containing structured combat log entries
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        config = CombatLogConfig(
            types=types or [],
            max_entries=max_entries,
            heroes_only=heroes_only
        )

        path_bytes = actual_path.encode('utf-8')
        config_json = config.model_dump_json().encode('utf-8')

        result_ptr = self.lib.ParseCombatLog(path_bytes, config_json)

        if not result_ptr:
            raise ValueError("ParseCombatLog returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = CombatLogResult(**result_dict)

            if not result.success:
                raise ValueError(f"Combat log parsing failed: {result.error}")

            return result
        finally:
            pass

    def get_parser_info(self, demo_file_path: str) -> ParserInfo:
        """
        Get parser state information from a Dota 2 demo file.

        This includes game build, tick counts, available string tables,
        and entity counts.

        Args:
            demo_file_path: Path to the .dem file

        Returns:
            ParserInfo containing parser state information
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")

        # Handle bz2 compression if needed
        actual_path = self._prepare_demo_file(demo_file_path)

        path_bytes = actual_path.encode('utf-8')

        result_ptr = self.lib.GetParserInfo(path_bytes)

        if not result_ptr:
            raise ValueError("GetParserInfo returned null pointer")

        try:
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            result_dict = json.loads(result_json)
            result = ParserInfo(**result_dict)

            if not result.success:
                raise ValueError(f"Parser info extraction failed: {result.error}")

            return result
        finally:
            pass

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
        parser = MantaParser()
        header = parser.parse_header(demo_file)
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