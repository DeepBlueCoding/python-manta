---
name: release-version
description: Cuts a python-manta release (dev build to TestPyPI or final to PyPI) and/or bumps the locked upstream dotabuff/manta version, using the correct PEP 440 4-part version scheme and the exact git tag format the GitHub Actions CI keys on. Use whenever the user wants to release a new version, bump the version, publish to PyPI/TestPyPI, cut a dev/prerelease, tag a release, upgrade or sync the manta version, or change .manta-version. Use this even if the user just says "ship it", "make a dev build", or "update manta to vX.Y.Z".
allowed-tools: Bash(git tag *) Bash(git push *) Bash(git add *) Bash(git commit *) Bash(gh run *) Bash(gh workflow *)
---

# Cutting a python-manta release

Version scheme is PEP 440, 4-part: `{manta_major}.{manta_minor}.{manta_patch}.{python_release}`
optionally `+ .devN`. Convention: the first 3 parts SHOULD match the upstream manta version locked
in `.manta-version`; the 4th part is the python-manta release counter. Current state:
`pyproject.toml` version is `1.4.7.5`, `.manta-version` is `v1.4.7`.

Read `CLAUDE.md` ("Releasing a new version") and `RELEASE_PROCESS.md` first. RELEASE_PROCESS.md
documents a commitizen `cz bump` flow, but actual recent history uses manual `sed -i` bumps +
`git tag` + push. Default branch is `master`.

## What drives publishing: the tag regex

CI (`.github/workflows/build-wheels.yml`, job `check-version`) decides everything from the tag: it
derives the published version purely from the tag via the regex below (`BASH_REMATCH`) — it does NOT
read or validate `pyproject.toml`. So keep the tag and `pyproject.toml` version IDENTICAL anyway: a
from-scratch wheel build (cibuildwheel) reads the wheel version from `pyproject.toml`, so a mismatch
yields wheels named differently than the tag/release. The tag MUST start with `v`.

| Tag pushed | Classified | Publishes to |
|---|---|---|
| `v1.4.7.5` (no suffix) | `is_release` | PyPI |
| `v1.4.7.5.dev3` | `is_prerelease` | TestPyPI |
| `v1.4.7.5a1` / `b2` / `rc1` | `is_prerelease` | TestPyPI |
| branch push (no tag) | neither | nothing (builds wheels only) |

The base regex accepts 3 OR 4 numeric parts: `^refs/tags/v([0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?)$`.

## Flow A — dev release to TestPyPI

```bash
cd /home/juanma/projects/python-manta
# bump the .devN suffix (or add one) in pyproject.toml
sed -i 's/1.4.7.5.dev2/1.4.7.5.dev3/g' pyproject.toml
git add pyproject.toml && git commit -m "bump: version 1.4.7.5.dev2 → 1.4.7.5.dev3"
git tag v1.4.7.5.dev3
git push origin master --tags
```

Prerelease optimization: if `go_wrapper/` did NOT change since the base release tag, CI skips
rebuilding and instead downloads the base release wheels and reversions them via
`tools/reversion_wheel.py` (fast dev cuts). If `go_wrapper/` changed, it rebuilds all wheels.

## Flow B — final release to PyPI

```bash
cd /home/juanma/projects/python-manta
# remove the .devN suffix
sed -i 's/1.4.7.5.dev3/1.4.7.5/g' pyproject.toml
git add pyproject.toml && git commit -m "bump: version 1.4.7.5.dev3 → 1.4.7.5"
git tag v1.4.7.5
git push origin master --tags
```

Final-release tags additionally upload wheels to the GitHub Release and trigger the docs deploy
(`docs.yml` fires on `v[0-9]+.[0-9]+.[0-9]+.[0-9]+` 4-part non-dev tags).

## Upgrading the locked manta version

Never hand-edit `.manta-version`. Use the helper, then sync `pyproject.toml`'s first 3 parts:

```bash
cd /home/juanma/projects/python-manta
./tools/upgrade_manta_version.sh v1.4.8
sed -i 's/version = "1.4.7.5"/version = "1.4.8.0"/' pyproject.toml
```

`.manta-version` accepts a git ref: a tag (`v1.4.8`), `master`, or a commit hash. `build.sh` and CI
read it via `grep -v '^#' .manta-version | ... | tail -n1`. Override per-build with
`MANTA_REF=<ref> ./build.sh`. Changing `go_wrapper/manta` means CI will rebuild from scratch (no
reversion shortcut). Python-only patches keep `.manta-version` and just bump the 4th segment.

## Verify after push (static-safe)

Do NOT run the full local test suite (one may be running on this machine). CI runs the wheel tests.

```bash
gh run list --workflow build-wheels.yml --limit 3
gh run watch   # optional, follow the latest run
```

Wheels build for cp38–cp313 on linux / macos (x86_64 + arm64) / windows; each job smoke-imports the
wheel and runs `pytest tests/python_manta/ --no-cov` with replays from GCS. After publish, smoke-test
the install: `uv pip install --index-url https://test.pypi.org/simple/ python-manta==1.4.7.5.dev3`
(TestPyPI) or `uv pip install python-manta==1.4.7.5` (PyPI).
