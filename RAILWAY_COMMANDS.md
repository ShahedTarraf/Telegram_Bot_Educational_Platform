# أوامر Railway المفيدة

## تثبيت Railway CLI

```bash
# على Windows (باستخدام npm)
npm install -g @railway/cli

# أو باستخدام Homebrew (على macOS/Linux)
brew install railway
```

## الأوامر الأساسية

### تسجيل الدخول
```bash
railway login
```

### إنشاء مشروع جديد
```bash
railway init
```

### نشر المشروع
```bash
railway up
```

### عرض السجلات
```bash
railway logs
```

### عرض المتغيرات
```bash
railway variables
```

### تعيين متغير بيئة
```bash
railway variables set VARIABLE_NAME value
```

### عرض حالة النشر
```bash
railway status
```

### فتح لوحة التحكم
```bash
railway open
```

## أوامر مفيدة للتطوير

### اختبار محلي
```bash
# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل التطبيق
python -m uvicorn server:app --host 0.0.0.0 --port 8000

# أو استخدام reload للتطوير
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### بناء Docker محلي
```bash
# بناء الصورة
docker build -t educational-platform .

# تشغيل الحاوية
docker run -p 8000:8000 --env-file .env educational-platform
```

## أوامر متقدمة

### عرض معلومات المشروع
```bash
railway projects
```

### اختيار مشروع
```bash
railway projects select
```

### عرض البيئات
```bash
railway environments
```

### اختيار بيئة
```bash
railway environments select
```

### إعادة النشر
```bash
railway redeploy
```

### إيقاف التطبيق
```bash
railway stop
```

### حذف النشر
```bash
railway remove
```

## أوامر Telegram Bot

### تحديث webhook
```bash
# استبدل YOUR_BOT_TOKEN و your-app-name بقيمك
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook \
  -d url=https://your-app-name.up.railway.app/webhook
```

### الحصول على معلومات webhook
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

### حذف webhook
```bash
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
```

### اختبار الـ bot
```bash
# أرسل رسالة اختبار
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage \
  -d chat_id=<YOUR_CHAT_ID> \
  -d text="Test message"
```

## أوامر MongoDB

### الاتصال بـ MongoDB Atlas
```bash
# استخدم الـ connection string من MongoDB Atlas
# يجب أن يكون بهذا الشكل:
# mongodb+srv://username:password@cluster.mongodb.net/database_name
```

### اختبار الاتصال
```bash
curl https://your-app-name.up.railway.app/health/db
```

## أوامر مراقبة الأداء

### عرض استخدام الموارد
```bash
railway status
```

### عرض السجلات مع التصفية
```bash
# عرض آخر 100 سطر
railway logs -n 100

# عرض السجلات الحية
railway logs -f
```

## استكشاف الأخطاء

### عرض الأخطاء
```bash
railway logs | grep ERROR
```

### عرض التحذيرات
```bash
railway logs | grep WARNING
```

### عرض معلومات الاتصال
```bash
railway logs | grep "MongoDB\|Telegram\|webhook"
```

## نصائح مفيدة

### حفظ المتغيرات محلياً
```bash
# تحميل المتغيرات من Railway
railway variables > .env.railway.local

# استخدمها محلياً
export $(cat .env.railway.local | xargs)
```

### مقارنة المتغيرات
```bash
# عرض الفروقات بين .env و .env.railway
diff .env .env.railway
```

### إعادة تشغيل التطبيق
```bash
# في Railway dashboard، انقر على "Redeploy"
# أو استخدم CLI:
railway redeploy
```

## الموارد الإضافية

- [توثيق Railway CLI](https://docs.railway.app/cli/commands)
- [توثيق Railway Dashboard](https://docs.railway.app/dashboard)
- [توثيق متغيرات البيئة](https://docs.railway.app/develop/variables)
- [استكشاف الأخطاء](https://docs.railway.app/troubleshoot)

---

**ملاحظة**: استبدل `your-app-name` و `YOUR_BOT_TOKEN` بقيمك الفعلية.
