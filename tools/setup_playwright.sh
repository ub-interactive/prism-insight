#!/bin/bash
# Playwright Browser Installation Script
# For local development environments (Mac, Linux, Windows WSL)

echo "🎭 Playwright Browser Installation"
echo "===================================="

# Check Python environment
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed."
    exit 1
fi

echo "✅ Python3 detected"

# Check Playwright package installation
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "⚠️  Playwright package is not installed."
    echo "📦 Installing Playwright..."
    pip install playwright
fi

echo "✅ Playwright package verified"

# Install Chromium browser
echo "🌐 Installing Chromium browser..."
python3 -m playwright install chromium

if [ $? -eq 0 ]; then
    echo "✅ Playwright browser installation complete!"
    echo ""
    echo "You can now use PDF conversion:"
    echo "  python3 -m prism.ops.pipelines.stock_analysis_orchestrator --mode afternoon"
else
    echo "❌ Browser installation failed"
    exit 1
fi
