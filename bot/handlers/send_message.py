"""
Send Message to Students Handler
نظام إرسال رسائل للطلاب
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from config.settings import settings
from database.models.user import User

# Conversation states
SELECTING_STUDENT, ENTERING_MESSAGE = range(2)


async def start_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إرسال رسالة لطالب"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return ConversationHandler.END
    
    # Get all students
    try:
        all_users = await User.find().to_list()
        students = [u for u in all_users if u.telegram_id != settings.TELEGRAM_ADMIN_ID]
        
        if not students:
            await update.message.reply_text(
                "❌ لا يوجد طلاب مسجلين بعد!\n\n"
                "انتظر حتى يسجل الطلاب في المنصة."
            )
            return ConversationHandler.END
        
        text = "📬 **إرسال رسالة لطالب**\n\n"
        text += f"اختر الطالب الذي تريد إرسال رسالة له:\n"
        text += f"(عدد الطلاب: {len(students)})\n\n"
        
        keyboard = []
        
        for student in students[:20]:  # عرض أول 20 طالب
            student_name = student.full_name or "طالب بدون اسم"
            button_text = f"👤 {student_name}"
            
            keyboard.append([
                InlineKeyboardButton(
                    button_text,
                    callback_data=f"msg_student_{student.telegram_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="msg_cancel")])
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return SELECTING_STUDENT
        
    except Exception as e:
        logger.error(f"Error loading students: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")
        return ConversationHandler.END


async def select_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الطالب"""
    query = update.callback_query
    await query.answer()
    
    student_id = query.data.replace("msg_student_", "")
    
    # Get student info
    try:
        student = await User.find_one(User.telegram_id == int(student_id))
        
        if not student:
            await query.edit_message_text("❌ الطالب غير موجود!")
            return ConversationHandler.END
        
        # Store student info in context
        context.user_data['msg_student_id'] = student_id
        context.user_data['msg_student_name'] = student.full_name
        
        text = f"✅ **تم اختيار الطالب:**\n\n"
        text += f"👤 **الاسم:** {student.full_name}\n"
        text += f"📧 **البريد:** {student.email}\n"
        text += f"📱 **الهاتف:** {student.phone}\n\n"
        text += f"━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"✏️ **الآن اكتب الرسالة** التي تريد إرسالها:\n\n"
        text += f"💡 يمكنك كتابة نص عادي أو استخدام Markdown"
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="msg_cancel")]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return ENTERING_MESSAGE
        
    except Exception as e:
        logger.error(f"Error selecting student: {e}")
        await query.edit_message_text(f"❌ حدث خطأ: {str(e)}")
        return ConversationHandler.END


async def send_message_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال الرسالة للطالب"""
    message_text = update.message.text.strip()
    
    if len(message_text) < 1:
        await update.message.reply_text(
            "❌ الرسالة فارغة!\n\n"
            "اكتب الرسالة التي تريد إرسالها:"
        )
        return ENTERING_MESSAGE
    
    student_id = context.user_data.get('msg_student_id')
    student_name = context.user_data.get('msg_student_name', 'الطالب')
    
    if not student_id:
        await update.message.reply_text("❌ خطأ: لم يتم اختيار طالب!")
        return ConversationHandler.END
    
    try:
        # Send message to student
        student_message = f"""
📬 **رسالة من الإدارة**

━━━━━━━━━━━━━━━━━━━━

{message_text}

━━━━━━━━━━━━━━━━━━━━

💡 إذا كان لديك استفسار، يمكنك الرد عبر زر "💬 الدردشة"
        """
        
        await context.bot.send_message(
            chat_id=int(student_id),
            text=student_message,
            parse_mode="Markdown"
        )
        
        # Confirm to admin
        confirmation = f"""
✅ **تم إرسال الرسالة بنجاح!**

👤 **إلى:** {student_name}
📨 **الرسالة:**

{message_text}

━━━━━━━━━━━━━━━━━━━━

هل تريد إرسال رسالة أخرى؟
        """
        
        keyboard = [
            [InlineKeyboardButton("📬 إرسال رسالة أخرى", callback_data="msg_send_another")],
            [InlineKeyboardButton("✔️ تم", callback_data="msg_done")]
        ]
        
        await update.message.reply_text(
            confirmation,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        await update.message.reply_text(
            f"❌ فشل إرسال الرسالة!\n\n"
            f"الخطأ: {str(e)}\n\n"
            f"تأكد من أن الطالب بدأ محادثة مع البوت."
        )
        return ConversationHandler.END


async def send_another_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال رسالة أخرى"""
    query = update.callback_query
    await query.answer()
    
    # Restart the conversation
    update.message = query.message
    return await start_send_message(update, context)


async def cancel_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء إرسال الرسالة"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ تم إلغاء إرسال الرسالة.")
    
    # Clear context
    context.user_data.clear()
    
    return ConversationHandler.END
