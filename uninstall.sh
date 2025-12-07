#!/bin/bash

# NotebookLM Generation Tool - Uninstall Script
# ==============================================

set -e

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
MAN_DIR="/usr/local/share/man/man1"

echo "========================================"
echo "NotebookLM Generation Tool Uninstaller"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Confirm uninstallation
echo -e "${YELLOW}This will remove the nlmgen command and man page.${NC}"
echo "The source code and virtual environment will NOT be deleted."
echo ""
read -p "Are you sure you want to uninstall? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""

# Remove nlmgen command from /usr/local/bin
echo "Removing nlmgen command..."
if [ -L "${INSTALL_DIR}/nlmgen" ] || [ -f "${INSTALL_DIR}/nlmgen" ]; then
    if [ -w "${INSTALL_DIR}" ]; then
        rm -f "${INSTALL_DIR}/nlmgen"
    else
        sudo rm -f "${INSTALL_DIR}/nlmgen"
    fi
    echo -e "${GREEN}✓ Removed nlmgen from ${INSTALL_DIR}${NC}"
else
    echo -e "${YELLOW}⚠ nlmgen not found in ${INSTALL_DIR}${NC}"
fi

# Remove local nlmgen wrapper
if [ -f "${SCRIPT_DIR}/nlmgen" ]; then
    rm -f "${SCRIPT_DIR}/nlmgen"
    echo -e "${GREEN}✓ Removed local nlmgen wrapper${NC}"
fi

# Remove man page
echo ""
echo "Removing man page..."
if [ -f "${MAN_DIR}/nlmgen.1.gz" ] || [ -f "${MAN_DIR}/nlmgen.1" ]; then
    if [ -w "${MAN_DIR}" ]; then
        rm -f "${MAN_DIR}/nlmgen.1.gz" "${MAN_DIR}/nlmgen.1"
    else
        sudo rm -f "${MAN_DIR}/nlmgen.1.gz" "${MAN_DIR}/nlmgen.1"
    fi
    echo -e "${GREEN}✓ Removed man page${NC}"
else
    echo -e "${YELLOW}⚠ Man page not found${NC}"
fi

# Remove run.sh
if [ -f "${SCRIPT_DIR}/run.sh" ]; then
    rm -f "${SCRIPT_DIR}/run.sh"
    echo -e "${GREEN}✓ Removed run.sh${NC}"
fi

# Ask about removing virtual environment
echo ""
read -p "Do you also want to remove the virtual environment (venv/)? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "${SCRIPT_DIR}/venv" ]; then
        rm -rf "${SCRIPT_DIR}/venv"
        echo -e "${GREEN}✓ Removed virtual environment${NC}"
    fi
fi

# Ask about removing .env file
read -p "Do you want to remove the .env configuration file? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "${SCRIPT_DIR}/.env" ]; then
        rm -f "${SCRIPT_DIR}/.env"
        echo -e "${GREEN}✓ Removed .env file${NC}"
    fi
fi

# Ask about removing saved cookies
read -p "Do you want to remove saved Google session cookies? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    COOKIES_DIR="${HOME}/.notebook_lm_gen"
    if [ -d "${COOKIES_DIR}" ]; then
        rm -rf "${COOKIES_DIR}"
        echo -e "${GREEN}✓ Removed saved cookies from ${COOKIES_DIR}${NC}"
    fi
fi

echo ""
echo "========================================"
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "========================================"
echo ""
echo "The source code remains in: ${SCRIPT_DIR}"
echo ""
echo "To completely remove, delete the directory:"
echo -e "   ${YELLOW}rm -rf ${SCRIPT_DIR}${NC}"
echo ""
echo "========================================"
echo ""
