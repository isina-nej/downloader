#!/bin/bash

# Docker Deployment Script for Telegram Bot
# Usage: ./docker-deploy.sh <server-ip> <domain>

set -e

if [ $# -lt 2 ]; then
    echo "Usage: ./docker-deploy.sh <server-ip> <domain>"
    echo "Example: ./docker-deploy.sh 155.103.71.153 downloder.nodia.ir"
    exit 1
fi

SERVER_IP=$1
DOMAIN=$2
SERVER_USER="botuser"
PROJECT_DIR="/home/botuser/bot-project"

echo "=== Docker Deployment Script ==="
echo "Server IP: $SERVER_IP"
echo "Domain: $DOMAIN"
echo ""

# Step 1: Create deployment package
echo "[1/6] Creating deployment package..."
tar --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' \
    --exclude='.venv' --exclude='logs' --exclude='storage' \
    --exclude='*.pyc' --exclude='.env' \
    -czf /tmp/telegram-bot-docker.tar.gz \
    Dockerfile docker-compose.yml .dockerignore \
    requirements.txt pyproject.toml .env.production \
    src/ start_service.sh

echo "[✓] Package created"

# Step 2: Upload to server
echo "[2/6] Uploading to server..."
scp /tmp/telegram-bot-docker.tar.gz ${SERVER_USER}@${SERVER_IP}:/tmp/

echo "[✓] Upload complete"

# Step 3: Deploy on server
echo "[3/6] Deploying on server..."
ssh ${SERVER_USER}@${SERVER_IP} << DEPLOY_EOF
set -e

echo "[3.1/6] Creating project directory..."
mkdir -p ${PROJECT_DIR}
cd ${PROJECT_DIR}

echo "[3.2/6] Stopping existing container..."
docker-compose down 2>/dev/null || true
docker stop telegram-bot 2>/dev/null || true
docker rm telegram-bot 2>/dev/null || true

echo "[3.3/6] Extracting files..."
tar -xzf /tmp/telegram-bot-docker.tar.gz

echo "[3.4/6] Building Docker image..."
docker build -t telegram-bot:latest .

echo "[3.5/6] Creating storage and logs directories..."
mkdir -p storage logs
chmod 755 storage logs

echo "[✓] Docker image built successfully"

DEPLOY_EOF

# Step 4: Setup systemd service
echo "[4/6] Setting up systemd service..."
ssh ${SERVER_USER}@${SERVER_IP} << SERVICE_EOF
set -e

# Create systemd service file
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << 'SYSTEMD_EOF'
[Unit]
Description=Telegram Bot (Docker)
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=${SERVER_USER}
WorkingDirectory=${PROJECT_DIR}
Restart=always
RestartSec=10

ExecStartPre=-/usr/bin/docker stop telegram-bot
ExecStartPre=-/usr/bin/docker rm telegram-bot

ExecStart=/usr/bin/docker run \
    --name telegram-bot \
    -v ${PROJECT_DIR}/storage:/app/storage \
    -v ${PROJECT_DIR}/logs:/app/logs \
    -e DOWNLOAD_URL_BASE=https://${DOMAIN} \
    --restart unless-stopped \
    telegram-bot:latest

ExecStop=/usr/bin/docker stop telegram-bot

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service

echo "[✓] Systemd service configured"

SERVICE_EOF

# Step 5: Setup Nginx
echo "[5/6] Setting up Nginx..."
ssh ${SERVER_USER}@${SERVER_IP} << NGINX_EOF
set -e

# Create nginx config
sudo tee /etc/nginx/sites-available/${DOMAIN} > /dev/null << 'NGINX_CONFIG_EOF'
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};
    return 301 https://\$server_name\$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    # SSL certificates (set by certbot)
    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Proxy to bot API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Root
    location / {
        return 404;
    }
}
NGINX_CONFIG_EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/${DOMAIN} /etc/nginx/sites-enabled/ 2>/dev/null || true

# Test nginx
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

echo "[✓] Nginx configured"

NGINX_EOF

# Step 6: Start the bot
echo "[6/6] Starting bot service..."
ssh ${SERVER_USER}@${SERVER_IP} << START_EOF
set -e

sudo systemctl start telegram-bot.service
sleep 3

# Check status
sudo systemctl status telegram-bot.service || true

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "📊 Service Status:"
sudo systemctl status telegram-bot.service --no-pager

echo ""
echo "📝 View Logs:"
echo "  docker logs telegram-bot"
echo "  journalctl -u telegram-bot.service -f"
echo ""
echo "🌐 Access bot at: https://${DOMAIN}"
echo ""

START_EOF

# Cleanup
rm /tmp/telegram-bot-docker.tar.gz

echo ""
echo "✅ Deployment finished!"
echo ""
echo "Next steps:"
echo "1. SSH: ssh ${SERVER_USER}@${SERVER_IP}"
echo "2. Setup SSL: sudo certbot --nginx -d ${DOMAIN}"
echo "3. View logs: docker logs telegram-bot"
echo "4. Restart bot: sudo systemctl restart telegram-bot"
