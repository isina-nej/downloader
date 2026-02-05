#!/bin/bash

# Post-Setup Script - Run after server-setup.sh

set -e

DOMAIN="${1:-downloder.nodia.ir}"
PROJECT_DIR="/home/botuser/bot-project"

echo "=========================================="
echo "Post-Setup Configuration"
echo "=========================================="
echo "Domain: $DOMAIN"
echo ""

# 1. Setup Nginx for domain
echo "[1/3] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null << NGINX_EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL will be set by certbot
    # ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Bot API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        client_max_body_size 2G;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # File downloads
    location /files/ {
        alias /var/www/files/;
        autoindex off;
        expires 30d;
    }
}
NGINX_EOF

sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/ 2>/dev/null || true
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx

echo "✓ Nginx configured"
echo ""

# 2. Get SSL certificate
echo "[2/3] Getting SSL certificate..."
echo "Make sure DNS is pointing to this server's IP!"
read -p "Press Enter after DNS is updated, then press Enter again to continue..."

sudo certbot certonly --nginx -d $DOMAIN -d www.$DOMAIN

echo "✓ SSL certificate obtained"
echo ""

# 3. Create systemd service
echo "[3/3] Setting up systemd service..."

sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << SERVICE_EOF
[Unit]
Description=Telegram Bot (Docker)
After=docker.service network.target
Requires=docker.service

[Service]
Type=simple
User=botuser
WorkingDirectory=$PROJECT_DIR
Restart=always
RestartSec=10

ExecStartPre=-/usr/bin/docker stop telegram-bot
ExecStartPre=-/usr/bin/docker rm telegram-bot

ExecStart=/usr/bin/docker run \
    --name telegram-bot \
    -v $PROJECT_DIR/storage:/app/storage \
    -v $PROJECT_DIR/logs:/app/logs \
    -v /var/www/files:/app/files \
    --env-file $PROJECT_DIR/.env.production \
    --restart unless-stopped \
    telegram-bot:latest

ExecStop=/usr/bin/docker stop -t 5 telegram-bot

StandardOutput=journal
StandardError=journal
StandardOutputVerbose=yes

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service

echo "✓ Systemd service created"
echo ""

echo "=========================================="
echo "Post-Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Start the service:"
echo "   sudo systemctl start telegram-bot"
echo ""
echo "2. Check status:"
echo "   sudo systemctl status telegram-bot"
echo "   docker logs -f telegram-bot"
echo ""
echo "3. Verify:"
echo "   curl -k https://$DOMAIN/health"
echo ""
