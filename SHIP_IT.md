# Ship It! 🚀

The smart way: Test first, then ship to production.

## Pre-Flight Check (2 minutes)

```bash
# 1. Tests pass
python run_tests.py --all

# 2. Build works
./build.sh

# 3. Git is clean
git status  # Should be clean

# 4. Version updated
grep "^version = " pyproject.toml  # Verify correct version

# 5. CHANGELOG updated
head -30 CHANGELOG.md  # Check your changes are documented
```

## Phase 1: Test Release (TestPyPI)

```bash
# Test release (note the hyphen!)
./tools/prepare_release.sh 0.1.0.dev1

# Push it
git push origin main
git push origin v0.1.0.dev1
```

**Goes to TestPyPI** → test.pypi.org

## Verify Test (After ~30 min)

```bash
# 1. Monitor build
# https://github.com/YOUR-USERNAME/python-manta/actions

# 2. Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

# 3. Test it
python -c "import python_manta; print('✅ Test passed!')"
```

## Phase 2: Production Release (PyPI)

**Only after test passes!**

```bash
# Production release (NO hyphen!)
./tools/prepare_release.sh 0.1.0

# Push it
git push origin main
git push origin v0.1.0
```

**Goes to PyPI** → pypi.org

## Verify Production (After ~30 min)

```bash
# 1. Monitor build
# https://github.com/YOUR-USERNAME/python-manta/actions

# 2. Check PyPI
# https://pypi.org/project/python-manta/

# 3. Test install
pip install python-manta==0.1.0
python -c "import python_manta; print('🎉 SHIPPED!')"
```

## If It Breaks

```bash
# Delete tag
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# Fix, bump patch, retry
./tools/prepare_release.sh 0.1.1
git push origin main && git push origin v0.1.1
```

## What Gets Published

- **20 wheels** across all platforms:
  - 5 Linux wheels (Python 3.8-3.12)
  - 10 macOS wheels (Intel + ARM64, Python 3.8-3.12)
  - 5 Windows wheels (Python 3.8-3.12)

## Expected Timeline

- 0-5 min: Linux builds
- 5-15 min: macOS builds
- 10-20 min: Windows builds
- 20-25 min: Publish to PyPI
- **25-30 min: DONE** ✅

## Red Flags 🚨

Stop and investigate if:
- ❌ Any platform build fails
- ❌ Publish job fails
- ❌ Less than 20 wheels uploaded
- ❌ `pip install` fails

## Post-Launch

```bash
# Create GitHub release
# https://github.com/YOUR-USERNAME/python-manta/releases/new
# - Choose tag: v0.1.0
# - Copy CHANGELOG.md content
# - Publish

# Done! 🍻
```

---

**Quick start:** [RELEASE_QUICK_START.md](RELEASE_QUICK_START.md)

**Full workflow:** [PROPER_RELEASE_WORKFLOW.md](PROPER_RELEASE_WORKFLOW.md)

**Production only:** [PRODUCTION_RELEASE_CHECKLIST.md](PRODUCTION_RELEASE_CHECKLIST.md)

**Need help?** [RELEASE_PROCESS.md](RELEASE_PROCESS.md)
