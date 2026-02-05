#!/bin/bash

# SSL Setup Script for Telegram Downloader

set -e

DOMAIN="downloder.nodia.ir"
EMAIL="admin@nodia.ir"

echo "=== Setting up SSL certificate for ${DOMAIN} ==="

# Stop services that might be using port 80
systemctl stop nginx 2>/dev/null || true

echo "=== Obtaining SSL certificate ==="
certbot certonly \
    --standalone \
    --register-unsafely-without-email \
    --non-interactive \
    --agree-tos \
    -d ${DOMAIN}

echo "=== Setting up auto-renewal ==="
systemctl enable certbot.timer
systemctl start certbot.timer

echo "=== Restarting nginx ==="
systemctl restart nginx

echo ""
echo "✓ SSL certificate installed successfully!"
echo "✓ Auto-renewal enabled"
echo ""
echo "Certificate path: /etc/letsencrypt/live/${DOMAIN}/"
echo "Renewal test: certbot renew --dry-run"
