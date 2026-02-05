#!/bin/bash

# Quick Fix - Remove Docker cache and rebuild
# اجرای این اسکریپت Docker cache رو پاک می‌کند و دوباره بیلد می‌کند

set -e

echo "🧹 Cleaning Docker cache..."
docker system prune -af

echo "🔨 Rebuilding image..."
docker build --no-cache -t telegram-bot:latest .

echo ""
echo "✅ Build complete!"
echo ""
echo "Test the image:"
echo "  docker run --rm -it --name test-bot telegram-bot:latest"
echo ""
echo "Check logs:"
echo "  docker logs test-bot"
