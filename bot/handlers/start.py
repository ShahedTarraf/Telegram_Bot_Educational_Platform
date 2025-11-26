"""
Start Handler - Registration
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from database.models.user import User
from bot.keyboards.main_keyboards import get_main_menu_keyboard, get_admin_menu_keyboard, get_cancel_button
from config.settings import settings


# Conversation states
ASKING_NAME, ASKING_PHONE, ASKING_EMAIL = range(3)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    telegram_id = update.effective_user.id
    
    # Check if user is admin FIRST
    is_admin = telegram_id == settings.TELEGRAM_ADMIN_ID
    
    # Check if user already registered
    user = await User.find_one(User.telegram_id == telegram_id)
    
    if user:
        # User already registered
        await user.update_last_active()
        
        if is_admin:
            keyboard = get_admin_menu_keyboard()
            text = f"مرحباً بعودتك يا {user.full_name}! 👋\n\n🔑 **لوحة الأدمن**\n\nاستخدم القائمة بالأسفل:"
        else:
            keyboard = get_main_menu_keyboard()
            text = f"مرحباً بعودتك يا {user.full_name}! 👋\n\nاستخدم القائمة بالأسفل للتصفح:"
        
        await update.message.reply_text(text, reply_markup=keyboard)
        return ConversationHandler.END
    
    # New user
    if is_admin:
        # Auto-register admin with default info
        first_name = update.effective_user.first_name or "Admin"
        
        user = User(
            telegram_id=telegram_id,
            full_name=first_name,
            phone="+963000000000",
            email=settings.ADMIN_EMAIL
        )
        await user.insert()
        
        keyboard = get_admin_menu_keyboard()
        text = f"""
🔑 **مرحباً Admin!**

تم تسجيلك تلقائياً كمدير للمنصة! 🎉

استخدم القائمة بالأسفل لإدارة المنصة:
        """
        
        await update.message.reply_text(text, reply_markup=keyboard)
        logger.info(f"Admin auto-registered: {telegram_id} - {first_name}")
        return ConversationHandler.END
    
    # Regular user - start registration
    welcome_text = """
🎓 **مرحباً بك في المنصة التعليمية!**

للبدء، نحتاج بعض المعلومات:

👤 **الخطوة 1/3:** أدخل اسمك الثلاثي
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_cancel_button()
    )
    
    return ASKING_NAME


async def asking_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for user's name"""
    name = update.message.text.strip()
    
    if name == "❌ إلغاء":
        await update.message.reply_text("تم إلغاء التسجيل.")
        return ConversationHandler.END
    
    if len(name.split()) < 3:
        await update.message.reply_text(
            "❌ يرجى إدخال الاسم الثلاثي كاملاً\n\n"
            "مثال: محمد أحمد علي"
        )
        return ASKING_NAME
    
    # Save name in context
    context.user_data['full_name'] = name
    
    await update.message.reply_text(
        "✅ تم حفظ الاسم\n\n"
        "📱 **الخطوة 2/3:** أدخل رقم هاتفك\n\n"
        "مثال: +963999999999"
    )
    
    return ASKING_PHONE


async def asking_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for user's phone"""
    phone = update.message.text.strip()
    
    if phone == "❌ إلغاء":
        await update.message.reply_text("تم إلغاء التسجيل.")
        return ConversationHandler.END
    
    if not phone.startswith('+') or len(phone) < 10:
        await update.message.reply_text(
            "❌ يرجى إدخال رقم هاتف صحيح\n\n"
            "مثال: +963999999999"
        )
        return ASKING_PHONE
    
    # Save phone in context
    context.user_data['phone'] = phone
    
    await update.message.reply_text(
        "✅ تم حفظ رقم الهاتف\n\n"
        "📧 **الخطوة 3/3:** أدخل بريدك الإلكتروني\n\n"
        "مثال: student@example.com"
    )
    
    return ASKING_EMAIL


async def asking_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for user's email and complete registration"""
    email = update.message.text.strip().lower()
    
    if email == "❌ إلغاء":
        await update.message.reply_text("تم إلغاء التسجيل.")
        return ConversationHandler.END
    
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ يرجى إدخال بريد إلكتروني صحيح\n\n"
            "مثال: student@example.com"
        )
        return ASKING_EMAIL
    
    # Check if email already exists
    existing_user = await User.find_one(User.email == email)
    if existing_user:
        await update.message.reply_text(
            "❌ هذا البريد الإلكتروني مسجل مسبقاً!\n\n"
            "يرجى استخدام بريد آخر أو التواصل مع الإدارة."
        )
        return ASKING_EMAIL
    
    # Create new user
    try:
        user = User(
            telegram_id=update.effective_user.id,
            full_name=context.user_data['full_name'],
            phone=context.user_data['phone'],
            email=email
        )
        await user.insert()
        
        logger.info(f"New user registered: {user.full_name} ({user.telegram_id})")
        
        success_text = f"""
✅ **تم التسجيل بنجاح!**

👤 الاسم: {user.full_name}
📱 الهاتف: {user.phone}
📧 البريد: {user.email}

يمكنك الآن تصفح الدورات والمواد من القائمة بالأسفل 👇
        """
        
        await update.message.reply_text(
            success_text,
            reply_markup=get_main_menu_keyboard()
        )
        
        # Clear user data
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        error_msg = f"""
❌ **حدث خطأ أثناء التسجيل!**

**الخطأ:** {str(e)}

يرجى المحاولة مرة أخرى أو التواصل مع الإدارة.
        """
        await update.message.reply_text(error_msg)
        context.user_data.clear()
        return ConversationHandler.END


async def cancel_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel registration"""
    await update.message.reply_text(
        "تم إلغاء التسجيل. يمكنك البدء من جديد بكتابة /start"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get user's Telegram ID"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    is_admin = user_id == settings.TELEGRAM_ADMIN_ID
    
    text = f"""
🆔 **معلوماتك:**

👤 الاسم: {first_name}
📱 Username: @{username if username else 'لا يوجد'}
🔢 Telegram ID: `{user_id}`

{'🔑 **أنت Admin حالياً**' if is_admin else '👤 **أنت طالب حالياً**'}

---

💡 **لجعل حساب Admin:**

1. افتح ملف `.env`
2. عدّل هذا السطر:
   ```
   TELEGRAM_ADMIN_ID={user_id}
   ```
3. احفظ الملف
4. أعد تشغيل البوت

🎉 ستصبح Admin!
    """
    
    await update.message.reply_text(text)
    logger.info(f"User {first_name} (@{username}) - ID: {user_id} - Is Admin: {is_admin}")
