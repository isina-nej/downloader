#!/bin/bash

# Server Setup Script - Complete Professional Setup
# Usage: chmod +x server-setup.sh && ./server-setup.sh

set -e

echo "=========================================="
echo "Server Setup - Telegram Bot (Professional)"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Create botuser
echo -e "${YELLOW}[1/7] Creating botuser...${NC}"
if id "botuser" &>/dev/null; then
    echo "✓ botuser already exists"
else
    sudo adduser botuser --shell /bin/bash --gecos "Bot User" --disabled-password
    echo "botuser" | sudo passwd botuser --stdin 2>/dev/null || echo "Set password manually"
fi

# Add to groups
sudo usermod -aG sudo botuser
sudo usermod -aG docker botuser
sudo usermod -aG www-data botuser

echo -e "${GREEN}✓ botuser created${NC}"
echo ""

# Step 2: Update system
echo -e "${YELLOW}[2/7] Updating system...${NC}"
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y \
    git curl wget software-properties-common \
    ufw ca-certificates gnupg lsb-release \
    build-essential python3-dev

echo -e "${GREEN}✓ System updated${NC}"
echo ""

# Step 3: UFW Firewall
echo -e "${YELLOW}[3/7] Setting up firewall...${NC}"
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status

echo -e "${GREEN}✓ Firewall configured${NC}"
echo ""

# Step 4: Docker
echo -e "${YELLOW}[4/7] Installing Docker...${NC}"
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

docker --version
echo -e "${GREEN}✓ Docker installed${NC}"
echo ""

# Step 5: Nginx
echo -e "${YELLOW}[5/7] Installing Nginx...${NC}"
sudo apt-get install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx

echo -e "${GREEN}✓ Nginx installed${NC}"
echo ""

# Step 6: SSL (Certbot)
echo -e "${YELLOW}[6/7] Installing Certbot...${NC}"
sudo apt-get install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

echo -e "${GREEN}✓ Certbot installed${NC}"
echo ""

# Step 7: Create directories
echo -e "${YELLOW}[7/7] Creating directories...${NC}"
sudo mkdir -p /var/www/files
sudo chown -R botuser:www-data /var/www/files
sudo chmod -R 775 /var/www/files

mkdir -p /home/botuser/bot-project
sudo chown -R botuser:botuser /home/botuser/bot-project

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Server Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Switch to botuser:"
echo "   su - botuser"
echo ""
echo "2. Clone/upload bot project:"
echo "   cd ~/bot-project"
echo "   git clone <repo> . OR scp files"
echo ""
echo "3. Build Docker image:"
echo "   cd ~/bot-project"
echo "   docker build -t telegram-bot:latest ."
echo ""
echo "4. Setup SSL certificate:"
echo "   sudo certbot certonly --nginx -d yourdomain.com"
echo ""
echo "5. Create systemd service and start"
echo ""
echo "=========================================="
