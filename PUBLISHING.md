# Publishing to PyPI Guide

## Overview

This guide walks through publishing the `rdfmap` package to the Python Package Index (PyPI), making it installable via `pip install rdfmap`.

---

## Prerequisites

### 1. Create PyPI Accounts

You'll need accounts on both:

- **TestPyPI** (for testing): https://test.pypi.org/account/register/
- **PyPI** (production): https://pypi.org/account/register/

### 2. Install Build Tools

```bash
pip install --upgrade build twine
```

**Tools:**
- `build`: Creates distribution packages (wheel and source)
- `twine`: Uploads packages to PyPI securely

---

## Pre-Publishing Checklist

### ✅ 1. Update Version Number

Edit `pyproject.toml`:
```toml
[project]
version = "0.1.0"  # Change this for each release
```

**Version scheme:**
- `0.1.0` - Initial release
- `0.1.1` - Bug fixes
- `0.2.0` - New features
- `1.0.0` - Stable release

### ✅ 2. Update Author Email and URLs

Edit `pyproject.toml`:
```toml
authors = [
    {name = "Your Name", email = "your-email@example.com"}
]

[project.urls]
Homepage = "https://github.com/your-username/SemanticModelDataMapper"
Repository = "https://github.com/your-username/SemanticModelDataMapper"
Issues = "https://github.com/your-username/SemanticModelDataMapper/issues"
```

### ✅ 3. Create a LICENSE File

If you don't have one, create `LICENSE` with MIT license:

```
MIT License

Copyright (c) 2025 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### ✅ 4. Review README.md

Make sure your `README.md` is up-to-date and includes:
- Clear description
- Installation instructions
- Quick start examples
- Link to documentation

### ✅ 5. Run Tests

```bash
pytest
```

Ensure all tests pass before publishing.

### ✅ 6. Clean Previous Builds

```bash
rm -rf dist/ build/ *.egg-info
```

---

## Publishing Process

### Step 1: Build the Package

From your project root:

```bash
python -m build
```

This creates two files in `dist/`:
- `rdfmap-0.1.0-py3-none-any.whl` (wheel - binary distribution)
- `rdfmap-0.1.0.tar.gz` (source distribution)

**Verify the build:**
```bash
ls -lh dist/
```

### Step 2: Test on TestPyPI (RECOMMENDED)

Always test on TestPyPI first!

#### A. Upload to TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: Your TestPyPI username (or `__token__`)
- Password: Your TestPyPI password (or API token)

#### B. Test Installation from TestPyPI

Create a fresh virtual environment:

```bash
# Create test environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ rdfmap

# Test the command
rdfmap --help

# Test functionality
rdfmap generate --help
```

**Note:** The `--extra-index-url` allows pip to install dependencies from the real PyPI, since TestPyPI might not have all dependencies.

#### C. Verify Everything Works

Test all commands:
```bash
rdfmap convert --help
rdfmap generate --help
rdfmap validate --help
rdfmap info --help
```

If everything works, proceed to production PyPI!

### Step 3: Upload to Production PyPI

⚠️ **WARNING**: Once uploaded to PyPI, you **cannot** re-upload the same version. Make sure everything is correct!

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- Username: Your PyPI username (or `__token__`)
- Password: Your PyPI password (or API token)

### Step 4: Verify on PyPI

1. Visit https://pypi.org/project/rdfmap/
2. Check that all information displays correctly
3. Verify the README renders properly

### Step 5: Test Installation

In a fresh environment:

```bash
pip install rdfmap
rdfmap --help
```

---

## Using API Tokens (Recommended)

API tokens are more secure than passwords.

### Create API Token

1. **For TestPyPI**: https://test.pypi.org/manage/account/token/
2. **For PyPI**: https://pypi.org/manage/account/token/

### Configure `.pypirc`

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...  # Your PyPI token

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...  # Your TestPyPI token
```

**Permissions:**
```bash
chmod 600 ~/.pypirc
```

Now you won't be prompted for credentials:

