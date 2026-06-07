---
name: test-with-replay-cache
description: Writes and debugs python-manta tests that parse real Dota replays without re-parsing, using the module-scoped cached-fixture system (conftest.py + caching_parser.py), the GCS replay auto-download, the correct pytest markers, and the right subset commands. Use whenever the user wants to write or fix a test for the parser, add a fixture, debug a test that can't find a replay, speed up slow/re-parsing tests, add a unit vs integration test, deal with the coverage gate, or configure DOTA_REPLAY_CACHE. Use this even when the user just says "test the wards collector" or "the tests are re-parsing".
---

# Testing with the replay cache

Parsing a full replay takes 5+ minutes, so tests share parsed results via a global cache and
module-scoped fixtures. Read `CLAUDE.md` ("Test Caching System") first — this skill adds the
locations, cache-key behavior, and exact run commands.

HARD CONSTRAINT: a full test run may already be in progress on this machine. Prefer reading code and
running narrow subsets over launching the whole suite.

## Architecture

- `tests/caching_parser.py` — wraps the real `Parser` with global caches. `parse()` is keyed on
  `(demo_path, json.dumps(kwargs, sort_keys=True))`; `build_index()` on `(demo_path, interval_ticks)`;
  `snapshot()` on `(demo_path, target_tick, include_illusions)`. IDENTICAL `parse()` kwargs reuse the
  cache; DIFFERENT kwargs create a new (expensive) parse. So reuse an existing fixture's kwargs EXACTLY
  when you can.
- `tests/conftest.py` — defines ALL fixtures, every one `scope="module"`. Examples:
  `parser`, `parser_secondary`, `combat_log`, `attacks_result`, `melee_attacks`, `ranged_attacks`,
  `wards_result` (kwargs `parser.parse(wards={})`), `attacks_result` (kwargs `attacks={"max_events": 0}`),
  `snapshot_30k` (tick 30000), `demo_index` (interval_ticks 1800).

## Two hard rules (banned in CLAUDE.md)

- NEVER define a local `def parser()` (or any duplicate) fixture in a test file — use the conftest one.
- NEVER `from python_manta import Parser` in a test file. Get the parser only via the `parser`
  fixture argument. To parse with custom options inside a test, call `parser.parse(...)` on the
  injected fixture (still cached).

Need a reusable result? Add a `scope="module"` fixture to `tests/conftest.py` (never in the test
file), reusing existing kwargs where possible:

```python
@pytest.fixture(scope="module")
def foo_result(parser):
    """Cached foo parsing result."""
    result = parser.parse(foo={})
    assert result.success, f"Failed to parse foo: {result.error}"
    return result.foo
```

## Replay location / download

Replays auto-download from GCS `https://storage.googleapis.com/dota-replays/<match_id>.dem` via
`tests/replay_cache.py`. Cache dir resolution order: `DOTA_REPLAY_CACHE` env var → `.data/replays/`
→ `~/.cache/dota-replays/` → project `replays/`. Point at a local copy to avoid re-downloading:

```bash
DOTA_REPLAY_CACHE=/path/to/replays uv run pytest ...
```

Primary match id is `8447659831` (Team Spirit vs Tundra); secondary is `8461956309`. A "can't find
replay" failure is almost always cache-dir / network, not a code bug.

## Layout, markers, and what CI runs

- `tests/python_manta/**` — unit-ish; this is the suite CI runs against built wheels
  (`pytest tests/python_manta/ --no-cov`). Mark units `-m unit`.
- `tests/scenarios/**` — integration/slow; existing files start with
  `pytestmark = [pytest.mark.slow, pytest.mark.integration]`.
- Also: `tests/parity`, `tests/cli`, `tests/performance`.
- `pytest.ini` declares ONLY `unit` and `integration` (not `slow`) and sets `--strict-markers`. The
  scenario files use `slow` regardless, so it must be registered at run time (e.g. by a plugin) or a
  `--strict-markers` run errors on it. Prefer selecting by `integration` for scenario tests; if you
  add a new marker, declare it under `markers =` in `pytest.ini` first.

## Golden values, not type checks

Assert REAL expected values from the actual replay. `tests/scenarios/test_wards.py` is the model:
`EXPECTED_TOTAL_WARDS == 105`, `EXPECTED_OBSERVER_WARDS == 38`, `EXPECTED_SENTRY_WARDS == 67`. Do NOT
write `isinstance` / `len >= 0` / field-existence checks.

## Running subsets (and the coverage caveat)

`pytest.ini` enforces `--cov-fail-under=90` globally; the 90% gate only passes on the FULL suite, so a
partial run reports a coverage FAILURE. Use `--no-cov` while iterating:

```bash
cd /home/juanma/projects/python-manta
uv run pytest tests/scenarios/test_wards.py --no-cov            # one scenario file
uv run pytest tests/python_manta/enums/test_enums.py --no-cov   # one unit file
uv run pytest tests/python_manta/ -m unit --no-cov              # all units, no demos needed
```

Helper runner (does coverage/markers for you): `uv run python run_tests.py --unit` /
`--integration` / `--all --coverage`.
