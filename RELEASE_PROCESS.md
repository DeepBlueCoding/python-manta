# Release Process for Python Manta

This project uses **commitizen** for automated version management and changelog generation.
All versions follow [PEP 440](https://peps.python.org/pep-0440/) format.

## Version Types

| Type | Example | Tag | Publish To |
|------|---------|-----|------------|
| Development | `1.4.5.2.dev0` | `v1.4.5.2.dev0` | TestPyPI |
| Final Release | `1.4.5.2` | `v1.4.5.2` | PyPI |

## Development Workflow

During development, commits can be low-level or messy:

```bash
# Work on features/fixes with any commit style
git commit -m "wip: trying new approach"
git commit -m "fix typo"
git commit -m "more work"

# Bump dev version for testing (no changelog)
cz bump --devrelease
git push origin master --tags
```

CI will build and publish to TestPyPI for testing.

## Release Workflow

When ready for a release, squash commits into clean conventional commits:

### Step 1: Squash commits

```bash
# Find the last release tag
git tag --list 'v*' | grep -v dev | tail -1

# Interactive rebase to squash since last release
git rebase -i <last-release-tag>

# In the editor:
# - Keep first commit as "pick"
# - Change others to "squash" (s)
# - Write clean conventional commit message(s)
```

### Step 2: Write clean commit messages

Use conventional commit format for changelog generation:

```
feat: add HeroSnapshot combat stats

- armor, magic_resistance, damage_min, damage_max
- strength, agility, intellect attributes
```

**Types that appear in changelog:**
- `feat:` → **Added** section
- `fix:` → **Fixed** section
- `perf:` → **Performance** section

**Types excluded from changelog:**
- `docs:`, `style:`, `refactor:`, `test:`, `build:`, `ci:`, `chore:`

### Step 3: Bump and release

```bash
# Preview what will happen
cz bump --dry-run

# Bump version (auto-updates changelog)
cz bump

# Push
git push origin master --tags
```

### Step 4: Verify

1. Check GitHub Actions: https://github.com/DeepBlueCoding/python-manta/actions
2. Check PyPI: https://pypi.org/project/python-manta/
3. Test:
   ```bash
   pip install python-manta==X.Y.Z
   python -c "from python_manta import Parser; print('OK')"
   ```

## Quick Reference

```bash
cz version              # Check current version
cz bump --dry-run       # Preview next version
cz bump --devrelease    # Dev bump (TestPyPI, no changelog)
cz bump                 # Release bump (PyPI, with changelog)
cz bump --increment PATCH  # Force specific increment
cz bump --increment MINOR
cz bump --increment MAJOR
```

## Troubleshooting

### "No commits found"
```bash
cz bump --increment PATCH  # Force increment
```

### "Version exists on PyPI"
Cannot overwrite. Bump to next version.

## See Also

- `MANTA_VERSION_MANAGEMENT.md` - Upstream manta version sync
- `CHANGELOG.md` - Project changelog
- `CLAUDE.md` - Development guidelines
