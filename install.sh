#!/bin/bash

# NotebookLM Generation Tool - Installation Script
# ================================================

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
MAN_DIR="/usr/local/share/man/man1"

echo "========================================"
echo "NotebookLM Generation Tool Installer"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${YELLOW}⚠ Python 3.11+ recommended (found $PYTHON_VERSION)${NC}"
    fi
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

# Check for Chrome
echo ""
echo "Checking for Chrome browser..."
if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null || [ -d "/Applications/Google Chrome.app" ]; then
    echo -e "${GREEN}✓ Chrome browser found${NC}"
else
    echo -e "${YELLOW}⚠ Chrome browser not found. Browser automation may not work.${NC}"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓ pip upgraded${NC}"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env template if it doesn't exist
echo ""
echo "Setting up configuration..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# NotebookLM Generation Tool Configuration
# ========================================

# Gemini API Key (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=

# Browser settings
HEADLESS_BROWSER=false

# Logging
LOG_LEVEL=INFO

# Optional: Google OAuth (for advanced features)
# GOOGLE_CLIENT_ID=
# GOOGLE_CLIENT_SECRET=
EOF
    echo -e "${GREEN}✓ Created .env template${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists${NC}"
fi

# Make main script executable
echo ""
echo "Setting permissions..."
chmod +x src/main.py 2>/dev/null || true

# Create convenience script
echo ""
echo "Creating convenience script..."
cat > run.sh << 'EOF'
#!/bin/bash
# Convenience script to run NotebookLM Generator

# Activate virtual environment
source "$(dirname "$0")/venv/bin/activate"

# Run the tool
python -m src.main "$@"
EOF
chmod +x run.sh
echo -e "${GREEN}✓ Created run.sh${NC}"

# Install nlmgen command globally
echo ""
echo "Installing nlmgen command..."

# Create the nlmgen wrapper script
cat > "${SCRIPT_DIR}/nlmgen" << EOF
#!/bin/bash
# nlmgen - NotebookLM Generation Tool
# Wrapper script to run the tool from anywhere

NLMGEN_HOME="${SCRIPT_DIR}"

# Activate virtual environment and run
source "\${NLMGEN_HOME}/venv/bin/activate"
python -m src.main "\$@"
EOF
chmod +x "${SCRIPT_DIR}/nlmgen"

# Install to /usr/local/bin (may require sudo)
if [ -w "${INSTALL_DIR}" ]; then
    ln -sf "${SCRIPT_DIR}/nlmgen" "${INSTALL_DIR}/nlmgen"
    echo -e "${GREEN}✓ Installed nlmgen command${NC}"
else
    echo -e "${YELLOW}Installing nlmgen to ${INSTALL_DIR} (requires sudo)...${NC}"
    sudo ln -sf "${SCRIPT_DIR}/nlmgen" "${INSTALL_DIR}/nlmgen"
    echo -e "${GREEN}✓ Installed nlmgen command${NC}"
fi

# Install man page
echo ""
echo "Installing man page..."
if [ ! -d "${MAN_DIR}" ]; then
    sudo mkdir -p "${MAN_DIR}"
fi

if [ -w "${MAN_DIR}" ]; then
    cp "${SCRIPT_DIR}/nlmgen.1" "${MAN_DIR}/nlmgen.1"
    gzip -f "${MAN_DIR}/nlmgen.1" 2>/dev/null || true
else
    sudo cp "${SCRIPT_DIR}/nlmgen.1" "${MAN_DIR}/nlmgen.1"
    sudo gzip -f "${MAN_DIR}/nlmgen.1" 2>/dev/null || true
fi
echo -e "${GREEN}✓ Installed man page (run 'man nlmgen' for help)${NC}"

# Print summary
echo ""
echo "========================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "========================================"
echo ""
echo "The 'nlmgen' command is now available system-wide!"
echo ""
echo "Next steps:"
echo ""
echo "1. Add your Gemini API key to .env:"
echo -e "   ${YELLOW}nano ${SCRIPT_DIR}/.env${NC}"
echo ""
echo "2. Run the tool (use single quotes around password for special characters):"
echo -e "   ${YELLOW}nlmgen your_document.pdf -e email@gmail.com -p 'your_password'${NC}"
echo ""
echo "3. For help:"
echo -e "   ${YELLOW}nlmgen --help${NC}"
echo -e "   ${YELLOW}man nlmgen${NC}"
echo ""
echo "4. To uninstall:"
echo -e "   ${YELLOW}${SCRIPT_DIR}/uninstall.sh${NC}"
echo ""
echo "========================================"
echo ""
