"""
Admin Course Statistics and Management
إحصائيات وإدارة الدورات للأدمن
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from pathlib import Path
import json

from config.settings import settings


async def show_course_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات شاملة لجميع الدورات"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return
    
    # Load all data
    courses_path = Path('data/courses.json')
    videos_path = Path('data/videos.json')
    assignments_path = Path('data/assignments.json')
    exams_path = Path('data/exams.json')
    submissions_path = Path('data/submissions.json')
    
    courses = []
    videos = []
    assignments = []
    exams = []
    submissions = []
    
    if courses_path.exists():
        with open(courses_path, 'r', encoding='utf-8') as f:
            courses = json.load(f)
    
    if videos_path.exists():
        with open(videos_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    
    if assignments_path.exists():
        with open(assignments_path, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    
    if exams_path.exists():
        with open(exams_path, 'r', encoding='utf-8') as f:
            exams = json.load(f)
    
    if submissions_path.exists():
        with open(submissions_path, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
    
    if not courses:
        await update.message.reply_text(
            "❌ لا توجد دورات بعد!\n\n"
            "أضف دورة من Dashboard أولاً."
        )
        return
    
    # Build statistics text
    text = "📊 **إحصائيات الدورات الشاملة**\n\n"
    text += f"📚 **إجمالي الدورات:** {len(courses)}\n"
    text += f"🎥 **إجمالي الفيديوهات:** {len(videos)}\n"
    text += f"📝 **إجمالي الواجبات:** {len(assignments)}\n"
    text += f"📋 **إجمالي الاختبارات:** {len(exams)}\n"
    text += f"📤 **إجمالي التسليمات:** {len(submissions)}\n\n"
    text += "---\n\n"
    
    keyboard = []
    
    # Show each course with details
    for course in courses:
        course_id = course.get('id')
        course_title = course.get('title', 'دورة بدون عنوان')
        
        # Count items for this course
        course_videos = [v for v in videos if v.get('item_id') == course_id]
        course_assignments = [a for a in assignments if a.get('item_id') == course_id]
        course_exams = [e for e in exams if e.get('course_id') == course_id]
        course_submissions = [s for s in submissions if s.get('course_id') == course_id]
        
        text += f"📚 **{course_title}**\n"
        text += f"   🆔 ID: `{course_id}`\n"
        text += f"   🎥 فيديوهات: {len(course_videos)}\n"
        text += f"   📝 واجبات: {len(course_assignments)}\n"
        text += f"   📋 اختبارات: {len(course_exams)}\n"
        text += f"   📤 تسليمات: {len(course_submissions)}\n\n"
        
        keyboard.append([
            InlineKeyboardButton(
                f"📊 تفاصيل {course_title[:20]}",
                callback_data=f"course_stats_{course_id}"
            )
        ])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_detailed_course_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تفاصيل دورة محددة"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("course_stats_", "")
    
    # Load all data
    courses_path = Path('data/courses.json')
    videos_path = Path('data/videos.json')
    assignments_path = Path('data/assignments.json')
    exams_path = Path('data/exams.json')
    submissions_path = Path('data/submissions.json')
    
    courses = []
    videos = []
    assignments = []
    exams = []
    submissions = []
    
    if courses_path.exists():
        with open(courses_path, 'r', encoding='utf-8') as f:
            courses = json.load(f)
    
    if videos_path.exists():
        with open(videos_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    
    if assignments_path.exists():
        with open(assignments_path, 'r', encoding='utf-8') as f:
            assignments = json.load(f)
    
    if exams_path.exists():
        with open(exams_path, 'r', encoding='utf-8') as f:
            exams = json.load(f)
    
    if submissions_path.exists():
        with open(submissions_path, 'r', encoding='utf-8') as f:
            submissions = json.load(f)
    
    # Find course
    course = next((c for c in courses if c.get('id') == course_id), None)
    if not course:
        await query.edit_message_text("❌ الدورة غير موجودة!")
        return
    
    # Get items for this course
    course_videos = [v for v in videos if v.get('item_id') == course_id]
    course_assignments = [a for a in assignments if a.get('item_id') == course_id]
    course_exams = [e for e in exams if e.get('course_id') == course_id]
    course_submissions = [s for s in submissions if s.get('course_id') == course_id]
    
    text = f"📚 **{course.get('title')}**\n\n"
    text += f"🆔 **ID:** `{course_id}`\n"
    text += f"💰 **السعر:** {course.get('price', 0)} SYP\n\n"
    
    # Videos section
    text += "🎥 **الفيديوهات:**\n"
    if course_videos:
        for i, v in enumerate(course_videos, 1):
            duration = v.get('duration', 0)
            mins = duration // 60
            text += f"   {i}. {v.get('title')} ({mins}دقيقة)\n"
    else:
        text += "   لا توجد فيديوهات\n"
    
    text += "\n"
    
    # Assignments section
    text += "📝 **الواجبات:**\n"
    if course_assignments:
        for i, a in enumerate(course_assignments, 1):
            text += f"   {i}. {a.get('title')}\n"
            # Count submissions for this assignment
            assign_subs = [s for s in course_submissions if s.get('assignment_index') == i-1]
            pending = len([s for s in assign_subs if s.get('status') == 'pending'])
            graded = len([s for s in assign_subs if s.get('status') == 'graded'])
            text += f"      📤 تسليمات: {len(assign_subs)} (🔄 {pending} بانتظار، ✅ {graded} مقيّمة)\n"
    else:
        text += "   لا توجد واجبات\n"
    
    text += "\n"
    
    # Exams section
    text += "📋 **الاختبارات:**\n"
    if course_exams:
        for i, e in enumerate(course_exams, 1):
            text += f"   {i}. {e.get('title')}\n"
            text += f"      🔗 {e.get('link')[:50]}...\n"
    else:
        text += "   لا توجد اختبارات\n"
    
    keyboard = [
        [InlineKeyboardButton("« رجوع للإحصائيات", callback_data="back_course_stats")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def back_to_course_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة لصفحة الإحصائيات"""
    query = update.callback_query
    await query.answer()
    
    # Simulate message to reuse show_course_statistics
    update.message = query.message
    await show_course_statistics(update, context)
