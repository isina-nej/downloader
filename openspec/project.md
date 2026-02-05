# Project Context

## Purpose
Telegram File Downloader Bot - A secure, high-performance bridge between Telegram and a private storage server.
The bot receives files from users, downloads them securely, stores them with UUID-based identification,
and generates shareable HTTP/S download links. Designed for content sharing, archiving, and web distribution.

## Tech Stack
- **Language**: Python 3.10+ with type hints
- **Bot Framework**: python-telegram-bot[all] 20.5 (async/await)
- **Web Framework**: FastAPI 0.104.1 (async HTTP)
- **Async Client**: httpx 0.25.2 (streaming)
- **Database**: SQLite with SQLAlchemy ORM
- **Code Quality**: black, flake8, pytest-asyncio
- **Deployment**: PM2 or systemd

## Project Conventions

### Code Style
- **Format**: black (line-length=100)
- **Linting**: flake8 (ignore E203, W503)
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style (parameter, return, raises sections)
- **Naming**: snake_case (functions/vars), PascalCase (classes)
- **Imports**: Organized (stdlib, third-party, local) separated by blank lines

### Architecture Patterns
- **Async-First Design**: All I/O is non-blocking (async/await)
- **Streaming**: Files never fully loaded in memory
- **Modular Structure**:
  - `bot.py`: Telegram interaction only
  - `web.py`: HTTP API endpoints
  - `storage.py`: File persistence layer
  - `database.py`: ORM models
  - `config.py`: Environment configuration
- **Security**: UUID v4 for file IDs, env-based secrets, rate limiting
- **Error Handling**: Graceful fallbacks with structured logging

### Testing Strategy
- pytest + pytest-asyncio for async testing
- 80%+ code coverage target
- Mock Telegram API for unit tests
- Integration tests for end-to-end flows
- Load testing for concurrent operations

### Git Workflow
- Branch naming: `feature/x`, `bugfix/x`, `docs/x`
- Commit format: `[type]: brief description`
- OpenSpace proposal required before implementation
- All changes must pass linting, type checking, and tests

## Domain Context
- **Telegram API**: Uses polling (development) / webhooks (production)
- **File Streaming**: Direct from Telegram servers to disk storage
- **User Model**: Telegram IDs only (no registration)
- **Security Model**: URL obfuscation via UUID, not password-based
- **Deployment**: Ubuntu/Debian with systemd or PM2
- **Rate Limiting**: Per-user sliding window (10 req/min default)
- **File Lifecycle**: TTL-based with auto-cleanup (30 days default)

## Important Constraints
- **Max File Size**: 2GB (Telegram non-premium limit)
- **Storage**: Disk space is finite (monitor via /stats)
- **Rate Limit**: 10 requests per minute per user
- **File TTL**: 30 days default (configurable)
- **Token Security**: .env only, never hardcode
- **Auth Model**: URL-based (UUID), not token-based
- **Bandwidth**: Monitor egress (potential costs)

## External Dependencies
- **Telegram Bot API**: https://api.telegram.org/
- **Telegram File Streaming**: getFile + download
- **python-telegram-bot**: Official community wrapper
- **FastAPI**: Starlette-based async framework
- **SQLAlchemy**: Database abstraction layer
