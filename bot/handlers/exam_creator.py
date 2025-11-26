"""
Exam Creator Handler (Google Forms Links)
معالج إنشاء الاختبارات عبر روابط Google Forms
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
import json
from pathlib import Path

from config.settings import settings

# Conversation states
EXAM_SELECTING_TYPE, EXAM_SELECTING_COURSE, EXAM_ENTERING_TITLE, EXAM_ENTERING_LINK, EXAM_ENTERING_MAX_GRADE = range(5)


async def start_create_exam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء إنشاء اختبار جديد"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذه الوظيفة متاحة للأدمن فقط.")
        return ConversationHandler.END
    
    text = "📋 **إنشاء اختبار جديد**\n\nاختر نوع المحتوى:"
    keyboard = [
        [InlineKeyboardButton("🎓 الدورات الاحترافية", callback_data="exam_type_courses")],
        [InlineKeyboardButton("📚 المواد الجامعية", callback_data="exam_type_university")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="exam_cancel")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return EXAM_SELECTING_TYPE


async def select_exam_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار نوع المحتوى (دورات أو مواد جامعية)"""
    query = update.callback_query
    await query.answer()
    
    exam_type = query.data.replace("exam_type_", "")
    context.user_data['exam_type'] = exam_type
    
    if exam_type == "courses":
        # Load courses from courses_config.py
        from config.courses_config import get_all_courses
        
        try:
            courses = get_all_courses()
            
            if not courses or len(courses) == 0:
                await query.edit_message_text(
                    "❌ لا توجد دورات متاحة!\n\n"
                    "يرجى إضافة دورات في config/courses_config.py"
                )
                return ConversationHandler.END
        except Exception as e:
            logger.error(f"Error loading courses: {e}")
            await query.edit_message_text(f"❌ حدث خطأ في تحميل الدورات: {str(e)}")
            return ConversationHandler.END
        
        text = "🎓 **الدورات الاحترافية**\n\nاختر الدورة:"
        keyboard = []
        
        for course in courses:
            keyboard.append([
                InlineKeyboardButton(
                    course.get('name', 'دورة بدون عنوان'),
                    callback_data=f"exam_course_{course.get('id', 'unknown')}"
                )
            ])
    
    elif exam_type == "university":
        text = "📚 **المواد الجامعية**\n\nاختر السنة:"
        keyboard = [
            [InlineKeyboardButton("السنة الثالثة", callback_data="exam_course_year_3")],
            [InlineKeyboardButton("السنة الرابعة", callback_data="exam_course_year_4")],
            [InlineKeyboardButton("السنة الخامسة", callback_data="exam_course_year_5")],
        ]
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data="exam_back_type"),
                     InlineKeyboardButton("❌ إلغاء", callback_data="exam_cancel")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return EXAM_SELECTING_COURSE


async def select_exam_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار الدورة أو المادة الجامعية للاختبار"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("exam_course_", "")
    context.user_data['exam_course_id'] = course_id
    
    exam_type = context.user_data.get('exam_type', 'courses')
    
    if exam_type == 'courses':
        # Get course name from courses_config.py
        from config.courses_config import get_course
        
        course = get_course(course_id)
        
        if not course:
            await query.edit_message_text("❌ الدورة غير موجودة!")
            return ConversationHandler.END
        
        context.user_data['exam_course_name'] = course['name']
        selected_name = course['name']
    
    elif exam_type == 'university':
        # Handle university years
        if course_id.startswith('year_'):
            year = course_id.replace('year_', '')
            context.user_data['exam_course_name'] = f"السنة {year}"
            selected_name = f"السنة {year}"
        else:
            await query.edit_message_text("❌ اختيار غير صحيح!")
            return ConversationHandler.END
    
    await query.edit_message_text(
        f"✅ تم اختيار: **{selected_name}**\n\n"
        f"📝 الآن أدخل **عنوان الاختبار**:\n\n"
        f"مثال: الاختبار الأول - Python Basics",
        parse_mode="Markdown"
    )
    
    return EXAM_ENTERING_TITLE


