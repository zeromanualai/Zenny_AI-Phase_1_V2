#!/bin/bash
# Zenny AI — Hetzner VPS Setup Script
# Run as root on a fresh Ubuntu 22.04 CX11 instance

set -e

echo "🚀 Zenny Hetzner Setup Starting..."

# Update system
apt update && apt upgrade -y

# Install essentials
apt install -y curl wget git ufw nginx certbot python3-certbot-nginx

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose plugin
apt install -y docker-compose-plugin

# Create project directory
mkdir -p /opt/zenny
cd /opt/zenny

echo "✅ System packages installed"

# Setup firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5678/tcp
ufw allow 3001/tcp
ufw --force enable

echo "✅ Firewall configured"

# Create n8n user for security
useradd -r -s /bin/false n8n || true

echo ""
echo "═══════════════════════════════════════════════════"
echo "Next steps:"
echo "1. Copy docker-compose.yml to /opt/zenny/"
echo "2. Create .env file with your credentials"
echo "3. Run: docker compose up -d"
echo "4. Configure nginx with: scripts/infrastructure/nginx-n8n.conf"
echo "═══════════════════════════════════════════════════"
