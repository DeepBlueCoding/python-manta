# PyPI Publishing Setup Guide

This guide explains how to set up automated PyPI publishing for python-manta using GitHub Actions and API tokens.

## Overview

The project uses GitHub Actions to automatically publish wheels to PyPI when you push a version tag. We support two PyPI environments:

1. **TestPyPI** - For testing releases (pre-release versions like `v0.1.0-beta.1`)
2. **PyPI** - For production releases (stable versions like `v0.1.0`)

## How It Works

### Automatic Publishing Trigger

When you push a git tag:

```bash
# Production release (publishes to PyPI)
git tag v0.2.0
git push origin v0.2.0

# Pre-release/test (publishes to TestPyPI)
git tag v0.2.0-beta.1
git push origin v0.2.0-beta.1
```

GitHub Actions will:
1. ✅ Build wheels for all platforms (Linux, macOS, Windows)
2. ✅ Test each wheel
3. ✅ Publish to appropriate PyPI repository
   - Tags **without** hyphen (e.g., `v0.2.0`) → **PyPI**
   - Tags **with** hyphen (e.g., `v0.2.0-beta.1`) → **TestPyPI**

## Setup Instructions

### Step 1: Create PyPI API Tokens

You need to create API tokens on both PyPI and TestPyPI.

#### Create PyPI Token (Production)

1. **Log in to PyPI**
   - Go to https://pypi.org/
   - Log in with your account