async def enter_exam_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال عنوان الاختبار"""
    exam_title = update.message.text.strip()
    
    if len(exam_title) < 3:
        await update.message.reply_text("❌ العنوان قصير جداً! أدخل عنوان أطول:")
        return EXAM_ENTERING_TITLE
    
    context.user_data['exam_title'] = exam_title
    
    await update.message.reply_text(
        f"✅ العنوان: **{exam_title}**\n\n"
        f"🔗 الآن أدخل **رابط Google Forms**:\n\n"
        f"مثال:\n"
        f"https://forms.gle/xxxxx\n\n"
        f"💡 تأكد أن الرابط يعمل!"
    )
    
    return EXAM_ENTERING_LINK


async def enter_exam_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال رابط الاختبار"""
    exam_link = update.message.text.strip()
    
    # Basic validation
    if not exam_link.startswith('http'):
        await update.message.reply_text(
            "❌ الرابط غير صحيح!\n\n"
            "يجب أن يبدأ بـ http:// أو https://\n\n"
            "أدخل الرابط مرة أخرى:"
        )
        return EXAM_ENTERING_LINK
    
    context.user_data['exam_link'] = exam_link
    
    # Ask for max grade
    text = f"""✅ **تم حفظ الرابط**

🔗 الرابط: {exam_link}

🎯 **الآن أدخل الدرجة القصوى للاختبار:**

مثال: 100 أو 50 أو 20

(افتراضياً سيكون من 100 إذا لم تدخل)"""
    
    keyboard = [
        [InlineKeyboardButton("استخدام 100 (افتراضي)", callback_data="exam_grade_100")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="exam_cancel")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return EXAM_ENTERING_MAX_GRADE


async def enter_exam_max_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إدخال الدرجة القصوى وحفظ الاختبار"""
    # Check if callback (default 100) or text message
    if update.callback_query:
        max_grade = 100
        query = update.callback_query
        await query.answer()
        message_to_reply = query.message
    else:
        try:
            max_grade = float(update.message.text.strip())
            if max_grade <= 0:
                await update.message.reply_text("❌ الدرجة يجب أن تكون أكبر من 0")
                return EXAM_ENTERING_MAX_GRADE
            message_to_reply = update.message
        except:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح")
            return EXAM_ENTERING_MAX_GRADE
    
    # Save exam
    try:
        exams_path = Path("data/exams.json")
        exams = []
        
        if exams_path.exists():
            with open(exams_path, 'r', encoding='utf-8') as f:
                exams = json.load(f)
        
        new_exam = {
            'course_id': context.user_data['exam_course_id'],
            'title': context.user_data['exam_title'],
            'link': context.user_data['exam_link'],
            'description': f"اختبار لدورة {context.user_data['exam_course_name']}",
            'max_grade': max_grade
        }
        
        exams.append(new_exam)
        
        with open(exams_path, 'w', encoding='utf-8') as f:
            json.dump(exams, f, ensure_ascii=False, indent=2)
        
        await message_to_reply.reply_text(
            f"✅ **تم إنشاء الاختبار بنجاح!**\n\n"
            f"📚 الدورة: {context.user_data['exam_course_name']}\n"
            f"📝 العنوان: {context.user_data['exam_title']}\n"
            f"🔗 الرابط: {context.user_data['exam_link']}\n"
            f"🎯 الدرجة القصوى: {max_grade}\n\n"
            f"🎉 يمكن للطلاب الآن الوصول للاختبار!"
        )
        
        logger.info(f"Exam created: {new_exam}")
        
    except Exception as e:
        logger.error(f"Error creating exam: {e}")
        await message_to_reply.reply_text("❌ حدث خطأ في حفظ الاختبار!")
    
    # Clear context
    context.user_data.clear()
    return ConversationHandler.END


async def back_to_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الرجوع إلى اختيار نوع المحتوى"""
    query = update.callback_query
    await query.answer()
    
    text = "📋 **إنشاء اختبار جديد**\n\nاختر نوع المحتوى:"
    keyboard = [
        [InlineKeyboardButton("🎓 الدورات الاحترافية", callback_data="exam_type_courses")],
        [InlineKeyboardButton("📚 المواد الجامعية", callback_data="exam_type_university")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="exam_cancel")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return EXAM_SELECTING_TYPE


async def cancel_exam_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء إنشاء الاختبار"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("❌ تم إلغاء إنشاء الاختبار.")
    else:
        await update.message.reply_text("❌ تم إلغاء إنشاء الاختبار.")
    
    context.user_data.clear()
    return ConversationHandler.END
