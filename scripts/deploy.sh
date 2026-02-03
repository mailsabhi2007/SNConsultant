#!/bin/bash
# Deployment script for ServiceNow Consultant Multi-Agent System

set -e  # Exit on error

echo "=========================================="
echo "ServiceNow Consultant Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${NC}→${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root"
    exit 1
fi

# Step 1: Check prerequisites
print_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi
print_success "Python 3 found: $(python3 --version)"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_warning "Node.js not found. Frontend deployment will be skipped."
    DEPLOY_FRONTEND=false
else
    print_success "Node.js found: $(node --version)"
    DEPLOY_FRONTEND=true
fi

# Check pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 not found. Please install pip"
    exit 1
fi
print_success "pip3 found"

echo ""

# Step 2: Backup database
print_info "Creating database backup..."
if [ -f "data/app.db" ]; then
    BACKUP_FILE="data/app.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp data/app.db "$BACKUP_FILE"
    print_success "Database backed up to $BACKUP_FILE"
else
    print_warning "No existing database found. Skipping backup."
fi

echo ""

# Step 3: Install Python dependencies
print_info "Installing Python dependencies..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    print_info "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

echo ""

# Step 4: Run database migration
print_info "Running database migration..."
python3 database.py
if [ $? -eq 0 ]; then
    print_success "Database migration completed"
else
    print_error "Database migration failed"
    exit 1
fi

echo ""

# Step 5: Deploy frontend (if Node.js available)
if [ "$DEPLOY_FRONTEND" = true ]; then
    print_info "Installing frontend dependencies..."
    cd frontend
    npm install > /dev/null 2>&1
    print_success "Frontend dependencies installed"

    print_info "Building frontend..."
    npm run build > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Frontend built successfully"
    else
        print_error "Frontend build failed"
        cd ..
        exit 1
    fi
    cd ..
else
    print_warning "Skipping frontend deployment (Node.js not found)"
fi

echo ""

# Step 6: Initialize configuration
print_info "Initializing multi-agent configuration..."
python3 -c "
from user_config import set_multi_agent_rollout_percentage, get_system_config
current = get_system_config('multi_agent_rollout_percentage')
if current is None:
    set_multi_agent_rollout_percentage(0)
    print('Rollout initialized to 0%')
else:
    print(f'Rollout already set to {current}%')
"
print_success "Configuration initialized"

echo ""

# Step 7: Run tests
print_info "Running tests..."
if [ -f "test_multi_agent.py" ]; then
    python3 test_multi_agent.py > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Tests passed"
    else
        print_warning "Some tests failed. Check test output."
    fi
else
    print_warning "Test file not found. Skipping tests."
fi

echo ""

# Step 8: Display summary
echo "=========================================="
echo "Deployment Summary"
echo "=========================================="
echo ""
print_success "Backend deployed successfully"
if [ "$DEPLOY_FRONTEND" = true ]; then
    print_success "Frontend built successfully"
fi
print_success "Database migrated"
print_success "Configuration initialized"

echo ""
echo "Next steps:"
echo "1. Configure environment variables in .env"
echo "2. Make first user superadmin:"
echo "   python3 -c 'from database import get_db_connection; conn = get_db_connection(); conn.cursor().execute(\"UPDATE users SET is_superadmin = 1 WHERE username = \\\"admin\\\"\"); conn.commit()'"
echo "3. Start the backend:"
echo "   uvicorn api.main:app --reload"
echo "4. Access at: http://localhost:8000"
echo ""
print_info "For production deployment, see DEPLOYMENT_GUIDE.md"
echo ""
