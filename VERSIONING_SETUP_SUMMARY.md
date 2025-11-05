# Versioning and Changelog Setup Summary

## Overview

This document summarizes the complete versioning and changelog system now in place for python-manta.

## What Was Added

### 📚 Documentation

1. **VERSIONING_AND_CHANGELOG_GUIDE.md** (Comprehensive guide)
   - Semantic Versioning (SemVer) explained
   - Keep a Changelog format
   - Conventional Commits specification
   - Release workflows
   - Automation tools overview
   - Best practices for OSS projects

2. **CHANGELOG.md** (Project changelog)
   - Follows Keep a Changelog format
   - Documents all releases
   - Current version: 0.1.0
   - [Unreleased] section for upcoming changes

3. **RELEASE_PROCESS.md** (Step-by-step release guide)
   - How to prepare a release
   - Automated script usage
   - Manual process fallback
   - Emergency hotfix process
   - Troubleshooting guide

4. **CONTRIBUTING.md** (Contributor guidelines)
   - Development workflow
   - Commit message conventions
   - Pull request process
   - Testing guidelines
   - Code style requirements

### 🤖 Automation

1. **tools/prepare_release.sh** (Release automation script)
   ```bash
   ./tools/prepare_release.sh 0.2.0
   ```
   - Validates version format
   - Checks branch and uncommitted changes
   - Prompts for CHANGELOG.md update
   - Updates pyproject.toml automatically
   - Creates commit and tag
   - Shows next steps

2. **.github/workflows/pr-labels.yml** (PR automation)
   - Auto-labels PRs based on files changed
   - Checks if CHANGELOG.md was updated
   - Validates version bumps
   - Enforces changelog discipline

3. **.github/labeler.yml** (Label configuration)
   - Automatic PR labeling rules
   - Categories: documentation, build, ci, go, python, tests, etc.
   - Branch-based labels: feature, bugfix, breaking, etc.

## Quick Start Guide

### For Contributors

1. **Create a feature branch**:
   ```bash
   git checkout -b feat/my-new-feature
   ```

2. **Make changes with conventional commits**:
   ```bash
   git commit -m "feat(parser): add support for new callback"
   ```

3. **Update CHANGELOG.md**:
   ```markdown
   ## [Unreleased]
   ### Added
   - Support for new callback type (#123)
   ```

4. **Create PR** - Automated checks will validate everything

### For Maintainers (Releasing)

1. **Run the release script**:
   ```bash
   ./tools/prepare_release.sh 0.2.0
   ```

2. **Follow the prompts** - script handles most steps

3. **Push to trigger CI/CD**:
   ```bash
   git push origin main
   git push origin v0.2.0
   ```

4. **Create GitHub release** - Copy changelog content

5. **Verify on PyPI** - Check wheels published

## Versioning Strategy

### Current Phase: 0.x.y (Pre-1.0)

We're in initial development:
- **0.1.0 → 0.2.0**: New features (may include breaking changes)
- **0.1.0 → 0.1.1**: Bug fixes only

### Future: 1.x.y (Stable)

After 1.0.0 release (when API is stable):
- **1.0.0 → 2.0.0**: MAJOR - Breaking changes only
- **1.0.0 → 1.1.0**: MINOR - New features (backwards compatible)
- **1.0.0 → 1.0.1**: PATCH - Bug fixes only

## Changelog Categories

Use these categories in CHANGELOG.md:

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features to be removed soon
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

## Commit Message Format

```
<type>[scope]: <description>

Examples:
feat(parser): add Windows support
fix(cgo): resolve memory leak
docs(readme): update installation instructions
chore(deps): update Go to 1.21.5
```

**Types**: feat, fix, docs, style, refactor, perf, test, build, ci, chore

## Automated Checks

When you open a PR, GitHub Actions will:
- ✅ Auto-label based on files changed
- ✅ Check if CHANGELOG.md was updated
- ✅ Warn if version was bumped (unusual for feature PRs)
- ✅ Run all tests
- ✅ Build wheels for all platforms

## Files Structure

