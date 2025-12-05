# Release Process for Python Manta

This project uses **commitizen** for automated version management and changelog generation.
All versions follow [PEP 440](https://peps.python.org/pep-0440/) format.

## Prerequisites

Before starting a release:
- [ ] All planned features/fixes are merged to `master`
- [ ] All tests pass
- [ ] You have write access to the repository
- [ ] PyPI API tokens are configured in GitHub Secrets
- [ ] commitizen is installed: `pip install commitizen`

## Version Types (PEP 440)

| Type | Example | Tag | Publish To |
|------|---------|-----|------------|
| Development | `1.5.0.dev0` | `v1.5.0.dev0` | TestPyPI |
| Alpha | `1.5.0a0` | `v1.5.0a0` | TestPyPI |
| Beta | `1.5.0b0` | `v1.5.0b0` | TestPyPI |
| Release Candidate | `1.5.0rc0` | `v1.5.0rc0` | TestPyPI |
| Final Release | `1.5.0` | `v1.5.0` | PyPI |

## Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types that affect version:**
- `feat:` → bumps MINOR version
- `fix:` → bumps PATCH version
- `feat!:` or `BREAKING CHANGE:` → bumps MAJOR version

**Types that don't affect version:**
- `docs:`, `style:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`, `chore:`

## Release Workflows

### Development Release (TestPyPI)

For testing changes before a proper release:

```bash
# Check current version
cz version

# Bump to next dev version (auto-increments)
cz bump --devrelease

# Push changes and tag
git push origin master --tags
```

The CI pipeline will:
1. Build wheels for all platforms
2. Publish to TestPyPI

Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta
```

### Pre-Release (TestPyPI)

For alpha/beta/rc releases:

```bash
# Alpha release
cz bump --prerelease alpha

# Beta release
cz bump --prerelease beta

# Release candidate
cz bump --prerelease rc

# Push
git push origin master --tags
```

### Final Release (PyPI)

When ready for production:

```bash
# Graduate from dev/pre-release to final
cz bump

# Or force specific increment
cz bump --increment MINOR

# Push
git push origin master --tags
```

The CI pipeline will:
1. Build wheels for all platforms
2. Publish to PyPI
3. Upload wheels to GitHub Release

### Verify Release

1. Check GitHub Actions: https://github.com/DeepBlueCoding/python-manta/actions
2. Check PyPI: https://pypi.org/project/python-manta/
3. Test installation:
   ```bash
   pip install python-manta==X.Y.Z
   python -c "from python_manta import Parser; print('Success')"
   ```

## Quick Reference

```bash
# Interactive commit with prompts
cz commit

# Check current version
cz version

# Dry run (see what would happen)
cz bump --dry-run

# View changelog
cz changelog --dry-run

# Bump commands
cz bump --devrelease        # 1.5.0 → 1.5.1.dev0
cz bump --prerelease alpha  # 1.5.0 → 1.5.1a0
cz bump --prerelease beta   # 1.5.1a0 → 1.5.1b0
cz bump --prerelease rc     # 1.5.1b0 → 1.5.1rc0
cz bump                     # 1.5.1rc0 → 1.5.1
cz bump --increment PATCH   # Force patch bump
cz bump --increment MINOR   # Force minor bump
cz bump --increment MAJOR   # Force major bump
```

## Emergency Hotfix

For critical bugs:

```bash
# 1. Make the fix
git checkout master
# ... fix the bug ...

# 2. Commit with fix type
git commit -m "fix: critical parser crash on malformed demo"

# 3. Bump and release
cz bump --increment PATCH
git push origin master --tags
```

## Troubleshooting

### "No commits found to generate a release"
```bash
# Force increment manually
cz bump --increment PATCH
```

### "Version already exists on PyPI"
You cannot overwrite. Bump to next version and release again.

### "Wheels failed to build"
1. Check GitHub Actions logs
2. Fix the issue
3. Release a new version

## See Also

- `MANTA_VERSION_MANAGEMENT.md` - Version synchronization with upstream manta
- `CHANGELOG.md` - Project changelog
- `CLAUDE.md` - Development guidelines
