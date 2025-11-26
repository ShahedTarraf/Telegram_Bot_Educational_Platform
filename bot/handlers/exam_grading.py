"""
Exam Grading System
نظام تقييم الاختبارات - مشابه لنظام تقييم الواجبات
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from pathlib import Path
import json
from datetime import datetime

from config.settings import settings
from database.models.user import User

# Conversation states
SELECTING_EXAM = 1
SELECTING_STUDENT_EXAM = 2
ENTERING_EXAM_GRADE = 3
ENTERING_EXAM_FEEDBACK = 4


async def start_exam_grading_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء قائمة تقييم الاختبارات"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return ConversationHandler.END
    
    # Load exams
    exams_path = Path('data/exams.json')
    if not exams_path.exists():
        await update.message.reply_text(
            "❌ لا توجد اختبارات بعد!\n\n"
            "أضف اختبار باستخدام زر \"📋 إنشاء اختبار\" أولاً."
        )
        return ConversationHandler.END
    
    with open(exams_path, 'r', encoding='utf-8') as f:
        exams = json.load(f)
    
    if not exams:
        await update.message.reply_text("❌ لا توجد اختبارات بعد!")
        return ConversationHandler.END
    
    # Create exam grades file if not exists
    grades_path = Path('data/exam_grades.json')
    if not grades_path.exists():
        with open(grades_path, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    
    # Load exam grades
    with open(grades_path, 'r', encoding='utf-8') as f:
        exam_grades = json.load(f)
    
    text = "📊 **تقييم الاختبارات**\n\n"
    text += "اختر الاختبار الذي تريد تقييمه:\n\n"
    
    keyboard = []
    
    for i, exam in enumerate(exams):
        title = exam.get('title', f'اختبار {i+1}')
        course_id = exam.get('course_id', 'unknown')
        
        # Count graded students for this exam
        graded_count = len([g for g in exam_grades if g.get('exam_index') == i and g.get('status') == 'graded'])
        
        button_text = f"📋 {title}"
        if graded_count > 0:
            button_text += f" ({graded_count} مقيّمة)"
        
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"grade_exam_{i}")
        ])
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_exam_grading")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_EXAM


async def select_exam_for_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار اختبار للتقييم"""
    query = update.callback_query
    await query.answer()
    
    exam_index = int(query.data.split('_')[2])
    
    # Load exams
    exams_path = Path('data/exams.json')
    with open(exams_path, 'r', encoding='utf-8') as f:
        exams = json.load(f)
    
    if exam_index >= len(exams):
        await query.edit_message_text("❌ الاختبار غير موجود!")
        return ConversationHandler.END
    
    exam = exams[exam_index]
    course_id = exam.get('course_id')
    
    # Store exam info in context
    context.user_data['exam_index'] = exam_index
    context.user_data['exam_title'] = exam.get('title', 'الاختبار')
    context.user_data['course_id'] = course_id
    
    # Get students enrolled in this course
    try:
        all_students = await User.find().to_list()
        students = [s for s in all_students if s.has_approved_course(course_id)]
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        students = []
    
    if not students:
        await query.edit_message_text(
            f"❌ لا يوجد طلاب مسجلين في دورة هذا الاختبار!\n\n"
            f"الاختبار: {exam.get('title')}"
        )
        return ConversationHandler.END
    
    # Load exam grades
    grades_path = Path('data/exam_grades.json')
    with open(grades_path, 'r', encoding='utf-8') as f:
        exam_grades = json.load(f)
    
    text = f"📋 **{exam.get('title')}**\n\n"
    text += "اختر الطالب لتقييم اختباره:\n\n"
    
    keyboard = []
    
    for student in students:
        # Check if already graded
        existing_grade = next(
            (g for g in exam_grades 
             if g.get('student_id') == str(student.telegram_id) 
             and g.get('exam_index') == exam_index),
            None
        )
        
        button_text = f"👤 {student.full_name}"
        if existing_grade:
            if existing_grade.get('status') == 'graded':
                grade = existing_grade.get('grade', 0)
                button_text += f" ✅ ({grade})"
            else:
                button_text += " ⏳"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"grade_exam_student_{exam_index}_{student.telegram_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data="back_exam_grading")])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="cancel_exam_grading")])
    
    # Store exam index in context
    context.user_data['grading_exam_index'] = exam_index
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return SELECTING_STUDENT_EXAM


async def select_student_for_exam_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار طالب لتقييم اختباره"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    exam_index = int(parts[3])
    student_id = parts[4]
    
    # Get student
    student = await User.find_one(User.telegram_id == int(student_id))
    if not student:
        await query.edit_message_text("❌ الطالب غير موجود!")
        return ConversationHandler.END
    
    # Load exams
    exams_path = Path('data/exams.json')
    with open(exams_path, 'r', encoding='utf-8') as f:
        exams = json.load(f)
    
    exam = exams[exam_index]
    max_grade = exam.get('max_grade', 100)  # Get max grade from exam
    
    # Store in context
    context.user_data['grading_exam_index'] = exam_index
    context.user_data['grading_student_id'] = student_id
    context.user_data['grading_student_name'] = student.full_name
    context.user_data['exam_title'] = exam.get('title')
    context.user_data['exam_max_grade'] = max_grade
    
    text = f"📊 **تقييم الاختبار**\n\n"
    text += f"📋 **الاختبار:** {exam.get('title')}\n"
    text += f"👤 **الطالب:** {student.full_name}\n"
    text += f"🔗 **رابط الاختبار:** {exam.get('link')}\n\n"
    text += f"✏️ **أدخل الدرجة** (من 0 إلى {max_grade}):"
    
    keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel_exam_grading")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return ENTERING_EXAM_GRADE


