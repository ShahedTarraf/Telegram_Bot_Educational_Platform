"""
Live Chat System
نظام الدردشة المباشرة
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from datetime import datetime

from database.models.user import User
from config.settings import settings


# Conversation states
WAITING_FOR_MESSAGE = 1


async def start_chat_with_instructor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start chat conversation with instructor"""
    # Check if this is a callback query or regular message
    query = update.callback_query
    if query:
        await query.answer()
    
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        target = update.callback_query.message if query else update.message
        await target.reply_text(
            "❌ يرجى التسجيل أولاً باستخدام /start"
        )
        return ConversationHandler.END
    
    text = """
💬 **الدردشة مع المدرس**

يمكنك الآن إرسال رسالتك أو سؤالك إلى المدرس مباشرة.

📝 **إرشادات:**
• كن واضحاً ومحدداً
• اذكر اسم الدورة أو الموضوع إن أمكن
• سيتم الرد عليك في أقرب وقت ممكن

الآن، اكتب رسالتك:
    """
    
    keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel_chat")]]
    
    target = update.callback_query.message if query else update.message
    await target.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return WAITING_FOR_MESSAGE


async def receive_chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and forward message to instructor"""
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")
        return ConversationHandler.END
    
    message_text = update.message.text
    
    # Forward to admin with user info
    admin_message = f"""
💬 **رسالة جديدة من طالب**

👤 **الطالب:** {user.full_name}
📧 **البريد:** {user.email}
📱 **الهاتف:** {user.phone}
🆔 **Telegram ID:** {user.telegram_id}

📝 **الرسالة:**
{message_text}

⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---
**للرد:** استخدم /reply {user.telegram_id} ثم اكتب الرد
    """
    
    try:
        # Save message to bot_data
        if 'student_messages' not in context.bot_data:
            context.bot_data['student_messages'] = []
        
        context.bot_data['student_messages'].append({
            'student_id': user.telegram_id,
            'student_name': user.full_name,
            'message': message_text,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        })
        
        # Keep only last 20 messages
        if len(context.bot_data['student_messages']) > 20:
            context.bot_data['student_messages'] = context.bot_data['student_messages'][-20:]
        
        # Send to admin
        await context.bot.send_message(
            chat_id=settings.TELEGRAM_ADMIN_ID,
            text=admin_message
        )
        
        # Confirm to student
        await update.message.reply_text(
            "✅ **تم إرسال رسالتك بنجاح!**\n\n"
            "سيتم الرد عليك في أقرب وقت ممكن.\n"
            "شكراً لتواصلك معنا! 🙏"
        )
        
        logger.info(f"Chat message from {user.full_name} sent to admin")
        
    except Exception as e:
        logger.error(f"Failed to send chat message: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ في إرسال الرسالة. يرجى المحاولة لاحقاً."
        )
    
    return ConversationHandler.END


async def admin_reply_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin replies to student message"""
    if update.effective_user.id != settings.TELEGRAM_ADMIN_ID:
        return
    
    # Parse command: /reply <telegram_id> <message>
    parts = update.message.text.split(' ', 2)
    
    if len(parts) < 3:
        await update.message.reply_text(
            "❌ استخدام خاطئ!\n\n"
            "الصيغة الصحيحة:\n"
            "/reply <telegram_id> <الرسالة>"
        )
        return
    
    try:
        student_id = int(parts[1])
        reply_message = parts[2]
        
        # Get student info
        student = await User.find_one(User.telegram_id == student_id)
        if not student:
            await update.message.reply_text("❌ الطالب غير موجود!")
            return
        
        # Send reply to student
        student_message = f"""
📩 **رد من المدرس**

{reply_message}

---
💬 إذا كان لديك أسئلة أخرى، لا تتردد في التواصل معنا!
        """
        
        await context.bot.send_message(
            chat_id=student_id,
            text=student_message
        )
        
        # Confirm to admin
        await update.message.reply_text(
            f"✅ تم إرسال الرد إلى {student.full_name}"
        )
        
        logger.info(f"Admin replied to student {student_id}")
        
    except ValueError:
        await update.message.reply_text("❌ Telegram ID غير صحيح!")
    except Exception as e:
        logger.error(f"Failed to send admin reply: {e}")
        await update.message.reply_text("❌ حدث خطأ في إرسال الرد.")


async def cancel_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel chat conversation"""
    query = update.callback_query
    await query.answer()
    
    await query.message.edit_text("❌ تم إلغاء المحادثة.")
    
    return ConversationHandler.END


async def show_chat_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show chat button to user"""
    keyboard = [[InlineKeyboardButton("💬 تواصل مع المدرس", callback_data="start_chat")]]
    
    await update.message.reply_text(
        "📞 **التواصل**\n\n"
        "هل لديك سؤال أو استفسار؟\n"
        "تواصل مع المدرس مباشرة!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# Group chat functions
async def create_group_discussion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create group discussion for a course"""
    if update.effective_user.id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الميزة متاحة للأدمن فقط.")
        return
    
    text = """
👥 **مناقشة جماعية**

📚 إنشاء مجموعة نقاش لدورة معينة:

1. أنشئ مجموعة Telegram جديدة
2. أضف البوت إلى المجموعة
3. أضف الطلاب المسجلين في الدورة
4. استخدم /setgroup <course_id> لربط المجموعة بالدورة

🔒 سيتمكن الطلاب المسجلون فقط من الوصول!
    """
    
    await update.message.reply_text(text)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle messages in group chats"""
    # Check if this is a group chat
    if update.message.chat.type not in ['group', 'supergroup']:
        return
    
    # Check if message mentions bot
    if not update.message.text or '@' not in update.message.text:
        return
    
    # Get mentioned users
    bot_username = (await context.bot.get_me()).username
    
    if f'@{bot_username}' in update.message.text:
        # Bot was mentioned
        await update.message.reply_text(
            "👋 مرحباً! كيف يمكنني مساعدتك؟\n\n"
            "استخدم /help لرؤية الأوامر المتاحة."
        )
