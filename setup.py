#!/usr/bin/env python3
"""
Setup script for python-manta

This setup.py is needed to tell setuptools that python-manta contains
platform-specific binary extensions (.so files), even though we don't
build them here (they're pre-built by the CGO wrapper).

Without this, setuptools creates a pure Python wheel (py3-none-any.whl)
instead of a platform-specific wheel (e.g., cp39-cp39-linux_x86_64.whl).
"""

from setuptools import setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """
    Distribution which always forces a binary package with platform name.

    This is necessary because the .so files are pre-built by CGO in the
    before_build_*.sh scripts, not built by setuptools' normal Extension
    build process. By overriding has_ext_modules(), we tell setuptools:
    "This package contains compiled code specific to this platform."
    """
    def has_ext_modules(self):
        return True


# All configuration comes from pyproject.toml
# This setup.py only exists to mark the package as binary
setup(
    distclass=BinaryDistribution,
)
