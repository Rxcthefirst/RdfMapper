#!/bin/bash

# PyCharm Python 3.13 Configuration Script
# Run this script to help configure PyCharm to use Python 3.13

PROJECT_DIR="/Users/rxcthefirst/Dev/PythonProjects/SemanticModelDataMapper"
PYTHON_PATH="$PROJECT_DIR/.venv_py313/bin/python3.13"

echo "🐍 PyCharm Python 3.13 Configuration Helper"
echo "============================================="

# Verify Python 3.13 installation
echo "1. Verifying Python 3.13 installation..."
if [ -f "$PYTHON_PATH" ]; then
    VERSION=$("$PYTHON_PATH" --version)
    echo "   ✅ Found: $VERSION at $PYTHON_PATH"
else
    echo "   ❌ Python 3.13 not found at expected path"
    exit 1
fi

# Check if .idea directory exists
echo "2. Checking PyCharm configuration directory..."
if [ -d "$PROJECT_DIR/.idea" ]; then
    echo "   ✅ .idea directory exists"
else
    echo "   📁 Creating .idea directory..."
    mkdir -p "$PROJECT_DIR/.idea"
fi

# Verify package installation
echo "3. Verifying package installation in Python 3.13..."
if "$PYTHON_PATH" -c "import rdfmap; print('✅ rdfmap package available')" 2>/dev/null; then
    echo "   ✅ rdfmap package is installed"
else
    echo "   ⚠️  rdfmap package not found - installing..."
    cd "$PROJECT_DIR" && "$PYTHON_PATH" -m pip install -e .
fi

echo ""
echo "🔧 MANUAL PYCHARM CONFIGURATION STEPS:"
echo "======================================"
echo ""
echo "1. Open PyCharm with your project"
echo ""
echo "2. Go to PyCharm → Preferences (Cmd + ,)"
echo ""
echo "3. Navigate to: Project: SemanticModelDataMapper → Python Interpreter"
echo ""
echo "4. Click the ⚙️ gear icon → Add..."
echo ""
echo "5. Select 'Existing environment'"
echo ""
echo "6. Set interpreter path to:"
echo "   $PYTHON_PATH"
echo ""
echo "7. Click OK and Apply"
echo ""
echo "🎯 ALTERNATIVE METHOD:"
echo "====================="
echo ""
echo "If the above doesn't work, try:"
echo ""
echo "1. Close PyCharm completely"
echo "2. Delete the .idea directory: rm -rf $PROJECT_DIR/.idea"
echo "3. Restart PyCharm and open the project"
echo "4. When prompted, select the Python interpreter at:"
echo "   $PYTHON_PATH"
echo ""
echo "🔍 VERIFICATION:"
echo "==============="
echo ""
echo "After configuration, verify in PyCharm:"
echo "• Check Python interpreter shows Python 3.13.x"
echo "• Run: import sys; print(sys.version)"
echo "• Should show Python 3.13.x"
echo ""
echo "✅ Configuration files created. Please follow manual steps above."
