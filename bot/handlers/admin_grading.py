"""
Admin Grading Interface - Easy Grading System
واجهة التقييم للأدمن - نظام تقييم سهل
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from datetime import datetime
from pathlib import Path
import json

from database.models.user import User
from config.settings import settings

# Conversation states
SELECTING_ASSIGNMENT, SELECTING_STUDENT, ENTERING_GRADE, ENTERING_FEEDBACK = range(4)


async def start_grading_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة التقييم الرئيسية"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return ConversationHandler.END
    
    # Load submissions
    submissions_file = Path('data/submissions.json')
    if not submissions_file.exists():
        await update.message.reply_text(
            "❌ لا توجد تسليمات بعد!\n\n"
            "انتظر حتى يسلم الطلاب واجباتهم."
        )
        return ConversationHandler.END
    
    with open(submissions_file, 'r', encoding='utf-8') as f:
        submissions = json.load(f)
    
    # Get pending submissions (not graded yet)
    pending = [s for s in submissions if s.get('status') == 'pending']
    
    if not pending:
        await update.message.reply_text(
            "✅ **جميع الواجبات مقيّمة!**\n\n"
            "لا توجد تسليمات بانتظار التقييم.\n\n"
            "رائع! أنت على اطلاع 👍"
        )
        return ConversationHandler.END
    
    # Group by assignment
    assignments_map = {}
    for sub in pending:
        key = f"{sub['course_id']}_{sub['assignment_index']}"
        if key not in assignments_map:
            assignments_map[key] = {
                'title': sub['assignment_title'],
                'course_id': sub['course_id'],
                'assignment_index': sub['assignment_index'],
                'count': 0,
                'submissions': []
            }
        assignments_map[key]['count'] += 1
        assignments_map[key]['submissions'].append(sub)
    
    # Show list
    text = "📝 **تقييم الواجبات**\n\n"
    text += "الواجبات بانتظار التقييم:\n\n"
    
    keyboard = []
    for key, data in assignments_map.items():
        text += f"📌 {data['title']} - {data['count']} طالب\n"
        keyboard.append([
            InlineKeyboardButton(
                f"📝 {data['title']} ({data['count']} طالب)",
                callback_data=f"grade_assign_{key}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="grade_cancel")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_ASSIGNMENT


async def select_assignment_for_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الواجب للتقييم"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "grade_cancel":
        await query.edit_message_text("❌ تم الإلغاء.")
        context.user_data.clear()
        return ConversationHandler.END
    
    # Extract assignment info: grade_assign_{course_id}_{assignment_index}
    parts = query.data.replace("grade_assign_", "").split('_')
    assignment_index = int(parts[-1])
    course_id = '_'.join(parts[:-1])
    
    # Load assignments
    assignments_file = Path('data/assignments.json')
    with open(assignments_file, 'r', encoding='utf-8') as f:
        assignments = json.load(f)
    
    # Get assignment from assignments by matching index position
    max_grade = 100  # Default
    assignment_title = 'الواجب'
    
    # Filter assignments for this course
    course_assignments = [a for a in assignments if a.get('item_id') == course_id]
    
    if assignment_index < len(course_assignments):
        assignment = course_assignments[assignment_index]
        assignment_title = assignment.get('title', 'الواجب')
        max_grade = assignment.get('max_grade', 100)  # Get max grade from assignment
    
    # Store grading info
    context.user_data['grading_assignment_index'] = assignment_index
    context.user_data['grading_assignment_title'] = assignment_title
    context.user_data['grading_course_id'] = course_id
    context.user_data['grading_max_grade'] = max_grade
    
    # Load submissions
    submissions_file = Path('data/submissions.json')
    with open(submissions_file, 'r', encoding='utf-8') as f:
        submissions = json.load(f)
    
    # Filter pending submissions for this assignment
    pending = [
        s for s in submissions 
        if s.get('course_id') == course_id 
        and s.get('assignment_index') == assignment_index
        and s.get('status') == 'pending'
    ]
    
    if not pending:
        await query.edit_message_text("❌ لا توجد تسليمات بانتظار التقييم لهذا الواجب.")
        return ConversationHandler.END
    
    # Show students list
    text = f"📝 **{assignment_title}**\n\n"
    text += "الطلاب بانتظار التقييم:\n\n"
    
    keyboard = []
    for sub in pending:
        text += f"👤 {sub['student_name']}\n"
        keyboard.append([
            InlineKeyboardButton(
                f"👤 {sub['student_name']}",
                callback_data=f"grade_student_{sub['student_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data="grade_back")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_STUDENT


async def select_student_for_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الطالب للتقييم"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "grade_back":
        # Go back to assignment selection
        context.user_data.clear()
        await query.edit_message_text("تم الإلغاء. استخدم /grade_assignments للبدء من جديد.")
        return ConversationHandler.END
    
    # Extract student_id: grade_student_{student_id}
    student_id = query.data.replace("grade_student_", "")
    context.user_data['grading_student_id'] = student_id
    
    # Get student info
    user = await User.find_one(User.telegram_id == int(student_id))
    if not user:
        await query.edit_message_text("❌ الطالب غير موجود!")
        return ConversationHandler.END
    
    context.user_data['grading_student_name'] = user.full_name
    
    # Load submission
    submissions_file = Path('data/submissions.json')
    with open(submissions_file, 'r', encoding='utf-8') as f:
        submissions = json.load(f)
    
    course_id = context.user_data['grading_course_id']
    assignment_index = context.user_data['grading_assignment_index']
    
    submission = None
    for s in submissions:
        if (s.get('student_id') == student_id and
            s.get('course_id') == course_id and
            s.get('assignment_index') == assignment_index):
            submission = s
            break
    
    if not submission:
        await query.edit_message_text("❌ التسليم غير موجود!")
        return ConversationHandler.END
    
    # Send the submitted file to admin for review
    try:
        file_id = submission.get('file_id')
        file_type = submission.get('file_type')
        
        caption = f"""
