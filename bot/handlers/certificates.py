"""
Certificate and Messages Handlers
معالجات الشهادات والرسائل
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
import json
from pathlib import Path

from database.models.user import User
from config.settings import settings


async def request_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب استلام الشهادة للطالب"""
    user_id = update.effective_user.id
    
    try:
        # Get user
        user = await User.find_one(User.telegram_id == user_id)
        if not user:
            await update.message.reply_text("❌ يرجى التسجيل أولاً.")
            return
        
        # Get approved courses
        approved_courses = [e for e in user.courses if e.approval_status == "approved"]
        
        if not approved_courses:
            await update.message.reply_text(
                "❌ **لا توجد دورات مكتملة!**\n\n"
                "يجب عليك:\n"
                "1️⃣ التسجيل في دورة\n"
                "2️⃣ إكمال جميع المتطلبات\n"
                "3️⃣ النجاح في الاختبارات\n\n"
                "📚 سجل في دورة من القائمة أولاً!"
            )
            return
        
        # Load courses from JSON
        courses_path = Path("data/courses.json")
        courses_data = {}
        if courses_path.exists():
            with open(courses_path, 'r', encoding='utf-8') as f:
                courses_list = json.load(f)
                courses_data = {c['id']: c for c in courses_list}
        
        # Show available certificates
        keyboard = []
        for enrollment in approved_courses:
            course = courses_data.get(enrollment.course_id)
            if course and enrollment.completed:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎓 {course['title']}",
                        callback_data=f"cert_request_{course['id']}"
                    )
                ])
        
        if not keyboard:
            await update.message.reply_text(
                "❌ **لا توجد دورات مكتملة!**\n\n"
                "أكمل متطلبات الدورة أولاً:\n"
                "✅ مشاهدة جميع الفيديوهات\n"
                "✅ تسليم جميع الواجبات\n"
                "✅ اجتياز الاختبارات"
            )
            return
        
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data="back_main")])
        
        await update.message.reply_text(
            "🎓 **استلام الشهادة**\n\n"
            "اختر الدورة للحصول على شهادتك:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in request_certificate: {e}")
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة لاحقاً.")


# Certificate export states
CERT_UPLOAD_PDF, CERT_ENTER_STUDENT_ID = range(2)


async def export_certificate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية تصدير شهادة"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return ConversationHandler.END
    
    text = """
📜 **تصدير شهادة**

📎 أرسل **ملف PDF** للشهادة:

💡 تأكد أن الملف:
• بصيغة PDF
• يحتوي على اسم الطالب والدورة
• واضح وقابل للقراءة

أرسل ملف الشهادة الآن:
    """
    
    await update.message.reply_text(text)
    return CERT_UPLOAD_PDF


async def upload_certificate_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام PDF وطلب student_id"""
    # Check if it's a document
    if not update.message.document:
        await update.message.reply_text(
            "❌ يرجى إرسال **ملف PDF**!\n\n"
            "تأكد من إرسال الملف كمستند (Document) وليس صورة."
        )
        return CERT_UPLOAD_PDF
    
    file = update.message.document
    
    # Check if it's PDF
    if not file.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ يجب أن يكون الملف بصيغة **PDF**!\n\n"
            f"الملف المرسل: {file.file_name}\n\n"
            "أرسل ملف PDF من فضلك:"
        )
        return CERT_UPLOAD_PDF
    
    # Store file info
    context.user_data['cert_file_id'] = file.file_id
    context.user_data['cert_file_name'] = file.file_name
    
    text = f"""
✅ تم استلام الشهادة: {file.file_name}

🆔 الآن أدخل **Telegram ID** للطالب:

مثال: 1993109100

