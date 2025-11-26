"""
Assignment Submissions Handler
معالج تسليم الواجبات
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from datetime import datetime

from database.models.assignment import Assignment
from database.models.user import User
from database.models.notification import Notification
from config.settings import settings
import httpx


# Conversation states
WAITING_FOR_SUBMISSION = 1


async def submit_assignment_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle file submission for assignment"""
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ يرجى التسجيل أولاً باستخدام /start")
        return
    
    # Check if user is in submission mode
    assignment_id = context.user_data.get('submitting_assignment_id')
    if not assignment_id:
        # Not in submission mode, ignore
        return
    
    assignment = await Assignment.find_one(Assignment.id == assignment_id)
    if not assignment:
        await update.message.reply_text("❌ الواجب غير موجود")
        context.user_data.pop('submitting_assignment_id', None)
        return
    
    # Check if past deadline
    if assignment.is_past_deadline() and not assignment.allow_late_submission:
        await update.message.reply_text(
            "❌ عذراً، انتهى الموعد النهائي للتسليم ولا يُسمح بالتسليم المتأخر."
        )
        context.user_data.pop('submitting_assignment_id', None)
        return
    
    # Get file ID based on type
    file_id = None
    file_type = None
    
    if update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
        file_name = update.message.document.file_name
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        file_name = "صورة"
    elif update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
        file_name = "فيديو"
    else:
        await update.message.reply_text(
            "❌ يرجى إرسال ملف PDF أو صورة أو فيديو.\n\n"
            "الأنواع المدعومة: PDF, JPG, PNG, MP4"
        )
        return
    
    try:
        # Add submission to database
        await assignment.add_submission(
            user_id=str(update.effective_user.id),
            file_id=file_id
        )
        
        # Send confirmation
        text = f"""
✅ **تم تسليم الحل بنجاح!**

📝 الواجب: {assignment.title}
📎 الملف: {file_name}
⏰ وقت التسليم: {datetime.now().strftime('%Y-%m-%d %H:%M')}

سيتم مراجعة حلك وإعطائك الدرجة قريباً.
شكراً لك! 🙏
        """
        
        await update.message.reply_text(text)
        
        # Notify admin
        try:
            admin_text = f"""
🔔 **تسليم واجب جديد!**

👤 الطالب: {user.full_name}
📝 الواجب: {assignment.title}
📎 نوع الملف: {file_type}

للمراجعة والتقييم، اذهب إلى لوحة التحكم.
            """
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": settings.TELEGRAM_ADMIN_ID,
                        "text": admin_text,
                        "parse_mode": "Markdown"
                    }
                )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
        
        # Clear submission mode
        context.user_data.pop('submitting_assignment_id', None)
        
        logger.info(f"Assignment submission: {user.full_name} -> {assignment.title}")
        
    except Exception as e:
        logger.error(f"Error submitting assignment: {e}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء تسليم الحل. يرجى المحاولة لاحقاً."
        )


async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE, assignment_id: str):
    """Start assignment submission process"""
    context.user_data['submitting_assignment_id'] = assignment_id
    
    assignment = await Assignment.find_one(Assignment.id == assignment_id)
    if not assignment:
        await update.callback_query.message.reply_text("❌ الواجب غير موجود")
        return
    
    text = f"""
📤 **تسليم الواجب: {assignment.title}**

يرجى إرسال حلك بأحد الطرق التالية:

📄 **ملف PDF** - الطريقة المفضلة
📷 **صورة** - لحل مكتوب بخط اليد
📹 **فيديو** - لشرح الحل

⚠️ **ملاحظات:**
• تأكد من وضوح الملف
• يمكنك إرسال ملف واحد فقط
• سيتم استبدال الحل السابق إذا كان موجوداً

أرسل الملف الآن:
    """
    
    keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_submission_{assignment_id}")]]
    
    await update.callback_query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def view_submission_status(update: Update, context: ContextTypes.DEFAULT_TYPE, assignment_id: str):
    """View submission status and grade"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(update.effective_user.id)
    assignment = await Assignment.find_one(Assignment.id == assignment_id)
    
    if not assignment:
        await query.message.reply_text("❌ الواجب غير موجود")
        return
    
    submission = assignment.get_submission(user_id)
    
    if not submission:
        text = f"""
📝 **{assignment.title}**

📊 **حالة التسليم:** لم يتم التسليم بعد

{assignment.get_info_text()}

📤 لتسليم الحل، اضغط على الزر بالأسفل
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 تسليم الحل", callback_data=f"submit_{assignment_id}")],
            [InlineKeyboardButton("« رجوع", callback_data="assignments")]
        ]
    else:
        text = f"""
📝 **{assignment.title}**

📊 **حالة التسليم:** ✅ تم التسليم
⏰ **وقت التسليم:** {submission.submitted_at.strftime('%Y-%m-%d %H:%M')}
        """
        
        if submission.status == "graded":
            text += f"""
📈 **الدرجة:** {submission.grade}/{assignment.max_grade}
📊 **النسبة:** {(submission.grade/assignment.max_grade)*100:.1f}%
        """
            
            if submission.grade >= assignment.pass_grade:
                text += "\n✅ **النتيجة:** ناجح 🎉"
            else:
                text += "\n❌ **النتيجة:** راسب"
            
            if submission.feedback:
                text += f"\n\n💬 **ملاحظات المدرس:**\n{submission.feedback}"
            
            text += f"\n\n📅 **تاريخ التصحيح:** {submission.graded_at.strftime('%Y-%m-%d %H:%M')}"
        else:
            text += "\n\n⏳ **الحالة:** قيد المراجعة..."
        
        keyboard = [
            [InlineKeyboardButton("🔄 إعادة التسليم", callback_data=f"submit_{assignment_id}")],
            [InlineKeyboardButton("« رجوع", callback_data="assignments")]
        ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def cancel_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel submission process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.pop('submitting_assignment_id', None)
    
    await query.message.edit_text(
        "❌ تم إلغاء عملية التسليم.",
        reply_markup=None
    )
