"""Caching Parser wrapper for tests.

Provides a Parser class that caches parse(), build_index(), and snapshot() results
for improved test performance. Uses GLOBAL cache shared across all instances.
"""

import json
from python_manta import Parser as _Parser

# Global caches shared across all Parser instances
_PARSE_CACHE = {}
_INDEX_CACHE = {}
_SNAPSHOT_CACHE = {}
_PARSER_CACHE = {}


class Parser:
    """Parser wrapper that caches parse(), build_index(), and snapshot() results."""

    def __init__(self, demo_path: str, library_path: str = None):
        self._demo_path = demo_path
        self._library_path = library_path
        cache_key = (demo_path, library_path)
        if cache_key not in _PARSER_CACHE:
            _PARSER_CACHE[cache_key] = _Parser(demo_path, library_path=library_path) if library_path else _Parser(demo_path)
        self._parser = _PARSER_CACHE[cache_key]

    def parse(self, **kwargs):
        cache_key = (self._demo_path, json.dumps(kwargs, sort_keys=True))
        if cache_key not in _PARSE_CACHE:
            _PARSE_CACHE[cache_key] = self._parser.parse(**kwargs)
        return _PARSE_CACHE[cache_key]

    def build_index(self, interval_ticks: int = 1800):
        cache_key = (self._demo_path, interval_ticks)
        if cache_key not in _INDEX_CACHE:
            _INDEX_CACHE[cache_key] = self._parser.build_index(interval_ticks)
        return _INDEX_CACHE[cache_key]

    def snapshot(self, target_tick=None, game_time=None, include_illusions=False):
        if target_tick is None and game_time is not None:
            target_tick = self._parser._game_time_to_tick(game_time)
        cache_key = (self._demo_path, target_tick, include_illusions)
        if cache_key not in _SNAPSHOT_CACHE:
            _SNAPSHOT_CACHE[cache_key] = self._parser.snapshot(
                target_tick=target_tick, include_illusions=include_illusions
            )
        return _SNAPSHOT_CACHE[cache_key]

    @property
    def game_start_tick(self):
        return self._parser.game_start_tick

    def __getattr__(self, name):
        return getattr(self._parser, name)
