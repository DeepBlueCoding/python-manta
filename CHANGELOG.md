# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with [PEP 440](https://peps.python.org/pep-0440/) version identifiers.

## [1.4.5.2] - 2025-12-05

### Added
- **Commitizen integration** for automated versioning and changelog generation
- **HeroSnapshot combat stats**: `armor`, `magic_resistance`, `damage_min`, `damage_max`, `attack_range`
- **HeroSnapshot attributes**: `strength`, `agility`, `intellect`
- **MCP use-case documentation** with 5 validated examples (docs/guides/use-cases.md)
- **MCP use-case validation tests** (35 tests in test_mcp_usecase_validation.py)
- **Parser v2 API**: Unified single-pass parsing with `parser.parse(**collectors)`
- **Entity snapshots**: `parser.snapshot(target_tick=...)` for hero state at any tick
- **Index/Seek API**: `parser.build_index()` for random access
- **GameInfo model**: Complete game info with draft, teams, players, and winner
- `DamageType.COMPOSITE = 3` (legacy damage type)
- `DamageType.HP_REMOVAL = 4`
- `Team.NEUTRAL = 4`
- `ChatWheelMessage` enum for chat wheel phrases
- `GameActivity` enum for game activity types
- `EntityType` enum for entity classification
- `RuneType` enum for rune types
- `Hero` enum with all 145 heroes and ID/name lookup
- `NeutralItem` and `NeutralItemTier` enums

### Changed
- **Version format**: Migrated to PEP 440 format
- **CI/CD pipelines**: Updated for PEP 440 version detection
- Refactored to Pythonic model names (e.g., `HeroSnapshot` instead of `hero_snapshot`)
- Removed convenience functions in favor of `Parser` class methods

### Fixed
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

[1.4.5.2]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.5...v1.4.5.2
[1.4.5]: https://github.com/DeepBlueCoding/python-manta/compare/v1.4.0...v1.4.5
[1.4.0]: https://github.com/DeepBlueCoding/python-manta/compare/v0.1.0...v1.4.0
[0.1.0]: https://github.com/DeepBlueCoding/python-manta/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/DeepBlueCoding/python-manta/releases/tag/v0.0.1