📝 **{submission['assignment_title']}**
👤 الطالب: {user.full_name}
🆔 ID: {student_id}
⏰ وقت التسليم: {submission['submitted_at'][:16]}

---

✍️ الآن أدخل **الدرجة** (من 0 إلى {context.user_data['grading_max_grade']}):
        """
        
        if file_type == "document":
            await context.bot.send_document(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                document=file_id,
                caption=caption,
                parse_mode="Markdown"
            )
        elif file_type == "photo":
            await context.bot.send_photo(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                photo=file_id,
                caption=caption,
                parse_mode="Markdown"
            )
        elif file_type == "video":
            await context.bot.send_video(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                video=file_id,
                caption=caption,
                parse_mode="Markdown"
            )
        
        await query.edit_message_text(
            f"✅ تم عرض حل {user.full_name}\n\n"
            f"✍️ الآن أدخل **الدرجة** (من 0 إلى {context.user_data['grading_max_grade']}):",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error sending file: {e}")
        await query.edit_message_text(
            f"⚠️ لم أتمكن من إرسال الملف، لكن يمكنك المتابعة.\n\n"
            f"✍️ أدخل **الدرجة** (من 0 إلى {context.user_data['grading_max_grade']}):",
            parse_mode="Markdown"
        )
    
    return ENTERING_GRADE


async def enter_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال الدرجة"""
    max_grade = context.user_data.get('grading_max_grade', 100)
    
    try:
        grade = float(update.message.text.strip())
        
        if grade < 0 or grade > max_grade:
            await update.message.reply_text(
                f"❌ الدرجة يجب أن تكون بين 0 و {max_grade}!\n\n"
                "أدخل الدرجة مرة أخرى:"
            )
            return ENTERING_GRADE
        
        context.user_data['grading_grade'] = grade
        
        student_name = context.user_data.get('grading_student_name', 'الطالب')
        
        await update.message.reply_text(
            f"✅ الدرجة: {grade}/{max_grade}\n\n"
            f"💬 الآن أدخل **التعليق** للطالب {student_name}:\n\n"
            f"أمثلة:\n"
            f"• ممتاز! عمل رائع 🎉\n"
            f"• جيد، لكن يحتاج تحسين في النقطة X\n"
            f"• حل صحيح، واصل التميز!\n\n"
            f"أو اكتب: لا يوجد (إذا لم تكن هناك ملاحظات)"
        )
        
        return ENTERING_FEEDBACK
        
    except ValueError:
        await update.message.reply_text(
            "❌ يجب أن تكون الدرجة رقماً!\n\n"
            "مثال: 95\n\n"
            "أدخل الدرجة مرة أخرى:"
        )
        return ENTERING_GRADE


