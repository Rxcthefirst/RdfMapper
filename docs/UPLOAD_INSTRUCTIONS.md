# 🔐 PyPI Upload Instructions - Authentication Required

**Status:** Package built and ready, authentication needed

---

## The Issue

The upload command encountered a **403 Forbidden** error, which means:
- Your PyPI credentials need to be updated, OR
- You need to use an API token for authentication

---

## ✅ What's Already Done

- [x] Package built successfully
- [x] All tests passing (176/176)
- [x] Distribution files validated
- [x] Files ready in `dist/` directory:
  - `semantic_rdf_mapper-0.2.0-py3-none-any.whl`
  - `semantic_rdf_mapper-0.2.0.tar.gz`

---

## 🔑 Option 1: Use PyPI API Token (Recommended)

### Step 1: Get Your API Token
1. Log in to PyPI: https://pypi.org/account/login/
2. Go to Account Settings: https://pypi.org/manage/account/
3. Scroll to "API tokens" section
4. Click "Add API token"
5. Set:
   - **Token name:** `semantic-rdf-mapper-upload`
   - **Scope:** "Project: semantic-rdf-mapper" (or "Entire account")
6. Click "Add token"
7. **COPY THE TOKEN NOW** (you won't see it again!)

### Step 2: Upload Using Token
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper

# Upload with token authentication
twine upload dist/semantic_rdf_mapper-0.2.0* -u __token__ -p YOUR_TOKEN_HERE
```

Replace `YOUR_TOKEN_HERE` with the token you copied (starts with `pypi-`).

---

## 🔑 Option 2: Interactive Upload (Username/Password)

If you prefer to enter credentials interactively:

```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper

# This will prompt for username and password
twine upload dist/semantic_rdf_mapper-0.2.0*
```

When prompted:
- **Username:** Your PyPI username
- **Password:** Your PyPI password

---

## 🔑 Option 3: Update .pypirc File

You have a `~/.pypirc` file but it needs updating. Edit it:

```bash
nano ~/.pypirc
```

Add or update to include:

```ini
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
```

Or for username/password:

```ini
[pypi]
username = your_pypi_username
password = your_pypi_password
```

Then run:
```bash
twine upload dist/semantic_rdf_mapper-0.2.0*
```

---

## ✅ After Successful Upload

### 1. Verify on PyPI (within 2-5 minutes)
Visit: https://pypi.org/project/semantic-rdf-mapper/

You should see version 0.2.0 listed!

### 2. Test Installation
```bash
# Create a fresh environment
python -m venv test_install
source test_install/bin/activate

# Install from PyPI
pip install semantic-rdf-mapper==0.2.0

# Quick test
python -c "
import rdfmap
from rdfmap import create_default_pipeline
print(f'✅ Successfully installed version {rdfmap.__version__}')
print('✅ Package is live on PyPI!')
"

# Cleanup
deactivate
rm -rf test_install
```

### 3. Create Git Tag
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
git tag -a v0.2.0 -m "Release version 0.2.0 - Polars integration, semantic matching, and major improvements"
git push origin v0.2.0
```

### 4. Create GitHub Release
1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Tag: `v0.2.0`
4. Title: `Version 0.2.0 - Major Feature Release`
5. Copy the changelog from `CHANGELOG.md`
6. Publish release

---

## 🚨 Troubleshooting

### Error: "File already exists"
This means 0.2.0 was already uploaded. You cannot replace it. Options:
1. If it's broken, "yank" it on PyPI and upload 0.2.1
2. If it's working, you're done! Just verify it works.

### Error: "Invalid token"
- Make sure you copied the entire token including the `pypi-` prefix
- Token might have expired - generate a new one
- Make sure scope includes your project

### Error: "Package name already exists"
- You already have the package name registered
- This is fine! Just proceed with the upload

---

## 📦 Current Package Status

**Location:** `/Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper/dist/`

**Files ready to upload:**
- ✅ `semantic_rdf_mapper-0.2.0-py3-none-any.whl` (113 KB)
- ✅ `semantic_rdf_mapper-0.2.0.tar.gz` (350 KB)

**Command to retry:**
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
twine upload dist/semantic_rdf_mapper-0.2.0*
```

---

## 📞 Need Help?

- **PyPI Help:** https://pypi.org/help/
- **Authentication Guide:** https://pypi.org/help/#invalid-auth
- **API Token Guide:** https://pypi.org/help/#apitoken
- **Twine Docs:** https://twine.readthedocs.io/

---

## ✨ Quick Copy-Paste Commands

### With API Token:
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
twine upload dist/semantic_rdf_mapper-0.2.0* -u __token__ -p pypi-YOUR_TOKEN_HERE
```

### Interactive (will prompt):
```bash
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
twine upload dist/semantic_rdf_mapper-0.2.0*
```

---

**Everything is ready! Just need the authentication sorted out and you'll be live on PyPI! 🚀**

