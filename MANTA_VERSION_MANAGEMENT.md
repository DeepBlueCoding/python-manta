# Manta Version Management

This project uses a **centralized version locking system** to ensure consistent manta library versions across all builds.

## Quick Start

### Check Current Manta Version

```bash
cat .manta-version
```

### Upgrade Manta Version

```bash
# Upgrade to specific release
./tools/upgrade_manta_version.sh v3.0.3

# Use latest development
./tools/upgrade_manta_version.sh master

# Lock to specific commit
./tools/upgrade_manta_version.sh abc123def
```

### Build with Locked Version

```bash
# Uses version from .manta-version automatically
./build.sh

# Or override temporarily
MANTA_REF=v3.0.2 ./build.sh
```

## How It Works

### Centralized Version File: `.manta-version`

This file contains the locked manta library version used for all builds:

```bash
# .manta-version
master
```

**Valid values:**
- `v3.0.2` - Specific release tag (recommended for stable releases)
- `master` - Latest development code
- `abc123def` - Specific commit hash

### Automatic Version Reading

All build scripts automatically read from `.manta-version`:

1. **GitHub Actions** (`.github/workflows/build-wheels.yml`):
   ```yaml
   - name: Read manta version
     run: |
       MANTA_REF=$(grep -v '^#' .manta-version | tail -n1)
       echo "MANTA_REF=${MANTA_REF}" >> $GITHUB_ENV
   ```

2. **Build Scripts** (`tools/prepare_manta.sh`):
   ```bash
   if [[ -z "${MANTA_REF:-}" ]]; then
       MANTA_REF=$(grep -v '^#' .manta-version | tail -n1)
   fi
   ```

3. **Local Builds** (`./build.sh`):
   - Calls `tools/prepare_manta.sh` which reads `.manta-version`

### Version Synchronization Strategy

**Core Principle:** python-manta version should match upstream manta version

| Scenario | `.manta-version` | `pyproject.toml` version |
|----------|------------------|--------------------------|
| Stable release | `v3.0.2` | `"3.0.2"` |
| Development | `master` | `"0.1.0.dev1"` |
| Python-specific patch | `v3.0.2` | `"3.0.2.post1"` |

## Common Workflows

### Releasing python-manta 3.0.3

```bash
# 1. Check latest upstream manta version
curl -s https://api.github.com/repos/dotabuff/manta/releases/latest | grep tag_name
# Output: "tag_name": "v3.0.3"

# 2. Upgrade manta version
./tools/upgrade_manta_version.sh v3.0.3

# 3. Update python-manta version to match
sed -i 's/version = ".*"/version = "3.0.3"/' pyproject.toml

# 4. Test the build
./build.sh
python run_tests.py --unit

# 5. Commit and tag
git add .manta-version pyproject.toml
git commit -m "chore: upgrade to manta v3.0.3"
git tag v3.0.3
git push origin main
git push origin v3.0.3
```

### Using Development Version

```bash
# 1. Switch to master
./tools/upgrade_manta_version.sh master

# 2. Use dev version number
sed -i 's/version = ".*"/version = "3.1.0.dev1"/' pyproject.toml

# 3. Test
./build.sh
python run_tests.py --unit

# 4. Commit
git add .manta-version pyproject.toml
git commit -m "chore: switch to manta master for development"
```

### Python-Specific Patch (No Manta Changes)

If you need to fix a bug in python-manta without changing manta version:

```bash
# 1. Keep same manta version
cat .manta-version
# Output: v3.0.2

# 2. Use post-release version
sed -i 's/version = ".*"/version = "3.0.2.post1"/' pyproject.toml

# 3. Make your Python fixes
# ... edit Python code ...

# 4. Test and release
./build.sh
python run_tests.py --unit
git tag v3.0.2.post1
```

## CI/CD Integration

GitHub Actions automatically uses `.manta-version`:

```yaml
# Workflow reads .manta-version at the start of each job
# All wheels built with the same manta version
# Ensures consistency across Linux, macOS, Windows builds
```

**Tag-based releases:**
- `git tag v3.0.3` → Builds with manta `v3.0.3` (from `.manta-version`)
- Publishes to PyPI as `python-manta==3.0.3`

## Override for Testing

You can temporarily override the locked version:

```bash
# Override for single build
MANTA_REF=v3.0.4-rc1 ./build.sh

# Override for CI (set as environment variable)
# In GitHub Actions workflow_dispatch, set MANTA_REF input
```

## Benefits

✅ **Single Source of Truth** - Version defined in one place (`.manta-version`)
✅ **Consistent Builds** - All platforms use the same manta version
✅ **Easy Upgrades** - Simple script to upgrade versions
✅ **Version Tracking** - Git tracks version changes
✅ **CI/CD Ready** - GitHub Actions automatically uses locked version
✅ **Override Support** - Can still override for testing

## Troubleshooting

### Build fails with "Remote branch not found"

The version in `.manta-version` doesn't exist:

```bash
# Check what versions exist
git ls-remote --tags https://github.com/dotabuff/manta.git

# Update to valid version
./tools/upgrade_manta_version.sh v3.0.2
```

### CI uses wrong manta version

Check that `.manta-version` is committed:

```bash
git add .manta-version
git commit -m "chore: lock manta version"
git push
```

### Want to test specific commit

```bash
# Use full commit hash
./tools/upgrade_manta_version.sh abc123def456789

# Or set temporarily
MANTA_REF=abc123def ./build.sh
```

## See Also

- `VERSION_SYNC_STRATEGY.md` - Version synchronization philosophy
- `RELEASE_PROCESS.md` - Complete release workflow
- `tools/upgrade_manta_version.sh` - Version upgrade script
- `tools/prepare_manta.sh` - Manta clone/update script
