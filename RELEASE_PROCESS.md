# Release Process for Python Manta

This document describes the step-by-step process for releasing a new version of python-manta.

## Prerequisites

Before starting a release:
- [ ] All planned features/fixes are merged to `master`
- [ ] All tests pass
- [ ] You have write access to the repository
- [ ] PyPI API tokens are configured in GitHub Secrets (see [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md))

## Release Types

### Patch Release (1.4.5 → 1.4.6)
- Bug fixes, performance improvements, documentation updates

### Minor Release (1.4.5 → 1.5.0)
- New features (backwards compatible)

### Major Release (1.4.5 → 2.0.0)
- Breaking API changes

## Release Process

### Step 1: Update Version

Edit `pyproject.toml`:
```toml
[project]
name = "python-manta"
version = "1.4.6"  # Update this line
```

### Step 2: Update Changelog

Add an entry to `CHANGELOG.md` based on git commits since last release:

```bash
# View commits since last tag
git log v1.4.5..HEAD --oneline
```

### Step 3: Commit and Tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v1.4.6"
git tag -a v1.4.6 -m "Release v1.4.6"
```

### Step 4: Push

```bash
git push origin master
git push origin v1.4.6
```

### Step 5: Monitor GitHub Actions

1. Go to https://github.com/equilibrium-coach/python-manta/actions
2. Watch the "Build Wheels" workflow
3. Verify all platform builds succeed (Linux, macOS, Windows)
4. Check that PyPI publishing succeeds

### Step 7: Create GitHub Release

1. Go to https://github.com/equilibrium-coach/python-manta/releases/new
2. Choose the tag you just created (v1.4.6)
3. Title: `v1.4.6`
4. Description: Copy the changelog content for this version
5. Check "Set as the latest release"
6. Publish release

### Step 8: Verify PyPI

1. Go to https://pypi.org/project/python-manta/
2. Verify new version is listed
3. Check that all platform wheels are available
4. Test installation:
   ```bash
   pip install python-manta==1.4.6
   python -c "import python_manta; print('Success')"
   ```

## Testing Releases with TestPyPI

Before publishing to production PyPI, you can test releases using TestPyPI.

### How to Publish to TestPyPI

Use a version tag with a hyphen (triggers TestPyPI instead of PyPI):

```bash
# 1. Prepare test release (use .dev suffix for PEP 440 compliance)
./tools/prepare_release.sh 1.4.6.dev1

# 2. Push tag (triggers TestPyPI upload)
git push origin master
git push origin v1.4.6-dev1

# 3. Wait for GitHub Actions to complete

# 4. Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==1.4.6.dev1

# 5. If everything works, release to production
./tools/prepare_release.sh 1.4.6
git push origin v1.4.6
```

### TestPyPI vs PyPI

| Feature | TestPyPI | PyPI |
|---------|----------|------|
| Trigger | Tags **with** hyphen (`v1.4.6-dev1`) | Tags **without** hyphen (`v1.4.6`) |
| Purpose | Testing | Production |
| URL | test.pypi.org | pypi.org |
| Install | Requires `--index-url` flag | Normal `pip install` |

## Emergency Hotfix Process

For critical bugs that need immediate release:

```bash
# 1. Create hotfix branch from the release tag
git checkout -b hotfix/1.4.6 v1.4.5

# 2. Fix the bug and test
# ... make changes ...
python run_tests.py --all

# 3. Update CHANGELOG.md and version
# pyproject.toml: version = "1.4.6"

# 4. Commit and tag
git commit -am "fix: critical bug in parser (hotfix)"
git tag -a v1.4.6 -m "Hotfix v1.4.6"

# 5. Merge to master and push
git checkout master
git merge hotfix/1.4.6
git push origin master
git push origin v1.4.6
```

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/) and synchronizes with upstream [dotabuff/manta](https://github.com/dotabuff/manta) versions.

- **MAJOR (2.0.0)**: Breaking API changes
- **MINOR (1.5.0)**: New features (backwards compatible)
- **PATCH (1.4.6)**: Bug fixes

For Python-specific patches without manta changes, use post-release versions: `1.4.5.post1`

## Troubleshooting

### "PyPI publishing failed"

1. Check GitHub Actions logs for errors
2. Verify PyPI API tokens are configured in GitHub Secrets
3. Check if version already exists on PyPI (can't overwrite)

### "Wheels failed to build for some platforms"

1. Check the specific platform's build logs in GitHub Actions
2. Common issues:
   - Go installation failed
   - Manta clone failed
   - CGO compilation failed
3. Fix the issue and push a new patch tag

### "Wrong version published to PyPI"

You cannot delete from PyPI, but you can:
1. Yank the release: `twine yank python-manta 1.4.6`
2. Release a fixed version: `1.4.7`

## See Also

- `MANTA_VERSION_MANAGEMENT.md` - Version synchronization with upstream manta
- `PYPI_SETUP_GUIDE.md` - PyPI token configuration
- `BUILDING.md` - Build system documentation
- `CHANGELOG.md` - Project changelog
