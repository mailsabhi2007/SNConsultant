#!/bin/bash
# Deployment script for ServiceNow Consultant

set -e

echo "🚀 ServiceNow Consultant Deployment Script"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}Please update .env with your API keys${NC}"
    else
        echo -e "${RED}❌ .env.example not found. Please create .env manually.${NC}"
        exit 1
    fi
fi

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python 3.10+ required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python version OK: $python_version${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p chroma_db user_context_data .cursor

# Check environment variables
echo "Checking environment variables..."
required_vars=("ANTHROPIC_API_KEY" "OPENAI_API_KEY" "TAVILY_API_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if ! grep -q "^${var}=" .env 2>/dev/null; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Missing environment variables: ${missing_vars[*]}${NC}"
    echo "Please add them to your .env file"
fi

# Run basic health check
echo "Running health check..."
python3 -c "
import sys
try:
    from agent import get_agent
    from knowledge_base import get_embeddings
    print('✅ Core modules import successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo ""
echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo "To start the application:"
echo "  source venv/bin/activate"
echo "  streamlit run streamlit_app.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up -d"