```
python-manta/
├── CHANGELOG.md                          # Project changelog
├── VERSIONING_AND_CHANGELOG_GUIDE.md    # Comprehensive guide
├── RELEASE_PROCESS.md                   # Release instructions
├── CONTRIBUTING.md                      # Contributor guide
├── .github/
│   ├── workflows/
│   │   ├── build-wheels.yml             # Build & publish
│   │   └── pr-labels.yml                # PR automation
│   └── labeler.yml                      # Label config
└── tools/
    └── prepare_release.sh               # Release script
```

## Example Workflow

### Adding a New Feature

```bash
# 1. Create branch
git checkout -b feat/add-callback-xyz

# 2. Implement feature
# ... code changes ...

# 3. Write tests
# ... test code ...

# 4. Commit with conventional format
git commit -m "feat(parser): add callback XYZ support

- Implement XYZ callback
- Add tests
- Update documentation"

# 5. Update CHANGELOG.md
# Add to [Unreleased] > Added section

# 6. Push and create PR
git push origin feat/add-callback-xyz
```

### Releasing a New Version

```bash
# 1. Ensure all PRs are merged to main
git checkout main
git pull origin main

# 2. Run release script
./tools/prepare_release.sh 0.2.0

# 3. Script will:
#    - Prompt you to update CHANGELOG.md
#    - Update pyproject.toml
#    - Create commit and tag

# 4. Push (triggers automatic PyPI publish)
git push origin main
git push origin v0.2.0

# 5. Create GitHub release
# Copy changelog content to release notes
```

## Benefits of This System

### For Contributors
✅ Clear guidelines on how to contribute
✅ Automated checks prevent mistakes
✅ Consistent commit history
✅ Easy to find what changed and when

### For Maintainers
✅ Semi-automated release process
✅ No manual version tracking needed
✅ Clear changelog for every release
✅ Enforced changelog updates via CI

### For Users
✅ Know exactly what changed in each version
✅ Clear migration guides for breaking changes
✅ Can track down when features were added
✅ Understand impact of upgrading

## Migration to Full Automation (Optional)

Currently using **semi-automated** approach (manual CHANGELOG updates).

Can upgrade to **fully automated** with tools like:

### Option 1: release-please (Recommended)
```yaml
# Generates changelog from commits
# Auto-bumps version based on conventional commits
# Creates release PR automatically
```

### Option 2: commitizen
```bash
# Interactive commit messages
# Automatic version bumping
# Changelog generation
```

See `VERSIONING_AND_CHANGELOG_GUIDE.md` section "Automation Tools" for details.

## Best Practices We're Following

✅ **Semantic Versioning** - Predictable version numbers
✅ **Keep a Changelog** - Human-readable changelog
✅ **Conventional Commits** - Searchable, parseable history
✅ **Automated Validation** - PR checks enforce standards
✅ **Release Automation** - Reduce human error
✅ **Clear Documentation** - Everyone knows the process

## Common Tasks Quick Reference

| Task | Command |
|------|---------|
| Release new version | `./tools/prepare_release.sh 0.2.0` |
| Commit new feature | `git commit -m "feat(scope): description"` |
| Commit bug fix | `git commit -m "fix(scope): description"` |
| Update changelog | Edit `CHANGELOG.md` > `[Unreleased]` section |
| Run tests | `python run_tests.py --all` |
| Check coverage | `python run_tests.py --coverage` |
| Build locally | `./build.sh` |

## Troubleshooting

### "Changelog check failed on my PR"
➡️ Update `CHANGELOG.md` or add `skip-changelog` label if not needed

### "I forgot to update the changelog"
➡️ Add another commit with changelog update to your PR

### "How do I know which version to release?"
➡️ See version bump decision tree in `VERSIONING_AND_CHANGELOG_GUIDE.md`

### "Can I skip the release script?"
➡️ Yes, see "Manual Process" in `RELEASE_PROCESS.md`

## Next Steps

1. **Start using conventional commits** in all PRs
2. **Update CHANGELOG.md** with every feature/fix
3. **Use the release script** when ready to publish
4. **Create GitHub releases** with changelog content
5. **Consider full automation** (release-please) later

## Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- Project docs: `VERSIONING_AND_CHANGELOG_GUIDE.md`

## Questions?

See detailed guides:
- `VERSIONING_AND_CHANGELOG_GUIDE.md` - Theory and best practices
- `RELEASE_PROCESS.md` - Step-by-step release guide
- `CONTRIBUTING.md` - How to contribute
- `BUILDING.md` - Build system details

Or open a GitHub discussion!
