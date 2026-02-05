# Telegram File Downloader

A high-performance Telegram bot that downloads files to a private storage server and generates shareable URLs.

## Features

- **Async File Streaming**: Non-blocking downloads using httpx and aiohttp
- **Secure Storage**: UUID-based file identification to prevent ID guessing
- **Web Server**: FastAPI endpoint for direct file downloads
- **Database Tracking**: SQLite for file metadata and ownership
- **Rate Limiting**: Built-in protection against abuse
- **Automatic Cleanup**: Configurable file retention with automatic deletion
- **Structured Logging**: Detailed logs for monitoring and debugging
- **Support for Multiple File Types**: Documents, videos, and audio files

## System Architecture

```
┌─────────────────────┐
│  Telegram Users     │
└──────────┬──────────┘
           │ (files)
           ▼
┌─────────────────────┐
│  TelegramBot        │ ← Receives files from Telegram
│  (async/polling)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  StorageManager     │ ← Streams files to disk
│  (UUID based)       │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────────┐
│Storage │  │   Database   │ ← Tracks metadata
│Disk    │  │  (SQLite)    │
└────────┘  └──────────────┘
    ▲
    │ (HTTP GET)
    │
┌─────────────────────┐
│  FastAPI Web Server │
│ (/download/{id})    │
└─────────────────────┘
    ▲
    │ (user downloads)
    │
┌─────────────────────┐
│  Web Browsers       │
└─────────────────────┘
```

## Setup

### Prerequisites

- Python 3.10+
- pip or conda
- A Telegram Bot Token (from @BotFather)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram-downloader
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Create a `.env` file with your settings:
```
TELEGRAM_BOT_TOKEN=your_token_here
DOWNLOAD_URL_BASE=https://your-domain.com
```

## Configuration

Edit `.env` file with the following variables:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_for_notifications

# Server
STORAGE_PATH=./storage
MAX_FILE_SIZE=2147483648              # 2GB in bytes
DOWNLOAD_URL_BASE=https://yourdomain.com
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Database
DATABASE_URL=sqlite:///./telegram_downloader.db

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10

# File Retention
FILE_RETENTION_DAYS=30

# Logging
LOG_LEVEL=INFO
```

## Usage

### Start the Application

```bash
python -m src.main
```

This will start:
- **Telegram Bot**: Polling for messages
- **Web Server**: Running on http://localhost:8000

### Bot Commands

- `/start` - Show welcome message
- `/help` - Show help information
- `/stats` - Show storage statistics

### API Endpoints

#### Download File
```
GET /download/{file_id}
```
Downloads the file associated with the given file ID.

#### Health Check
```
GET /health
```
Returns server status and storage statistics.

#### Storage Stats
```
GET /stats
```
Returns storage statistics (total files, size, available space).

#### Root Endpoint
```
GET /
```
Returns service information.

#### Cleanup (Admin)
```
POST /cleanup
```
Trigger cleanup of files older than retention period.

## Project Structure

```
telegram-downloader/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main entry point
│   ├── config.py            # Configuration management
│   ├── bot.py               # Telegram bot handler
│   ├── web.py               # FastAPI web server
│   ├── storage.py           # File storage manager
│   ├── database.py          # Database models
│   ├── logging_config.py    # Logging setup
│   └── rate_limiter.py      # Rate limiting
├── storage/                 # Downloaded files storage
├── logs/                    # Application logs
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project metadata
├── .env.example            # Example environment variables
└── README.md               # This file
```

## Performance Notes

- **Streaming**: Files are streamed directly to disk, avoiding RAM overload
- **Async I/O**: All I/O operations are non-blocking
- **UUID-based IDs**: Prevents brute-force attacks on file IDs
- **Rate Limiting**: Default 10 requests per minute per user
- **Auto-cleanup**: Old files automatically deleted based on retention policy

## Security Considerations

1. **Token Security**: Bot token stored in .env, never committed to Git
2. **File ID Obfuscation**: Using UUID v4 makes guessing impossible
3. **Rate Limiting**: Prevents abuse and ensures fair resource usage
4. **Input Validation**: File size limits and format validation
5. **Access Logging**: All downloads are logged for audit trails

## Monitoring & Maintenance

### Logs

Logs are stored in the `logs/` directory:
- `bot.log` - Bot operations
- `web.log` - Web server operations
- `storage.log` - Storage operations

### Storage Management

Check available storage:
```bash
curl http://localhost:8000/stats
```

Manually trigger cleanup:
```bash
curl -X POST http://localhost:8000/cleanup
```

## Development

### Code Quality

Run linting:
```bash
flake8 src/
```

Format code:
```bash
black src/
```

### Testing

Run tests (when available):
```bash
pytest
```

## Deployment

### Using PM2

```bash
npm install -g pm2
pm2 start "python -m src.main" --name telegram-downloader
pm2 save
pm2 startup
```

### Using systemd

Create `/etc/systemd/system/telegram-downloader.service`:
```ini
[Unit]
Description=Telegram File Downloader
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/path/to/telegram-downloader
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m src.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-downloader
sudo systemctl start telegram-downloader
```

## Troubleshooting

### Bot not responding
- Check `TELEGRAM_BOT_TOKEN` in `.env`
- Verify bot is running: `python -m src.main`
- Check `logs/bot.log` for errors

### Download link not working
- Ensure web server is running on configured port
- Verify `DOWNLOAD_URL_BASE` matches your domain
- Check file hasn't expired (default 30 days)

### Storage space issues
- Check available disk space: `curl http://localhost:8000/stats`
- Reduce `FILE_RETENTION_DAYS` in .env
- Manually delete old files from `storage/` directory

## Contributing

1. Create a feature branch
2. Make your changes
3. Run linting and tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check existing issues on GitHub
2. Review logs in `logs/` directory
3. Check configuration in `.env` file

## Roadmap

- [ ] User authentication for download links
- [ ] Custom retention policies per user
- [ ] Web UI for file management
- [ ] Download statistics dashboard
- [ ] S3 storage backend support
- [ ] Email notifications on upload
- [ ] Webhook integration for external systems
