# فارسی: راهنمای استفاده از ربات تلگرامی

## نحوه استفاده

### شروع سریع

1. **دانلود و نصب وابستگی‌ها**:
```bash
pip install -r requirements.txt
```

2. **تنظیم محیط**:
```bash
cp .env.example .env
```

3. **اجرای ربات**:
```bash
python -m src.main
```

### دستورات ربات

#### /start
- **توضیح**: پیام خوشامدگویی را نمایش می‌دهد
- **استفاده**: کاربر جدید باید این دستور را اجرا کند

#### /help
- **توضیح**: راهنمای کامل استفاده از ربات
- **شامل**:
  - نحوه ارسال فایل
  - محدودیت‌های اندازه
  - سیاست نگهداری فایل‌ها
  - دستورات موجود

#### /stats
- **توضیح**: آمار استفاده از فضای ذخیره‌سازی
- **نمایش**:
  - تعداد فایل‌های ذخیره‌شده
  - حجم کل استفاده‌شده
  - فضای دسترس‌پذیر

### ارسال فایل

1. کاربر فایل (سند، ویدیو، یا صوت) را به ربات ارسال می‌کند
2. ربات پیام "در حال پردازش..." را نمایش می‌دهد
3. فایل به سرور دانلود می‌شود
4. یک شناسه منحصر به فرد (UUID) برای فایل ایجاد می‌شود
5. ربات لینک دانلود را برای کاربر ارسال می‌کند

### مثال واقعی

```
کاربر: [ارسال یک فایل PDF 50MB]
ربات: ⏳ Processing document.pdf...
      Size: 50.25 MB
      
ربات: ✅ File Uploaded Successfully!

     📁 File: document.pdf
     💾 Size: 50.25 MB
     🔗 Link: https://yourdomain.com/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890

     The link will be available for 30 days.
```

---

# English: User Guide

## Quick Start

### Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Setup environment**:
```bash
cp .env.example .env
```

3. **Run the bot**:
```bash
python -m src.main
```

### Bot Commands

#### /start
- **Description**: Shows welcome message
- **When**: Run when first starting with the bot

#### /help
- **Description**: Shows comprehensive usage guide
- **Includes**:
  - How to send files
  - Size limits
  - File retention policy
  - Available commands

#### /stats
- **Description**: Shows storage statistics
- **Displays**:
  - Total files stored
  - Total storage used
  - Available disk space

### Sending Files

1. User sends a file (document, video, or audio) to the bot
2. Bot shows "Processing..." message
3. Bot downloads file to secure server
4. Unique ID (UUID) is generated for the file
5. Bot sends download link to user

### Real Example

```
User: [Sends a 50MB PDF file]
Bot: ⏳ Processing document.pdf...
     Size: 50.25 MB
     
Bot: ✅ File Uploaded Successfully!

    📁 File: document.pdf
    💾 Size: 50.25 MB
    🔗 Link: https://yourdomain.com/download/a1b2c3d4-e5f6-7890-abcd-ef1234567890

    The link will be available for 30 days.
```

## System Limits

| Limit | Value | Notes |
|-------|-------|-------|
| Max File Size | 2GB | Telegram limitation for non-premium users |
| Files Per Minute | 10 | Rate limiting per user |
| File Retention | 30 days | Auto-deleted after this period |
| Concurrent Users | 1000+ | System capacity dependent |

## Troubleshooting

### Bot not responding
- Verify bot token in `.env`
- Check bot is running: `python -m src.main`
- Review logs: `cat logs/bot.log`

### Download link not working
- Ensure link is not expired (30 days max)
- Verify web server is running
- Check `DOWNLOAD_URL_BASE` configuration

### Storage full
- Check available space: `curl http://localhost:8000/stats`
- Reduce `FILE_RETENTION_DAYS` in `.env`
- Manually delete old files from `storage/` directory

---

# فارسی: دستورالعمل توسعه‌دهندگان

## ساختار پروژه

```
src/
├── main.py              # نقطه ورودی اصلی
├── config.py            # مدیریت تنظیمات
├── bot.py               # ربات تلگرام
├── web.py               # سرور وب FastAPI
├── storage.py           # مدیریت فایل‌ها
├── database.py          # مدل‌های دیتابیس
├── logging_config.py    # تنظیمات لاگ‌گذاری
└── rate_limiter.py      # محدود‌کننده نرخ درخواست

storage/                 # ذخیره‌سازی فایل‌ها
logs/                    # فایل‌های لاگ
```

## OpenSpace Implementation

این پروژه از استاندارد **OpenSpace** برای توسعه پیروی می‌کند:

### مستندسازی

- **[openspec/project.md](openspec/project.md)**: تنظیمات و قوانین پروژه
- **[openspec/prd.1.1.md](openspec/prd.1.1.md)**: مشخصات محصول
- **[openspec/specs/](openspec/specs/)**: مستندسازی قابلیت‌ها

