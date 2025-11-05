"""
Python interface for Manta Dota 2 replay parser using ctypes.
Provides basic file header reading functionality through Go CGO wrapper.
"""
import ctypes
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


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


class CHeroSelectEvent(BaseModel):
    """Pydantic model for hero select event (pick/ban) - matches Manta naming."""
    is_pick: bool      # true for pick, false for ban
    team: int         # 2=Radiant, 3=Dire
    hero_id: int      # Hero ID


class CDotaGameInfo(BaseModel):
    """Pydantic model for Dota game info including draft - matches Manta naming."""
    picks_bans: List[CHeroSelectEvent]
    success: bool
    error: Optional[str] = None


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


class MantaParser:
    """Python wrapper for Manta Dota 2 replay parser."""
    
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
    
    def _setup_function_signatures(self):
        """Configure ctypes function signatures for the shared library."""
        # ParseHeader function: takes char* filename, returns char* JSON
        self.lib.ParseHeader.argtypes = [ctypes.c_char_p]
        self.lib.ParseHeader.restype = ctypes.c_char_p
        
        # ParseDraft function: takes char* filename, returns char* JSON
        self.lib.ParseDraft.argtypes = [ctypes.c_char_p]
        self.lib.ParseDraft.restype = ctypes.c_char_p
        
        # ParseUniversal function: takes char* filename, char* filter, int maxMessages, returns char* JSON
        self.lib.ParseUniversal.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        self.lib.ParseUniversal.restype = ctypes.c_char_p
        
        # FreeString function: takes char* to free
        self.lib.FreeString.argtypes = [ctypes.c_char_p]
        self.lib.FreeString.restype = None
    
    def parse_header(self, demo_file_path: str) -> HeaderInfo:
        """
        Parse the header of a Dota 2 demo file.
        
        Args:
            demo_file_path: Path to the .dem file
            
        Returns:
            HeaderInfo object containing parsed header data
            
        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")
        
        # Convert path to bytes for C function
        path_bytes = demo_file_path.encode('utf-8')
        
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
    
    def parse_draft(self, demo_file_path: str) -> CDotaGameInfo:
        """
        Parse the draft phase (picks/bans) from a Dota 2 demo file.
        
        Args:
            demo_file_path: Path to the .dem file
            
        Returns:
            CDotaGameInfo object containing draft picks and bans
            
        Raises:
            FileNotFoundError: If demo file doesn't exist
            ValueError: If parsing fails
        """
        if not os.path.exists(demo_file_path):
            raise FileNotFoundError(f"Demo file not found: {demo_file_path}")
        
        # Convert path to bytes for C function
        path_bytes = demo_file_path.encode('utf-8')
        
        # Call the Go function
        result_ptr = self.lib.ParseDraft(path_bytes)
        
        if not result_ptr:
            raise ValueError("ParseDraft returned null pointer")
            
        try:
            # Convert C string result to Python string
            result_json = ctypes.string_at(result_ptr).decode('utf-8')
            
            # Parse JSON response
            result_dict = json.loads(result_json)
            
            # Convert to Pydantic model
            draft_info = CDotaGameInfo(**result_dict)
            
            if not draft_info.success:
                raise ValueError(f"Draft parsing failed: {draft_info.error}")
            
            return draft_info
            
        finally:
            # Note: Skipping FreeString call to avoid memory issues
            # TODO: Fix memory management properly
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
        
        # Convert parameters to bytes for C function
        path_bytes = demo_file_path.encode('utf-8')
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


# Convenience functions for quick parsing
def parse_demo_header(demo_file_path: str) -> HeaderInfo:
    """
    Quick function to parse demo file header.
    
    Args:
        demo_file_path: Path to the .dem file
        
    Returns:
        HeaderInfo object containing parsed header data
    """
    parser = MantaParser()
    return parser.parse_header(demo_file_path)


def parse_demo_draft(demo_file_path: str) -> CDotaGameInfo:
    """
    Quick function to parse demo file draft (picks/bans).
    
    Args:
        demo_file_path: Path to the .dem file
        
    Returns:
        CDotaGameInfo object containing draft picks and bans
    """
    parser = MantaParser()
    return parser.parse_draft(demo_file_path)


def parse_demo_universal(demo_file_path: str, message_filter: str = "", max_messages: int = 0) -> UniversalParseResult:
    """
    Quick function to universally parse ALL Manta message types from demo file.
    
    Args:
        demo_file_path: Path to the .dem file
        message_filter: Optional filter for specific message type (e.g., "CDOTAUserMsg_ChatEvent")
        max_messages: Maximum number of messages to return (0 = no limit)
        
    Returns:
        UniversalParseResult containing all captured messages
    """
    parser = MantaParser()
    return parser.parse_universal(demo_file_path, message_filter, max_messages)


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
        header = parse_demo_header(demo_file)
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