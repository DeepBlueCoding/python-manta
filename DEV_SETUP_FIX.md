# Development Setup Quick Fix

## The Problem

When running tests with `uv run python run_tests.py --all`, you get:
```
❌ Missing dependency: No module named 'pytest'
```

## The Solution

Pytest is an **optional dev dependency**. You need to install it explicitly:

### Option 1: Using pip (Recommended)

```bash
pip install -e '.[dev]'
```

### Option 2: Using uv

```bash
uv pip install -e '.[dev]'
```

### Option 3: Just for testing (no editable install)

```bash
pip install pytest pytest-cov
```

## Why This Happens

In `pyproject.toml`, pytest is defined as an optional dependency:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    ...
]
```

When you run `uv run` or `pip install -e .`, it only installs the **main** dependencies (pydantic), not the optional ones.

## Complete Development Setup

```bash
# 1. Build the Go library
./build.sh

# 2. Install Python package with dev dependencies
pip install -e '.[dev]'

# 3. Run tests
python run_tests.py --all

# Or with uv
uv run --with pytest --with pytest-cov python run_tests.py --all
```

## What Gets Installed

With `'.[dev]'`, you get:
- ✅ pytest (test runner)
- ✅ pytest-cov (coverage reporting)
- ✅ black (code formatter)
- ✅ isort (import sorter)
- ✅ mypy (type checker)

Without `[dev]`, you only get:
- pydantic (runtime dependency)

## Permanent Solution

Add this to your development workflow:

```bash
# After cloning the repo
git clone <repo>
cd python-manta

# One-time setup
./build.sh
pip install -e '.[dev]'

# Now you can run tests anytime
python run_tests.py --all
```

## Using uv Specifically

If you prefer using `uv`:

```bash
# Install dev dependencies with uv
uv pip install -e '.[dev]'

# Then run tests normally (not with uv run)
python run_tests.py --all

# Or if you want to use uv run
uv run --with pytest --with pytest-cov python run_tests.py --all
```

## Fixed!

The error message has been updated to show this solution automatically:

```
❌ Missing dependency: No module named 'pytest'

💡 To install test dependencies, run:
   pip install -e '.[dev]'
   OR with uv:
   uv pip install -e '.[dev]'
```

---

**TL;DR:** Run `pip install -e '.[dev]'` before running tests! 🎯
