# Building Python Manta

This document explains how Python Manta is built and distributed as a standalone pip package.

## Overview

Python Manta is a Python wrapper around the Go-based Manta library. To make it work as a standalone pip package **without requiring Go on the user's machine**, we:

1. **Pre-compile** the Go code into platform-specific shared libraries (`.so`, `.dylib`, `.dll`)
2. **Bundle** these libraries into Python wheels for each platform
3. **Distribute** via PyPI so users just run `pip install python-manta`

## User Experience

### End Users (NO Go Required!)

Once the wheels are published to PyPI, users install with zero Go dependencies:

```bash
pip install python-manta
```

The wheel automatically includes the pre-compiled shared library for their platform:
- **Linux**: `libmanta_wrapper.so` (x86_64)
- **macOS**: `libmanta_wrapper.so` (x86_64 and ARM64/Apple Silicon)
- **Windows**: `libmanta_wrapper.so` (actually a renamed `.dll`)

### Developers (Go Required for Building)

To build from source, you need:
- Go 1.19+
- Python 3.8+
- The Manta repository

```bash
./build.sh  # Local development build
```

## Automated Wheel Building

We use **GitHub Actions** with **cibuildwheel** to build wheels for all platforms automatically.

### Supported Platforms

| Platform | Architectures | Python Versions |
|----------|--------------|-----------------|
| Linux (manylinux) | x86_64 | 3.8, 3.9, 3.10, 3.11, 3.12 |
| macOS | x86_64, ARM64 | 3.8, 3.9, 3.10, 3.11, 3.12 |
| Windows | AMD64 | 3.8, 3.9, 3.10, 3.11, 3.12 |

This creates **30+ different wheel files** covering all combinations!

### Build Workflow

The GitHub Actions workflow (`.github/workflows/build-wheels.yml`) triggers on:
- Push to `main`/`master` branch (for testing)
- Push of version tags like `v0.1.0` (for releases)
- Pull requests (for validation)
- Manual trigger via workflow_dispatch

#### Build Process Per Platform

**Linux:**
```bash
tools/before_build_linux.sh
  ├── Install Go 1.21.5
  ├── Clone/update Manta dependency
  ├── Build: go build -buildmode=c-shared
  └── Copy libmanta_wrapper.so to Python package
```

**macOS:**
```bash
tools/before_build_macos.sh
  ├── Install Go for x86_64 or ARM64
  ├── Clone/update Manta dependency
  ├── Build: go build -buildmode=c-shared
  └── Copy libmanta_wrapper.so to Python package
```

**Windows:**
```bash
tools/before_build_windows.sh
  ├── Install Go for Windows
  ├── Clone/update Manta dependency
  ├── Build: go build -buildmode=c-shared (creates .dll)
  ├── Rename .dll to .so (for ctypes compatibility)
  └── Copy to Python package
```

### cibuildwheel Configuration

Key environment variables in the workflow:

```yaml
CIBW_BEFORE_BUILD_LINUX: bash tools/before_build_linux.sh
CIBW_BEFORE_BUILD_MACOS: bash tools/before_build_macos.sh
CIBW_BEFORE_BUILD_WINDOWS: bash tools/before_build_windows.sh

# Specify which Python versions to build for
CIBW_BUILD: cp38-* cp39-* cp310-* cp311-* cp312-*

# Test each wheel after building
CIBW_TEST_COMMAND: python -c "import python_manta; print('import success')"
```

### PyPI Publishing

When you push a version tag (e.g., `v0.1.0`), the workflow:

1. Builds all wheels (Linux, macOS, Windows)
2. Downloads all artifacts
3. Publishes to PyPI using **Trusted Publishing** (no API tokens needed!)

```yaml
publish:
  needs: [linux-wheels, macos-wheels, windows-wheels]
  if: github.event_name == 'push' && startsWith(github.ref, 'refs/tags/v')
```

## Setting Up PyPI Publishing

### 1. Configure Trusted Publishing on PyPI

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - **PyPI Project Name**: `python-manta`
   - **Owner**: `equilibrium-coach` (or your GitHub org/user)
   - **Repository**: `python-manta`
   - **Workflow**: `build-wheels.yml`
   - **Environment**: (leave blank)

This allows GitHub Actions to publish without storing API tokens!

### 2. Create a Release

```bash
# Update version in pyproject.toml
vim pyproject.toml  # Change version = "0.1.0" to "0.2.0"

# Commit and tag
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

GitHub Actions will automatically build and publish to PyPI!

## Local Testing

### Build Wheels Locally

You can test wheel building locally using cibuildwheel:

```bash
# Install cibuildwheel
pip install cibuildwheel

# Build for current platform only
python -m cibuildwheel --platform linux --output-dir dist

# Test the wheel
pip install dist/python_manta-*.whl
python -c "import python_manta; print('Success!')"
```

### Manual Build

For development, use the standard build script:

```bash
./build.sh  # Builds the .so file and sets up the package
```

## Troubleshooting

### "Go not found" during wheel build

The `before_build_*.sh` scripts automatically install Go. If this fails:
- Check the Go version in the script (default: 1.21.5)
- Ensure curl/wget are available
- Check network connectivity to https://go.dev/

### "Manta repository not found"

The `prepare_manta.sh` script clones the Manta repo automatically. Check:
- Network connectivity to GitHub
- Git is installed in the build environment

### Import fails on specific platform

Check:
1. The `.so` file was actually included in the wheel
2. The correct architecture was built (x86_64 vs ARM64)
3. Python version compatibility

Extract and inspect a wheel:
```bash
unzip -l dist/python_manta-*.whl
```

Should contain: `python_manta/libmanta_wrapper.so`

### Windows-specific issues

On Windows, the shared library is actually a `.dll` but renamed to `.so`. Python's ctypes can load it fine. If you see import errors:
- Check that MinGW-w64 was available during build
- Verify the .dll was successfully renamed to .so
- Check Windows Defender didn't quarantine the file

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│  Developer pushes tag v0.1.0             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  GitHub Actions Workflow Triggers        │
└──────────────┬──────────────────────────┘
               │
       ┌───────┼───────┐
       ▼       ▼       ▼
   ┌──────┐ ┌──────┐ ┌──────┐
   │Linux │ │macOS │ │Windows│
   │Build │ │Build │ │Build │
   └───┬──┘ └───┬──┘ └───┬──┘
       │        │        │
       │  Install Go     │
       │  Clone Manta    │
       │  Build CGO lib  │
       │  Build wheels   │
       │        │        │
       └────────┼────────┘
                ▼
    ┌────────────────────────┐
    │  Collect All Wheels     │
    │  30+ .whl files         │
    └───────────┬─────────────┘
                ▼
    ┌────────────────────────┐
    │  Publish to PyPI        │
    │  (Trusted Publishing)   │
    └───────────┬─────────────┘
                ▼
    ┌────────────────────────┐
    │  Users: pip install     │
    │  python-manta           │
    │  (No Go required!)      │
    └─────────────────────────┘
```

## Key Files

- `.github/workflows/build-wheels.yml` - Main CI/CD workflow
- `tools/before_build_linux.sh` - Linux build preparation
- `tools/before_build_macos.sh` - macOS build preparation
- `tools/before_build_windows.sh` - Windows build preparation
- `tools/prepare_manta.sh` - Manta dependency fetching
- `pyproject.toml` - Package metadata and wheel configuration

## Learn More

- [cibuildwheel documentation](https://cibuildwheel.readthedocs.io/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Go CGO](https://pkg.go.dev/cmd/cgo)
- [Python ctypes](https://docs.python.org/3/library/ctypes.html)
