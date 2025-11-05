# Release Quick Start Guide

The smart way to release: Test → Production

## TL;DR

```bash
# Test release (note the hyphen! Use .dev for testing)
./tools/prepare_release.sh 0.1.0.dev1
git push origin main && git push origin v0.1.0-dev1

# Wait for builds, then test install
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

# If it works, ship to production (no hyphen!)
./tools/prepare_release.sh 0.1.0
git push origin main && git push origin v0.1.0
```

## The Tag-Based Routing System

| You Push | It Goes To | Example |
|----------|------------|---------|
| Tag **with** `-` | TestPyPI | `v0.1.0-dev1` → test.pypi.org |
| Tag **without** `-` | PyPI | `v0.1.0` → pypi.org |

**The hyphen controls everything.**

## Phase 1: Test (TestPyPI)

```bash
# Create test tag (use .dev1, .dev2, etc.)
./tools/prepare_release.sh 0.1.0.dev1
git push origin main
git push origin v0.1.0-dev1
```

**Publishes to TestPyPI** → https://test.pypi.org/project/python-manta/

### Test Installation

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

python -c "import python_manta; print('✅ Works!')"
```

**Note:** Use `.dev1`, `.dev2` for development testing or `rc1`, `rc2` for release candidates (PEP 440 compliant)

## Phase 2: Production (PyPI)

**Only after TestPyPI works!**

```bash
# Create production tag (NO hyphen!)
./tools/prepare_release.sh 0.1.0
git push origin main
git push origin v0.1.0
```

**Publishes to PyPI** → https://pypi.org/project/python-manta/

### Verify Production

```bash
# Wait 2-3 min for CDN sync
pip install python-manta==0.1.0
python -c "import python_manta; print('🎉 LIVE!')"
```

## What Gets Published

Both TestPyPI and PyPI releases build:
- **20 wheels** across all platforms
- Linux (5 wheels: Python 3.8-3.12)
- macOS Intel (5 wheels: Python 3.8-3.12)
- macOS ARM64 (5 wheels: Python 3.8-3.12)
- Windows (5 wheels: Python 3.8-3.12)

## Timeline

From tag push to published:
- `0-5 min`: Linux builds
- `5-15 min`: macOS builds (both architectures)
- `10-20 min`: Windows builds
- `20-25 min`: Publishing
- **`25-30 min`: Done!**

## If Test Fails

```bash
# Fix your code

# Increment test version
./tools/prepare_release.sh 0.1.0.dev2
git push origin main && git push origin v0.1.0-dev2

# Test again
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev2

# Repeat until perfect, then release to production
```

## Common Test Tags (PEP 440 Compliant)

```bash
v0.1.0-dev1        # Development version 1
v0.1.0-dev2        # Development version 2
v0.1.0-rc1         # Release candidate 1
v0.1.0-b1          # Beta 1
v0.1.0-a1          # Alpha 1
```

All go to TestPyPI because they have a hyphen!

**See [TESTPYPI_VERSIONS.md](TESTPYPI_VERSIONS.md) for valid version formats.**

## Pre-Flight Checklist

Before ANY release (test or production):

```bash
# 1. Tests pass
python run_tests.py --all

# 2. Build works
./build.sh

# 3. Git clean
git status

# 4. Version correct
grep "^version" pyproject.toml

# 5. CHANGELOG updated
head -30 CHANGELOG.md
```

## Your First Release (Step-by-Step)

### Day 1: Test

```bash
# 1. Pre-flight checks (above)
python run_tests.py --all
./build.sh

# 2. Create test release
./tools/prepare_release.sh 0.1.0.dev1
git push origin main
git push origin v0.1.0-dev1

# 3. Wait for GitHub Actions (30 min)
# https://github.com/YOUR-USERNAME/python-manta/actions

# 4. Test install
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

python -c "import python_manta; print('Test passed!')"
```

### Day 2: Production (If Test Passed)

```bash
# 1. Create production release
./tools/prepare_release.sh 0.1.0
git push origin main
git push origin v0.1.0

# 2. Wait for GitHub Actions (30 min)

# 3. Verify production
pip install python-manta==0.1.0
python -c "import python_manta; print('🚀 SHIPPED!')"

# 4. Create GitHub release
# https://github.com/YOUR-USERNAME/python-manta/releases/new
```

## Why This Works

- ✅ **Catches errors** before users see them
- ✅ **Tests all platforms** automatically
- ✅ **Verifies pip install** works correctly
- ✅ **Zero risk** to production PyPI
- ✅ **Professional workflow** used by major projects

## Need More Details?

- **Full workflow**: [PROPER_RELEASE_WORKFLOW.md](PROPER_RELEASE_WORKFLOW.md)
- **Production checklist**: [PRODUCTION_RELEASE_CHECKLIST.md](PRODUCTION_RELEASE_CHECKLIST.md)
- **Release process**: [RELEASE_PROCESS.md](RELEASE_PROCESS.md)
- **PyPI setup**: [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md)

## Secrets Required

Both configured ✅:
- `PYPI_API_TOKEN` - Production releases
- `TEST_PYPI_API_TOKEN` - Test releases

---

**Remember:** Hyphen = Test, No hyphen = Production 🎯
