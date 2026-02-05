FROM python:3.12-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# نصب وابستگی‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد برنامه
COPY src/ src/
COPY .env.production .env

# صاحب فایل‌ها
RUN mkdir -p /app/storage /app/logs /app/files && \
    chmod -R 755 /app

# Volume برای ذخیره فایل‌ها و لاگ‌ها
VOLUME ["/app/storage", "/app/logs", "/app/files"]

# Port برای uvicorn
EXPOSE 8000

# اجرا
CMD ["python", "-m", "src.main"]
