# Docker Deployment Guide (Professional Setup 2026)

## سخت‌افزار و نرم‌افزار پیشنهادی

- **OS**: Ubuntu 24.04 LTS یا 22.04 LTS
- **RAM**: ۲ GB (کافی برای بات)
- **Storage**: ۲۰-۱۰۰ GB (بسته به فایل‌های ذخیره‌شده)
- **CPU**: ۱-۲ Core

## مراحل راه‌اندازی (حرفه‌ای)

### ۱. آماده‌سازی سرور

```bash
# SSH به سرور
ssh root@155.103.71.153

# ایجاد کاربر جدید
adduser botuser
# رمز قوی انتخاب کنید

# دسترسی sudo
usermod -aG sudo botuser

# تعطیل ورود root
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# ذخیره و خروج
sudo systemctl restart ssh

# حالا از botuser کار کنید
ssh botuser@155.103.71.153
```

### ۲. به‌روزرسانی سیستم

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl software-properties-common ufw ca-certificates gnupg lsb-release
```

### ۳. فایروال (ufw)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### ۴. نصب Docker

```bash
# Add Docker repository
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker botuser

# Log out and log back in
exit
ssh botuser@155.103.71.153

# Test
docker --version
```

### ۵. نصب Nginx و SSL

```bash
# Install Nginx
sudo apt install -y nginx
sudo systemctl enable --now nginx

# Install Certbot
sudo apt install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot

# Get certificate (after pointing domain DNS to IP)
sudo certbot --nginx -d downloder.nodia.ir -d www.downloder.nodia.ir
# Choose auto-redirect to HTTPS
```

### ۶. کلون کد پروژه

```bash
mkdir -p ~/bot-project
cd ~/bot-project
git clone https://github.com/your-repo.git .
# OR
# scp -r /local/path botuser@IP:~/bot-project
```

### ۷. آماده‌سازی .env

```bash
cp .env.example .env.production
nano .env.production
# Edit: TELEGRAM_BOT_TOKEN و TELEGRAM_CHAT_ID
```

### ۸. استقرار خودکار

```bash
chmod +x docker-deploy.sh
./docker-deploy.sh 155.103.71.153 downloder.nodia.ir
```

یا دستی:

```bash
scp docker-deploy.sh botuser@155.103.71.153:~/bot-project/
ssh botuser@155.103.71.153
cd ~/bot-project
chmod +x docker-deploy.sh
./docker-deploy.sh 155.103.71.153 downloder.nodia.ir
```

### ۹. تنظیم SSL

```bash
ssh botuser@155.103.71.153
sudo certbot --nginx -d downloder.nodia.ir
```

### ۱۰. شروع سرویس

```bash
# Start service
sudo systemctl start telegram-bot.service

# Enable on boot
sudo systemctl enable telegram-bot.service

# Check status
sudo systemctl status telegram-bot.service

# View logs
docker logs telegram-bot
# یا
journalctl -u telegram-bot.service -f
```

## دستورات مفید

### مدیریت

```bash
# ببینید سرویس دارد اجرا می‌شود
sudo systemctl status telegram-bot.service

# متوقف کنید
sudo systemctl stop telegram-bot.service

# شروع کنید
sudo systemctl start telegram-bot.service

# دوباره شروع کنید
sudo systemctl restart telegram-bot.service

# لاگ‌ها
docker logs -f telegram-bot
docker logs --tail 100 telegram-bot

# درون container
docker exec -it telegram-bot bash
```

### بروزرسانی کد

```bash
cd ~/bot-project

# Pull latest code
git pull origin main

# Rebuild image
docker build -t telegram-bot:latest .

# Restart service
sudo systemctl restart telegram-bot.service
```

### Backup

```bash
# Backup storage
cd ~
tar -czf backup-$(date +%Y%m%d).tar.gz bot-project/storage/

# Transfer to local
scp botuser@IP:~/backup-*.tar.gz .
```

## مراقبت‌سازی

```bash
# CPU و RAM
htop

# Disk usage
df -h
du -sh ~/bot-project/storage/

# Network
sudo ss -tlnp | grep docker
```

## مشکل‌گشایی

### بات شروع نمی‌شود

```bash
docker logs telegram-bot
journalctl -u telegram-bot.service -n 50
```

### Permission denied

```bash
docker ps
sudo usermod -aG docker botuser
# Log out and back in
```

### Nginx error

```bash
sudo nginx -t
sudo systemctl status nginx
sudo systemctl restart nginx
```

### SSL issues

```bash
sudo certbot renew --dry-run
sudo systemctl restart nginx
```

## مزایای این setup

✅ **Isolation** - Docker container جدا
✅ **Security** - SSL/TLS، firewall، کاربر محدود
✅ **Scalability** - آسان برای بزرگ کردن
✅ **Automatic restart** - systemd
✅ **Easy updates** - git pull + rebuild
✅ **Monitoring** - logs via docker/journalctl
✅ **Backup** - حفاظت داده‌ها

---

**موفق باشید!** 🚀
