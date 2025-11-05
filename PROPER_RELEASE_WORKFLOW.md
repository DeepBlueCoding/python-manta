# The Proper Release Workflow (TestPyPI → Production)

Now that you have both `TEST_PYPI_API_TOKEN` and `PYPI_API_TOKEN` configured, here's the smart way to release.

## Why TestPyPI Is Actually Smart

TestPyPI catches:
- ✅ Wheel build issues across platforms
- ✅ PyPI upload/authentication problems
- ✅ Installation issues from pip
- ✅ Version conflicts
- ✅ Missing files in wheels
- ✅ Platform-specific import errors

**All before your users see them.**

## The Two-Phase Release Process

### Phase 1: Test Release (TestPyPI)

#### Step 1: Prepare Test Release

```bash
# Create a test version (note the hyphen!)
./tools/prepare_release.sh 0.1.0-test.1

# Push test tag
git push origin main
git push origin v0.1.0-test.1
```

**What happens:**
- GitHub Actions detects tag with hyphen
- Builds wheels for ALL platforms (Linux, macOS, Windows)
- Publishes to **TestPyPI** (not production)

#### Step 2: Monitor Test Build (5-30 min)

```bash
# Watch GitHub Actions
# https://github.com/YOUR-USERNAME/python-manta/actions

# Wait for:
# ✅ All platform builds succeed
# ✅ "Publish to TestPyPI" job succeeds
```

#### Step 3: Test Installation from TestPyPI

```bash
# Create clean test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1

# Note: TestPyPI normalizes version (0.1.0-test.1 → 0.1.0.test1)
```

**Why the extra-index-url?**
- TestPyPI doesn't have your dependencies (pydantic, etc.)
- Falls back to PyPI for dependencies
- Only python-manta comes from TestPyPI

#### Step 4: Verify Everything Works

```bash
# Test import
python -c "import python_manta; print('✅ Import works')"

# Test basic functionality
python -c "
from python_manta import MantaParser
print('✅ Package works')
print(f'Version: {python_manta.__version__}')
"

# Run your own tests if you have them
python -c "
from python_manta import parse_demo_header
# Test with real demo file if available
print('✅ Functionality verified')
"
```

#### Step 5: Test on Multiple Platforms (If Possible)

If you have access to different platforms:

```bash
# Linux
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1
python -c "import python_manta; print('✅ Linux works')"

# macOS (Intel)
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1
python -c "import python_manta; print('✅ macOS Intel works')"

# macOS (Apple Silicon/ARM64)
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1
python -c "import python_manta; print('✅ macOS ARM64 works')"

# Windows
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1
python -c "import python_manta; print('✅ Windows works')"
```

**Don't have all platforms?**
- Check GitHub Actions logs - each platform runs smoke tests
- If builds and tests pass there, you're good

### Phase 2: Production Release (PyPI)

**Only proceed if TestPyPI release worked perfectly!**

#### Step 1: Prepare Production Release

```bash
# Create production version (NO hyphen!)
./tools/prepare_release.sh 0.1.0

# Push production tag
git push origin main
git push origin v0.1.0
```

**What happens:**
- GitHub Actions detects tag WITHOUT hyphen
- Builds wheels for ALL platforms (again, fresh builds)
- Publishes to **PyPI** (production)

#### Step 2: Monitor Production Build

```bash
# Watch GitHub Actions
# https://github.com/YOUR-USERNAME/python-manta/actions

# Wait for:
# ✅ All platform builds succeed
# ✅ "Publish to PyPI" job succeeds
```

#### Step 3: Verify Production Install

```bash
# Wait 2-3 minutes for PyPI CDN sync

# Install from production PyPI (normal pip install!)
pip install python-manta==0.1.0

# Verify
python -c "
import python_manta
print(f'✅ Production install works!')
print(f'Version: {python_manta.__version__}')
"
```

#### Step 4: Create GitHub Release

```bash
# Go to: https://github.com/YOUR-USERNAME/python-manta/releases/new

# Choose tag: v0.1.0
# Title: v0.1.0
# Description: Copy from CHANGELOG.md

# Mark as "Latest release"
# Publish
```

## Quick Reference: Tag Format Matters!

| Tag Format | Destination | Example | Use Case |
|------------|-------------|---------|----------|
| `vX.Y.Z` | **PyPI** (production) | `v0.1.0`, `v1.2.3` | Final releases |
| `vX.Y.Z-*` | **TestPyPI** (testing) | `v0.1.0-test.1`, `v0.2.0-beta.1` | Testing before production |

**The hyphen is the magic:** Tags with `-` go to TestPyPI, without go to PyPI.

## Common Test Tag Formats

