# Repository Guidelines

## Project Structure & Module Organization
Source lives under `src/python_manta/`, with `manta_python.py` exposing the parser API and `libmanta_wrapper.{so,h}` embedded for runtime use. The Go CGO bridge is maintained in `go_wrapper/`; rebuilds drop fresh artifacts back into the Python package. Tests sit in `tests/` and follow `test_*.py`. Example scripts are in `examples/`, while packaging assets land in `build/` and `dist/` during releases.

## Build, Test, and Development Commands
Run `./build.sh` to regenerate the Go shared library and verify the Python package; ensure `../manta` is present and Go ≥1.20 is available. Use `python run_tests.py --all` for the full suite, or `python -m pytest` directly. Coverage-driven runs (`python run_tests.py --coverage`) publish HTML results in `htmlcov/`. For quick sanity checks, `python simple_example.py` demonstrates the parser against a local `.dem` replay.

## Coding Style & Naming Conventions
Adopt Black formatting (88-char lines) and four-space indentation. Sort imports with `isort --profile black .` and keep type hints strict enough for `mypy --config-file pyproject.toml`. Public APIs mirror Manta naming; prefer CamelCase for data models (`UniversalParseResult`) and snake_case for module-level helpers. Keep docstrings focused on replay parsing semantics and include callback identifiers when relevant.

## Testing Guidelines
Tests rely on `pytest` with markers `unit`, `integration`, and `slow`; the default `pytest.ini` enforces 90% coverage. Place new tests in `tests/` and name files `test_<feature>.py`; add focused helpers under the same directory to keep fixtures discoverable. When touching CGO or demo assets, gate them behind `@pytest.mark.integration` so CI can skip them when artifacts are missing. The new Go parity check (`tests/test_go_parity.py`) requires `go`, a freshly built `libmanta_wrapper.so`, and a local replay under `tests/fixtures/replays/` (or `PYTHON_MANTA_REPLAY_DIR`).

## Commit & Pull Request Guidelines
The repository has minimal history—default to Conventional Commits (e.g., `feat: add draft parsing helper`) and keep changes narrowly scoped. Reference issue IDs in the body, describe replay files or fixtures exercised, and call out any new callbacks wired in. Before opening a PR, run the full test suite with coverage, attach the resulting summary, and note any manual replay validations or required `../manta` revisions.

## Shared Library & Asset Notes
Regenerated shared libraries must continue shipping inside `src/python_manta/`; do not commit system-specific builds. If you add demo samples, place them under `examples/` or a dedicated fixtures directory and document their provenance for licensing clarity.
