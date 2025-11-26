"""
Assignment Submission Handler for JSON-based assignments
معالج تسليم الواجبات للواجبات المحفوظة في JSON
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime
from pathlib import Path
import json

from database.models.user import User
from config.settings import settings
import httpx


# Conversation states
WAITING_FOR_FILE = 1


async def start_assignment_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء عملية تسليم واجب"""
    query = update.callback_query
    await query.answer()
    
    # Extract assignment info: submit_solution_{index}_{course_id}
    parts = query.data.split('_')
    assignment_index = int(parts[2])
    course_id = '_'.join(parts[3:])
    
    # Store in context
    context.user_data['submitting_assignment_index'] = assignment_index
    context.user_data['submitting_course_id'] = course_id
    
    # Load assignment
    assignments_file = Path('data/assignments.json')
    if not assignments_file.exists():
        await query.message.reply_text("❌ الواجبات غير موجودة")
        return
    
    with open(assignments_file, 'r', encoding='utf-8') as f:
        all_assignments = json.load(f)
        assignments = [a for a in all_assignments if a.get('type') == 'courses' and a.get('item_id') == course_id]
    
    if assignment_index >= len(assignments):
        await query.message.reply_text("❌ الواجب غير موجود")
        return
    
    assignment = assignments[assignment_index]
    
    text = f"""
📤 **تسليم الواجب: {assignment.get('title')}**

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
    
    await query.message.reply_text(text, parse_mode="Markdown")
    return WAITING_FOR_FILE


async def receive_submission_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام ملف التسليم"""
    assignment_index = context.user_data.get('submitting_assignment_index')
    course_id = context.user_data.get('submitting_course_id')
    
    if assignment_index is None or course_id is None:
        # User sent file without starting submission process
        logger.warning(f"File received without submission context from {update.effective_user.id}")
        return  # Silently ignore files not part of submission process
    
    # Get user
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ يرجى التسجيل أولاً")
        return
    
    # Get file info
    file_id = None
    file_type = None
    file_name = None
    
    if update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
        file_name = update.message.document.file_name
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_type = "photo"
        file_name = "صورة.jpg"
    elif update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
        file_name = "فيديو.mp4"
    else:
        await update.message.reply_text(
            "❌ يرجى إرسال ملف PDF أو صورة أو فيديو.\n\n"
            "الأنواع المدعومة: PDF, JPG, PNG, MP4"
        )
        return
    
    # Load assignments
    assignments_file = Path('data/assignments.json')
    with open(assignments_file, 'r', encoding='utf-8') as f:
        all_assignments = json.load(f)
    
    # Find assignment
    assignments = [a for a in all_assignments if a.get('type') == 'courses' and a.get('item_id') == course_id]
    if assignment_index >= len(assignments):
        await update.message.reply_text("❌ الواجب غير موجود")
        return
    
    assignment = assignments[assignment_index]
    
    # Load submissions
    submissions_file = Path('data/submissions.json')
    submissions = []
    if submissions_file.exists():
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
    
    # Create submission
    submission = {
        'student_id': str(update.effective_user.id),
        'student_name': user.full_name,
        'course_id': course_id,
        'assignment_index': assignment_index,
        'assignment_title': assignment.get('title'),
        'file_id': file_id,
        'file_type': file_type,
        'file_name': file_name,
        'submitted_at': datetime.now().isoformat(),
        'status': 'pending',  # pending, graded
        'grade': None,
        'feedback': None,
        'graded_at': None
    }
    
    # Remove old submission if exists
    submissions = [s for s in submissions if not (
        s.get('student_id') == str(update.effective_user.id) and
        s.get('course_id') == course_id and
        s.get('assignment_index') == assignment_index
    )]
    
    # Add new submission
    submissions.append(submission)
    
    # Save submissions
    with open(submissions_file, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)
    
    # Confirmation message
    text = f"""
✅ **تم تسليم الحل بنجاح!**

📝 الواجب: {assignment.get('title')}
📎 الملف: {file_name}
⏰ وقت التسليم: {datetime.now().strftime('%Y-%m-%d %H:%M')}

سيتم مراجعة حلك وإعطائك الدرجة قريباً.
شكراً لك! 🙏
    """
    
    await update.message.reply_text(text, parse_mode="Markdown")
    
    # Notify admin
    try:
        admin_text = f"""
🔔 **تسليم واجب جديد!**

👤 الطالب: {user.full_name}
🆔 Telegram ID: {update.effective_user.id}
📝 الواجب: {assignment.get('title')}
📚 الدورة: {course_id}
📎 نوع الملف: {file_type}

للتقييم، استخدم الأمر:
`/grade {update.effective_user.id} {course_id} {assignment_index} [الدرجة] [الملاحظات]`

مثال:
`/grade {update.effective_user.id} {course_id} {assignment_index} 95 ممتاز! عمل رائع`
        """
        
        # Send file to admin
        if file_type == "document":
            await context.bot.send_document(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                document=file_id,
                caption=admin_text,
                parse_mode="Markdown"
            )
        elif file_type == "photo":
            await context.bot.send_photo(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                photo=file_id,
                caption=admin_text,
                parse_mode="Markdown"
            )
        elif file_type == "video":
            await context.bot.send_video(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                video=file_id,
                caption=admin_text,
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
    
    # Clear context
    context.user_data.pop('submitting_assignment_index', None)
    context.user_data.pop('submitting_course_id', None)
    
    logger.info(f"Assignment submission: {user.full_name} -> {assignment.get('title')}")


async def grade_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييم واجب من الأدمن"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return
    
    # Parse command: /grade {student_id} {course_id} {assignment_index} {grade} {feedback}
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text(
                "❌ الاستخدام الصحيح:\n\n"
                "`/grade {student_id} {course_id} {assignment_index} {grade} [feedback]`\n\n"
                "مثال:\n"
                "`/grade 1993109100 nlp_beginner 0 95 ممتاز!`",
                parse_mode="Markdown"
            )
            return
        
        student_id = args[0]
        course_id = args[1]
        assignment_index = int(args[2])
        grade = float(args[3])
        feedback = ' '.join(args[4:]) if len(args) > 4 else "لا توجد ملاحظات"
        
        # Load submissions
        submissions_file = Path('data/submissions.json')
        if not submissions_file.exists():
            await update.message.reply_text("❌ لا توجد تسليمات")
            return
        
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
        
        # Find submission
        submission = None
        for s in submissions:
            if (s.get('student_id') == student_id and
                s.get('course_id') == course_id and
                s.get('assignment_index') == assignment_index):
                submission = s
                break
        
        if not submission:
            await update.message.reply_text("❌ التسليم غير موجود")
            return
        
        # Update submission
        submission['status'] = 'graded'
        submission['grade'] = grade
        submission['feedback'] = feedback
        submission['graded_at'] = datetime.now().isoformat()
        
        # Save
        with open(submissions_file, 'w', encoding='utf-8') as f:
            json.dump(submissions, f, ensure_ascii=False, indent=2)
        
        # Confirm to admin
        await update.message.reply_text(
            f"✅ **تم تقييم الواجب!**\n\n"
            f"👤 الطالب: {submission['student_name']}\n"
            f"📝 الواجب: {submission['assignment_title']}\n"
            f"📊 الدرجة: {grade}/100\n"
            f"💬 الملاحظات: {feedback}\n\n"
            f"سيتم إرسال إشعار للطالب الآن...",
            parse_mode="Markdown"
        )
        
        # Notify student
        try:
            passed = grade >= 60  # Pass grade
            status_emoji = "✅" if passed else "❌"
            status_text = "ناجح 🎉" if passed else "راسب"
            
            student_text = f"""
🔔 **تم تصحيح واجبك!**

📝 الواجب: {submission['assignment_title']}
📊 الدرجة: {grade}/100
{status_emoji} النتيجة: {status_text}

💬 **ملاحظات المدرس:**
{feedback}

📅 تاريخ التصحيح: {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'🎉 مبارك! واصل التميز!' if passed else '💪 لا تستسلم! يمكنك تحسين أدائك في الواجبات القادمة'}
            """
            
            await context.bot.send_message(
                chat_id=int(student_id),
                text=student_text,
                parse_mode="Markdown"
            )
            
            await update.message.reply_text(
                f"✅ تم إرسال الإشعار للطالب {submission['student_name']}!",
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Failed to notify student: {e}")
            await update.message.reply_text(
                f"⚠️ تم التقييم لكن فشل إرسال الإشعار للطالب.\n"
                f"الخطأ: {str(e)}",
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error grading assignment: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")


async def view_submission_status_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض حالة التسليم"""
    query = update.callback_query
    await query.answer()
    
    # Extract: submission_status_{index}_{course_id}
    parts = query.data.split('_')
    assignment_index = int(parts[2])
    course_id = '_'.join(parts[3:])
    
    student_id = str(update.effective_user.id)
    
    # Load submissions
    submissions_file = Path('data/submissions.json')
    submission = None
    if submissions_file.exists():
        with open(submissions_file, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
            for s in submissions:
                if (s.get('student_id') == student_id and
                    s.get('course_id') == course_id and
                    s.get('assignment_index') == assignment_index):
                    submission = s
                    break
    
    # Load assignment
    assignments_file = Path('data/assignments.json')
    with open(assignments_file, 'r', encoding='utf-8') as f:
        all_assignments = json.load(f)
        assignments = [a for a in all_assignments if a.get('type') == 'courses' and a.get('item_id') == course_id]
    
    if assignment_index >= len(assignments):
        await query.message.reply_text("❌ الواجب غير موجود")
        return
    
    assignment = assignments[assignment_index]
    
    if not submission:
        text = f"""
📝 **{assignment.get('title')}**

📊 **حالة التسليم:** لم يتم التسليم بعد

📋 الوصف: {assignment.get('description', '')}

📤 لتسليم الحل، اضغط على الزر بالأسفل
        """
        
        keyboard = [
            [InlineKeyboardButton("📤 تسليم الحل", callback_data=f"submit_solution_{assignment_index}_{course_id}")],
            [InlineKeyboardButton("« رجوع", callback_data=f"assignments_{course_id}")]
        ]
    else:
        text = f"""
📝 **{assignment.get('title')}**

📊 **حالة التسليم:** ✅ تم التسليم
⏰ **وقت التسليم:** {submission.get('submitted_at', '')[:16]}
        """
        
        if submission.get('status') == 'graded':
            grade = submission.get('grade', 0)
            passed = grade >= 60
            text += f"""
📈 **الدرجة:** {grade}/100
{'✅ **النتيجة:** ناجح 🎉' if passed else '❌ **النتيجة:** راسب'}
            """
            
            if submission.get('feedback'):
                text += f"\n\n💬 **ملاحظات المدرس:**\n{submission.get('feedback')}"
            
            text += f"\n\n📅 **تاريخ التصحيح:** {submission.get('graded_at', '')[:16]}"
        else:
            text += "\n\n⏳ **الحالة:** قيد المراجعة..."
        
        keyboard = [
            [InlineKeyboardButton("🔄 إعادة التسليم", callback_data=f"submit_solution_{assignment_index}_{course_id}")],
            [InlineKeyboardButton("« رجوع", callback_data=f"assignments_{course_id}")]
        ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