```bash
# Upload to TestPyPI
twine upload -r testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

---

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    
    - name: Build package
      run: python -m build
    
    - name: Check package
      run: twine check dist/*
    
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

**Setup:**
1. Create API token on PyPI
2. Add token to GitHub Secrets as `PYPI_API_TOKEN`
3. Create a GitHub release
4. Package automatically publishes!

---

## Updating Your Package

### For Bug Fixes (0.1.0 → 0.1.1)

```bash
# 1. Update version in pyproject.toml
# version = "0.1.1"

# 2. Commit changes
git add pyproject.toml
git commit -m "Bump version to 0.1.1"
git tag v0.1.1
git push origin main --tags

# 3. Clean and build
rm -rf dist/
python -m build

# 4. Upload
twine upload dist/*
```

### For New Features (0.1.0 → 0.2.0)

Same process, but update to `0.2.0`.

---

## Troubleshooting

### Error: "File already exists"

You uploaded this version before. You must:
1. Increment the version number in `pyproject.toml`
2. Rebuild: `python -m build`
3. Upload again

### Error: "Invalid package"

```bash
# Check for issues
twine check dist/*
```

Common issues:
- Missing `README.md`
- Invalid metadata in `pyproject.toml`
- Missing `LICENSE` file

### Error: "HTTPError: 403 Forbidden"

- Wrong username/password
- API token doesn't have upload permissions
- Trying to upload to a name you don't own

### Large Package Size

Check what's included:

```bash
tar -tzf dist/rdfmap-0.1.0.tar.gz | less
```

Exclude unnecessary files in `pyproject.toml`:

```toml
[tool.setuptools]
packages = ["rdfmap"]

[tool.setuptools.package-data]
rdfmap = ["py.typed"]

[tool.setuptools.exclude-package-data]
"*" = ["tests", "docs", "*.pyc"]
```

---

## Best Practices

### 1. Version Management

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes

### 2. Changelog

Maintain `CHANGELOG.md`:

```markdown
# Changelog

## [0.1.0] - 2025-10-29
### Added
- Initial release
- Mapping generator feature
- CLI with convert, generate, validate commands
- JSON Schema export
- Comprehensive validation guardrails
```

### 3. Git Tags

Tag each release:
```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 4. Pre-release Versions

For testing:
```toml
version = "0.1.0a1"  # Alpha
version = "0.1.0b1"  # Beta
version = "0.1.0rc1" # Release candidate
```

Install with:
```bash
pip install --pre rdfmap
```

### 5. Check Before Uploading

```bash
# Lint the package
twine check dist/*

# Test installation locally
pip install dist/rdfmap-0.1.0-py3-none-any.whl
```

---

## After Publishing

### 1. Announce It

- Create GitHub release with changelog
- Tweet/post on social media
- Share on Reddit (r/Python, r/semanticweb)
- Post on relevant forums

### 2. Monitor

- Watch for issues on GitHub
- Check PyPI statistics: https://pypistats.org/packages/rdfmap
- Respond to questions

### 3. Badge for README

Add to `README.md`:

```markdown
[![PyPI version](https://badge.fury.io/py/rdfmap.svg)](https://badge.fury.io/py/rdfmap)
[![Downloads](https://pepy.tech/badge/rdfmap)](https://pepy.tech/project/rdfmap)
```

---

## Quick Reference

```bash
# Complete publishing workflow
rm -rf dist/ build/ *.egg-info    # Clean
python -m build                     # Build
twine check dist/*                  # Verify
twine upload -r testpypi dist/*    # Test
twine upload dist/*                 # Publish

# Test installation
pip install rdfmap
rdfmap --help
```

---

## Resources

- **PyPI**: https://pypi.org/
- **TestPyPI**: https://test.pypi.org/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **PEP 517/518**: Modern Python packaging standards

---

## Security Notes

- ⚠️ Never commit `.pypirc` to git
- ✅ Use API tokens instead of passwords
- ✅ Add `.pypirc` to `.gitignore`
- ✅ Use GitHub Secrets for CI/CD tokens
- ⚠️ Revoke tokens if compromised

---

## Maintenance Checklist

- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated
- [ ] All tests passing
- [ ] README.md reviewed
- [ ] Previous dist/ cleaned
- [ ] Package built with `python -m build`
- [ ] Package checked with `twine check`
- [ ] Tested on TestPyPI
- [ ] Git tagged with version
- [ ] Uploaded to PyPI
- [ ] Installation tested
- [ ] GitHub release created
