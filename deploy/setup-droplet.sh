#!/bin/bash
# DigitalOcean Droplet Setup Script for SN Consultant
# Run as root on a fresh Ubuntu 22.04 droplet

set -e

echo "=========================================="
echo "SN Consultant - DigitalOcean Setup Script"
echo "=========================================="

# Update system
echo "[1/8] Updating system packages..."
apt update && apt upgrade -y

# Install dependencies
echo "[2/8] Installing dependencies..."
apt install -y python3 python3-venv python3-pip nodejs npm nginx git curl

# Install Node.js 18+ (if default is older)
echo "[3/8] Setting up Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Create app directory
echo "[4/8] Creating application directory..."
mkdir -p /var/www/sn-consultant
chown -R www-data:www-data /var/www/sn-consultant

# Clone or copy your app (you'll do this manually or via git)
echo "[5/8] Application directory ready at /var/www/sn-consultant"
echo "       Copy your app files there or clone from git"

# Create data directories
mkdir -p /var/www/sn-consultant/data
mkdir -p /var/www/sn-consultant/chroma_db
mkdir -p /var/www/sn-consultant/user_context_data
chown -R www-data:www-data /var/www/sn-consultant

# Setup Python virtual environment
echo "[6/8] Python venv will be created during deploy..."

# Configure Nginx
echo "[7/8] Configuring Nginx..."
rm -f /etc/nginx/sites-enabled/default

# Setup firewall
echo "[8/8] Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo ""
echo "=========================================="
echo "Initial setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Copy your app to /var/www/sn-consultant"
echo "2. Run the deploy script: ./deploy/deploy.sh"
echo "3. Set up SSL with: certbot --nginx -d your-domain.com"
echo ""
