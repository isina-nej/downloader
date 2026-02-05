# Telegram Bot Capability

**Capability ID**: `telegram-bot`  
**Version**: 1.0.0  
**Status**: Active  

## Overview

The Telegram Bot module provides asynchronous interaction with Telegram users. It receives files,
documents, videos, and audio through the Telegram Bot API and coordinates with storage and web
modules to generate shareable download links.

## Architecture

```
User (Telegram Client)
        ↓
    Bot Message
        ↓
TelegramBot Handler
        ↓
    ├─→ Document Handler
    ├─→ Video Handler
    ├─→ Audio Handler
    └─→ Command Handler (/start, /help, /stats)
        ↓
StorageManager (async file streaming)
        ↓
Database (metadata tracking)
        ↓
Bot Response (URL to user)
```

## Requirements

### Requirement: Handle File Uploads
**ID**: REQ-BOT-001  
**Priority**: Critical  
**Status**: Implemented  

The bot must accept file uploads (documents, videos, audio) from Telegram users.

#### Scenario: User uploads a document
```
Given: User sends a document file
When: Bot receives the file message
Then: Bot acknowledges receipt with "Processing..." message
And: Bot streams file to storage manager
And: Bot generates download link
And: Bot sends link to user
```

#### Scenario: File exceeds size limit
```
Given: User sends a 3GB file
When: Bot receives the file message
Then: Bot rejects with error message
And: Bot notifies user of 2GB limit
And: No file is stored
```

### Requirement: Command Handling
**ID**: REQ-BOT-002  
**Priority**: High  
**Status**: Implemented  

The bot must support user commands for help, status, and statistics.

#### Scenario: User requests help
```
Given: User sends /help command
When: Bot processes the command
Then: Bot sends formatted help message
And: Help includes usage instructions
And: Help includes file size limits
And: Help includes retention policy
```

#### Scenario: User requests statistics
```
Given: User sends /stats command
When: Bot processes the command
Then: Bot queries storage statistics
And: Bot shows total files, size, available space
And: Statistics are current and accurate
```

### Requirement: Rate Limiting
**ID**: REQ-BOT-003  
**Priority**: High  
**Status**: Implemented  

The bot must enforce per-user rate limiting to prevent abuse.

#### Scenario: User exceeds rate limit
```
Given: User has sent 10 files in 1 minute
When: User attempts to send 11th file
Then: Bot rejects with rate limit message
And: Bot suggests waiting
And: Request is logged
```

### Requirement: Error Handling
**ID**: REQ-BOT-004  
**Priority**: High  
**Status**: Implemented  

The bot must handle errors gracefully and inform users.

#### Scenario: Storage fails
```
Given: Storage service is unavailable
When: User sends a file
Then: Bot shows processing message
And: Storage operation fails
And: Bot notifies user of failure
And: Error is logged with details
```

### Requirement: Async File Streaming
**ID**: REQ-BOT-005  
**Priority**: Critical  
**Status**: Implemented  

File downloads must be non-blocking and stream-based.

#### Scenario: Download large file efficiently
```
Given: User sends 500MB file
When: Bot downloads from Telegram
Then: File is streamed in chunks
And: Memory usage stays under 50MB
And: Download completes in reasonable time
And: Partial download is cleaned up on error
```

## Implementation Details

### Module Location
- **File**: [src/bot.py](../../../src/bot.py)
- **Class**: `TelegramBot`
- **Factory**: `create_bot()`

### Public Interface

```python
class TelegramBot:
    async def start() -> None
    async def stop() -> None
    def run_polling() -> None
    
    # Private handlers
    async def _process_file(update, context, file_obj) -> None
    async def handle_document(update, context) -> None
    async def handle_video(update, context) -> None
    async def handle_audio(update, context) -> None
```

### Dependencies
- `telegram` (python-telegram-bot)
- `src.storage.storage_manager`
- `src.rate_limiter.rate_limiter`
- `src.logging_config.bot_logger`

### Configuration
- `TELEGRAM_BOT_TOKEN`: Bot API token (from @BotFather)
- `RATE_LIMIT_PER_MINUTE`: Max files per user per minute (default: 10)
- `MAX_FILE_SIZE`: Maximum uploadable file size in bytes (default: 2GB)

## Performance Characteristics

| Metric | Target | Achieved |
|--------|--------|----------|
| File Download (100MB) | < 30s | ~20s (varies with network) |
| URL Generation | < 1s | ~0.1s |
| Message Response | < 2s | ~1s |
| Concurrent Users | 100+ | Limited by Telegram rate limits |
| Memory per File | < 50MB | < 30MB (streaming) |

## Security Considerations

- Token stored in `.env`, never logged
- Rate limiting prevents denial of service
- User IDs logged for audit trail
- File size validation before processing
- Graceful handling of malformed requests
- Timeout handling for stuck connections

## Testing

### Unit Tests
- Command handler tests with mocked Telegram API
- File validation tests (size, format)
- Rate limiter integration tests
- Error scenario tests

### Integration Tests
- End-to-end file upload and link generation
- Multiple concurrent file uploads
- Rate limiting across user IDs
- Cleanup of failed partial uploads

## Deployment Notes

- Runs in polling mode (development) or webhooks (production)
- Requires network connectivity to Telegram API
- Single instance recommended (polling mode handles concurrency)
- Graceful shutdown supported via SIGINT/SIGTERM
