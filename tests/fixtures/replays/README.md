# Replay Fixtures

Place small Dota 2 `.dem` files in this directory (ignored by git) to exercise integration tests.

Recommended approach:

1. Copy or symlink replays from `~/dota2/replays`.
2. Keep file sizes modest (<25 MB) to avoid bloating the repository clone size.
3. Document the source match in pull requests when adding new sample data.

Alternatively, set `PYTHON_MANTA_REPLAY_DIR` to the directory containing your replays. The test suite will fall back to `~/dota2/replays` if available.
