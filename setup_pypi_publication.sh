#!/bin/bash

# PyPI Publication Setup Script
echo "🚀 Setting up PyPI publication for RDFMap..."

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    echo "❌ Error: Please run this from the project root directory"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [[ -d ".venv_py313" ]]; then
    source .venv_py313/bin/activate
else
    echo "❌ Error: Virtual environment .venv_py313 not found"
    exit 1
fi

# Install publishing tools
echo "🔧 Installing publication tools..."
pip install twine readme-renderer

# Validate packages
echo "✅ Validating built packages..."
if [[ -f "dist/rdfmap-0.1.0.tar.gz" && -f "dist/rdfmap-0.1.0-py3-none-any.whl" ]]; then
    echo "  ✅ Found source distribution: dist/rdfmap-0.1.0.tar.gz"
    echo "  ✅ Found wheel: dist/rdfmap-0.1.0-py3-none-any.whl"
else
    echo "  ❌ Package files not found. Building packages..."
    rm -rf dist/
    python -m build
fi

# Check package quality
echo "🔍 Checking package quality..."
twine check dist/*
if [[ $? -eq 0 ]]; then
    echo "  ✅ Package validation passed!"
else
    echo "  ❌ Package validation failed. Please fix issues before uploading."
    exit 1
fi

# Test local installation
echo "🧪 Testing local installation..."
python3.13 -m venv temp_test_env
source temp_test_env/bin/activate
pip install dist/rdfmap-0.1.0-py3-none-any.whl

# Test import
python -c "import rdfmap; print('✅ Package imports successfully')" 2>/dev/null
if [[ $? -eq 0 ]]; then
    echo "  ✅ Package imports correctly"
else
    echo "  ❌ Package import failed"
    deactivate
    rm -rf temp_test_env
    exit 1
fi

# Test CLI
echo "  Testing CLI command..."
if command -v rdfmap &> /dev/null; then
    echo "  ✅ CLI command 'rdfmap' is available"
else
    echo "  ⚠️  CLI command not found (might be a PATH issue)"
fi

# Cleanup test environment
deactivate
rm -rf temp_test_env

# Reactivate main environment
source .venv_py313/bin/activate

echo ""
echo "🎉 Package validation complete!"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Create PyPI accounts:"
echo "   - Test PyPI: https://test.pypi.org/account/register/"
echo "   - Production PyPI: https://pypi.org/account/register/"
echo ""
echo "2. Set up API tokens (recommended):"
echo "   - Test PyPI: https://test.pypi.org/manage/account/token/"
echo "   - Production PyPI: https://pypi.org/manage/account/token/"
echo ""
echo "3. Configure credentials in ~/.pypirc:"
echo "   See PYPI_PUBLICATION_GUIDE.md for details"
echo ""
echo "4. Upload to Test PyPI first:"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "5. Then upload to Production PyPI:"
echo "   twine upload dist/*"
echo ""
echo "📖 For detailed instructions, see: PYPI_PUBLICATION_GUIDE.md"
