#!/bin/bash

# Deployment script for Telegram Downloader Bot

set -e

SERVER_IP="155.103.71.153"
SERVER_USER="root"
REMOTE_PORT="22"

cd "$(dirname "$0")"

echo "Creating deployment package..."
tar --exclude='.git' --exclude='__pycache__' --exclude='.pytest_cache' \
    --exclude='.venv' --exclude='logs' --exclude='storage/*.bin' \
    -czf /tmp/telegram-downloader.tar.gz \
    src/ requirements.txt pyproject.toml .env.production start_service.sh telegram-downloader.service

echo "Uploading to server..."
scp -P ${REMOTE_PORT} /tmp/telegram-downloader.tar.gz ${SERVER_USER}@${SERVER_IP}:/tmp/

echo "Deploying on server..."
ssh -p ${REMOTE_PORT} ${SERVER_USER}@${SERVER_IP} << 'DEPLOY_EOF'
set -e

echo "=== Installing dependencies ==="
apt-get update -qq
apt-get install -y -qq nginx certbot python3-certbot-nginx

echo "=== Stopping existing services ==="
systemctl stop telegram-downloader 2>/dev/null || true
systemctl stop nginx 2>/dev/null || true

echo "=== Creating app directory ==="
rm -rf /app
mkdir -p /app /app/storage
cd /app

echo "=== Extracting files ==="
tar -xzf /tmp/telegram-downloader.tar.gz

echo "=== Installing dependencies ==="
python3 -m pip install -q --upgrade pip
python3 -m pip install -q -r requirements.txt

echo "=== Setting up systemd service ==="
cp telegram-downloader.service /etc/systemd/system/
chmod 644 /etc/systemd/system/telegram-downloader.service
chmod +x start_service.sh
systemctl daemon-reload

echo "=== Setting up nginx reverse proxy ==="
cat > /etc/nginx/sites-available/downloder.nodia.ir << 'NGINX_EOF'
server {
    listen 80;
    server_name downloder.nodia.ir;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name downloder.nodia.ir;

    ssl_certificate /etc/letsencrypt/live/downloder.nodia.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/downloder.nodia.ir/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 2G;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

ln -sf /etc/nginx/sites-available/downloder.nodia.ir /etc/nginx/sites-enabled/ 2>/dev/null || true
nginx -t && systemctl enable nginx

echo "=== Starting services ==="
systemctl enable telegram-downloader
systemctl start telegram-downloader
systemctl start nginx

echo "=== SSL Certificate Setup ==="
echo "Run this command on the server:"
echo "certbot certonly --standalone --register-unsafely-without-email --non-interactive --agree-tos -d downloder.nodia.ir"
echo ""
echo "Then restart nginx:"
echo "systemctl restart nginx"
echo ""

echo "=== Deployment complete ==="
systemctl status telegram-downloader

DEPLOY_EOF

echo "Cleaning up..."
rm /tmp/telegram-downloader.tar.gz

echo ""
echo "✓ Deployment successful!"
echo "✓ Service is running at http://155.103.71.153:8000"
echo ""
echo "Next steps:"
echo "  1. SSH to server: ssh root@155.103.71.153"
echo "  2. Edit config: nano /app/.env.production"
echo "  3. Restart service: systemctl restart telegram-downloader"
echo "  4. View logs: journalctl -u telegram-downloader -f"
