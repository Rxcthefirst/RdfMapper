#!/bin/bash

# PyPI Upload Authentication Fix Script
echo "🔐 Fixing PyPI Authentication for rdfmap-semantic"
echo "=================================================="

# Go to project directory
cd /Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper
source .venv_py313/bin/activate

echo "📦 Current package files:"
ls -la dist/

echo ""
echo "🔍 Checking twine installation..."
if ! command -v twine &> /dev/null; then
    echo "Installing twine..."
    pip install twine
else
    echo "✅ Twine is installed: $(twine --version)"
fi

echo ""
echo "🛠️  AUTHENTICATION SETUP REQUIRED"
echo "=================================="
echo ""
echo "The 403 error means authentication failed. You need to:"
echo ""
echo "1. 🌐 CREATE TEST PYPI ACCOUNT (if not done):"
echo "   Visit: https://test.pypi.org/account/register/"
echo "   - Register with your email"
echo "   - Verify your email"
echo ""
echo "2. 🔑 CREATE API TOKEN:"
echo "   Visit: https://test.pypi.org/manage/account/token/"
echo "   - Click 'Add API token'"
echo "   - Name: rdfmap-semantic-token"
echo "   - Scope: Entire account"
echo "   - COPY THE TOKEN (starts with 'pypi-...')"
echo ""
echo "3. 🚀 UPLOAD WITH EXPLICIT CREDENTIALS:"
echo "   When you have your token, run:"
echo ""
echo "   twine upload --repository testpypi --username __token__ --password YOUR_TOKEN_HERE dist/*"
echo ""
echo "   Replace YOUR_TOKEN_HERE with your actual token"
echo ""
echo "📋 ALTERNATIVE: Interactive Upload"
echo "================================="
echo "You can also run this command and enter credentials when prompted:"
echo ""
echo "twine upload --repository testpypi dist/*"
echo ""
echo "When prompted:"
echo "- Username: __token__"
echo "- Password: [paste your token here]"
echo ""
echo "🎯 EXPECTED SUCCESS MESSAGE:"
echo "Uploading distributions to https://test.pypi.org/legacy/"
echo "Uploading rdfmap_semantic-0.1.0-py3-none-any.whl"
echo "100% ████████████████████ XX.X/XX.X kB • 00:01 • ?"
echo "Uploading rdfmap_semantic-0.1.0.tar.gz"
echo "100% ████████████████████ XX.X/XX.X kB • 00:01 • ?"
echo ""
echo "View at: https://test.pypi.org/project/rdfmap-semantic/"

echo ""
echo "❓ Need help creating accounts or tokens?"
echo "See: PYPI_PUBLICATION_GUIDE.md for detailed instructions"
