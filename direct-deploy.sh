#!/bin/bash

# Direct Python Deployment (Without Docker)
# راه‌اندازی مستقیم بدون Docker

set -e

echo "=========================================="
echo "Direct Python Deployment"
echo "=========================================="
echo ""

PROJECT_DIR="/home/botuser/bot-project"
VENV_DIR="$PROJECT_DIR/venv"

# 1. Create virtual environment
echo "[1/4] Creating virtual environment..."
cd "$PROJECT_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

echo "[✓] venv created"
echo ""

# 2. Install dependencies
echo "[2/4] Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "[✓] Dependencies installed"
echo ""

# 3. Create systemd service
echo "[3/4] Creating systemd service..."
sudo tee /etc/systemd/system/telegram-bot.service > /dev/null << SERVICE_EOF
[Unit]
Description=Telegram Downloader Bot (Python)
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env.production
ExecStart=$VENV_DIR/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_EOF

sudo systemctl daemon-reload
sudo systemctl enable telegram-bot.service

echo "[✓] Systemd service created"
echo ""

# 4. Setup Nginx
echo "[4/4] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/downloader.nodia.ir > /dev/null << NGINX_EOF
# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name downloader.nodia.ir www.downloader.nodia.ir;
    
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
    server_name downloader.nodia.ir www.downloader.nodia.ir;

    ssl_certificate /etc/letsencrypt/live/downloader.nodia.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/downloader.nodia.ir/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

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

sudo ln -sf /etc/nginx/sites-available/downloader.nodia.ir /etc/nginx/sites-enabled/ 2>/dev/null || true
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl reload nginx

echo "[✓] Nginx configured"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Start the service:"
echo "  sudo systemctl start telegram-bot"
echo ""
echo "Check status:"
echo "  sudo systemctl status telegram-bot"
echo ""
echo "View logs:"
echo "  journalctl -u telegram-bot -f"
echo ""
echo "Verify:"
echo "  curl https://downloader.nodia.ir/health"
echo ""
