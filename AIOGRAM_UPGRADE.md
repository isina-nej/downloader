# Telegram Downloader Bot - Upgrade Guide

## تغییر به aiogram

بات به **aiogram** (نسخه 3) ارتقا یافت - یک لایبرری مدرن و async-first برای ربات‌های تلگرام.

### تفاوت‌ها و بهبودی‌ها:

✅ **async/await کامل** - بدون بلاک شدن، مدیریت بهتر ترافیک
✅ **Finite State Machine (FSM)** - برای فرم‌های چندمرحله‌ای
✅ **Middleware support** - برای middleware سفارشی
✅ **بهتر scalability** - هزاران کاربر همزمان
✅ **کد تمیزتر** - Pythonic و قابل نگهداری

### فایل‌های جدید:

- **`src/bot_aiogram.py`** - ربات جدید با aiogram
- **`requirements.txt`** - نیازمندی‌های به‌روز شده

### فایل‌های کهنه (برای reference):

- **`src/bot.py`** - ربات قدیمی با python-telegram-bot (کپی برای مرجع)

## نحوه استفاده:

```python
from src.bot_aiogram import AiogramBot

bot = AiogramBot()
await bot.start()
```

## مزایا در عمل:

1. **بهتر error handling** - message handlers معایب خود رو مدیریت می‌کنند
2. **FSM برای workflow** - مثلاً فرم آپلود فایل چند گام
3. **Rate limiting** - داخلی و مدرن‌تر
4. **کم‌تر memory** - async نسبت به blocking calls

## Migration Notes:

- قدیمی `telegram.ext.Application` → جدید `aiogram.Dispatcher`
- قدیمی `filters.Document.ALL` → جدید `F.document`
- قدیمی `await context.bot.get_file()` → جدید `await bot.get_file()`

## نسخه جدید شامل:

- ✨ Telegram API support کامل (Telegram Bot API 7.x)
- 🚀 Polling + Webhook support
- 📝 Detailed logging
- 🔐 عملکرد ایمن برای production

---

**نتیجه: ربات حالا خفن‌تر، تند‌تر و حرفه‌ای‌تره!** 🚀
