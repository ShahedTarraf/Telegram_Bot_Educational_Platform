# استكشاف الأخطاء على Railway

## الأخطاء الشائعة والحلول

### 1. Build Failed

#### الأعراض
```
Build failed: Error during build
```

#### الحلول
```bash
# تحقق من السجلات
railway logs

# تأكد من:
# 1. Dockerfile موجود
# 2. requirements.txt صحيح
# 3. جميع الملفات مرفوعة على GitHub
```

**الأسباب الشائعة:**
- ملف `Dockerfile` غير صحيح
- `requirements.txt` يحتوي على مكتبات غير متوفرة
- مشكلة في الإنترنت أثناء التثبيت

---

### 2. MongoDB Connection Timeout

#### الأعراض
```
MongoDB connection failed: serverSelectionTimeoutMS
Database not initialized
```

#### الحلول

**إذا كنت تستخدم MongoDB Atlas:**
```bash
# 1. تحقق من الـ connection string
# يجب أن يكون بهذا الشكل:
# mongodb+srv://username:password@cluster.mongodb.net/database

# 2. أضف IP Railway إلى whitelist
# في MongoDB Atlas:
# - اذهب إلى Network Access
# - أضف 0.0.0.0/0 (أو IP Railway المحدد)

# 3. تحقق من كلمة المرور
# تأكد من أن الأحرف الخاصة مُشفرة بشكل صحيح
```

**إذا كنت تستخدم MongoDB محلي:**
```bash
# استخدم MongoDB Atlas بدلاً منه
# MongoDB محلي لا يعمل على Railway
```

**اختبر الاتصال:**
```bash
curl https://your-app.up.railway.app/health/db
```

---

### 3. Bot Webhook Not Working

#### الأعراض
```
Bot doesn't respond to messages
Webhook returns 404
```

#### الحلول

**تحقق من الـ webhook:**
```bash
# احصل على معلومات الـ webhook
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo

# يجب أن ترى:
{
  "url": "https://your-app.up.railway.app/webhook",
  "has_custom_certificate": false,
  "pending_update_count": 0
}
```

**حدّث الـ webhook:**
```bash
# احذف الـ webhook القديم
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook

# أضف الـ webhook الجديد
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -d url=https://your-app-name.up.railway.app/webhook
```

**اختبر الـ webhook:**
```bash
# أرسل رسالة اختبار
curl -X POST https://your-app.up.railway.app/webhook \
  -H "Content-Type: application/json" \
  -d '{"update_id": 1, "message": {"text": "test"}}'
```

---

### 4. Admin Dashboard Not Loading

#### الأعراض
```
404 Not Found
Admin page shows error
```

#### الحلول

**تحقق من المتغيرات:**
```bash
railway variables

# تأكد من وجود:
# - SECRET_KEY
# - ADMIN_USERNAME
# - ADMIN_PASSWORD
# - ADMIN_EMAIL
```

**اختبر الـ dashboard:**
```bash
# اختبر الـ health check
curl https://your-app.up.railway.app/

# يجب أن ترى:
{
  "status": "ok",
  "service": "Educational Platform",
  "bot_webhook": true,
  "admin_dashboard": true,
  "database": "connected"
}
```

---

### 5. Database Not Connected

#### الأعراض
```
Database: disconnected
health/db returns error
```

#### الحلول

**اختبر الاتصال:**
```bash
curl https://your-app.up.railway.app/health/db

# يجب أن ترى:
{
  "status": "healthy",
  "database": "MongoDB",
  "connected": true
}
```

**إذا فشل:**
```bash
# عرض السجلات
railway logs -f

# ابحث عن:
# - MongoDB connection errors
# - Authentication errors
# - Network errors
```

---

### 6. Application Crashes

#### الأعراض
```
Application crashed
Status: crashed
```

#### الحلول

**عرض السجلات:**
```bash
railway logs -n 100
```

**ابحث عن:**
- `ERROR` - أخطاء حرجة
- `Exception` - استثناءات
- `Traceback` - تتبع الأخطاء

**الأسباب الشائعة:**
- متغير بيئة مفقود
- خطأ في الكود
- مشكلة في قاعدة البيانات

---

### 7. High Memory Usage

#### الأعراض
```
Memory usage: 95%+
Application slow
```

#### الحلول

**عرض الموارد:**
```bash
railway status
```

**تقليل الاستهلاك:**
```python
# استخدم connection pooling (بالفعل مُطبّق)
maxPoolSize=10
minPoolSize=1

# تجنب تحميل البيانات الكبيرة
# استخدم pagination
```

**ترقية الموارد:**
- في Railway dashboard
- اختر plan أعلى

---

### 8. Slow Response Times

#### الأعراض
```
Requests take 5+ seconds
Timeouts
```

#### الحلول

**قياس الأداء:**
```bash
# اختبر السرعة
time curl https://your-app.up.railway.app/

# يجب أن تكون أقل من 1 ثانية
```

**تحسين الأداء:**
```python
# استخدم caching
# قلل حجم الاستجابات
# استخدم async/await
```

**عرض السجلات:**
```bash
railway logs | grep "response time"
```

---

## أدوات التشخيص

### 1. عرض السجلات
```bash
# آخر 50 سطر
railway logs -n 50

# السجلات الحية
railway logs -f

# البحث عن كلمة
railway logs | grep "ERROR"

# حفظ السجلات
railway logs > logs.txt
```

### 2. عرض المتغيرات
```bash
# عرض جميع المتغيرات
railway variables

# حفظ المتغيرات
railway variables > env.txt
```

### 3. اختبار الاتصال
```bash
# الصحة العامة
curl https://your-app.up.railway.app/

# قاعدة البيانات
curl https://your-app.up.railway.app/health/db

# الـ webhook
curl https://your-app.up.railway.app/webhook

# مع التفاصيل
curl -v https://your-app.up.railway.app/
```

### 4. عرض الحالة
```bash
# الحالة العامة
railway status

# معلومات المشروع
railway projects

# معلومات البيئة
railway environments
```

---

## نصائح مفيدة

### 1. تفعيل Debug Mode
```bash
# في Railway dashboard
# عيّن DEBUG=True مؤقتاً
# سيعطيك معلومات أكثر في السجلات
```

### 2. إعادة النشر
```bash
# إذا لم تنجح المحاولة الأولى
railway redeploy
```

### 3. حذف وإعادة النشر
```bash
# إذا كانت المشكلة عميقة
railway remove
# ثم أنشئ مشروعاً جديداً
```

### 4. الاتصال بـ Support
- [Railway Support](https://railway.app/support)
- [Railway Discord](https://discord.gg/railway)

---

## قائمة التحقق السريعة

- [ ] هل جميع المتغيرات محددة؟
- [ ] هل MONGODB_URL صحيح؟
- [ ] هل BOT_TOKEN صحيح؟
- [ ] هل الـ webhook محدّث؟
- [ ] هل السجلات تظهر أخطاء؟
- [ ] هل الـ health check يعمل؟
- [ ] هل الـ database متصل؟

---

## الموارد الإضافية

- [Railway Troubleshooting](https://docs.railway.app/troubleshoot)
- [FastAPI Debugging](https://fastapi.tiangolo.com/deployment/concepts/)
- [MongoDB Connection Issues](https://docs.mongodb.com/manual/reference/connection-string/)

---

**تذكر**: السجلات هي أفضل صديق لك! 📋
