# Release Process for Python Manta

This document describes the step-by-step process for releasing a new version of python-manta.

## Prerequisites

Before starting a release:
- [ ] All planned features/fixes for the release are merged to `main`
- [ ] All tests pass
- [ ] Documentation is up to date
- [ ] You have write access to the repository
- [ ] PyPI Trusted Publishing is configured (one-time setup)

## Release Types

### Patch Release (0.1.0 → 0.1.1)
- Bug fixes
- Performance improvements
- Documentation updates
- No new features or API changes

### Minor Release (0.1.0 → 0.2.0)
- New features (backwards compatible)
- New callbacks or functionality
- Deprecation warnings (but don't remove features yet)

### Major Release (0.1.0 → 1.0.0)
- Breaking API changes
- Removal of deprecated features
- Incompatible changes

**Note**: While in 0.x.y, breaking changes can happen in minor versions, but should still be well-documented.

## Release Process

### Automated (Recommended)

We provide a helper script that automates most steps:

```bash
# Run the release preparation script
./tools/prepare_release.sh 0.2.0
```

The script will:
1. ✅ Validate version format
2. ✅ Check you're on the right branch
3. ✅ Check for uncommitted changes
4. ✅ Prompt you to update CHANGELOG.md
5. ✅ Update version in pyproject.toml
6. ✅ Create commit and tag
7. ✅ Show you next steps

Then just:
```bash
git push origin main
git push origin v0.2.0
```

### Manual Process

If you prefer to do it manually or the script doesn't work for you:

#### Step 1: Update CHANGELOG.md

Edit `CHANGELOG.md`:

```markdown
## [Unreleased]
<!-- Leave empty for future changes -->

## [0.2.0] - 2025-01-20
### Added
- Support for macOS ARM64 (Apple Silicon)
- Windows wheel building

### Changed
- Improved error messages in parser

### Fixed
- Memory leak in message handling

[Unreleased]: https://github.com/equilibrium-coach/python-manta/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/equilibrium-coach/python-manta/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/equilibrium-coach/python-manta/releases/tag/v0.1.0
```

**Tips:**
- Move all content from `[Unreleased]` to the new version section
- Add today's date
- Update the comparison links at the bottom
- Leave `[Unreleased]` empty for future changes

#### Step 2: Update Version in pyproject.toml

Edit `pyproject.toml`:
```toml
[project]
name = "python-manta"
version = "0.2.0"  # Update this line
```

#### Step 3: Commit Changes

```bash
git add CHANGELOG.md pyproject.toml
git commit -m "chore: release v0.2.0"
```

#### Step 4: Create Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
```

#### Step 5: Push

```bash
git push origin main
git push origin v0.2.0
```

### Step 6: Monitor GitHub Actions

1. Go to https://github.com/equilibrium-coach/python-manta/actions
2. Watch the "Build Wheels" workflow
3. Verify all platform builds succeed (Linux, macOS, Windows)
4. Check that PyPI publishing succeeds

### Step 7: Create GitHub Release

1. Go to https://github.com/equilibrium-coach/python-manta/releases/new
2. Choose the tag you just created (v0.2.0)
3. Title: `v0.2.0`
4. Description: Copy the changelog content for this version

Example:
```markdown
## What's New in v0.2.0

### Added
- Support for macOS ARM64 (Apple Silicon)
- Windows wheel building
- Automated PyPI publishing

### Changed
- Improved error messages in parser

### Fixed
- Memory leak in message handling

## Installation

```bash
pip install python-manta==0.2.0
```

## Full Changelog
https://github.com/equilibrium-coach/python-manta/compare/v0.1.0...v0.2.0
```

5. Check "Set as the latest release"
6. Publish release

### Step 8: Verify PyPI

1. Go to https://pypi.org/project/python-manta/
2. Verify new version is listed
3. Check that all platform wheels are available
4. Test installation:
   ```bash
   pip install python-manta==0.2.0
   python -c "import python_manta; print(python_manta.__version__)"
   ```

### Step 9: Announce (Optional)

- Tweet about the release
- Post in Discord/Slack communities
- Update any documentation sites
- Notify users of breaking changes (if any)

## Emergency Hotfix Process

For critical bugs that need immediate release:

```bash
# 1. Create hotfix branch from the release tag
git checkout -b hotfix/0.2.1 v0.2.0

# 2. Fix the bug
# ... make changes ...

# 3. Test thoroughly
pytest

# 4. Update CHANGELOG.md
# Add [0.2.1] section with the fix

# 5. Update version
# pyproject.toml: version = "0.2.1"

# 6. Commit and tag
git commit -am "fix: critical bug in parser (hotfix)"
git tag -a v0.2.1 -m "Hotfix v0.2.1"

# 7. Merge to main
git checkout main
git merge hotfix/0.2.1

# 8. Push everything
git push origin main
git push origin v0.2.1
```

## Pre-release (Alpha/Beta/RC)

For testing before official release:

```bash
# Alpha: 1.0.0-alpha.1
./tools/prepare_release.sh 1.0.0-alpha.1

# Beta: 1.0.0-beta.1
./tools/prepare_release.sh 1.0.0-beta.1

# Release Candidate: 1.0.0-rc.1
./tools/prepare_release.sh 1.0.0-rc.1
```

Users can test with:
```bash
pip install python-manta==1.0.0-alpha.1
```

## Version Numbering Guidelines

### Current Status (0.x.y)

We're in initial development (0.x.y). Use this scheme:

- **0.1.0 → 0.2.0**: New features (may include breaking changes)
- **0.1.0 → 0.1.1**: Bug fixes only

### When to Release 1.0.0?

Release 1.0.0 when:
- ✅ API is stable and tested in production
- ✅ All major features are complete
- ✅ Documentation is comprehensive
- ✅ Ready to commit to backwards compatibility
- ✅ Breaking changes will require 2.0.0

For python-manta, consider 1.0.0 when:
- [ ] All 272 callbacks are production-tested
- [ ] API design is stable (unlikely to change parse method signatures)
- [ ] Used in production by multiple projects
- [ ] Performance is optimized
- [ ] Error handling is comprehensive

### After 1.0.0

Strict SemVer:
- **1.0.0 → 2.0.0**: Breaking changes only
- **1.0.0 → 1.1.0**: New features (backwards compatible)
- **1.0.0 → 1.0.1**: Bug fixes only

## Checklist for Major Releases (1.0.0, 2.0.0, etc.)

- [ ] Update all documentation
- [ ] Write migration guide (if breaking changes)
- [ ] Update README with new features
- [ ] Update examples
- [ ] Run full test suite on all platforms
- [ ] Test on real demo files
- [ ] Check performance hasn't regressed
- [ ] Update CHANGELOG with migration guide
- [ ] Announce deprecations well in advance
- [ ] Blog post or announcement
- [ ] Update dependent projects

## Troubleshooting

### "PyPI publishing failed"

1. Check GitHub Actions logs for errors
2. Verify PyPI Trusted Publishing is configured
3. Check if version already exists on PyPI (can't overwrite)
4. Try republishing manually:
   ```bash
   python -m pip install build twine
   python -m build
   python -m twine upload dist/*
   ```

### "Wheels failed to build for some platforms"

1. Check the specific platform's build logs in GitHub Actions
2. Common issues:
   - Go installation failed (check Go version in before_build_*.sh)
   - Manta clone failed (check network/permissions)
   - CGO compilation failed (check compiler availability)
3. Fix the issue and push a new tag: `v0.2.1`

### "Wrong version published to PyPI"

You cannot unpublish from PyPI! But you can:
1. Yank the release: `twine yank python-manta 0.2.0`
2. Release a new version: `0.2.1`
3. Add note in CHANGELOG:
   ```markdown
   ## [0.2.1] - 2025-01-21
   ### Fixed
   - Re-release of 0.2.0 (previous release yanked due to build issue)
   ```

### "Forgot to update CHANGELOG"

Before the release is widely announced:
1. Update CHANGELOG.md
2. Amend the commit: `git commit --amend -a`
3. Force push tag: `git tag -fa v0.2.0 -m "Release v0.2.0"`
4. Push: `git push -f origin v0.2.0`

After announcement:
1. Too late to change the tag
2. Add missing info to GitHub release notes
3. Consider a patch release with updated changelog

## Automation Opportunities

### Current Status
- ✅ Wheel building automated
- ✅ PyPI publishing automated
- ✅ PR labeling automated
- ✅ Changelog validation on PRs
- ⚠️  Release preparation script (semi-automated)

### Future Automation (Optional)
- [ ] Fully automated releases with release-please
- [ ] Automatic changelog generation from commit messages
- [ ] Semantic versioning automation based on commits
- [ ] Automated GitHub release creation

See `VERSIONING_AND_CHANGELOG_GUIDE.md` for tools like:
- release-please (Google)
- commitizen (Python)
- standard-version (JavaScript)

## Questions?

See also:
- `VERSIONING_AND_CHANGELOG_GUIDE.md` - Comprehensive versioning guide
- `BUILDING.md` - Build system documentation
- `CHANGELOG.md` - Project changelog

Need help? Open an issue or discussion on GitHub!
