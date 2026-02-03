#!/bin/bash
# DigitalOcean Deployment Script for ServiceNow Consultant Multi-Agent System

set -e  # Exit on error

echo "=========================================="
echo "DigitalOcean Deployment Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_info() { echo -e "${NC}→${NC} $1"; }

# Configuration
APP_DIR="$HOME/SN-Consultant"
VENV_DIR="$APP_DIR/venv"
FRONTEND_DIR="$APP_DIR/frontend"

# Step 1: System Update
print_info "Updating system packages..."
sudo apt-get update -qq
print_success "System packages updated"

# Step 2: Install Dependencies
print_info "Installing system dependencies..."
sudo apt-get install -y -qq python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git sqlite3 > /dev/null 2>&1
print_success "System dependencies installed"

# Step 3: Install Node.js (if not present)
if ! command -v node &> /dev/null; then
    print_info "Installing Node.js 20.x..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - > /dev/null 2>&1
    sudo apt-get install -y nodejs > /dev/null 2>&1
    print_success "Node.js installed: $(node --version)"
else
    print_success "Node.js already installed: $(node --version)"
fi

# Step 4: Clone or Update Repository
if [ -d "$APP_DIR" ]; then
    print_info "Updating existing repository..."
    cd "$APP_DIR"
    git pull origin master
    print_success "Repository updated"
else
    print_info "Cloning repository..."
    git clone https://github.com/mailsabhi2007/SNConsultant.git "$APP_DIR"
    cd "$APP_DIR"
    print_success "Repository cloned"
fi

# Step 5: Setup Python Virtual Environment
print_info "Setting up Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

# Step 6: Create .env File (if not exists)
if [ ! -f "$APP_DIR/.env" ]; then
    print_warning ".env file not found. Creating template..."
    cat > "$APP_DIR/.env" <<'EOF'
# REQUIRED: Add your API keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
JWT_SECRET=your_jwt_secret_minimum_32_characters_here

# OPTIONAL: ServiceNow Configuration
SERVICENOW_INSTANCE=your_instance.service-now.com
SERVICENOW_USERNAME=your_servicenow_username
SERVICENOW_PASSWORD=your_servicenow_password

# OPTIONAL: Tavily Search
TAVILY_API_KEY=your_tavily_api_key_here

# Application Settings
ANTHROPIC_MODEL=claude-sonnet-4-20250514
PORT=8000
EOF
    print_warning "⚠ IMPORTANT: Edit $APP_DIR/.env and add your API keys!"
else
    print_success ".env file exists"
fi

# Step 7: Backup and Migrate Database
print_info "Setting up database..."
mkdir -p "$APP_DIR/data"
if [ -f "$APP_DIR/data/app.db" ]; then
    BACKUP_FILE="$APP_DIR/data/app.db.backup.$(date +%Y%m%d_%H%M%S)"
    cp "$APP_DIR/data/app.db" "$BACKUP_FILE"
    print_success "Database backed up to $BACKUP_FILE"
fi
python3 "$APP_DIR/database.py" > /dev/null 2>&1
print_success "Database initialized"

# Step 8: Build Frontend
print_info "Building frontend..."
cd "$FRONTEND_DIR"
npm install --legacy-peer-deps > /dev/null 2>&1
npm run build > /dev/null 2>&1
print_success "Frontend built"
cd "$APP_DIR"

# Step 9: Setup Systemd Service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/sn-consultant.service > /dev/null <<EOF
[Unit]
Description=ServiceNow Consultant API
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
print_success "Systemd service created"

# Step 10: Configure Nginx
print_info "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/sn-consultant > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    root /home/USER_PLACEHOLDER/SN-Consultant/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
        proxy_read_timeout 300s;
    }
}
EOF

# Replace USER_PLACEHOLDER with actual username
sudo sed -i "s|USER_PLACEHOLDER|$USER|g" /etc/nginx/sites-available/sn-consultant

# Enable site
sudo ln -sf /etc/nginx/sites-available/sn-consultant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
print_success "Nginx configured"

# Step 11: Test Nginx Configuration
print_info "Testing Nginx configuration..."
if sudo nginx -t > /dev/null 2>&1; then
    print_success "Nginx configuration valid"
else
    print_error "Nginx configuration invalid!"
    sudo nginx -t
    exit 1
fi

# Step 12: Start Services
print_info "Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable sn-consultant
sudo systemctl restart sn-consultant
sudo systemctl restart nginx
print_success "Services started"

# Step 13: Create Logs Directory
mkdir -p "$APP_DIR/logs"
print_success "Logs directory created"

# Step 14: Health Check
print_info "Performing health check..."
sleep 3
if curl -sf http://localhost:8000/api/health > /dev/null; then
    print_success "Backend is healthy!"
else
    print_warning "Backend health check failed. Check logs with: sudo journalctl -u sn-consultant -n 50"
fi

# Step 15: Display Summary
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
print_success "Backend deployed and running"
print_success "Frontend built and served via Nginx"
print_success "Database initialized"
echo ""
echo "Service Status:"
sudo systemctl status sn-consultant --no-pager -l | head -n 5
echo ""
echo "Next Steps:"
echo "1. Edit $APP_DIR/.env with your API keys"
echo "2. Restart backend: sudo systemctl restart sn-consultant"
echo "3. Create first admin user via UI or:"
echo "   python3 -c 'from database import get_db_connection; conn = get_db_connection(); conn.cursor().execute(\"UPDATE users SET is_superadmin = 1 WHERE username = \\\"admin\\\"\"); conn.commit()'"
echo "4. (Optional) Setup SSL:"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
echo "Access the application:"
echo "  - Local: http://localhost"
echo "  - Public: http://$(curl -s ifconfig.me)"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo journalctl -u sn-consultant -f"
echo "  - Restart backend: sudo systemctl restart sn-consultant"
echo "  - Restart nginx: sudo systemctl restart nginx"
echo "  - Check status: sudo systemctl status sn-consultant"
echo ""
print_info "For detailed documentation, see DEPLOYMENT_GUIDE.md"
echo ""