2. **Navigate to API tokens**
   - Go to your account settings
   - Click "API tokens" (https://pypi.org/manage/account/token/)

3. **Create new token**
   - Click "Add API token"
   - **Token name**: `python-manta-github-actions` (or any descriptive name)
   - **Scope**: Select "Project: python-manta" (if project exists)
     - OR "Entire account" (if project doesn't exist yet - can scope it later)

4. **Copy the token**
   - ⚠️ **IMPORTANT**: Copy the token immediately! It won't be shown again.
   - Format: `pypi-AgEIcHlwaS5vcmc...` (starts with `pypi-`)

#### Create TestPyPI Token (For Testing)

1. **Log in to TestPyPI**
   - Go to https://test.pypi.org/
   - Log in or create account (separate from main PyPI!)

2. **Navigate to API tokens**
   - Go to https://test.pypi.org/manage/account/token/

3. **Create new token**
   - Click "Add API token"
   - **Token name**: `python-manta-github-actions-test`
   - **Scope**: "Entire account" (TestPyPI doesn't support scoped tokens yet)

4. **Copy the token**
   - Format: `pypi-AgEIcHlwaS5vcmc...`

### Step 2: Add Secrets to GitHub Repository

Now add these tokens as GitHub repository secrets.

#### Via GitHub Web Interface

1. **Navigate to repository settings**
   - Go to your repository: `https://github.com/equilibrium-coach/python-manta`
   - Click "Settings" tab
   - Click "Secrets and variables" → "Actions" in left sidebar

2. **Add PyPI token**
   - Click "New repository secret"
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Paste your PyPI token (starts with `pypi-`)
   - Click "Add secret"

3. **Add TestPyPI token**
   - Click "New repository secret"
   - **Name**: `TEST_PYPI_API_TOKEN`
   - **Value**: Paste your TestPyPI token
   - Click "Add secret"

#### Via GitHub CLI (Alternative)

```bash
# Add PyPI token
gh secret set PYPI_API_TOKEN --body "pypi-AgEI..."

# Add TestPyPI token
gh secret set TEST_PYPI_API_TOKEN --body "pypi-AgEI..."
```

### Step 3: Verify Secrets Are Set

1. Go to repository Settings → Secrets → Actions
2. You should see:
   - ✅ `PYPI_API_TOKEN`
   - ✅ `TEST_PYPI_API_TOKEN`

**Note**: You can only see the names, not the values (for security).

### Step 4: Test the Setup

#### Test with TestPyPI First

Before publishing to production PyPI, test with TestPyPI:

```bash
# 1. Create a test release tag
git tag v0.1.0-test.1
git push origin v0.1.0-test.1

# 2. Monitor GitHub Actions
# Go to: https://github.com/equilibrium-coach/python-manta/actions

# 3. Watch the workflow run
# - All platform builds should succeed
# - "Publish to TestPyPI" job should run
# - Check for successful upload

# 4. Verify on TestPyPI
# https://test.pypi.org/project/python-manta/

# 5. Test installation
pip install --index-url https://test.pypi.org/simple/ python-manta==0.1.0-test.1
```

#### If TestPyPI Works, Release to PyPI

```bash
# 1. Create production release tag
git tag v0.1.0
git push origin v0.1.0

# 2. Monitor GitHub Actions
# "Publish to PyPI" job should run

# 3. Verify on PyPI
# https://pypi.org/project/python-manta/

# 4. Test installation
pip install python-manta==0.1.0
```

## Workflow Details

### Publishing Logic

The workflow uses conditional logic to determine where to publish:

```yaml
# TestPyPI: Tags with hyphen (v0.1.0-beta.1, v0.2.0-rc.1)
if: startsWith(github.ref, 'refs/tags/v') && contains(github.ref, '-')

# PyPI: Tags without hyphen (v0.1.0, v1.2.3)
if: startsWith(github.ref, 'refs/tags/v') && !contains(github.ref, '-')
```

**Examples:**
- `v0.1.0` → **PyPI** ✅
- `v1.2.3` → **PyPI** ✅
- `v0.1.0-alpha.1` → **TestPyPI** 🧪
- `v0.2.0-beta.1` → **TestPyPI** 🧪
- `v1.0.0-rc.1` → **TestPyPI** 🧪

### Security Features

1. **Environment Protection** (PyPI only)
   - Uses GitHub Environment `pypi` for production
   - Can add required reviewers
   - Can add deployment branches restrictions

2. **Secret Security**
   - Tokens stored as encrypted GitHub secrets
   - Never exposed in logs
   - Scoped to minimum permissions

3. **Skip Existing**
   - TestPyPI: `skip-existing: true` (won't fail if version exists)
   - PyPI: Will fail if version exists (prevents accidental overwrites)

## Troubleshooting

### Error: "Invalid or expired token"

**Cause**: The API token is incorrect or has expired.

**Solution**:
1. Create a new token on PyPI
2. Update the secret in GitHub:
   - Settings → Secrets → Actions → `PYPI_API_TOKEN` → Update

### Error: "Project does not exist"

**Cause**: First time publishing and token is scoped to specific project.

**Solution**:
1. Either:
   - **Option A**: Create token with "Entire account" scope for first release
   - **Option B**: Manually create project on PyPI first
2. After first release, recreate token with project scope for better security

### Error: "File already exists"

**Cause**: Trying to upload a version that already exists.

**Solution**:
- PyPI doesn't allow overwriting versions
- Bump version and create new tag:
  ```bash
  # Update version in pyproject.toml
  git tag v0.1.1
  git push origin v0.1.1
  ```

### Error: "403 Forbidden"

**Cause**: Token doesn't have permission for this project.

**Solution**:
1. Verify you're the owner or maintainer of the PyPI project
2. Recreate token with correct scope
3. Update GitHub secret

### Workflow doesn't trigger

**Cause**: Tag doesn't match the pattern or not pushed correctly.

**Solution**:
```bash
# Verify tag exists locally
git tag

# Verify tag was pushed
git ls-remote --tags origin

# Push tag explicitly
git push origin v0.1.0
```

### TestPyPI works but PyPI fails

**Cause**: Different permissions or project doesn't exist on production PyPI.

**Solution**:
1. Verify project exists on PyPI
2. Check you have maintainer access
3. Verify `PYPI_API_TOKEN` secret is set correctly
4. Try manual upload first:
   ```bash
   pip install twine
   twine upload dist/*
   ```

## Manual Publishing (Fallback)

If GitHub Actions fails, you can publish manually:

```bash
# 1. Download artifacts from GitHub Actions
# Go to workflow run → Artifacts → Download wheels-*

# 2. Extract all wheels to dist/
mkdir -p dist
unzip wheels-linux.zip -d dist/
unzip wheels-macos-x86_64.zip -d dist/
unzip wheels-macos-arm64.zip -d dist/
unzip wheels-windows.zip -d dist/

# 3. Install twine
pip install twine

# 4. Upload to PyPI
twine upload dist/*

# Enter your PyPI credentials when prompted
# Or use token: username=__token__, password=<your-token>
```

## Security Best Practices

### ✅ DO

- Use scoped tokens (project-specific) when possible
- Rotate tokens periodically (every 6-12 months)
- Delete tokens immediately if compromised
- Use separate tokens for TestPyPI and PyPI
- Monitor your PyPI account for unexpected activity

### ❌ DON'T

- Commit tokens to git (always use GitHub secrets)
- Share tokens in issues or pull requests
- Use the same token across multiple projects
- Give tokens broader permissions than needed
- Reuse tokens from other CI systems

## Token Scope Recommendations

### Initial Release (No project on PyPI yet)

```
Scope: Entire account
Reason: Project doesn't exist yet, need broad access for first upload
Action: After first successful release, recreate with project scope
```

### After Initial Release

```
Scope: Project: python-manta
Reason: Principle of least privilege
Action: Update GitHub secret with new scoped token
```

## Advanced: GitHub Environment Protection

You can add an extra layer of security for production releases:

### Setup Protected Environment

1. **Create Environment**
   - Settings → Environments → New environment
   - Name: `pypi`

2. **Add Protection Rules**
   - Required reviewers: Add maintainers
   - Deployment branches: Only `main` or `master`

3. **Update Workflow** (already configured)
   ```yaml
   environment:
     name: pypi
     url: https://pypi.org/p/python-manta
   ```

Now production releases require manual approval from maintainers!

## TestPyPI vs PyPI

| Feature | TestPyPI | PyPI |
|---------|----------|------|
| Purpose | Testing releases | Production releases |
| URL | test.pypi.org | pypi.org |
| Separate account | Yes | Yes |
| Auto cleanup | Files deleted after ~6 months | Permanent |
| CDN | No (slow downloads) | Yes (fast downloads) |
| Dependencies | Must use `--extra-index-url` | Normal install |

### Installing from TestPyPI

```bash
# TestPyPI only (dependencies might fail)
pip install --index-url https://test.pypi.org/simple/ python-manta

# TestPyPI + PyPI for dependencies
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            python-manta
```

## Migration from Trusted Publishing

If you previously used Trusted Publishing (OIDC), the new token-based system is:

**Advantages:**
- ✅ Works immediately (no PyPI configuration needed)
- ✅ Easier to set up
- ✅ Can be rotated without PyPI web UI changes

**Disadvantages:**
- ⚠️ Less secure (token can be stolen if repo is compromised)
- ⚠️ Requires secret management

**To switch back to Trusted Publishing:**
1. Remove `password:` from workflow
2. Add `permissions: id-token: write`
3. Configure on PyPI: Manage → Publishing → Add GitHub publisher

## Next Steps

1. ✅ Create PyPI and TestPyPI tokens
2. ✅ Add secrets to GitHub repository
3. ✅ Test with TestPyPI release (`v0.1.0-test.1`)
4. ✅ Release to production PyPI (`v0.1.0`)
5. ✅ Set up environment protection (optional)
6. ✅ Document token rotation schedule

## Resources

- [PyPI API Tokens](https://pypi.org/help/#apitoken)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [PyPA Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [TestPyPI](https://test.pypi.org/)
- [Twine Documentation](https://twine.readthedocs.io/)

## Questions?

- 🐛 Issues: Open a GitHub issue
- 💬 Discussions: GitHub Discussions
- 📧 Email: contact@equilibrium-coach.com
