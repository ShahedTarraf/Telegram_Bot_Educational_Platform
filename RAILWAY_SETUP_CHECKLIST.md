# قائمة التحقق من إعداد Railway

## قبل النشر ✓

- [ ] تحديث `.env.example` بجميع المتغيرات المطلوبة
- [ ] التأكد من أن جميع الملفات مرفوعة على GitHub
- [ ] اختبار التطبيق محلياً:
  ```bash
  python -m uvicorn server:app --host 0.0.0.0 --port 8000
  ```
- [ ] التأكد من أن MongoDB متصل بشكل صحيح

## إعداد Railway ✓

### 1. إنشاء المشروع
- [ ] اذهب إلى [railway.app](https://railway.app)
- [ ] انقر على "New Project"
- [ ] اختر "Deploy from GitHub"
- [ ] اختر المستودع الخاص بك
- [ ] انتظر انتهاء البناء الأول

### 2. إضافة متغيرات البيئة
في Railway dashboard، انقر على "Variables" وأضف:

```
TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_ID
MONGODB_URL
MONGODB_DB_NAME
SECRET_KEY
ADMIN_USERNAME
ADMIN_PASSWORD
ADMIN_EMAIL
SHAP_CASH_NUMBER
HARAM_NUMBER
BOT_WEBHOOK_URL
DASHBOARD_URL
DEBUG=False
```

### 3. الحصول على URL التطبيق
- [ ] انتظر انتهاء النشر
- [ ] انسخ URL التطبيق من Railway (مثل: `https://app-name.up.railway.app`)
- [ ] احفظه في مكان آمن

### 4. تحديث متغيرات البيئة
- [ ] حدّث `BOT_WEBHOOK_URL` إلى: `https://your-app-name.up.railway.app/webhook`
- [ ] حدّث `DASHBOARD_URL` إلى: `https://your-app-name.up.railway.app`

## اختبار النشر ✓

### 1. التحقق من الصحة
```bash
# اختبر الـ health check
curl https://your-app-name.up.railway.app/

# اختبر قاعدة البيانات
curl https://your-app-name.up.railway.app/health/db
```

### 2. عرض السجلات
- [ ] في Railway dashboard، انقر على "Deployments"
- [ ] اختر آخر deployment
- [ ] انقر على "Logs" وتحقق من عدم وجود أخطاء

### 3. تحديث webhook الـ Telegram
```bash
# استبدل YOUR_BOT_TOKEN و your-app-name بقيمك الفعلية
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://your-app-name.up.railway.app/webhook
```

### 4. اختبار الـ Bot
- [ ] أرسل `/start` للـ bot
- [ ] تحقق من أن الـ bot يرد بشكل صحيح
- [ ] اختبر بعض الأوامر الأساسية

## بعد النشر ✓

### المراقبة
- [ ] راقب السجلات بانتظام
- [ ] تحقق من استخدام الموارد (CPU، الذاكرة)
- [ ] تأكد من عدم وجود أخطاء متكررة

### الصيانة
- [ ] قم بتحديث المكتبات بانتظام
- [ ] احتفظ بنسخة احتياطية من قاعدة البيانات
- [ ] راقب الأداء والاستجابة

### التحديثات
عند تحديث الكود:
```bash
git add .
git commit -m "Update: description"
git push origin main
```
Railway سيكتشف التغييرات تلقائياً وسيعيد النشر.

## متغيرات البيئة المطلوبة

| المتغير | الوصف | مثال |
|---------|-------|------|
| `TELEGRAM_BOT_TOKEN` | رمز الـ bot من BotFather | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `TELEGRAM_ADMIN_ID` | معرّف الإدمن | `123456789` |
| `MONGODB_URL` | رابط قاعدة البيانات | `mongodb+srv://user:pass@cluster.mongodb.net/` |
| `MONGODB_DB_NAME` | اسم قاعدة البيانات | `educational_platform` |
| `SECRET_KEY` | مفتاح سري (32 حرف على الأقل) | `your-secret-key-here-minimum-32-characters` |
| `ADMIN_USERNAME` | اسم الإدمن | `admin` |
| `ADMIN_PASSWORD` | كلمة مرور الإدمن | `your-secure-password` |
| `ADMIN_EMAIL` | بريد الإدمن | `admin@example.com` |
| `SHAP_CASH_NUMBER` | رقم Shap Cash | `+963999999999` |
| `HARAM_NUMBER` | رقم Haram | `+963999999999` |
| `BOT_WEBHOOK_URL` | رابط webhook الـ bot | `https://your-app-name.up.railway.app/webhook` |
| `DASHBOARD_URL` | رابط لوحة التحكم | `https://your-app-name.up.railway.app` |
| `DEBUG` | وضع التصحيح | `False` |

## استكشاف الأخطاء

### الخطأ: "Build failed"
- تحقق من أن `Dockerfile` صحيح
- تحقق من أن `requirements.txt` يحتوي على جميع المكتبات
- عرض السجلات للتفاصيل

### الخطأ: "MongoDB connection timeout"
- تأكد من أن `MONGODB_URL` صحيح
- إذا كنت تستخدم MongoDB Atlas، أضف IP Railway إلى whitelist
- تحقق من أن قاعدة البيانات متاحة

### الخطأ: "Bot webhook not working"
- تأكد من أن `BOT_WEBHOOK_URL` صحيح
- تحقق من السجلات للأخطاء
- تأكد من أن الـ bot token صحيح

### الخطأ: "Admin dashboard not loading"
- تحقق من أن `SECRET_KEY` محدد
- تأكد من أن جميع متغيرات البيئة موجودة
- عرض السجلات للتفاصيل

## الخطوات التالية

1. **تحسين الأداء**
   - استخدم CDN للصور والملفات
   - أضف caching للبيانات الثابتة
   - استخدم Redis للجلسات

2. **الأمان**
   - استخدم HTTPS (Railway يوفره تلقائياً)
   - قم بتحديث كلمات المرور بانتظام
   - استخدم متغيرات البيئة للبيانات الحساسة

3. **المراقبة**
   - أضف تنبيهات للأخطاء
   - راقب استخدام الموارد
   - احتفظ بسجلات للأداء

---

**ملاحظة**: إذا واجهت أي مشاكل، تحقق من السجلات في Railway dashboard أولاً.
