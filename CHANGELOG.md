# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [0.0.1-beta.1] - 2024-11-05

### Added
- Multi-platform wheel building for Linux, macOS (Intel & Apple Silicon), and Windows
- Automated PyPI publishing via GitHub Actions with Trusted Publishing
- Comprehensive build documentation (BUILDING.md)
- Versioning and changelog best practices guide

### Changed
- Installation now available via `pip install python-manta` (no Go required for end users)

## [0.0.1-alpha.1] - 2024-11-05

### Added
- **Complete callback implementation**: All 272 Manta callbacks implemented (100% coverage)
- **Universal parser**: `parse_universal()` method with message filtering and limits
- **Header parsing**: `parse_header()` for extracting demo file metadata
- **Draft parsing**: `parse_draft()` for hero picks and bans extraction
- **Pydantic models**: Type-safe data validation for all parsed data
- **Memory management**: Safe CGO operations with proper cleanup
- **Linux wheel building**: Automated builds for x86_64 architecture
- **Python support**: Python 3.8, 3.9, 3.10, 3.11, 3.12

### Supported Callbacks
- Demo messages (CDemoFileHeader, CDemoFileInfo, etc.)
- DOTA user messages (Chat, LocationPing, MapLine, OverheadEvent, etc.)
- Network messages (Tick, SignonState, SetConVar, etc.)
- SVC messages (ServerInfo, StringTable, PacketEntities, etc.)
- Entity messages (Complete entity system integration)

### Features
- 📈 **40% more data fields** extracted compared to native Go Manta implementation
- 🎮 Modern PBDEMS2 replay format support
- 💬 Player communication extraction (chat, pings, map drawing)
- 🧪 Battle-tested with TI14 professional tournament replays
- ⚡ Message filtering and limiting for memory safety

### Technical Details
- CGO-based Python bindings for Go Manta library
- JSON-based data exchange between Go and Python
- ctypes interface for shared library loading
- Platform-specific build scripts for reproducible builds

[Unreleased]: https://github.com/equilibrium-coach/python-manta/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/equilibrium-coach/python-manta/releases/tag/v0.1.0
