"""
Start Handler - Registration
"""
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from pydantic import ValidationError

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
    user = None
    try:
        logger.debug(f"[START] Checking existing user by telegram_id={telegram_id}")
        print(f"[START] Attempting to find user with telegram_id={telegram_id}", flush=True)
        
        # Verify database connection first
        from database.connection import Database
        is_connected = await Database.is_connected()
        if not is_connected:
            logger.error(f"[START] Database not connected when checking user {telegram_id}")
            print(f"[START] ERROR: Database not connected", flush=True)
            user = None
        else:
            logger.debug(f"[START] Database is connected, proceeding with query")
            user = await User.find_one(User.telegram_id == telegram_id)
            logger.debug(f"[START] Query result: user={'Found' if user else 'Not found'}")
            print(f"[START] Query result: user={'Found' if user else 'Not found'}", flush=True)
            
    except ValidationError as e:
        # مشكلة في تحميل مستند مستخدم من قاعدة البيانات (سكيما قديمة أو بيانات تالفة)
        error_type = type(e).__name__
        error_msg = f"[START] Validation error while loading user {telegram_id}: {error_type}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}", flush=True)
        
        # Send admin notification
        try:
            from utils.admin_notifications import send_admin_error
            await send_admin_error(
                context.bot,
                f"Validation error while loading user data:\n\n`{str(e)}`",
                error_type="WARNING",
                user_id=telegram_id
            )
        except Exception as notify_error:
            logger.error(f"Failed to notify admin: {repr(notify_error)}")
        
        user = None
    except Exception as e:
        # أي خطأ آخر في قاعدة البيانات لا يجب أن يسقط البوت بالكامل
        error_type = type(e).__name__
        error_msg = f"[START] Unexpected DB error while fetching user {telegram_id}: {error_type}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}", flush=True)
        import traceback
        traceback.print_exc()
        
        # Send admin notification
        try:
            from utils.admin_notifications import send_admin_error
            await send_admin_error(
                context.bot,
                f"Database error while fetching user:\n\n`{error_type}: {str(e)}`",
                error_type="ERROR",
                user_id=telegram_id
            )
        except Exception as notify_error:
            logger.error(f"Failed to notify admin: {repr(notify_error)}")
        
        user = None
    
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
        # Admin: لا نعتمد على حفظه في قاعدة البيانات لعرض لوحة الأدمن
        first_name = update.effective_user.first_name or "Admin"
        keyboard = get_admin_menu_keyboard()
        text = f"""
🔑 **مرحباً Admin!**

تم التعرف عليك كمدير للمنصة! 🎉

استخدم القائمة بالأسفل لإدارة المنصة:
        """
        await update.message.reply_text(text, reply_markup=keyboard)
        logger.info(f"Admin logged in (without DB record): {telegram_id} - {first_name}")
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
    try:
        logger.debug(f"asking_email: checking existing user by email={email}")
        existing_user = await User.find_one(User.email == email)
    except ValidationError as e:
        # قد تشير إلى سجلات تالفة قديمة بنفس البريد - نحاول تنظيفها ثم نكمل
        logger.error(f"Validation error while checking email {email}: {repr(e)}. Attempting cleanup.")
        try:
            collection = User.get_motor_collection()
            result = await collection.delete_many({"email": email})
            logger.info(f"Deleted {result.deleted_count} corrupted user documents with email {email}")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup corrupted user docs with email {email}: {repr(cleanup_error)}")
        existing_user = None
    except Exception as e:
        logger.error(f"Unexpected DB error while checking email {email}: {repr(e)}")
        existing_user = None
    if existing_user:
        await update.message.reply_text(
            "❌ هذا البريد الإلكتروني مسجل مسبقاً!\n\n"
            "يرجى استخدام بريد آخر أو التواصل مع الإدارة."
        )
        return ASKING_EMAIL
    
    # Create new user
    try:
        telegram_id = update.effective_user.id
        full_name = context.user_data.get('full_name')
        phone = context.user_data.get('phone')
        
        logger.debug(
            f"[REGISTRATION] Creating new user: "
            f"telegram_id={telegram_id}, "
            f"full_name={full_name}, "
            f"phone={phone}, "
            f"email={email}"
        )
        print(f"[REGISTRATION] Creating new user: telegram_id={telegram_id}, email={email}", flush=True)
        
        # Verify database connection before attempting save
        from database.connection import Database
        is_connected = await Database.is_connected()
        if not is_connected:
            logger.error(f"[REGISTRATION] Database not connected for user {telegram_id}")
            print(f"[REGISTRATION] ERROR: Database not connected for user {telegram_id}", flush=True)
            await update.message.reply_text(
                "❌ **خطأ في الاتصال بقاعدة البيانات!**\n\n"
                "يرجى المحاولة مرة أخرى خلال لحظات."
            )
            context.user_data.clear()
            return ConversationHandler.END
        
        user = User(
            telegram_id=telegram_id,
            full_name=full_name,
            phone=phone,
            email=email
        )
        
        logger.debug(f"[REGISTRATION] User object created: {user}")
        print(f"[REGISTRATION] User object created successfully", flush=True)
        
        logger.debug(f"[REGISTRATION] Inserting user into MongoDB...")
        print(f"[REGISTRATION] Inserting user into MongoDB...", flush=True)
        await user.insert()
        
        logger.info(f"✅ [REGISTRATION] New user registered successfully: {full_name} (ID: {telegram_id})")
        print(f"✅ [REGISTRATION] New user registered: {full_name} (ID: {telegram_id})", flush=True)
        
        success_text = f"""
✅ **تم التسجيل بنجاح!**

👤 الاسم: {full_name}
📱 الهاتف: {phone}
📧 البريد: {email}

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
        # Comprehensive error logging for Vercel debugging
        error_type = type(e).__name__
        error_str = str(e)
        telegram_id = update.effective_user.id
        
        error_msg = (
            f"[REGISTRATION] ❌ FAILED for telegram_id={telegram_id}, email={email}\n"
            f"Error Type: {error_type}\n"
            f"Error Message: {error_str}"
        )
        logger.error(error_msg, exc_info=True)
        print(f"ERROR: {error_msg}", flush=True)
        
        # Print full traceback for debugging
        import traceback
        tb_str = traceback.format_exc()
        logger.error(f"[REGISTRATION] Traceback:\n{tb_str}")
        print(f"[REGISTRATION] Traceback:\n{tb_str}", flush=True)
        
        # Determine user-friendly error message
        msg = "❌ **حدث خطأ أثناء التسجيل!**\n\n"
        error_text = error_str.lower()
        
        if "duplicate key" in error_text or "e11000" in error_text:
            logger.warning(f"[REGISTRATION] Duplicate key error for email={email}")
            msg += (
                "يبدو أن هذا البريد الإلكتروني أو حساب التلغرام مسجّل مسبقاً في النظام.\n"
                "جرّب بريدًا إلكترونيًا آخر أو تواصل مع الإدارة إذا كنت متأكداً أن هذا خطأ."
            )
        elif "connection" in error_text or "timeout" in error_text:
            logger.error(f"[REGISTRATION] Connection/Timeout error for user {telegram_id}")
            msg += "خطأ في الاتصال بقاعدة البيانات. يرجى المحاولة مرة أخرى خلال لحظات."
        elif "validation" in error_text:
            logger.error(f"[REGISTRATION] Validation error for user {telegram_id}: {error_str}")
            msg += "بيانات غير صحيحة. يرجى التحقق من المعلومات المدخلة."
        else:
            logger.error(f"[REGISTRATION] Unexpected error for user {telegram_id}: {error_type}")
            msg += "يرجى المحاولة مرة أخرى لاحقاً أو التواصل مع الإدارة."
        
        await update.message.reply_text(msg)
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