async def enter_feedback_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال التعليق وحفظ التقييم"""
    feedback = update.message.text.strip()
    
    if feedback.lower() in ['لا يوجد', 'لا توجد', 'no', '-']:
        feedback = "لا توجد ملاحظات"
    
    # Get data from context
    student_id = context.user_data.get('grading_student_id')
    student_name = context.user_data.get('grading_student_name')
    course_id = context.user_data.get('grading_course_id')
    assignment_index = context.user_data.get('grading_assignment_index')
    grade = context.user_data.get('grading_grade')
    max_grade = context.user_data.get('grading_max_grade', 100)
    
    # Load submissions
    submissions_file = Path('data/submissions.json')
    with open(submissions_file, 'r', encoding='utf-8') as f:
        submissions = json.load(f)
    
    # Find and update submission
    submission = None
    for s in submissions:
        if (s.get('student_id') == student_id and
            s.get('course_id') == course_id and
            s.get('assignment_index') == assignment_index):
            submission = s
            s['status'] = 'graded'
            s['grade'] = grade
            s['feedback'] = feedback
            s['graded_at'] = datetime.now().isoformat()
            break
    
    if not submission:
        await update.message.reply_text("❌ حدث خطأ! التسليم غير موجود.")
        context.user_data.clear()
        return ConversationHandler.END
    
    # Save submissions
    with open(submissions_file, 'w', encoding='utf-8') as f:
        json.dump(submissions, f, ensure_ascii=False, indent=2)
    
    # Determine pass/fail (50% of max grade)
    passing_grade = max_grade / 2
    is_passing = grade >= passing_grade
    
    # Confirm to admin
    await update.message.reply_text(
        f"✅ **تم حفظ التقييم بنجاح!**\n\n"
        f"👤 الطالب: {student_name}\n"
        f"📝 الواجب: {submission['assignment_title']}\n"
        f"📊 الدرجة: {grade}/{max_grade}\n"
        f"{'✅ ناجح' if is_passing else '❌ راسب'}\n"
        f"💬 التعليق: {feedback}\n\n"
        f"⏳ جاري إرسال الإشعار للطالب...",
        parse_mode="Markdown"
    )
    
    # Notify student
    try:
        status_emoji = "✅" if is_passing else "❌"
        status_text = "ناجح 🎉" if is_passing else "راسب"
        
        student_text = f"""
🔔 **تم تصحيح واجبك!**

📝 **الواجب:** {submission['assignment_title']}
📊 **الدرجة:** {grade}/{max_grade}
{status_emoji} **النتيجة:** {status_text}

💬 **ملاحظات المدرس:**
{feedback}

📅 **تاريخ التصحيح:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

{'🎉 مبارك! واصل التميز!' if is_passing else '💪 لا تستسلم! يمكنك تحسين أدائك في الواجبات القادمة'}
"""
        
        await context.bot.send_message(
            chat_id=int(student_id),
            text=student_text,
            parse_mode="Markdown"
        )
        
        await update.message.reply_text(
            f"✅ تم إرسال الإشعار إلى {student_name}!\n\n"
            f"🎉 التقييم مكتمل!",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Failed to notify student: {e}")
        await update.message.reply_text(
            f"⚠️ تم حفظ التقييم لكن فشل إرسال الإشعار للطالب.\n"
            f"الخطأ: {str(e)}",
            parse_mode="Markdown"
        )
    
    # Clear context
    context.user_data.clear()
    
    # Ask if admin wants to grade more
    keyboard = [
        [InlineKeyboardButton("✅ تقييم واجب آخر", callback_data="grade_more")],
        [InlineKeyboardButton("❌ انتهيت", callback_data="grade_done")]
    ]
    
    await update.message.reply_text(
        "هل تريد تقييم واجب آخر؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return ConversationHandler.END


async def grade_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييم واجب آخر"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "grade_done":
        await query.edit_message_text("✅ تم الانتهاء من التقييم. شكراً! 🙏")
        return
    
    # Restart the grading process
    await query.edit_message_text("جاري تحميل قائمة الواجبات...")
    
    # Simulate a new message to restart
    update.message = query.message
    await start_grading_menu(update, context)


async def cancel_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء عملية التقييم"""
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.edit_message_text("❌ تم إلغاء التقييم.")
    else:
        await update.message.reply_text("❌ تم إلغاء التقييم.")
    
    return ConversationHandler.END
