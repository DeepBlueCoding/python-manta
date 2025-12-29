# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) version identifiers.

## [1.4.7.3] - 2025-12-29

### Fixed
- **Manta library version**: Updated from v1.4.5 to v1.4.7 to fix buffer overread errors in certain replays

## [1.4.7.2] - 2025-12-28

### Added
- **Attacks collector**: Track hero attacks with `parser.parse(attacks={"max_events": 50000})`
  - Melee attacks: `target_x`, `target_y`, `target_entity_id`, `attack_record_id`
  - Ranged attacks: `projectile_source_x`, `projectile_source_y`, `projectile_speed`
  - Common fields: `attacker`, `target`, `game_time`, `tick`, `is_projectile`
- **Entity deaths collector**: Track creep deaths for wave detection with `parser.parse(entity_deaths={"creeps_only": True})`
- **Hero level injection**: Combat log entries now include `attacker_hero_level` and `target_hero_level`
- **HeroSnapshot.entity_id**: Entity ID field for cross-referencing with other data

### Fixed
- **Panic recovery for all CGO exports**: Added `defer recover()` to all 14 exported parsing functions to gracefully handle buffer overread panics from the manta library
- **AttacksResult struct**: Added missing `Success` and `Error` fields for consistent error reporting

### Changed
- All parsing functions now return proper JSON error responses instead of crashing on malformed replay data
- Improved error messages to include panic details for debugging
- Reorganized test suite with cached fixtures (10x faster test runs)

## [1.4.5.3] - 2025-12-12

### Added
- **Python 3.13 support**: Pre-built wheels now available for Python 3.13 on Linux, macOS (Intel & Apple Silicon), and Windows

## [1.4.5.2] - 2025-12-07

### Added
- **Parser v2 API**: Unified single-pass parsing with `parser.parse(**collectors)`
- **Entity snapshots**: `parser.snapshot(target_tick=...)` for hero state at any tick
- **Index/Seek API**: `parser.build_index()` for random access to replay data
- **GameInfo model**: Complete game info with draft, teams, players, and winner
- **HeroSnapshot combat stats**: `armor`, `magic_resistance`, `damage_min`, `damage_max`, `attack_range`
- **HeroSnapshot attributes**: `strength`, `agility`, `intellect`
- **HeroSnapshot economy data**: `gold`, `net_worth`, `last_hits`, `denies`, `gpm`, `xpm`
- **Hero ability tracking**: `abilities` list with `level`, `cooldown`, `max_cooldown`, `slot`, `is_ultimate`
- **Hero talent tracking**: `talents` list with `tier`, `is_left`, `name`
- **NeutralCampType enum**: Camp types (`SMALL=0`, `MEDIUM=1`, `HARD=2`, `ANCIENT=3`)
- **ChatWheelMessage enum**: Chat wheel phrases
- **GameActivity enum**: Game activity types
- **EntityType enum**: Entity classification
- **RuneType enum**: Rune types
- **Hero enum**: All 145 heroes with ID/name lookup
- **NeutralItem and NeutralItemTier enums**: Neutral items with tier classification
- `DamageType.COMPOSITE = 3` (legacy damage type)
- `DamageType.HP_REMOVAL = 4`
- `Team.NEUTRAL = 4`
- **MCP use-case documentation**: 5 validated examples in docs/guides/use-cases.md

### Changed
- **Version format**: Migrated to PEP 440 format (4-part: `manta_major.manta_minor.manta_patch.python_release`)
- Refactored to Pythonic model names (e.g., `HeroSnapshot` instead of `hero_snapshot`)
- Removed convenience functions in favor of `Parser` class methods
- Removed legacy `PlayerState` class (consolidated into `HeroSnapshot`)
- Optimized test suite with module-scoped fixtures for faster test execution

### Fixed
- Entity parsing now correctly populates player positions and hero names
- Python 3.8 compatibility with future annotations import
- Field aliases for game_info.players mapping

## [1.4.5] - 2024-11-30

### Changed
- Synchronized with upstream manta v1.4.5
- Consolidated documentation and removed redundant files

### Fixed
- PyPI token authentication for automated publishing

## [1.4.0] - 2024-11

### Changed
- Version synchronized with upstream dotabuff/manta v1.4.x releases
- Improved CI/CD workflow for multi-platform builds

## [0.1.0] - 2024-11

### Added
- Multi-platform wheel building for Linux, macOS (Intel & Apple Silicon), and Windows
- Automated PyPI publishing via GitHub Actions
- Centralized manta version management via `.manta-version` file

### Changed
- Installation now available via `pip install python-manta` (no Go required for end users)

## [0.0.1] - 2024-11-05

### Added
- **Complete callback implementation**: All 272 Manta callbacks implemented (100% coverage)
- **Universal parser**: `parse_universal()` method with message filtering and limits
- **Header parsing**: `parse_header()` for extracting demo file metadata
- **Draft parsing**: `parse_draft()` for hero picks and bans extraction
- **Pydantic models**: Type-safe data validation for all parsed data
- **Memory management**: Safe CGO operations with proper cleanup
- **Python support**: Python 3.8, 3.9, 3.10, 3.11, 3.12

### Supported Callbacks
- Demo messages (CDemoFileHeader, CDemoFileInfo, etc.)
- DOTA user messages (Chat, LocationPing, MapLine, OverheadEvent, etc.)
- Network messages (Tick, SignonState, SetConVar, etc.)
- SVC messages (ServerInfo, StringTable, PacketEntities, etc.)
- Entity messages (Complete entity system integration)

### Features
- 40% more data fields extracted compared to native Go Manta implementation
- Modern PBDEMS2 replay format support
- Player communication extraction (chat, pings, map drawing)
- Battle-tested with TI14 professional tournament replays
- Message filtering and limiting for memory safety

### Technical Details
- CGO-based Python bindings for Go Manta library
- JSON-based data exchange between Go and Python
- ctypes interface for shared library loading
- Platform-specific build scripts for reproducible builds

[1.4.7.3]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.7.2...v1.4.7.3
[1.4.7.2]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.5.3...v1.4.7.2
[1.4.5.3]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.5.2...v1.4.5.3
[1.4.5.2]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.5...v1.4.5.2
[1.4.5]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.0...v1.4.5
[1.4.0]: https://github.com/DeepBlueCoding/python-manta/compare/v0.1.0...v1.4.0
[0.1.0]: https://github.com/DeepBlueCoding/python-manta/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/DeepBlueCoding/python-manta/releases/tag/v0.0.1