```bash
# Test releases (all go to TestPyPI)
v0.1.0-test.1       # First test
v0.1.0-test.2       # Second test after fixes
v0.1.0-rc.1         # Release candidate 1
v0.1.0-beta.1       # Beta release
v0.1.0-alpha.1      # Alpha release

# Production releases (all go to PyPI)
v0.1.0              # Production
v0.2.0              # Production
v1.0.0              # Production
```

## Complete Example: First Release

Let's say you're releasing version 0.1.0 for the first time:

### Day 1: Test Release

```bash
# Morning: Create test release
./tools/prepare_release.sh 0.1.0-test.1
git push origin main
git push origin v0.1.0-test.1

# 30 minutes later: Verify build succeeded
# https://github.com/YOUR-USERNAME/python-manta/actions

# Afternoon: Test installation
python -m venv test_env
source test_env/bin/activate
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1

python -c "import python_manta; print('Works!')"

# Found a bug? Fix it and release test.2
# No bugs? Ready for production!
```

### Day 2: Production Release (After Test Passes)

```bash
# Morning: Create production release
./tools/prepare_release.sh 0.1.0
git push origin main
git push origin v0.1.0

# 30 minutes later: Verify on PyPI
pip install python-manta==0.1.0
python -c "import python_manta; print('🎉 LIVE!')"

# Create GitHub release
# https://github.com/YOUR-USERNAME/python-manta/releases/new

# Announce to users!
```

## Fixing Issues Found in TestPyPI

If you find problems during TestPyPI testing:

```bash
# 1. Fix the issue in your code

# 2. Increment the test version
./tools/prepare_release.sh 0.1.0-test.2
git push origin main
git push origin v0.1.0-test.2

# 3. Test again
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test2

# 4. Repeat until perfect

# 5. Then release to production with v0.1.0 (no -test suffix)
```

## TestPyPI Limitations to Know

1. **Dependencies**: Your package's dependencies (pydantic) must come from real PyPI
   - Always use `--extra-index-url https://pypi.org/simple/`

2. **Cleanup**: TestPyPI deletes old releases after ~6 months
   - Don't rely on TestPyPI for long-term storage

3. **Separate Accounts**: TestPyPI and PyPI are separate
   - Need different accounts
   - Need different tokens

4. **Version Normalization**: `0.1.0-test.1` becomes `0.1.0.test1`
   - PEP 440 normalization
   - Use the normalized version when installing

## Recommended Workflow for Different Release Types

### Patch Release (Bug Fix)

```bash
# Test first
git tag v0.1.1-test.1
git push origin v0.1.1-test.1

# If good, release
git tag v0.1.1
git push origin v0.1.1
```

### Minor Release (New Feature)

```bash
# Test first (important - new code!)
git tag v0.2.0-test.1
git push origin v0.2.0-test.1

# Test thoroughly, maybe even test.2 if needed
# Then release
git tag v0.2.0
git push origin v0.2.0
```

### Major Release (Breaking Changes)

```bash
# Definitely test first!
git tag v1.0.0-rc.1     # Release candidate
git push origin v1.0.0-rc.1

# Get user feedback on RC
# Fix any issues: v1.0.0-rc.2

# When perfect, release
git tag v1.0.0
git push origin v1.0.0
```

## Benefits You Get With Both Tokens

✅ **Catch build issues** before production
✅ **Test multi-platform** wheels before users see them
✅ **Verify installation** works correctly
✅ **Fix problems** without affecting production
✅ **Sleep better** knowing it works before going live
✅ **Professional workflow** used by major Python projects

## Quick Commands

```bash
# Test release
./tools/prepare_release.sh 0.1.0-test.1
git push origin main && git push origin v0.1.0-test.1

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.test1

# Production release (after test passes)
./tools/prepare_release.sh 0.1.0
git push origin main && git push origin v0.1.0

# Install from PyPI
pip install python-manta==0.1.0
```

## Success Checklist

Before going to production, verify:

**TestPyPI Phase:**
- [ ] Test tag pushed (has hyphen)
- [ ] All platform builds succeeded
- [ ] TestPyPI publish succeeded
- [ ] Installed from TestPyPI successfully
- [ ] Import works
- [ ] Basic functionality works
- [ ] Tested on multiple platforms (or CI tests passed)

**Production Phase:**
- [ ] Production tag pushed (no hyphen)
- [ ] All platform builds succeeded
- [ ] PyPI publish succeeded
- [ ] Installed from PyPI successfully
- [ ] GitHub release created
- [ ] Users notified (if applicable)

---

**You're now set up like a pro!** 🎯

Test with TestPyPI, ship to production with confidence.
