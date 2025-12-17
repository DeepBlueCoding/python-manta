"""Replay download and cache utility.

Similar to dotabuff/manta's util_test.go - downloads replays from GCS
on first use and caches them locally.

Cache location priority:
1. DOTA_REPLAY_CACHE env var (if set)
2. Shared project cache: ~/.cache/dota-replays/ or .data/replays/
3. Local replays/ directory (fallback)
"""

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass


# GCS bucket URL
GCS_BUCKET_URL = "https://storage.googleapis.com/dota-replays"


def _get_cache_dir() -> Path:
    """Get cache directory, checking multiple locations."""
    # 1. Environment variable override
    if env_cache := os.environ.get("DOTA_REPLAY_CACHE"):
        return Path(env_cache)

    # 2. Shared project cache (equilibrium_coach/.data/replays/)
    shared_cache = Path(__file__).parent.parent.parent / ".data" / "replays"
    if shared_cache.exists():
        return shared_cache

    # 3. User cache directory
    user_cache = Path.home() / ".cache" / "dota-replays"
    if user_cache.exists():
        return user_cache

    # 4. Create shared cache if parent exists
    if shared_cache.parent.exists():
        shared_cache.mkdir(parents=True, exist_ok=True)
        return shared_cache

    # 5. Fallback to local replays/ directory
    local_cache = Path(__file__).parent.parent / "replays"
    local_cache.mkdir(parents=True, exist_ok=True)
    return local_cache


# Lazy-loaded cache directory
_cache_dir = None

def get_cache_dir() -> Path:
    """Get the replay cache directory (cached)."""
    global _cache_dir
    if _cache_dir is None:
        _cache_dir = _get_cache_dir()
    return _cache_dir


@dataclass
class TestReplay:
    """Test replay definition with expected values for validation."""
    match_id: int
    description: str
    # Expected values for validation
    game_build: int = 0
    radiant_team_id: int = 0
    dire_team_id: int = 0
    game_winner: int = 0  # 2=Radiant, 3=Dire


# Test replays hosted on GCS
TEST_REPLAYS = {
    8447659831: TestReplay(
        match_id=8447659831,
        description="Team Spirit vs Tundra - TI match",
        game_build=10512,
        radiant_team_id=7119388,  # Team Spirit
        dire_team_id=8291895,     # Tundra
        game_winner=2,            # Radiant won
    ),
    8461956309: TestReplay(
        match_id=8461956309,
        description="TI 2025 Grand Finals Game 5",
        game_build=10512,
        game_winner=2,
    ),
}

# Default test replay (primary)
PRIMARY_MATCH_ID = 8447659831
SECONDARY_MATCH_ID = 8461956309


def get_replay_path(match_id: int) -> Path:
    """Get local path for a replay file."""
    return get_cache_dir() / f"{match_id}.dem"


def get_replay_url(match_id: int) -> str:
    """Get GCS URL for a replay file."""
    return f"{GCS_BUCKET_URL}/{match_id}.dem"


def ensure_replay(match_id: int) -> Path:
    """Ensure replay is downloaded and return local path.

    Downloads from GCS if not already cached locally.
    """
    path = get_replay_path(match_id)

    # Check local cache first
    if path.exists():
        return path

    # Download from GCS
    url = get_replay_url(match_id)
    print(f"Downloading replay {match_id} from {url}...")

    _download_file(url, path)

    print(f"Downloaded replay {match_id} to {path}")
    return path


def _download_file(url: str, dest: Path) -> None:
    """Download file from URL to destination path."""
    import urllib.request
    import shutil

    # Download to temp file first, then move (atomic)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".dem") as tmp:
        tmp_path = Path(tmp.name)

    try:
        with urllib.request.urlopen(url) as response:
            with open(tmp_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

        # Move to final destination
        shutil.move(str(tmp_path), str(dest))
    except Exception:
        # Clean up temp file on error
        tmp_path.unlink(missing_ok=True)
        raise


def get_primary_demo() -> str:
    """Get path to primary test demo file."""
    path = ensure_replay(PRIMARY_MATCH_ID)
    return str(path)


def get_secondary_demo() -> str:
    """Get path to secondary test demo file."""
    path = ensure_replay(SECONDARY_MATCH_ID)
    return str(path)


def get_test_replay(match_id: int) -> TestReplay:
    """Get test replay metadata by match ID."""
    if match_id not in TEST_REPLAYS:
        raise ValueError(f"Unknown test replay: {match_id}")
    return TEST_REPLAYS[match_id]
