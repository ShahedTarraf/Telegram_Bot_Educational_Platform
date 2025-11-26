# Telegram Bot Educational Platform

منصة تعليمية متكاملة مبنية على **Telegram Bot** مع لوحة تحكم **FastAPI** وقاعدة بيانات **MongoDB/Beanie**.

## المتطلبات

- Python 3.10+
- MongoDB يعمل محلياً على `mongodb://localhost:27017`
- حساب Telegram Bot Token

## التثبيت

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## تشغيل البوت

```bash
venv\Scripts\activate
python run_bot.py
```

## تشغيل لوحة التحكم (Dashboard)

```bash
venv\Scripts\activate
python run_dashboard.py
```

- لوحة التحكم تعمل عادة على: `http://localhost:8000`
- صفحة التوثيق (Swagger): `http://localhost:8000/docs`

## المتغيرات الحساسة

- ملف `.env` يحتوي على:
  - `TELEGRAM_BOT_TOKEN`
  - `MONGODB_URL`
  - إعدادات أخرى حساسة

> **مهم:** ملف `.env` مُستثنى في `.gitignore` ولن يتم رفعه إلى GitHub.
