# Production Release Checklist

For those who ship straight to production (no TestPyPI testing needed).

## Pre-Release Validation

Before you tag and release, verify everything locally:

### 1. Build the Library Locally

```bash
# Clean build
rm -rf dist/ build/ src/python_manta/*.so src/python_manta/*.h

# Build
./build.sh

# Verify build succeeded
ls -lh src/python_manta/*.so
```

### 2. Run All Tests

```bash
# Run full test suite
python run_tests.py --all

# Verify 100% pass rate
# No failures, no errors
```

### 3. Test Import

```bash
# Quick smoke test
python -c "
from python_manta import MantaParser
print('✅ Import successful')
"
```

### 4. Verify Version

```bash
# Check version in pyproject.toml matches your release
grep "^version = " pyproject.toml

# Should output: version = "0.1.0" (or your target version)
```

### 5. Check CHANGELOG

```bash
# Verify CHANGELOG.md is updated
cat CHANGELOG.md | head -50

# Should show:
# - [Unreleased] section (can be empty)
# - [0.1.0] section with your changes
# - Correct date
# - Proper categories (Added, Changed, Fixed, etc.)
```

### 6. Verify Git Status

```bash
# Clean working directory
git status

# Should show: "nothing to commit, working tree clean"
# If not, commit your changes first
```

### 7. Check GitHub Actions Is Working

```bash
# View recent workflow runs
# Go to: https://github.com/YOUR-USERNAME/python-manta/actions

# Verify:
# - Latest builds are passing
# - All platforms (Linux, macOS, Windows) build successfully
# - No recent failures
```

## Release Workflow

### Option 1: Using Release Script (Recommended)

```bash
# 1. Run the release script
./tools/prepare_release.sh 0.1.0

# 2. Script will:
#    - Validate version format
#    - Check you're on main branch
#    - Verify no uncommitted changes
#    - Prompt you to update CHANGELOG.md
#    - Update pyproject.toml
#    - Create commit and tag

# 3. Push (triggers production publish)
git push origin main
git push origin v0.1.0

# 4. Monitor the release
# https://github.com/YOUR-USERNAME/python-manta/actions
```

### Option 2: Manual Release

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml
# Change: version = "0.1.0"

# 2. Update CHANGELOG.md
vim CHANGELOG.md
# Move [Unreleased] content to [0.1.0] - 2025-01-20

# 3. Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.1.0"

# 4. Create tag
git tag -a v0.1.0 -m "Release v0.1.0"

# 5. Push (triggers production publish)
git push origin main
git push origin v0.1.0
```

## Post-Release Monitoring

### 1. Watch GitHub Actions (Critical!)

```bash
# Monitor workflow: https://github.com/YOUR-USERNAME/python-manta/actions

# Expected timeline:
# 0-5 min:    Linux wheels building
# 5-15 min:   macOS wheels building (x86_64 + ARM64)
# 10-20 min:  Windows wheels building
# 20-25 min:  All wheels collected, publishing to PyPI
# 25-30 min:  ✅ Complete!

# Watch for:
# ✅ All platform builds succeed (green checks)
# ✅ "Publish to PyPI" job succeeds
# ⚠️  Any red X's - investigate immediately
```

### 2. Verify PyPI Upload

```bash
# Check PyPI (may take 1-2 minutes to appear)
# https://pypi.org/project/python-manta/

# Should show:
# - New version listed
# - Correct version number
# - All platform wheels available:
#   * Linux: cp38-312, manylinux_x86_64
#   * macOS: cp38-312, macosx (x86_64 + arm64)
#   * Windows: cp38-312, win_amd64
```

### 3. Test Installation

```bash
# Wait 2-3 minutes for PyPI to sync to CDN

# Install from PyPI
pip install --upgrade python-manta==0.1.0

# Verify version
python -c "import python_manta; print(python_manta.__version__)"

# Should output: 0.1.0

# Quick functionality test
python -c "
from python_manta import MantaParser
print('✅ Production install successful!')
"
```

### 4. Create GitHub Release

```bash
# 1. Go to: https://github.com/YOUR-USERNAME/python-manta/releases/new

# 2. Choose tag: v0.1.0

# 3. Release title: v0.1.0

# 4. Description (copy from CHANGELOG.md):
```

**Example Release Notes:**
```markdown
## What's New in v0.1.0

### Added
- Complete implementation of all 272 Manta callbacks
- Universal parser with message filtering
- Multi-platform wheel building (Linux, macOS, Windows)
- Automated PyPI publishing

### Features
- 40% more data fields than native Go implementation
- Support for Python 3.8 through 3.12
- Battle-tested with TI14 professional replays

## Installation

```bash
pip install python-manta==0.1.0
```