### ایجاد تغییرات

قبل از کدنویسی:
1. بررسی `openspec/specs/` برای مستندسازی فعلی
2. ایجاد proposal.md در `openspec/changes/[change-id]/`
3. نوشتن design.md (در صورت نیاز)
4. تایید proposal قبل از اجرا

### کد زنی

```bash
# نصب وابستگی‌های توسعه
pip install -r requirements.txt

# Format کدها
black src/

# Linting
flake8 src/

# Type checking (اختیاری)
mypy src/

# تست‌ها (در توسعه)
pytest
```

## Architecture

```
┌─────────────────────┐
│  Telegram Users     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  TelegramBot        │ ← Async file handling
│  (polling)          │   Rate limiting
└──────────┬──────────┘   Command processing
           │
           ▼
┌─────────────────────┐
│  StorageManager     │ ← UUID generation
│  (streaming I/O)    │   Chunk writing
└──────────┬──────────┘   Size validation
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────────┐
│Storage │  │   SQLite     │ ← Metadata tracking
│Disk    │  │   Database   │   Owner tracking
└────────┘  └──────────────┘
    ▲
    │ (HTTP streaming)
    │
┌─────────────────────┐
│  FastAPI Web Server │
│  /download/{id}     │ ← Async responses
│  /health            │   Error handling
│  /stats             │   Cleanup triggers
└─────────────────────┘
```

---

# English: Developer Guide

## Project Structure

```
src/
├── main.py              # Main entry point
├── config.py            # Configuration management
├── bot.py               # Telegram bot handler
├── web.py               # FastAPI web server
├── storage.py           # File management
├── database.py          # Database models
├── logging_config.py    # Logging setup
└── rate_limiter.py      # Rate limiting

storage/                 # File storage
logs/                    # Log files
```

## OpenSpace Implementation

This project follows **OpenSpace** standards:

### Documentation

- **[openspec/project.md](openspec/project.md)**: Project settings and conventions
- **[openspec/prd.1.1.md](openspec/prd.1.1.md)**: Product specifications
- **[openspec/specs/](openspec/specs/)**: Capability documentation

### Creating Changes

Before coding:
1. Check `openspec/specs/` for current documentation
2. Create proposal.md in `openspec/changes/[change-id]/`
3. Write design.md (if needed)
4. Get proposal approval before implementation

### Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Format code
black src/

# Linting
flake8 src/

# Type checking (optional)
mypy src/

# Tests (in development)
pytest
```

## Architecture

```
┌─────────────────────┐
│  Telegram Users     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  TelegramBot        │ ← Async file handling
│  (polling)          │   Rate limiting
└──────────┬──────────┘   Command processing
           │
           ▼
┌─────────────────────┐
│  StorageManager     │ ← UUID generation
│  (streaming I/O)    │   Chunk writing
└──────────┬──────────┘   Size validation
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────────┐
│Storage │  │   SQLite     │ ← Metadata tracking
│Disk    │  │   Database   │   Owner tracking
└────────┘  └──────────────┘
    ▲
    │ (HTTP streaming)
    │
┌─────────────────────┐
│  FastAPI Web Server │
│  /download/{id}     │ ← Async responses
│  /health            │   Error handling
│  /stats             │   Cleanup triggers
└─────────────────────┘
```

## Key Design Decisions

1. **Async-First**: All I/O is non-blocking (async/await)
2. **Streaming**: Files never loaded fully into memory
3. **UUID-Based IDs**: Prevents brute-force attacks
4. **Rate Limiting**: Per-user sliding window
5. **Modular Design**: Clear separation of concerns
6. **SQLite**: Lightweight, file-based database
7. **Structured Logging**: JSON logs for monitoring

## Performance Optimizations

1. **Streaming Downloads**: Chunks written directly to disk
2. **Async Client**: Using httpx for concurrent requests
3. **Connection Pooling**: Reuse DB connections
4. **Index Optimization**: Database queries optimized
5. **Memory Limits**: Explicit buffer sizes (5MB chunks)
6. **Cleanup Batching**: Process multiple deletes efficiently

## Security Features

1. **UUID Randomization**: 2^122 possible IDs
2. **Token Protection**: Stored in .env only
3. **Rate Limiting**: 10 requests per minute per user
4. **Input Validation**: File size and format checks
5. **Error Masking**: No sensitive info in error messages
6. **Audit Logging**: All operations logged

## Deployment Options

### Development
```bash
python -m src.main
```

### PM2
```bash
npm install -g pm2
pm2 start "python -m src.main" --name telegram-downloader
pm2 save
```

### Systemd
```bash
sudo systemctl start telegram-downloader
sudo systemctl enable telegram-downloader
```

### Docker (Future)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ src/
CMD ["python", "-m", "src.main"]
```
