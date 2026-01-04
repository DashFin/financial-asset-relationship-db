#!/bin/bash
# Run PR Copilot tests
# Usage: ./run_tests.sh [options]

set -e

echo "🧪 Running PR Copilot Tests"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Set up Python virtual environment for cleaner install
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${BLUE}🐍 Using existing virtual environment${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔌 Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Upgrade pip in virtual environment
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install -q --upgrade pip

# Install dependencies
echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -q pytest pytest-cov
pip install -q -r .github/pr-copilot/scripts/requirements.txt

echo ""
echo -e "${BLUE}🧪 Running unit tests...${NC}"
pytest tests/unit/test_pr_copilot_*.py -v

echo ""
echo -e "${BLUE}🔗 Running integration tests...${NC}"
pytest tests/integration/test_pr_copilot_workflow.py -v

echo ""
echo -e "${GREEN}✅ All PR Copilot tests passed!${NC}"
echo ""

# Optional: Run with coverage
if [ "$1" == "--coverage" ]; then
    echo -e "${BLUE}📊 Generating coverage report...${NC}"
    pytest tests/unit/test_pr_copilot_*.py \
           tests/integration/test_pr_copilot_workflow.py \
           --cov=.github/pr-copilot/scripts \
           --cov-report=term \
           --cov-report=html
    echo ""
    echo -e "${GREEN}📊 Coverage report generated in htmlcov/index.html${NC}"
fi

# Deactivate virtual environment
deactivate
