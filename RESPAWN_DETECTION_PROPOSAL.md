# Hero Respawn Detection Proposal

## Problem Statement

Dota 2 replays do not contain explicit "hero respawned" events. Respawns are implicit - a hero dies and then reappears at the fountain after a delay.

## Findings from Testing

### 1. Combat Log DEATH Events Work Well
- Combat log type `DEATH (4)` captures all hero deaths
- Includes `will_reincarnate` flag for Aegis/Wraith King respawns
- Contains the exact `tick` when death occurred

### 2. Time Reference Issue Discovered
The combat log's `game_time` field does NOT match the entity snapshot time system:

| Source | Hoodwink Death | Tick |
|--------|----------------|------|
| Combat Log `game_time` | 03:07 | - |
| Combat Log `tick` | - | 36146 |
| Calculated `game_started + game_time*30` | - | 35268 |
| **Offset** | ~30 seconds | ~878 ticks |

**Recommendation**: Always use `tick` from combat log entries for time-accurate operations.

### 3. Entity Snapshots Confirm Deaths and Respawns
Using the combat log `tick` directly:
```
Hoodwink died:
  At combat log tick:     DEAD, HP=0/632, deaths=1
  +30s (900 ticks):       ALIVE, HP=610/610, deaths=1  ← RESPAWNED!
```

### 4. Reincarnation Detection Works
The `will_reincarnate` flag correctly identifies Aegis and Wraith King respawns:
- Troll Warlord at 31:50 (Aegis)
- Medusa at 49:41 (Aegis)

## Proposed Solution

### Option A: Pure Combat Log Derivation (Recommended)

Calculate respawn time from death events without needing entity snapshots:

```python
class HeroRespawnEvent(BaseModel):
    """Derived hero respawn event."""
    hero_name: str              # e.g., "npc_dota_hero_hoodwink"
    death_tick: int             # Tick when hero died
    death_game_time: float      # Game time from combat log (note: has offset)
    respawn_tick: int           # Calculated respawn tick
    respawn_game_time: float    # Calculated respawn game time
    respawn_duration: float     # Seconds dead
    is_reincarnation: bool      # True for Aegis/WK respawn
    killer: str                 # Who killed the hero
    death_index: int            # 1st, 2nd, 3rd death etc.

def calculate_respawn_time(level: int) -> float:
    """Dota 2 respawn formula: 6 + (level * 0.9) seconds."""
    return 6.0 + (level * 0.9)

def derive_respawn_events(combat_log_deaths: List[CombatLogEntry]) -> List[HeroRespawnEvent]:
    """Derive respawn events from death combat log entries."""
    # Group deaths by hero
    # Calculate respawn time based on level (from snapshot or estimated)
    # Handle reincarnation (5 second respawn)
    # Return list of respawn events
```

**Pros:**
- Single-pass extraction (no additional parsing needed)
- Uses only existing combat log data
- Fast and efficient

**Cons:**
- `target_hero_level` is always 0 in current parsing (bug to fix)
- Respawn time is estimated, not confirmed from entity state

### Option B: Snapshot-Validated Respawns

Use entity snapshots to confirm exact respawn time:

```python
def get_respawn_events_validated(
    parser: Parser,
    combat_log_deaths: List[CombatLogEntry]
) -> List[HeroRespawnEvent]:
    """Get respawn events with exact timing from entity snapshots."""
    respawns = []

    for death in combat_log_deaths:
        # Get hero state at death tick - should be dead
        # Binary search forward to find when is_alive becomes True
        # Record exact respawn tick
```

**Pros:**
- Exact respawn timing
- Handles edge cases (buyback, respawn talents)

**Cons:**
- Requires multiple snapshot seeks (slower)
- More complex implementation

### Option C: Hybrid Approach (Recommended for v1)

1. Calculate estimated respawn from combat log
2. Optionally validate with a single snapshot check

```python
def get_respawn_events(
    parser: Parser,
    validate: bool = False
) -> List[HeroRespawnEvent]:
    """Extract hero respawn events from a demo file.

    Args:
        parser: Parser instance bound to demo file
        validate: If True, confirm respawn timing with entity snapshots

    Returns:
        List of respawn events sorted by time
    """
```

## Implementation Plan

### Phase 1: Fix Known Issues
1. **Fix `target_hero_level` always being 0** in DEATH combat log entries
   - Investigate Go wrapper data extraction
   - Ensure level is captured from combat log protobuf

### Phase 2: Add Respawn Model and Utility
1. Add `HeroRespawnEvent` model to `manta_python.py`
2. Add `calculate_respawn_time()` utility function
3. Add `derive_respawn_events()` function

### Phase 3: Add Parser Integration
1. Add optional `respawns` collector to `Parser.parse()`
   ```python
   result = parser.parse(
       combat_log={"types": [CombatLogType.DEATH]},
       respawns=True  # Automatically derives respawns from deaths
   )
   print(result.respawns)  # List[HeroRespawnEvent]
   ```

## Respawn Time Formula Reference

### Standard Respawn
```
respawn_time = 6 + (level * 0.9)  # seconds
```

| Level | Respawn Time |
|-------|--------------|
| 1 | 6.9s |
| 10 | 15.0s |
| 15 | 19.5s |
| 20 | 24.0s |
| 25 | 28.5s |
| 30 | 33.0s |

### Special Cases
- **Aegis**: 5 seconds (with 3 second animation delay)
- **Wraith King Reincarnation**: 3 seconds (ability dependent)
- **Buyback**: Instant (0 seconds)
- **Bloodstone**: Reduces respawn time

## Testing Strategy

1. **Unit tests**: Test respawn time calculation
2. **Integration tests**: Validate respawn events against known match data
3. **Edge cases**: Aegis, WK, buyback detection

## Files to Modify

| File | Changes |
|------|---------|
| `src/python_manta/manta_python.py` | Add `HeroRespawnEvent` model, utility functions |
| `src/python_manta/__init__.py` | Export new model |
| `go_wrapper/data_parser.go` | Fix `target_hero_level` extraction |
| `tests/` | Add respawn detection tests |

## Summary

The recommended approach is **Option C (Hybrid)** for the initial implementation:
1. Derive respawns from DEATH combat log events
2. Calculate expected respawn time using Dota 2 formula
3. Optionally validate with entity snapshots for precision

This approach:
- Works with existing parsing infrastructure
- Is efficient (single-pass for basic use)
- Can be enhanced later with more precise validation
