# Deployment Guide

## Automatic Deployment (Linux/Mac)

```bash
./deploy.sh
```

## Manual Deployment

### 1. SSH to Server
```bash
ssh root@155.103.71.153
```

### 2. Setup Application
```bash
# Create app directory
mkdir -p /app
cd /app

# Copy your project files
# (via scp or git clone)
```

### 3. Install Dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Edit .env.production with your credentials
nano .env.production
```

### 5. Setup Systemd Service
```bash
cp telegram-downloader.service /etc/systemd/system/
chmod 644 /etc/systemd/system/telegram-downloader.service
systemctl daemon-reload
systemctl enable telegram-downloader
systemctl start telegram-downloader
```

### 6. Verify Service
```bash
systemctl status telegram-downloader
journalctl -u telegram-downloader -f  # View logs
```

## Health Check
```bash
curl http://155.103.71.153:8000/health
```

## Stop Service
```bash
systemctl stop telegram-downloader
```

## View Logs
```bash
journalctl -u telegram-downloader -f
```
