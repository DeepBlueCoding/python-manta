# TestPyPI Pre-Release Versions (PEP 440)

When creating test releases for TestPyPI, use valid PEP 440 version formats.

## Valid Pre-Release Version Formats

According to PEP 440, valid pre-release versions are:

### Development Releases (Recommended for Testing)
```bash
# Development versions
0.1.0.dev1    # First dev version
0.1.0.dev2    # Second dev version
0.1.0.dev3    # Third dev version

# Tag format
v0.1.0-dev1   # The hyphen triggers TestPyPI
```

### Release Candidates
```bash
# Release candidates (when close to final)
0.1.0rc1      # Release candidate 1
0.1.0rc2      # Release candidate 2

# Tag format
v0.1.0-rc1    # The hyphen triggers TestPyPI
```

### Alpha/Beta Releases
```bash
# Alpha releases (early testing)
0.1.0a1       # Alpha 1
0.1.0a2       # Alpha 2

# Beta releases (feature complete, testing)
0.1.0b1       # Beta 1
0.1.0b2       # Beta 2

# Tag formats
v0.1.0-a1     # Alpha → TestPyPI
v0.1.0-b1     # Beta → TestPyPI
```

## ❌ Invalid Formats

These will cause installation errors:

```bash
0.1.0-test.1  # ❌ "test" is not a valid identifier
0.1.0.test1   # ❌ "test" is not a valid identifier
0.1.0-foo.1   # ❌ "foo" is not a valid identifier
```

## Recommended Testing Workflow

### For Quick Testing
Use `.dev` versions:

```bash
# First test
./tools/prepare_release.sh 0.1.0.dev1
git push origin v0.1.0-dev1

# Install
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

# Need to fix something? Increment
./tools/prepare_release.sh 0.1.0.dev2
git push origin v0.1.0-dev2
```

### For Pre-Release Testing
Use `rc` (release candidate) versions:

```bash
# When you think it's ready
./tools/prepare_release.sh 0.1.0rc1
git push origin v0.1.0-rc1

# Install
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0rc1

# If good, release to production
./tools/prepare_release.sh 0.1.0
git push origin v0.1.0
```

## How Tags Map to TestPyPI

| Git Tag | PyPI Version | Destination |
|---------|--------------|-------------|
| `v0.1.0-dev1` | `0.1.0.dev1` | TestPyPI |
| `v0.1.0-rc1` | `0.1.0rc1` | TestPyPI |
| `v0.1.0-a1` | `0.1.0a1` | TestPyPI |
| `v0.1.0-b1` | `0.1.0b1` | TestPyPI |
| `v0.1.0` | `0.1.0` | PyPI (production) |

**Key:** Any tag with a hyphen goes to TestPyPI!

## Complete Example

```bash
# Development testing
./tools/prepare_release.sh 0.1.0.dev1
git push origin main
git push origin v0.1.0-dev1

# Wait for build (~30 min)

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.1.0.dev1

# Test it
python -c "import python_manta; print('Works!')"

# If issues found, fix and release dev2
./tools/prepare_release.sh 0.1.0.dev2
git push origin v0.1.0-dev2

# When perfect, release to production
./tools/prepare_release.sh 0.1.0
git push origin v0.1.0
```

## Why Not Just Use "test"?

PEP 440 (Python's versioning standard) only recognizes these pre-release identifiers:
- `a` or `alpha` - Alpha releases
- `b` or `beta` - Beta releases
- `rc` or `c` - Release candidates
- `dev` - Development releases
- `post` - Post releases

The identifier `test` is not in the spec, so pip rejects it.

## Quick Reference

**For testing:** Use `.dev` suffix
```bash
0.1.0.dev1 → v0.1.0-dev1 → TestPyPI
```

**For release candidates:** Use `rc` suffix
```bash
0.1.0rc1 → v0.1.0-rc1 → TestPyPI
```

**For production:** No suffix
```bash
0.1.0 → v0.1.0 → PyPI
```

## See Also

- [PEP 440 Version Identification](https://peps.python.org/pep-0440/)
- [RELEASE_QUICK_START.md](RELEASE_QUICK_START.md) - Updated with correct versions
- [PROPER_RELEASE_WORKFLOW.md](PROPER_RELEASE_WORKFLOW.md) - Full workflow guide
