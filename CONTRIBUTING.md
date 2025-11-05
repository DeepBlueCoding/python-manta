# Contributing to Python Manta

Thank you for your interest in contributing to Python Manta! This guide will help you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Changelog Guidelines](#changelog-guidelines)
- [Testing](#testing)
- [Code Style](#code-style)

## Code of Conduct

Be respectful, constructive, and collaborative. We're all here to build something great together.

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR-USERNAME/python-manta.git
cd python-manta
git remote add upstream https://github.com/equilibrium-coach/python-manta.git
```

### 2. Set Up Development Environment

```bash
# Install Go (1.19+)
go version

# Install Python (3.8+)
python3 --version

# Clone Manta dependency
cd ..
git clone https://github.com/dotabuff/manta.git
cd python-manta

# Build the library
./build.sh

# Install development dependencies
pip install -e ".[dev]"
```

### 3. Verify Setup

```bash
# Run tests
python run_tests.py --unit

# Try an example (update path first)
python simple_example.py
```

## Development Workflow

### Branch Naming

Use descriptive branch names with conventional prefixes:

```bash
feat/add-new-callback        # New feature
fix/memory-leak-parser       # Bug fix
docs/update-readme          # Documentation
refactor/cleanup-cgo        # Code refactoring
test/add-parser-tests       # Test additions
chore/update-deps           # Maintenance
```

### Making Changes

```bash
# 1. Create a feature branch
git checkout -b feat/your-feature-name

# 2. Make your changes
# ... edit files ...

# 3. Run tests
python run_tests.py --all

# 4. Commit with conventional commit message (see below)
git commit -m "feat(parser): add support for new callback type"

# 5. Keep your branch updated
git fetch upstream
git rebase upstream/main

# 6. Push to your fork
git push origin feat/your-feature-name
```

## Commit Message Guidelines

We use **Conventional Commits** for clear, searchable history.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code formatting (no logic change)
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

### Examples

```bash
# Simple feature
git commit -m "feat(parser): add macOS ARM64 support"

# Bug fix with scope
git commit -m "fix(cgo): resolve memory leak in message handling"

# Breaking change
git commit -m "feat!: change MantaParser constructor signature

BREAKING CHANGE: MantaParser now requires library_path parameter.
Migration: Use MantaParser('path/to/lib') instead of MantaParser()"

# With issue reference
git commit -m "fix(parser): handle empty demo files

Fixes #123"

# Multiple changes
git commit -m "feat(build): add Windows wheel building

- Create before_build_windows.sh
- Update GitHub Actions workflow
- Add Windows-specific documentation"
```

### Commit Message Tips

✅ **DO:**
- Use present tense ("add feature" not "added feature")
- Use imperative mood ("move cursor to..." not "moves cursor to...")
- Limit first line to 72 characters
- Reference issues/PRs when relevant
- Explain *what* and *why*, not *how*

❌ **DON'T:**
- Use vague messages like "fix bug" or "update code"
- Include file names (that's what git diff is for)
- Make multi-purpose commits (split into logical commits)

## Pull Request Process

### Before Creating PR

- [ ] Code follows project style
- [ ] Tests pass (`python run_tests.py --all`)
- [ ] CHANGELOG.md updated (see below)
- [ ] Documentation updated (if needed)
- [ ] Commits are clean and follow conventions
- [ ] Branch is rebased on latest main

### Creating the PR

1. **Push your branch**
   ```bash
   git push origin feat/your-feature
   ```

2. **Open PR on GitHub**
   - Title: Brief, descriptive summary
   - Description: What, why, how, and any special notes

3. **Use PR Template** (if provided)

### PR Title Format

Use conventional commit format for PR titles:

```
feat(parser): add support for new callback types
fix(build): resolve Windows compilation issue
docs(readme): update installation instructions
```

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Motivation
Why is this change needed?

## Changes
- Change 1
- Change 2
- Change 3

## Testing
How was this tested?

## Screenshots (if applicable)

## Checklist
- [ ] Tests pass
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Follows code style
```

### Review Process

1. **Automated checks** must pass
   - All platform builds
   - Tests
   - Changelog check (unless `skip-changelog` label)

2. **Code review** by maintainer
   - Address feedback
   - Push updates to same branch

3. **Approval and merge**
   - Squash merge with conventional commit message
   - Delete branch after merge

## Changelog Guidelines

### Update CHANGELOG.md

For **every PR** that changes functionality, update `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- Support for 50 new DOTA callbacks (#123)

### Changed
- Improved error messages in parser (#124)

### Fixed
- Memory leak in message handling (#125)
```

### Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

### Skip Changelog

Some PRs don't need changelog entries:
- Documentation-only changes
- CI/CD changes
- Test additions
- Code refactoring (if no behavior change)

Add the `skip-changelog` label to these PRs.

## Testing

### Run Tests Locally

```bash
# Unit tests only (fast)
python run_tests.py --unit

# Integration tests (requires demo files)
python run_tests.py --integration

# All tests
python run_tests.py --all

# With coverage
python run_tests.py --all --coverage

# Specific test file
python run_tests.py tests/test_parser.py
```

### Writing Tests

```python
# tests/test_your_feature.py
import pytest
from python_manta import MantaParser

@pytest.mark.unit
def test_your_feature():
    """Test description."""
    # Arrange
    parser = MantaParser("path/to/lib")

    # Act
    result = parser.some_method()

    # Assert
    assert result.success
    assert result.count == 10
```

### Test Coverage

We aim for **90%+ test coverage**. Check with:

```bash
python run_tests.py --coverage
```

## Code Style

### Python

- **PEP 8** compliant
- **Type hints** for all public functions
- **Docstrings** for classes and public methods

```python
def parse_universal(
    self,
    demo_file: str,
    callback_filter: str,
    max_messages: int
) -> ParseResult:
    """
    Parse demo file using universal callback filtering.

    Args:
        demo_file: Path to .dem file
        callback_filter: Message type to filter
        max_messages: Maximum messages to extract

    Returns:
        ParseResult with messages and metadata

    Raises:
        FileNotFoundError: If demo file doesn't exist
    """
    pass
```

### Go

- Follow Go conventions
- Use `gofmt` for formatting
- Add comments for exported functions

```go
// ParseUniversal parses a demo file with message filtering.
// It returns a JSON string containing the parsed messages.
//
//export ParseUniversal
func ParseUniversal(filePath *C.char, messageFilter *C.char, maxMessages C.int) *C.char {
    // Implementation
}
```

### Auto-formatting

```bash
# Python
black src/ tests/
isort src/ tests/

# Go
cd go_wrapper
gofmt -w .
```

## What to Contribute

### Good First Issues

Look for issues labeled `good-first-issue`:
- Documentation improvements
- Test additions
- Small bug fixes
- Example scripts

### Areas We Need Help

- 🧪 More test coverage
- 📚 Documentation improvements
- 🐛 Bug fixes
- 🎯 Performance optimizations
- 💡 New callback implementations
- 🌍 Platform support improvements

### Feature Proposals

For new features:
1. Open an issue first to discuss
2. Wait for feedback from maintainers
3. Then implement

This prevents wasted effort on features that might not be accepted.

## Documentation

### Update Documentation

When changing functionality:
- [ ] Update docstrings
- [ ] Update README.md examples
- [ ] Update BUILDING.md (if build process changes)
- [ ] Add/update examples in `examples/`
- [ ] Update CHANGELOG.md

### Documentation Style

- Clear and concise
- Include code examples
- Explain the "why", not just the "what"
- Keep examples up to date

## Getting Help

- 💬 **Discussions**: For questions and ideas
- 🐛 **Issues**: For bug reports and feature requests
- 📧 **Email**: contact@equilibrium-coach.com

## Recognition

Contributors will be:
- Listed in CHANGELOG.md for their contributions
- Mentioned in GitHub releases
- Added to a future CONTRIBUTORS.md file

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers this project.

---

Thank you for contributing to Python Manta! 🎉