async def enter_exam_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال درجة الاختبار"""
    max_grade = context.user_data.get('exam_max_grade', 100)
    
    try:
        grade = float(update.message.text.strip())
        
        # Determine pass/fail (50% of max grade)
        passing_grade = max_grade / 2
        is_passing = grade >= passing_grade
        
        if grade < 0 or grade > max_grade:
            await update.message.reply_text(
                f"❌ الدرجة يجب أن تكون بين 0 و {max_grade}\n\n"
                "أدخل الدرجة مرة أخرى:"
            )
            return ENTERING_EXAM_GRADE
        
        context.user_data['exam_grade'] = grade
        
        exam_title = context.user_data.get('exam_title', 'الاختبار')
        student_name = context.user_data.get('grading_student_name', 'الطالب')
        
        text = f"✅ **تم حفظ الدرجة: {grade}/{max_grade}**\n\n"
        text += f"📋 **الاختبار:** {exam_title}\n"
        text += f"👤 **الطالب:** {student_name}\n\n"
        text += "💬 **الآن أدخل ملاحظاتك** (مثال: أداء ممتاز!):"
        
        keyboard = [[InlineKeyboardButton("❌ إلغاء", callback_data="cancel_exam_grading")]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        return ENTERING_EXAM_FEEDBACK
        
    except ValueError:
        await update.message.reply_text(
            "❌ يرجى إدخال رقم صحيح!\n\n"
            "مثال: 85\n\n"
            "أدخل الدرجة:"
        )
        return ENTERING_EXAM_GRADE


async def enter_exam_feedback_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال الملاحظات وحفظ التقييم"""
    feedback = update.message.text.strip()
    
    exam_index = context.user_data.get('grading_exam_index')
    student_id = context.user_data.get('grading_student_id')
    student_name = context.user_data.get('grading_student_name')
    exam_title = context.user_data.get('exam_title')
    course_id = context.user_data.get('course_id')
    grade = context.user_data.get('exam_grade')
    max_grade = context.user_data.get('exam_max_grade', 100)
    
    # Load exam grades
    grades_path = Path('data/exam_grades.json')
    with open(grades_path, 'r', encoding='utf-8') as f:
        exam_grades = json.load(f)
    
    # Load exams to get course_id
    exams_path = Path('data/exams.json')
    with open(exams_path, 'r', encoding='utf-8') as f:
        exams = json.load(f)
    
    exam = exams[exam_index]
    course_id = exam.get('course_id')
    
    # Check if grade exists
    existing_grade = next(
        (g for g in exam_grades 
         if g.get('student_id') == student_id 
         and g.get('exam_index') == exam_index),
        None
    )
    
    grade_data = {
        'student_id': student_id,
        'student_name': student_name,
        'course_id': course_id,
        'exam_index': exam_index,
        'exam_title': exam_title,
        'grade': grade,
        'feedback': feedback,
        'status': 'graded',
        'graded_at': datetime.now().isoformat()
    }
    
    if existing_grade:
        # Update existing grade
        exam_grades[exam_grades.index(existing_grade)] = grade_data
    else:
        # Add new grade
        exam_grades.append(grade_data)
    
    # Save
    with open(grades_path, 'w', encoding='utf-8') as f:
        json.dump(exam_grades, f, ensure_ascii=False, indent=2)
    
    # Send notification to student
    try:
        status_emoji = "✅" if grade >= max_grade / 2 else "❌"
        status_text = "ناجح" if grade >= max_grade / 2 else "راسب"
        
        encouragement = "🎉 مبروك! استمر في التقدم!" if grade >= max_grade / 2 else "💪 لا تستسلم! راجع المادة وحاول مجدداً"
        
        student_message = f"""
✅ **تم تقييم اختبارك!**

📋 **الاختبار:** {exam_title}

📊 **نتيجتك:**
• الدرجة: {grade}/{max_grade}
• الحالة: {status_text}

💬 **ملاحظات المدرس:**
{feedback}

{encouragement}
        """
        
        await context.bot.send_message(
            chat_id=int(student_id),
            text=student_message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending exam grade notification: {e}")
    
    # Confirm to admin
    confirmation = f"""
✅ **تم حفظ التقييم بنجاح!**

👤 **الطالب:** {student_name}
📋 **الاختبار:** {exam_title}
📊 **الدرجة:** {grade}/{max_grade}
{status_emoji} **النتيجة:** {status_text}
💬 **الملاحظات:** {feedback}

✉️ تم إرسال إشعار للطالب

هل تريد تقييم اختبار آخر؟
    """
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم، تقييم طالب آخر", callback_data="grade_more_exam")],
        [InlineKeyboardButton("✔️ تم الانتهاء", callback_data="grade_done_exam")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END


async def grade_more_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تقييم المزيد من الاختبارات"""
    query = update.callback_query
    await query.answer()
    
    # Restart the conversation
    update.message = query.message
    return await start_exam_grading_menu(update, context)


async def cancel_exam_grading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء تقييم الاختبارات"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ تم إلغاء عملية التقييم.")
    
    # Clear context
    context.user_data.clear()
    
    return ConversationHandler.END
