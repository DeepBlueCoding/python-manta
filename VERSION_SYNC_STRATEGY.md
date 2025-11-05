# Version Synchronization Strategy

## Core Principle

**python-manta version MUST match upstream dotabuff/manta version exactly.**

If dotabuff/manta is at version `3.0.2`, then python-manta should also be `3.0.2`.

## Why This Matters

1. **Clear Compatibility** - Users immediately know which manta version they're using
2. **No Confusion** - No need to maintain a compatibility matrix
3. **Simpler Debugging** - Same version = same features/bugs
4. **Easier Support** - "Use python-manta 3.0.2 for manta 3.0.2"

## How It Works

### For Releases

When releasing python-manta:

1. **Check upstream manta version**
   ```bash
   # Visit https://github.com/dotabuff/manta/tags
   # Find latest tag, e.g., v3.0.2
   ```

2. **Set MANTA_REF to that exact tag**
   ```bash
   # In your environment or workflow
   export MANTA_REF=v3.0.2
   ```

3. **Set python-manta to same version**
   ```toml
   # pyproject.toml
   version = "3.0.2"  # Match manta exactly
   ```

4. **Build and release**
   ```bash
   ./tools/prepare_release.sh 3.0.2
   git push origin v3.0.2
   ```

### For Development

When building from master/latest:

```bash
# Default: uses master branch (latest development)
./build.sh

# Or specify exact version
MANTA_REF=v3.0.2 ./build.sh
```

### In CI/CD

The GitHub Actions workflow accepts `MANTA_REF`:

```yaml
env:
  MANTA_REF: v3.0.2  # Use exact version tag
```

For development builds (main branch pushes), it uses `master`:

```yaml
env:
  MANTA_REF: master  # Latest development
```

## Version Naming Convention

### Stable Releases

```
manta version: v3.0.2
python-manta version: 3.0.2
python-manta tag: v3.0.2
```

**Example:**
```bash
# Manta released v3.0.2
# We release python-manta 3.0.2
./tools/prepare_release.sh 3.0.2
export MANTA_REF=v3.0.2
git push origin v3.0.2
```

### Development Releases

For testing against manta master before a release:

```
manta version: master (unreleased)
python-manta version: 3.1.0.dev1 (pre-release)
MANTA_REF: master
```

**Example:**
```bash
# Testing against manta master
./tools/prepare_release.sh 3.1.0.dev1
export MANTA_REF=master
git push origin v3.1.0-dev1  # Goes to TestPyPI
```

## Release Workflow

### Step 1: Check Upstream Version

```bash
# Check latest manta release
curl -s https://api.github.com/repos/dotabuff/manta/releases/latest | grep tag_name

# Or visit: https://github.com/dotabuff/manta/releases
```

### Step 2: Update python-manta Version

```bash
# Edit pyproject.toml
vim pyproject.toml
# Set: version = "3.0.2"  (match manta)

# Update CHANGELOG.md
vim CHANGELOG.md
# Add:
## [3.0.2] - 2025-01-20
### Changed
- Updated to manta v3.0.2
- [List any python-manta specific changes]
```

### Step 3: Build Against Exact Version

```bash
# Set manta version for build
export MANTA_REF=v3.0.2

# Build locally to test
./build.sh

# Test
python run_tests.py --all
```

### Step 4: Release

```bash
# Create release
./tools/prepare_release.sh 3.0.2

# Push (this will build with MANTA_REF in CI)
git push origin main
git push origin v3.0.2
```

### Step 5: Update Workflow for This Release

For the specific release, you may want to temporarily update the workflow:

```yaml
# .github/workflows/build-wheels.yml
env:
  MANTA_REF: v3.0.2  # Lock to this version for this release
```

Or better, make it dynamic based on the tag:

```yaml
env:
  # Extract version from git tag (v3.0.2 → v3.0.2)
  MANTA_REF: ${{ github.ref_name }}
```

## Examples

### Example 1: Manta v3.0.2 Release

```bash
# 1. Manta team releases v3.0.2
# 2. We update python-manta:

# Update version
echo 'version = "3.0.2"' >> pyproject.toml

# Update CHANGELOG
cat >> CHANGELOG.md <<EOF
## [3.0.2] - 2025-01-20
### Changed
- Synchronized with manta v3.0.2
- All 272 callbacks updated to match manta v3.0.2 API
EOF

# Build and test with exact version
export MANTA_REF=v3.0.2
./build.sh
python run_tests.py --all

# Release
./tools/prepare_release.sh 3.0.2
git push origin main
git push origin v3.0.2
```

### Example 2: Development Build

```bash
# Working on new features against manta master

# Update version to dev
echo 'version = "3.1.0.dev1"' >> pyproject.toml

# Build against master
export MANTA_REF=master
./build.sh

# Test release to TestPyPI
./tools/prepare_release.sh 3.1.0.dev1
git push origin v3.1.0-dev1  # → TestPyPI
```

## Checking Compatibility

Users can verify they have matching versions:

```python
import python_manta

# python-manta version
print(python_manta.__version__)  # e.g., "3.0.2"

# This should match the manta version it was built against
# (Check CHANGELOG.md or GitHub release notes)
```

## When Versions Diverge (Special Cases)

Sometimes we may need python-manta-specific patch releases:

```
manta version: v3.0.2 (no changes)
python-manta version: 3.0.2.post1 (python-specific bugfix)
```

Use PEP 440 post-releases for python-manta-only fixes:

```bash
# Python-specific bugfix, no manta changes
./tools/prepare_release.sh 3.0.2.post1
export MANTA_REF=v3.0.2  # Still use same manta version
```

## Summary

| Scenario | Manta Version | python-manta Version | MANTA_REF |
|----------|---------------|---------------------|-----------|
| Stable release | v3.0.2 | 3.0.2 | v3.0.2 |
| Dev against master | master | 3.1.0.dev1 | master |
| Python-specific fix | v3.0.2 | 3.0.2.post1 | v3.0.2 |
| Release candidate | v3.1.0-rc1 | 3.1.0rc1 | v3.1.0-rc1 |

## Quick Commands

```bash
# Check latest manta release
curl -s https://api.github.com/repos/dotabuff/manta/releases/latest | jq -r .tag_name

# Build against specific manta version
MANTA_REF=v3.0.2 ./build.sh

# Release python-manta matching manta
./tools/prepare_release.sh 3.0.2
export MANTA_REF=v3.0.2
git push origin v3.0.2
```

---

**Remember:** Always sync versions! Users expect python-manta 3.0.2 to wrap manta 3.0.2. 🔒
