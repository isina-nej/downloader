#!/bin/bash

# Start the Telegram Downloader application

cd /app

# Load environment variables
export $(cat .env.production | grep -v '#' | xargs)

# Run the application
python3 -m src.main
