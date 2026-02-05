@echo off
REM Windows deployment script for Telegram Downloader

setlocal enabledelayedexpansion

set SERVER_IP=155.103.71.153
set SERVER_USER=root
set REMOTE_PORT=22

echo Creating deployment package...
tar --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache ^
    --exclude=.venv --exclude=logs --exclude=storage\*.bin ^
    -czf "%TEMP%\telegram-downloader.tar.gz" ^
    src requirements.txt pyproject.toml .env.production start_service.sh telegram-downloader.service

if errorlevel 1 (
    echo Failed to create package
    exit /b 1
)

echo Uploading to server...
scp -P %REMOTE_PORT% "%TEMP%\telegram-downloader.tar.gz" %SERVER_USER%@%SERVER_IP%:/tmp/

if errorlevel 1 (
    echo Failed to upload
    exit /b 1
)

echo Deploying on server...
ssh -p %REMOTE_PORT% %SERVER_USER%@%SERVER_IP% ^
    "cd /app || mkdir -p /app; cd /app; tar -xzf /tmp/telegram-downloader.tar.gz; python3 -m pip install -q -r requirements.txt; cp telegram-downloader.service /etc/systemd/system/; chmod 644 /etc/systemd/system/telegram-downloader.service; chmod +x start_service.sh; systemctl daemon-reload; systemctl enable telegram-downloader; systemctl restart telegram-downloader; echo DEPLOYMENT COMPLETE"

if errorlevel 1 (
    echo Failed to deploy
    exit /b 1
)

echo Cleaning up...
del "%TEMP%\telegram-downloader.tar.gz"

echo.
echo ✓ Deployment successful!
echo.
echo Service running at: http://155.103.71.153:8000
echo.
echo Next: SSH to server and edit /app/.env.production with your bot token
echo.

endlocal
