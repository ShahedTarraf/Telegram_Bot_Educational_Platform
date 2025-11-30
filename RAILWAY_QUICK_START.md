# البدء السريع مع Railway

## في 5 دقائق

### الخطوة 1: ادفع الكود (1 دقيقة)
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### الخطوة 2: أنشئ مشروع Railway (2 دقيقة)
1. اذهب إلى [railway.app](https://railway.app)
2. انقر "New Project"
3. اختر "Deploy from GitHub"
4. اختر المستودع الخاص بك
5. انتظر انتهاء البناء

### الخطوة 3: أضف المتغيرات (1 دقيقة)
في Railway dashboard:
```
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_ADMIN_ID=your_id
MONGODB_URL=your_mongodb_url
MONGODB_DB_NAME=educational_platform
SECRET_KEY=your_secret_key_32_chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password
ADMIN_EMAIL=admin@example.com
SHAP_CASH_NUMBER=+963999999999
HARAM_NUMBER=+963999999999
DEBUG=False
```

### الخطوة 4: حدّث الـ Webhook (1 دقيقة)
```bash
# احصل على URL من Railway (مثل: your-app-name.up.railway.app)
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -d url=https://your-app-name.up.railway.app/webhook
```

## تم! ✅

تطبيقك يعمل الآن على Railway!

## اختبر التطبيق

```bash
# الصحة العامة
curl https://your-app-name.up.railway.app/

# قاعدة البيانات
curl https://your-app-name.up.railway.app/health/db

# لوحة التحكم
https://your-app-name.up.railway.app/admin
```

## المشاكل الشائعة

### MongoDB لا تتصل
- تأكد من أن MONGODB_URL صحيح
- إذا كنت تستخدم MongoDB Atlas، أضف IP Railway إلى whitelist

### الـ Bot لا يرد
- تحقق من أن BOT_WEBHOOK_URL صحيح
- عرض السجلات: `railway logs`

### الصفحة لا تحمل
- تحقق من المتغيرات: `railway variables`
- عرض السجلات: `railway logs -f`

## الأوامر المفيدة

```bash
# عرض السجلات
railway logs

# السجلات الحية
railway logs -f

# المتغيرات
railway variables

# الحالة
railway status

# إعادة النشر
railway redeploy
```

## الخطوات التالية

- 📖 اقرأ [RAILWAY_DEPLOYMENT_GUIDE.md](./RAILWAY_DEPLOYMENT_GUIDE.md) للتفاصيل
- ✅ استخدم [RAILWAY_SETUP_CHECKLIST.md](./RAILWAY_SETUP_CHECKLIST.md) للتحقق
- 🔧 اطلع على [RAILWAY_COMMANDS.md](./RAILWAY_COMMANDS.md) للأوامر
- 💡 اقرأ [RAILWAY_BEST_PRACTICES.md](./RAILWAY_BEST_PRACTICES.md) للنصائح

---

**تم النشر بنجاح!** 🚀
