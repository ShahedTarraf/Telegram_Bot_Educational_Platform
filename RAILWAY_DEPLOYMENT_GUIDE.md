# دليل نشر المشروع على Railway

## نظرة عامة
تم تحضير المشروع بالكامل للنشر على منصة Railway. جميع الملفات اللازمة موجودة والمنطق والواجهة محفوظة بالكامل.

## الملفات المضافة

### 1. **Dockerfile**
- يستخدم Python 3.11 slim
- يثبت جميع المكتبات من requirements.txt
- يتضمن health check للتحقق من صحة التطبيق
- معد للعمل على Railway

### 2. **Procfile**
- يحدد أمر تشغيل التطبيق
- يستخدم uvicorn مع المنفذ الديناميكي من Railway

### 3. **railway.json و railway.yaml**
- ملفات إعدادات Railway
- تحدد كيفية بناء ونشر التطبيق
- تتضمن متغيرات البيئة الأساسية

### 4. **.dockerignore**
- يستبعد الملفات غير الضرورية من Docker image
- يقلل حجم الصورة ويسرع النشر

### 5. **requirements.txt (محدث)**
- تحديث جميع المكتبات بإصدارات محددة
- إضافة `requests` للـ health check

## خطوات النشر على Railway

### الخطوة 1: إعداد حساب Railway
1. اذهب إلى [railway.app](https://railway.app)
2. سجل حساباً جديداً أو سجل الدخول
3. أنشئ مشروعاً جديداً

### الخطوة 2: ربط مستودع Git
```bash
# تأكد من أن المشروع في مستودع Git
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### الخطوة 3: نشر على Railway
**الطريقة 1: من خلال لوحة التحكم**
1. في Railway dashboard، اختر "New Project"
2. اختر "Deploy from GitHub"
3. اختر مستودعك
4. Railway سيكتشف تلقائياً Dockerfile ويبدأ النشر

**الطريقة 2: من خلال Railway CLI**
```bash
# تثبيت Railway CLI
npm install -g @railway/cli

# تسجيل الدخول
railway login

# نشر المشروع
railway up
```

### الخطوة 4: إعداد متغيرات البيئة
في لوحة تحكم Railway، أضف المتغيرات التالية:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ADMIN_ID=your_admin_id_here
MONGODB_URL=your_mongodb_connection_string
MONGODB_DB_NAME=educational_platform
SECRET_KEY=your_secret_key_here_minimum_32_characters
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password
ADMIN_EMAIL=admin@example.com
SHAP_CASH_NUMBER=+963999999999
HARAM_NUMBER=+963999999999
BOT_WEBHOOK_URL=https://your-railway-domain.up.railway.app/webhook
DASHBOARD_URL=https://your-railway-domain.up.railway.app
DEBUG=False
```

### الخطوة 5: تحديث webhook الـ Telegram Bot
بعد النشر بنجاح، ستحصل على URL مثل: `https://your-app-name.up.railway.app`

قم بتحديث webhook الـ bot:
```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://your-app-name.up.railway.app/webhook
```

أو استخدم Python:
```python
import requests

bot_token = "YOUR_BOT_TOKEN"
webhook_url = "https://your-app-name.up.railway.app/webhook"

response = requests.post(
    f"https://api.telegram.org/bot{bot_token}/setWebhook",
    json={"url": webhook_url}
)
print(response.json())
```

## المميزات المحفوظة

✅ **المنطق البرمجي**: جميع الوظائف محفوظة بالكامل
✅ **الواجهة**: لوحة التحكم الإدارية تعمل بدون تغيير
✅ **قاعدة البيانات**: MongoDB متصلة بنفس الطريقة
✅ **الإشعارات**: جدولة الإشعارات تعمل في الخلفية
✅ **Webhook**: يعمل بدون تغيير

## استكشاف الأخطاء

### عرض السجلات
في Railway dashboard:
1. اذهب إلى "Deployments"
2. اختر آخر deployment
3. انقر على "Logs" لرؤية السجلات الحية

### التحقق من الصحة
```bash
# التحقق من أن التطبيق يعمل
curl https://your-app-name.up.railway.app/

# التحقق من قاعدة البيانات
curl https://your-app-name.up.railway.app/health/db
```

### مشاكل شائعة

**المشكلة: MongoDB connection timeout**
- تأكد من أن MONGODB_URL صحيح
- تحقق من أن IP Railway مسموح في MongoDB Atlas (إذا كنت تستخدمه)

**المشكلة: Bot webhook لا يعمل**
- تأكد من أن BOT_WEBHOOK_URL صحيح
- تحقق من السجلات للأخطاء

**المشكلة: الصور والملفات لا تحمل**
- تأكد من أن جميع المسارات نسبية وليست مطلقة
- استخدم `/data` أو مجلد مؤقت للملفات

## نصائح الأداء

1. **استخدام MongoDB Atlas**: أسرع من MongoDB محلي
2. **تقليل حجم الصور**: استخدم صور مضغوطة
3. **تفعيل caching**: استخدم Redis إذا لزم الأمر
4. **مراقبة الموارد**: Railway توفر معلومات عن استخدام CPU والذاكرة

## الدعم

- [توثيق Railway](https://docs.railway.app)
- [توثيق FastAPI](https://fastapi.tiangolo.com)
- [توثيق Python Telegram Bot](https://python-telegram-bot.readthedocs.io)

---

**ملاحظة**: جميع الملفات الأصلية محفوظة. لم يتم حذف أو تعديل أي شيء من المنطق الأساسي.