💡 يمكنك الحصول على ID من:
• رسائل الطلاب
• Dashboard → المستخدمين
• طلب من الطالب كتابة /start
    """
    
    await update.message.reply_text(text)
    return CERT_ENTER_STUDENT_ID


async def send_certificate_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال الشهادة للطالب"""
    try:
        student_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Telegram ID غير صحيح!\n\n"
            "يجب أن يكون رقماً فقط.\n\n"
            "مثال: 1993109100\n\n"
            "أدخل ID صحيح:"
        )
        return CERT_ENTER_STUDENT_ID
    
    # Get file info
    file_id = context.user_data.get('cert_file_id')
    file_name = context.user_data.get('cert_file_name')
    
    if not file_id:
        await update.message.reply_text("❌ حدث خطأ! الملف غير موجود.")
        context.user_data.clear()
        return ConversationHandler.END
    
    # Verify student exists
    user = await User.find_one(User.telegram_id == student_id)
    if not user:
        await update.message.reply_text(
            f"❌ لم يتم العثور على طالب بهذا ID: {student_id}\n\n"
            "تأكد من الرقم وحاول مرة أخرى:\n\n"
            "أو /cancel للإلغاء"
        )
        return CERT_ENTER_STUDENT_ID
    
    try:
        # Send certificate to student
        await context.bot.send_document(
            chat_id=student_id,
            document=file_id,
            caption=f"🎓 **مبارك! شهادتك جاهزة!**\n\n"
                    f"👏 تهانينا على إكمال الدورة!\n"
                    f"📜 الشهادة مرفقة بالأعلى\n\n"
                    f"✨ نتمنى لك كل التوفيق!"
        )
        
        # Confirm to admin
        await update.message.reply_text(
            f"✅ **تم إرسال الشهادة بنجاح!**\n\n"
            f"👤 الطالب: {user.full_name}\n"
            f"🆔 Telegram ID: {student_id}\n"
            f"📎 الملف: {file_name}\n\n"
            f"🎉 الشهادة وصلت للطالب!"
        )
        
        logger.info(f"Certificate sent to {user.full_name} (ID: {student_id})")
        
    except Exception as e:
        logger.error(f"Failed to send certificate: {e}")
        await update.message.reply_text(
            f"❌ فشل إرسال الشهادة!\n\n"
            f"الخطأ: {str(e)}\n\n"
            f"تأكد من أن الطالب لم يحظر البوت."
        )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_certificate_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء تصدير الشهادة"""
    await update.message.reply_text("❌ تم إلغاء تصدير الشهادة.")
    context.user_data.clear()
    return ConversationHandler.END


async def show_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض رسائل الطلاب للأدمن"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return
    
    try:
        # Get recent student messages from context
        messages = context.bot_data.get('student_messages', [])
        
        if not messages:
            await update.message.reply_text(
                "💬 **رسائل الطلاب**\n\n"
                "📊 **لا توجد رسائل حالياً**\n\n"
                "💡 **ملاحظة:**\n"
                "عندما يرسل طالب رسالة عبر \"💬 الدردشة\"،\n"
                "ستصلك إشعار مباشرة ويتم حفظها هنا!\n\n"
                "🔄 الرسائل الأخيرة ستظهر هنا تلقائياً."
            )
            return
        
        # Show last 5 messages with reply buttons
        text = "💬 **آخر الرسائل المستلمة:**\n\n"
        keyboard = []
        
        for i, msg in enumerate(messages[-5:], 1):
            text += f"{i}. 👤 {msg['student_name']}\n"
            text += f"   📝 {msg['message'][:50]}...\n"
            text += f"   ⏰ {msg['time']}\n\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"💬 رد على {msg['student_name']}", 
                    callback_data=f"reply_msg_{msg['student_id']}"
                )
            ])
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        logger.error(f"Error in show_admin_messages: {e}")
        await update.message.reply_text("❌ حدث خطأ. يرجى المحاولة لاحقاً.")


async def start_reply_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء الرد على طالب - من زر الرد السريع"""
    query = update.callback_query
    await query.answer()
    
    student_id = int(query.data.split('_')[-1])
    
    # Get student info
    user = await User.find_one(User.telegram_id == student_id)
    if not user:
        await query.edit_message_text("❌ الطالب غير موجود!")
        return
    
    # Store student ID in context for next message
    context.user_data['replying_to_student'] = student_id
    context.user_data['replying_to_name'] = user.full_name
    
    await query.edit_message_text(
        f"💬 **الرد على {user.full_name}**\n\n"
        f"📝 اكتب رسالتك الآن وسيتم إرسالها مباشرة:\n\n"
        f"أو استخدم: `/reply {student_id} <رسالتك>`\n\n"
        f"❌ /cancel للإلغاء"
    )


async def send_reply_to_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إرسال الرد للطالب"""
    if 'replying_to_student' not in context.user_data:
        return
    
    student_id = context.user_data['replying_to_student']
    student_name = context.user_data.get('replying_to_name', 'الطالب')
    reply_text = update.message.text
    
    if reply_text.startswith('/'):
        return  # Ignore commands
    
    try:
        # Send to student
        await context.bot.send_message(
            chat_id=student_id,
            text=f"📩 **رد من المدرس:**\n\n{reply_text}\n\n"
                 f"---\n💬 يمكنك الرد مرة أخرى من \"💬 الدردشة\""
        )
        
        # Confirm to admin
        await update.message.reply_text(
            f"✅ تم إرسال الرد إلى {student_name}!"
        )
        
        # Clear context
        context.user_data.pop('replying_to_student', None)
        context.user_data.pop('replying_to_name', None)
        
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")
        await update.message.reply_text("❌ فشل إرسال الرد!")


async def process_certificate_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة طلب الشهادة"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    course_id = '_'.join(parts[2:])  # Handle course IDs with underscores
    user_id = query.from_user.id
    
    try:
        user = await User.find_one(User.telegram_id == user_id)
        
        # Load course from JSON
        courses_path = Path("data/courses.json")
        course = None
        if courses_path.exists():
            with open(courses_path, 'r', encoding='utf-8') as f:
                courses_list = json.load(f)
                course = next((c for c in courses_list if c['id'] == course_id), None)
        
        if not user or not course:
            await query.edit_message_text("❌ حدث خطأ. يرجى المحاولة لاحقاً.")
            return
        
        # Check if course is completed
        enrollment = user.get_course_enrollment(course_id)
        if not enrollment or not enrollment.completed:
            await query.edit_message_text(
                "❌ **الدورة غير مكتملة!**\n\n"
                "أكمل جميع المتطلبات أولاً."
            )
            return
        
        # Send certificate request to admin
        admin_msg = (
            f"🎓 **طلب شهادة جديد!**\n\n"
            f"👤 الطالب: {user.full_name}\n"
            f"📚 الدورة: {course['title']}\n"
            f"🆔 User ID: {user.telegram_id}\n\n"
            f"✅ الدورة مكتملة!\n"
            f"📜 يرجى تصدير الشهادة للطالب."
        )
        
        try:
            await context.bot.send_message(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                text=admin_msg
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
        
        # Confirm to student
        await query.edit_message_text(
            "✅ **تم إرسال طلب الشهادة!**\n\n"
            f"📚 الدورة: {course['title']}\n\n"
            "⏳ سيتم مراجعة طلبك وإرسال الشهادة\n"
            "في أقرب وقت ممكن.\n\n"
            "📧 ستصلك الشهادة هنا مباشرة!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in process_certificate_request: {e}")
        await query.edit_message_text("❌ حدث خطأ. يرجى المحاولة لاحقاً.")
