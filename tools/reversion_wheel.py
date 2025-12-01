#!/usr/bin/env python3
"""
Re-version a wheel file to a new version number.

Usage:
    python reversion_wheel.py <wheel_file> <new_version> [--output-dir <dir>]

Example:
    python reversion_wheel.py python_manta-1.4.5-cp311-cp311-manylinux_x86_64.whl 1.4.5.1
"""

import argparse
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path


def parse_wheel_filename(filename: str) -> dict:
    """Parse wheel filename into components."""
    # Format: {distribution}-{version}(-{build tag})?-{python tag}-{abi tag}-{platform tag}.whl
    pattern = r'^([^-]+)-([^-]+)(-[^-]+)?-([^-]+)-([^-]+)-([^-]+)\.whl$'
    match = re.match(pattern, filename)
    if not match:
        raise ValueError(f"Invalid wheel filename: {filename}")

    return {
        'distribution': match.group(1),
        'version': match.group(2),
        'build': match.group(3) or '',
        'python': match.group(4),
        'abi': match.group(5),
        'platform': match.group(6),
    }


def build_wheel_filename(components: dict) -> str:
    """Build wheel filename from components."""
    return f"{components['distribution']}-{components['version']}{components['build']}-{components['python']}-{components['abi']}-{components['platform']}.whl"


def update_metadata(metadata_content: str, new_version: str) -> str:
    """Update the Version field in METADATA file."""
    lines = metadata_content.split('\n')
    updated_lines = []

    for line in lines:
        if line.startswith('Version:'):
            updated_lines.append(f'Version: {new_version}')
        else:
            updated_lines.append(line)

    return '\n'.join(updated_lines)


def update_record(record_content: str, old_dist_info: str, new_dist_info: str) -> str:
    """Update paths in RECORD file."""
    return record_content.replace(old_dist_info, new_dist_info)


def reversion_wheel(wheel_path: str, new_version: str, output_dir: str = None) -> str:
    """
    Re-version a wheel file to a new version.

    Args:
        wheel_path: Path to the original wheel file
        new_version: New version string (e.g., "1.4.5.1")
        output_dir: Output directory (defaults to same as input)

    Returns:
        Path to the new wheel file
    """
    wheel_path = Path(wheel_path)
    if not wheel_path.exists():
        raise FileNotFoundError(f"Wheel not found: {wheel_path}")

    # Parse original filename
    original_name = wheel_path.name
    components = parse_wheel_filename(original_name)
    old_version = components['version']

    # Build new filename
    components['version'] = new_version
    new_name = build_wheel_filename(components)

    # Determine output path
    if output_dir:
        output_path = Path(output_dir) / new_name
    else:
        output_path = wheel_path.parent / new_name

    # dist-info directory names
    dist_name = components['distribution']
    old_dist_info = f"{dist_name}-{old_version}.dist-info"
    new_dist_info = f"{dist_name}-{new_version}.dist-info"

    # Create new wheel
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Extract original wheel
        with zipfile.ZipFile(wheel_path, 'r') as zf:
            zf.extractall(tmpdir)

        # Rename dist-info directory
        old_dist_path = tmpdir / old_dist_info
        new_dist_path = tmpdir / new_dist_info

        if old_dist_path.exists():
            shutil.move(str(old_dist_path), str(new_dist_path))

        # Update METADATA
        metadata_path = new_dist_path / 'METADATA'
        if metadata_path.exists():
            content = metadata_path.read_text()
            updated = update_metadata(content, new_version)
            metadata_path.write_text(updated)

        # Update RECORD (paths changed due to dist-info rename)
        record_path = new_dist_path / 'RECORD'
        if record_path.exists():
            content = record_path.read_text()
            updated = update_record(content, old_dist_info, new_dist_info)
            record_path.write_text(updated)

        # Update WHEEL file if it contains version info
        wheel_file_path = new_dist_path / 'WHEEL'
        if wheel_file_path.exists():
            content = wheel_file_path.read_text()
            # WHEEL file typically doesn't have version, but check anyway
            wheel_file_path.write_text(content)

        # Create new wheel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in tmpdir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(tmpdir)
                    zf.write(file_path, arcname)

    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description='Re-version a wheel file')
    parser.add_argument('wheel', help='Path to the wheel file')
    parser.add_argument('version', help='New version string')
    parser.add_argument('--output-dir', '-o', help='Output directory')

    args = parser.parse_args()

    new_wheel = reversion_wheel(args.wheel, args.version, args.output_dir)
    print(f"Created: {new_wheel}")


if __name__ == '__main__':
    main()
