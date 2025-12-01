#!/usr/bin/env python3
"""
Download pre-built shared library from GitHub releases.

This script downloads the appropriate pre-built libmanta_wrapper for your platform
from the latest GitHub release, so you don't need Go installed to use python-manta
from source.

Usage:
    python scripts/download_library.py

Or from the project root:
    python -m scripts.download_library
"""

import os
import platform
import sys
import urllib.request
import urllib.error
import json
from pathlib import Path

GITHUB_REPO = "DeepBlueCoding/python-manta"
LIBRARY_DIR = Path(__file__).parent.parent / "src" / "python_manta"


def get_platform_library_name() -> str:
    """Get the library filename for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        return "libmanta_wrapper.so"
    elif system == "darwin":
        return "libmanta_wrapper.dylib"
    elif system == "windows":
        return "libmanta_wrapper.dll"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


def get_platform_asset_name() -> str:
    """Get the release asset name for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine

    if system == "linux":
        return f"libmanta_wrapper-linux-{arch}.so"
    elif system == "darwin":
        return f"libmanta_wrapper-macos-{arch}.dylib"
    elif system == "windows":
        return f"libmanta_wrapper-windows-{arch}.dll"
    else:
        raise RuntimeError(f"Unsupported platform: {system}-{machine}")


def get_latest_release() -> dict:
    """Fetch latest release info from GitHub API."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise RuntimeError(
                f"No releases found for {GITHUB_REPO}. "
                "Please build from source using ./build.sh"
            )
        raise


def download_library(release: dict) -> Path:
    """Download the library for the current platform."""
    asset_name = get_platform_asset_name()
    library_name = get_platform_library_name()

    # Find the asset in the release
    asset_url = None
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            asset_url = asset["browser_download_url"]
            break

    if not asset_url:
        available = [a["name"] for a in release.get("assets", [])]
        raise RuntimeError(
            f"No pre-built library found for your platform ({asset_name}).\n"
            f"Available assets: {available}\n"
            "Please build from source using ./build.sh"
        )

    # Download
    dest_path = LIBRARY_DIR / library_name
    print(f"Downloading {asset_name} from {release['tag_name']}...")

    try:
        urllib.request.urlretrieve(asset_url, dest_path)
        os.chmod(dest_path, 0o755)
        print(f"Downloaded to: {dest_path}")
        return dest_path
    except Exception as e:
        raise RuntimeError(f"Failed to download library: {e}")


def check_existing() -> bool:
    """Check if the library already exists."""
    library_name = get_platform_library_name()
    library_path = LIBRARY_DIR / library_name
    return library_path.exists()


def main():
    print("Python Manta - Library Downloader")
    print("=" * 40)

    if check_existing():
        print(f"Library already exists at {LIBRARY_DIR / get_platform_library_name()}")
        response = input("Re-download? [y/N]: ").strip().lower()
        if response != "y":
            print("Skipping download.")
            return 0

    try:
        release = get_latest_release()
        print(f"Latest release: {release['tag_name']}")

        path = download_library(release)
        print(f"\nSuccess! Library installed at: {path}")
        print("\nYou can now use python-manta:")
        print("  from python_manta import MantaParser")
        return 0

    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        print("\nAlternative: Build from source")
        print("  1. Install Go 1.19+")
        print("  2. Clone manta: git clone https://github.com/dotabuff/manta ../manta")
        print("  3. Run: ./build.sh")
        return 1


if __name__ == "__main__":
    sys.exit(main())
