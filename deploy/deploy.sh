#!/bin/bash
# Deployment script - run from /var/www/sn-consultant
# Usage: ./deploy/deploy.sh

set -e

APP_DIR="/var/www/sn-consultant"
cd $APP_DIR

echo "=========================================="
echo "Deploying SN Consultant"
echo "=========================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Create .env with your API keys before deploying."
    echo ""
    echo "Required variables:"
    echo "  ANTHROPIC_API_KEY=your_key"
    echo "  OPENAI_API_KEY=your_key"
    echo "  TAVILY_API_KEY=your_key"
    echo "  JWT_SECRET_KEY=your_secret"
    exit 1
fi

# Backend setup
echo "[1/5] Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Frontend build
echo "[2/5] Building frontend..."
cd frontend
npm ci --legacy-peer-deps
npm run build
cd ..

# Set permissions
echo "[3/5] Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod 600 .env

# Install systemd service
echo "[4/5] Installing systemd service..."
cp deploy/sn-consultant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable sn-consultant
systemctl restart sn-consultant

# Configure Nginx
echo "[5/5] Configuring Nginx..."
cp deploy/nginx.conf /etc/nginx/sites-available/sn-consultant
ln -sf /etc/nginx/sites-available/sn-consultant /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Service status:"
systemctl status sn-consultant --no-pager -l | head -15
echo ""
echo "View logs: journalctl -u sn-consultant -f"
echo ""
echo "If using a domain, set up SSL:"
echo "  apt install certbot python3-certbot-nginx"
echo "  certbot --nginx -d your-domain.com"
echo ""
