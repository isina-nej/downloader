# Quick Deployment Checklist

## بررسی‌های مهم قبل از배포

- [x] ChatAction import از `aiogram.enums` (نه `aiogram.types`)
- [x] aiogram version >= 3.10 در requirements.txt
- [x] Dockerfile با VOLUME برای storage و logs
- [x] .env.production با توکن و chat_id درست
- [x] server-setup.sh برای راه‌اندازی اولیه سرور
- [x] post-setup.sh برای تنظیم نهایی

## مراحل배포 (هر بار)

### روی سرور (اولین بار):

```bash
# 1. SSH به سرور
ssh root@155.103.71.153

# 2. اجرای راه‌اندازی
bash server-setup.sh

# 3. تبدیل به botuser
su - botuser
cd ~/bot-project

# 4. اپلود کد از محلی
# (برای هر جایی از terminal محلی‌ت)
scp -r /local/path/. botuser@155.103.71.153:~/bot-project/

# یا git clone
git clone <repo> .

# 5. ساخت Docker image
docker build -t telegram-bot:latest .

# 6. اجرای post-setup
cd ~
sudo bash post-setup.sh downloder.nodia.ir

# 7. شروع سرویس
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot

# 8. بررسی لاگ‌ها
docker logs -f telegram-bot
```

### بروزرسانی:

```bash
ssh botuser@155.103.71.153
cd ~/bot-project

# دریافت کد جدید
git pull origin main

# بیلد دوباره
docker build -t telegram-bot:latest .

# راه‌اندازی دوباره
sudo systemctl restart telegram-bot

# بررسی
docker logs -f telegram-bot
```

## دستورات مفید

```bash
# بررسی وضعیت
sudo systemctl status telegram-bot

# لاگ‌های realtime
docker logs -f telegram-bot

# اخرین 50 خط
docker logs --tail 50 telegram-bot

# متوقف کردن
sudo systemctl stop telegram-bot

# شروع دوباره
sudo systemctl restart telegram-bot

# درون container
docker exec -it telegram-bot bash

# حجم استفاده شده
du -sh ~/bot-project/storage/

# آزمایش سرویس وب
curl -k https://downloder.nodia.ir/health
```

## خطاهای شایع

| خطا | علت | راه‌حل |
|-----|------|--------|
| `ImportError: ChatAction` | ایمپورت از جای غلط | `from aiogram.enums import ChatAction` |
| `permission denied` | کاربر اشتباه | `su - botuser` |
| `docker: command not found` | Docker نصب نشده | `bash server-setup.sh` |
| `nginx: [error]` | تنظیم nginx اشتباه | `sudo nginx -t` و `post-setup.sh` |
| `Connection refused` | سرویس اجرا نشده | `sudo systemctl start telegram-bot` |

## نکات حرفه‌ای

✅ همیشه از `botuser` برای کار کن (نه root)
✅ فایل‌ها را در `/var/www/files` ذخیره کن
✅ لاگ‌ها را مانیتور کن: `journalctl -u telegram-bot -f`
✅ بک‌آپ منظم: `tar -czf backup-$(date +%s).tar.gz storage/`
✅ تست SSL: `sudo certbot renew --dry-run`

---

**Ready to deploy!** 🚀
