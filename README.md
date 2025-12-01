# Telegram Bot Educational Platform

منصة تعليمية متكاملة مبنية على **Telegram Bot** مع لوحة تحكم **FastAPI** وقاعدة بيانات **MongoDB/Beanie**.

## المتطلبات

- Python 3.10+
- MongoDB (محلي أو MongoDB Atlas)
- حساب Telegram Bot Token

## التثبيت المحلي

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## تشغيل البوت محلياً

```bash
venv\Scripts\activate
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

- التطبيق يعمل على: `http://localhost:8000`
- صفحة التوثيق (Swagger): `http://localhost:8000/docs`
- لوحة التحكم: `http://localhost:8000/admin`

## النشر على Railway

#)
