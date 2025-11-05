# PyPI Token Setup - Quick Start

Quick reference for setting up PyPI API tokens for automated publishing.

## What You Need

Two API tokens:
1. **PYPI_API_TOKEN** - For production releases (pypi.org)
2. **TEST_PYPI_API_TOKEN** - For test releases (test.pypi.org)

## 5-Minute Setup

### 1. Create PyPI Token

```
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: "python-manta-github-actions"
4. Scope: "Entire account" (or "Project: python-manta" if project exists)
5. Copy token (starts with pypi-...)
```

### 2. Create TestPyPI Token

```
1. Go to https://test.pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: "python-manta-github-actions-test"
4. Scope: "Entire account"
5. Copy token (starts with pypi-...)
```

### 3. Add Tokens to GitHub

```
1. Go to https://github.com/YOUR-USERNAME/python-manta/settings/secrets/actions
2. Click "New repository secret"

Secret 1:
  Name: PYPI_API_TOKEN
  Value: [paste PyPI token]

Secret 2:
  Name: TEST_PYPI_API_TOKEN
  Value: [paste TestPyPI token]
```

### 4. Verify Setup

```bash
# Test with TestPyPI
git tag v0.1.0-test.1
git push origin v0.1.0-test.1

# Check GitHub Actions:
# https://github.com/YOUR-USERNAME/python-manta/actions

# If successful, release to PyPI:
git tag v0.1.0
git push origin v0.1.0
```

## How Publishing Works

### Automatic Triggers

```bash
# Tag WITHOUT hyphen → PyPI (production)
git tag v0.2.0
git push origin v0.2.0

# Tag WITH hyphen → TestPyPI (testing)
git tag v0.2.0-beta.1
git push origin v0.2.0-beta.1
```

### What Happens

1. GitHub Actions detects the tag
2. Builds wheels for all platforms (Linux, macOS, Windows)
3. Publishes to PyPI or TestPyPI based on tag format
4. Users can install: `pip install python-manta`

## Token Security

✅ **DO:**
- Store tokens in GitHub Secrets only
- Use project-scoped tokens after first release
- Rotate tokens every 6-12 months

❌ **DON'T:**
- Commit tokens to git
- Share tokens publicly
- Reuse tokens across projects

## Troubleshooting

### "Invalid token" error
→ Recreate token on PyPI and update GitHub secret

### "Project doesn't exist" error
→ Use "Entire account" scope for first release

### Workflow doesn't run
→ Verify tag starts with 'v' (e.g., v0.1.0, not 0.1.0)

### TestPyPI works but PyPI fails
→ Check PYPI_API_TOKEN secret is set correctly

## Testing Before Production

Always test with TestPyPI first:

```bash
# 1. Test release
git tag v0.2.0-test.1
git push origin v0.2.0-test.1

# 2. Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta==0.2.0-test.1

# 3. If good, release to production
git tag v0.2.0
git push origin v0.2.0
```

## Complete Documentation

For detailed instructions, see:
- **Full Setup Guide**: [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md)
- **Release Process**: [RELEASE_PROCESS.md](RELEASE_PROCESS.md)
- **Troubleshooting**: See PYPI_SETUP_GUIDE.md "Troubleshooting" section

## Quick Commands

```bash
# View current secrets (names only)
gh secret list

# Set secret via CLI
gh secret set PYPI_API_TOKEN

# Delete secret
gh secret delete PYPI_API_TOKEN

# View workflow runs
gh run list --workflow=build-wheels.yml

# Watch latest run
gh run watch
```

## Checklist

Before first release:
- [ ] PyPI account created
- [ ] TestPyPI account created (separate)
- [ ] PYPI_API_TOKEN secret added to GitHub
- [ ] TEST_PYPI_API_TOKEN secret added to GitHub
- [ ] Tested with TestPyPI (v0.1.0-test.1)
- [ ] Ready for production release (v0.1.0)

## Support

Questions? See [PYPI_SETUP_GUIDE.md](PYPI_SETUP_GUIDE.md) for detailed help.
