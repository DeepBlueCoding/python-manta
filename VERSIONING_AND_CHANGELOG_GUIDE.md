# Versioning and Changelog Best Practices Guide

## Table of Contents
1. [Semantic Versioning (SemVer)](#semantic-versioning)
2. [Changelog Management](#changelog-management)
3. [Conventional Commits](#conventional-commits)
4. [Release Workflow](#release-workflow)
5. [Automation Tools](#automation-tools)
6. [Best Practices for OSS](#best-practices-for-oss)

---

## Semantic Versioning (SemVer)

### Overview
Semantic Versioning (https://semver.org/) is the industry standard for version numbers.

### Format: MAJOR.MINOR.PATCH

```
1.2.3
│ │ │
│ │ └─ PATCH: Bug fixes, minor changes (backwards compatible)
│ └─── MINOR: New features (backwards compatible)
└───── MAJOR: Breaking changes (NOT backwards compatible)
```

### Rules

1. **MAJOR (1.0.0 → 2.0.0)**
   - Breaking API changes
   - Remove deprecated features
   - Incompatible changes that require users to modify their code

   Examples:
   ```python
   # v1.x.x
   parser.parse(file)

   # v2.0.0 - BREAKING CHANGE
   parser.parse(file, encoding="utf-8")  # New required parameter
   ```

2. **MINOR (1.1.0 → 1.2.0)**
   - New features that are backwards compatible
   - New functionality added
   - Deprecation warnings (but don't remove yet)

   Examples:
   ```python
   # v1.1.0
   parser.parse_header(file)

   # v1.2.0 - NEW FEATURE (old methods still work)
   parser.parse_universal(file, filter, max_messages)  # New method added
   ```

3. **PATCH (1.1.1 → 1.1.2)**
   - Bug fixes
   - Performance improvements
   - Documentation updates
   - Internal refactoring (no API changes)

   Examples:
   ```python
   # v1.1.1 - Memory leak in parser
   # v1.1.2 - Fixed memory leak (same API)
   ```

### Pre-release Versions

For versions before 1.0.0 or pre-releases:

```
0.1.0      - Initial development (anything can change)
0.2.0      - More development
1.0.0-alpha.1   - Alpha release
1.0.0-beta.1    - Beta release
1.0.0-rc.1      - Release candidate
1.0.0      - First stable release
```

**Important**: Version 0.x.y is for initial development. Anything may change at any time. The public API should not be considered stable.

### When to Release 1.0.0?

Release 1.0.0 when:
- ✅ The API is stable and unlikely to change dramatically
- ✅ The software is being used in production
- ✅ You're ready to commit to backwards compatibility
- ✅ Core features are complete and tested

For python-manta:
- Currently: 0.1.0 (early development)
- Could go 1.0.0 when: All 272 callbacks are production-tested, API is stable

---

## Changelog Management

### Keep a Changelog Format

Use the **Keep a Changelog** format (https://keepachangelog.com/):

#### Basic Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- New feature that's not yet released

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security fixes

## [1.2.0] - 2025-01-15
### Added
- New universal parser with 272 callback support
- Support for all DOTA user messages

### Changed
- Improved error handling in CGO wrapper

### Fixed
- Memory leak in message parsing

## [1.1.0] - 2024-12-01
### Added
- Draft parsing support
- CDOTAUserMsg_ChatMessage callback

## [1.0.0] - 2024-11-01
### Added
- Initial stable release
- Header parsing functionality

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/user/repo/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/user/repo/releases/tag/v1.0.0
```

### Changelog Categories

| Category | When to Use | Example |
|----------|-------------|---------|
| **Added** | New features | "Added support for Windows platform" |
| **Changed** | Changes to existing functionality | "Changed default timeout from 30s to 60s" |
| **Deprecated** | Features that will be removed soon | "Deprecated `parse_old()` in favor of `parse()`" |
| **Removed** | Features that were removed | "Removed deprecated `legacy_parser()` method" |
| **Fixed** | Bug fixes | "Fixed memory leak in message handler" |
| **Security** | Security fixes | "Fixed CVE-2024-1234 in dependency" |

### What to Include in Changelog

✅ **DO include:**
- User-facing changes
- API changes
- New features
- Bug fixes that affect users
- Breaking changes (with migration guide)
- Deprecation warnings
- Security fixes

❌ **DON'T include:**
- Internal refactoring (unless it affects performance)
- Changes to development/build process (unless it affects contributors)
- Typo fixes in code comments
- Dependency updates (unless they fix bugs or add features)

---

## Conventional Commits

### Overview

Conventional Commits (https://www.conventionalcommits.org/) is a specification for commit messages that makes it easy to generate changelogs automatically.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

```
feat:     A new feature (MINOR version bump)
fix:      A bug fix (PATCH version bump)
docs:     Documentation only changes
style:    Code style changes (formatting, no code change)
refactor: Code refactoring (no feature change or bug fix)
perf:     Performance improvements
test:     Adding or updating tests
build:    Changes to build system or dependencies
ci:       Changes to CI configuration
chore:    Other changes (tooling, etc.)
```

### Breaking Changes

Add `!` after type or add `BREAKING CHANGE:` in footer:

```
feat!: remove support for Python 3.7

BREAKING CHANGE: Python 3.7 is no longer supported. Minimum version is now 3.8.
```

### Examples

```bash
# New feature
feat(parser): add support for macOS ARM64 wheels

# Bug fix
fix(cgo): resolve memory leak in message parsing

# Breaking change
feat!: change MantaParser constructor signature

BREAKING CHANGE: MantaParser now requires library_path as first argument.
Migration: MantaParser("path/to/lib") instead of MantaParser()

# Multiple changes
feat(parser): add Windows support

- Add Windows build script
- Create before_build_windows.sh
- Update CI workflow for Windows builds

Closes #123
```

### Benefits

1. **Automatic Changelog Generation**: Tools can parse commits and generate changelogs
2. **Semantic Versioning**: Automatically determine version bumps (feat = minor, fix = patch, BREAKING = major)
3. **Searchable History**: Easy to find specific types of changes
4. **Clear Communication**: Consistent format across team

---

## Release Workflow

### Recommended Workflow for OSS Projects

#### Step 1: Development

```bash
# Work on feature branch
git checkout -b feat/new-callback-support

# Make changes with conventional commits
git commit -m "feat(parser): add support for 50 new callbacks"
git commit -m "test(parser): add tests for new callbacks"
git commit -m "docs(readme): update callback list"

# Push and create PR
git push origin feat/new-callback-support
```

#### Step 2: Update Unreleased Section

Before merging, update `CHANGELOG.md`:

```markdown
## [Unreleased]
### Added
- Support for 50 new DOTA user message callbacks
- Test coverage for all new callbacks

### Changed
- Updated documentation with new callback list
```

#### Step 3: Prepare Release

When ready to release:

```bash
# 1. Update CHANGELOG.md
# Move [Unreleased] content to new version section
## [1.3.0] - 2025-01-20
### Added
- Support for 50 new DOTA user message callbacks
...

# 2. Update version in pyproject.toml
version = "1.3.0"

# 3. Commit release preparation
git commit -am "chore: prepare release 1.3.0"

# 4. Create and push tag
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin main
git push origin v1.3.0
```

#### Step 4: Create GitHub Release

On GitHub:
1. Go to Releases → Create new release
2. Choose tag `v1.3.0`
3. Copy changelog content for this version
4. Publish release

This triggers CI/CD to build and publish to PyPI automatically.

---

## Automation Tools

### 1. **release-please** (Recommended for GitHub)

Automates versioning and changelog generation based on conventional commits.

```yaml
# .github/workflows/release-please.yml
name: Release Please

on:
  push:
    branches:
      - main

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: python
          package-name: python-manta
```

**What it does:**
- Analyzes commit messages
- Determines version bump (based on feat/fix/BREAKING)
- Updates CHANGELOG.md automatically
- Creates a release PR
- When merged, creates GitHub release and tag

### 2. **commitizen** (CLI tool)

```bash
# Install
pip install commitizen

# Use for commits (interactive)
cz commit

# Bump version automatically
cz bump

# Generate changelog
cz changelog
```

### 3. **standard-version** (JavaScript ecosystem)

```bash
npm install -g standard-version

# Bump version and generate changelog
standard-version

# First release
standard-version --first-release
```

### 4. **towncrier** (Python-specific)

```bash
pip install towncrier

# Create news fragment
echo "Added new callback support" > changelog.d/123.feature

# Build changelog for release
towncrier build --version 1.3.0
```

---

## Best Practices for OSS

### 1. **Start with CHANGELOG.md from Day 1**

Even if it's just:
```markdown
# Changelog

## [0.1.0] - 2024-11-01
### Added
- Initial release
```

### 2. **Keep Unreleased Section Updated**

Update `[Unreleased]` section with every PR:
```markdown
## [Unreleased]
### Added
- New feature from PR #123
```

### 3. **Use Conventional Commits (at least for main branch)**

Even if developers don't use it in PRs, squash merge with conventional commit message:
```
Merge PR #123: Add Windows support

feat(platform): add Windows wheel building support

- Create before_build_windows.sh
- Update CI workflow
- Add Windows documentation
```

### 4. **Tag Every Release**

```bash
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

### 5. **Create GitHub Releases**

- Include changelog for that version
- Attach built artifacts (wheels, binaries)
- Mention contributors

### 6. **Communicate Breaking Changes Clearly**

```markdown
## [2.0.0] - 2025-02-01
### BREAKING CHANGES
⚠️ This release contains breaking changes!

- Minimum Python version is now 3.8 (was 3.7)
- `parse()` method signature changed

**Migration Guide:**
- Upgrade Python to 3.8+
- Change `parser.parse(file)` to `parser.parse(file, encoding='utf-8')`
```

### 7. **Version 0.x.y Guidelines**

While in 0.x.y (pre-1.0.0):
- Breaking changes can bump MINOR (0.1.0 → 0.2.0)
- Regular changes bump PATCH (0.1.0 → 0.1.1)
- Clearly communicate instability in README

### 8. **Link Everything**

```markdown
## [1.2.0] - 2025-01-15
### Added
- Windows support (#123) by @contributor

[#123]: https://github.com/user/repo/pull/123
[@contributor]: https://github.com/contributor
```

### 9. **Deprecation Policy**

When removing features:
1. **v1.0.0**: Feature exists
2. **v1.1.0**: Add deprecation warning (but keep feature)
3. **v1.2.0**: More warnings, document migration
4. **v2.0.0**: Remove feature (major bump)

```python
# v1.1.0
def old_method():
    warnings.warn("old_method() is deprecated, use new_method()", DeprecationWarning)
    return new_method()
```

### 10. **Security Releases**

For security fixes:
```markdown
## [1.2.3] - 2025-01-16
### Security
- **CRITICAL**: Fixed SQL injection vulnerability (CVE-2025-1234)
  - All users should upgrade immediately
  - See SECURITY.md for details
```

Release immediately, even if other changes are pending.

---

## Quick Reference

### Version Bump Decision Tree

```
Did the public API change in a backwards-incompatible way?
├─ YES → MAJOR (1.0.0 → 2.0.0)
└─ NO
   │
   Did you add new functionality (backwards compatible)?
   ├─ YES → MINOR (1.0.0 → 1.1.0)
   └─ NO
      │
      Did you fix bugs or make internal improvements?
      ├─ YES → PATCH (1.0.0 → 1.0.1)
      └─ NO → No version bump needed
```

### Changelog Entry Checklist

Before releasing, ask:
- [ ] All changes documented?
- [ ] Breaking changes clearly marked?
- [ ] Migration guide provided (if needed)?
- [ ] Links to PRs/issues included?
- [ ] Contributors mentioned?
- [ ] Date is correct?
- [ ] Version follows SemVer?

### Release Day Checklist

- [ ] Update CHANGELOG.md (move Unreleased to new version)
- [ ] Update version in pyproject.toml
- [ ] Commit changes: `git commit -am "chore: release v1.2.0"`
- [ ] Create tag: `git tag -a v1.2.0 -m "Release v1.2.0"`
- [ ] Push: `git push origin main && git push origin v1.2.0`
- [ ] Create GitHub release with changelog
- [ ] Verify CI/CD publishes to PyPI
- [ ] Announce release (Twitter, blog, etc.)

---

## Examples from Popular OSS Projects

### fastapi
- Uses SemVer strictly
- Detailed changelog with every PR linked
- Clear breaking change communication
- https://github.com/tiangolo/fastapi/blob/master/docs/en/docs/release-notes.md

### pydantic
- Keep a Changelog format
- Groups changes by category
- Links to PRs and contributors
- https://github.com/pydantic/pydantic/blob/main/HISTORY.md

### requests
- Simple, user-focused changelog
- Clear dates and versions
- Highlights important changes
- https://github.com/psf/requests/blob/main/HISTORY.md

---

## Tools & Resources

### Documentation
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)

### Automation
- [release-please](https://github.com/googleapis/release-please)
- [commitizen](https://commitizen-tools.github.io/commitizen/)
- [standard-version](https://github.com/conventional-changelog/standard-version)
- [towncrier](https://towncrier.readthedocs.io/)

### Validation
- [conventional-changelog](https://github.com/conventional-changelog/conventional-changelog)
- [commitlint](https://commitlint.js.org/)
- [semantic-release](https://semantic-release.gitbook.io/)