## Platform Support
- ✅ Linux (x86_64)
- ✅ macOS (Intel + Apple Silicon)
- ✅ Windows (AMD64)

## Full Changelog
https://github.com/YOUR-USERNAME/python-manta/blob/v0.1.0/CHANGELOG.md
```

```bash
# 5. Check "Set as the latest release"

# 6. Publish release
```

### 5. Verify Distribution

Test on different platforms if possible:

```bash
# Linux
pip install python-manta==0.1.0
python -c "import python_manta; print('✅ Linux')"

# macOS (Intel)
pip install python-manta==0.1.0
python -c "import python_manta; print('✅ macOS Intel')"

# macOS (Apple Silicon)
pip install python-manta==0.1.0
python -c "import python_manta; print('✅ macOS ARM64')"

# Windows
pip install python-manta==0.1.0
python -c "import python_manta; print('✅ Windows')"
```

## Rollback Procedure (If Something Goes Wrong)

### If Build Fails

```bash
# 1. Check GitHub Actions logs
# Identify which platform failed

# 2. Fix the issue locally
# Make necessary changes

# 3. Delete the tag
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0

# 4. Retry release with patch version
./tools/prepare_release.sh 0.1.1
git push origin main
git push origin v0.1.1
```

### If PyPI Upload Fails

```bash
# 1. Download built wheels from GitHub Actions
# Actions → Workflow run → Artifacts → Download all

# 2. Install twine
pip install twine

# 3. Upload manually
twine upload dist/*.whl

# Enter credentials when prompted
# Username: __token__
# Password: [your PYPI_API_TOKEN]
```

### If Bad Version Published to PyPI

**Important**: You CANNOT delete or overwrite versions on PyPI!

**Options:**

1. **Yank the release** (makes it unavailable but doesn't delete):
   ```bash
   pip install twine
   twine yank python-manta 0.1.0
   ```

2. **Release fixed version immediately**:
   ```bash
   ./tools/prepare_release.sh 0.1.1
   git push origin main
   git push origin v0.1.1
   ```

3. **Add notice in CHANGELOG**:
   ```markdown
   ## [0.1.1] - 2025-01-20
   ### Fixed
   - Re-release of 0.1.0 (previous version yanked due to critical bug)
   ```

## Common Issues

### ❌ "Version already exists on PyPI"

**Cause**: Trying to upload a version that already exists.

**Solution**: Bump to next version
```bash
./tools/prepare_release.sh 0.1.1
```

### ❌ "Invalid or non-existent authentication information"

**Cause**: PYPI_API_TOKEN secret is incorrect or expired.

**Solution**:
1. Create new token on PyPI
2. Update GitHub secret: Settings → Secrets → PYPI_API_TOKEN

### ❌ Platform-specific build failure

**Cause**: Build failed for one platform (e.g., Windows).

**Solution**:
1. Check build logs in GitHub Actions
2. Fix platform-specific issue
3. Delete tag and retry with patch version

### ❌ Wheels missing on PyPI

**Cause**: Some wheels didn't upload correctly.

**Solution**:
1. Download missing wheels from GitHub Actions artifacts
2. Upload manually with twine

## Emergency Contact

If you need to:
- Yank a release
- Get help with PyPI
- Report a security issue

See: [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md) "Troubleshooting" section

## Success Metrics

Your release is successful when:

- ✅ All platform builds succeeded (GitHub Actions)
- ✅ All wheels uploaded to PyPI
- ✅ Version shows on https://pypi.org/project/python-manta/
- ✅ `pip install python-manta==X.X.X` works
- ✅ Import test passes
- ✅ GitHub release created
- ✅ No user-reported issues in first 24 hours

## Next Release

After successful release:

1. **Update local repository**
   ```bash
   git pull origin main
   ```

2. **Start [Unreleased] section in CHANGELOG.md**
   ```markdown
   ## [Unreleased]
   <!-- Add changes here as you make them -->
   ```

3. **Continue development**
   - Future changes go into [Unreleased]
   - When ready, repeat this process for next version

## Pro Tips

🚀 **First release?**
- Use version 0.1.0
- Monitor closely for first 24 hours
- Be ready to release 0.1.1 if issues found

📊 **Track your release:**
- Star the GitHub Actions workflow tab
- Monitor PyPI download stats
- Watch for GitHub issues

⚡ **Speed up debugging:**
- Keep GitHub Actions tab open
- Use `gh run watch` CLI command
- Check individual job logs immediately on failure

🔒 **Security:**
- Rotate PYPI_API_TOKEN every 6-12 months
- Never commit tokens to git
- Use project-scoped tokens after first release

---

**Ready to ship?** Run through this checklist one more time, then send it! 🚀
