#!/bin/bash

# Simple startup script for local testing
# برای تست محلی

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "Starting Telegram Bot..."
echo ""

# Create venv if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

# Load env file
export $(cat .env | grep -v '#' | xargs)

# Start bot
echo "Bot token: ${TELEGRAM_BOT_TOKEN:0:20}..."
echo "Chat ID: $TELEGRAM_CHAT_ID"
echo ""
echo "Starting bot at http://127.0.0.1:8000"
echo "Press Ctrl+C to stop"
echo ""

python -m src.main
