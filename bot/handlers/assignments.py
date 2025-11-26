"""
Assignments & Exams Management for Admin
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger
from datetime import datetime, timedelta

from config.settings import settings
from config.courses_config import get_all_courses

# Conversation states
SELECTING_ITEM, ENTERING_TITLE, ENTERING_DESCRIPTION, UPLOADING_FILE, ENTERING_DEADLINE, ENTERING_MAX_GRADE = range(6)


async def create_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start creating assignment"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return ConversationHandler.END
    
    context.user_data['assignment_type'] = 'assignment'
    
    keyboard = [
        [InlineKeyboardButton("📚 الدورات", callback_data="assign_type_courses")],
        [InlineKeyboardButton("🎓 المواد", callback_data="assign_type_materials")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="assign_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "📝 إنشاء واجب جديد\n\nاختر النوع:"
    
    logger.info(f"Sending assignment creation menu to admin {user_id}")
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    
    return SELECTING_ITEM


async def select_assignment_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select course or material for assignment"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "assign_cancel":
        await query.message.reply_text("❌ تم الإلغاء")
        context.user_data.clear()
        return ConversationHandler.END
    
    item_type = query.data.replace("assign_type_", "")
    context.user_data['item_type'] = item_type
    
    keyboard = []
    
    if item_type == "courses":
        courses = get_all_courses()
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course['name'],
                callback_data=f"assign_item_{course['id']}"
            )])
        text = "📚 اختر الدورة:"
    else:
        from config.materials_config import get_all_materials
        materials = get_all_materials()
        for material in materials:
            keyboard.append([InlineKeyboardButton(
                f"{material['name']} - س{material['year']} ف{material['semester']}",
                callback_data=f"assign_item_{material['id']}"
            )])
        text = "🎓 اختر المادة:"
    
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="assign_cancel")])
    
    logger.info(f"Showing {len(keyboard)-1} items for {item_type}")
    
    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_ITEM


async def select_assignment_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Item selected, ask for title"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "assign_cancel":
        await query.message.reply_text("❌ تم الإلغاء")
        context.user_data.clear()
        return ConversationHandler.END
    
    if query.data.startswith("assign_type_"):
        return await select_assignment_type(update, context)
    
    item_id = query.data.replace("assign_item_", "")
    context.user_data['item_id'] = item_id
    
    assignment_type = context.user_data.get('assignment_type', 'assignment')
    type_label = "الواجب" if assignment_type == "assignment" else "الاختبار"
    
    text = f"""
✅ تم اختيار الدورة/المادة

📝 الآن أدخل عنوان {type_label}:

مثال: الواجب الأول - Python Basics
    """
    
    await query.message.edit_text(text)
    
    return ENTERING_TITLE


async def enter_assignment_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Title entered, ask for description"""
    title = update.message.text.strip()
    context.user_data['title'] = title
    
    assignment_type = context.user_data.get('assignment_type', 'assignment')
    type_label = "الواجب" if assignment_type == "assignment" else "الاختبار"
    
    text = f"""
✅ العنوان: {title}

📋 الآن أدخل وصف {type_label}:

مثال: حل التمارين التالية وإرسال الحل على شكل ملف PDF
    """
    
    await update.message.reply_text(text)
    
    return ENTERING_DESCRIPTION


async def enter_assignment_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Description entered, ask for PDF file"""
    description = update.message.text.strip()
    context.user_data['description'] = description
    
    assignment_type = context.user_data.get('assignment_type', 'assignment')
    type_label = "الواجب" if assignment_type == "assignment" else "الاختبار"
    
    text = f"""
✅ الوصف: {description}

📎 الآن أرسل **ملف PDF** للواجب:

💡 تأكد أن الملف:
• بصيغة PDF
• يحتوي على الأسئلة والتعليمات
• واضح وقابل للقراءة

أرسل الملف الآن:
    """
    
    await update.message.reply_text(text)
    
    return UPLOADING_FILE


async def upload_assignment_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """PDF file uploaded, ask for deadline"""
    # Check if it's a document
    if not update.message.document:
        await update.message.reply_text(
            "❌ يرجى إرسال **ملف PDF**!\n\n"
            "تأكد من إرسال الملف كمستند (Document) وليس صورة."
        )
        return UPLOADING_FILE
    
    file = update.message.document
    
    # Check if it's PDF
    if not file.file_name.lower().endswith('.pdf'):
        await update.message.reply_text(
            "❌ يجب أن يكون الملف بصيغة **PDF**!\n\n"
            f"الملف المرسل: {file.file_name}\n\n"
            "أرسل ملف PDF من فضلك:"
        )
        return UPLOADING_FILE
    
    # Download and save file
    file_data = await file.get_file()
    file_id = file.file_id
    file_name = file.file_name
    
    # Store file info
    context.user_data['file_id'] = file_id
    context.user_data['file_name'] = file_name
    
    assignment_type = context.user_data.get('assignment_type', 'assignment')
    type_label = "الواجب" if assignment_type == "assignment" else "الاختبار"
    
    text = f"""
✅ تم استلام الملف: {file_name}

⏰ الآن أدخل الموعد النهائي (بالأيام):

مثال: 7 (أي خلال 7 أيام من الآن)
أو 0 لعدم تحديد موعد نهائي
    """
    
    await update.message.reply_text(text)
    
    return ENTERING_DEADLINE


async def enter_assignment_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deadline entered, ask for max grade"""
    try:
        days = int(update.message.text.strip())
        deadline = datetime.now() + timedelta(days=days)
    except:
        await update.message.reply_text("❌ يرجى إدخال رقم صحيح (عدد الأيام)")
        return ENTERING_DEADLINE
    
    context.user_data['deadline'] = deadline
    
    text = f"""✅ **تم حفظ الموعد النهائي**

⏰ الموعد: {deadline.strftime('%Y-%m-%d %H:%M')}

🎯 **الآن أدخل الدرجة القصوى للواجب:**

مثال: 100 أو 50 أو 20

(افتراضياً سيكون من 100 إذا لم تدخل)"""
    
    keyboard = [
        [InlineKeyboardButton("استخدام 100 (افتراضي)", callback_data="max_grade_100")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_assignment")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    return ENTERING_MAX_GRADE


async def enter_max_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Max grade entered, save assignment"""
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
                return ENTERING_MAX_GRADE
            message_to_reply = update.message
        except:
            await update.message.reply_text("❌ يرجى إدخال رقم صحيح")
            return ENTERING_MAX_GRADE
    
    # Get saved data
    assignment_type = context.user_data.get('assignment_type', 'assignment')
    item_type = context.user_data.get('item_type', 'courses')
    item_id = context.user_data.get('item_id')
    title = context.user_data.get('title')
    description = context.user_data.get('description')
    questions = context.user_data.get('questions')
    deadline = context.user_data.get('deadline')
    
    # Save to JSON
    import json
    from pathlib import Path
    
    file_name = 'assignments.json' if assignment_type == 'assignment' else 'exams.json'
    file_path = Path(f'data/{file_name}')
    file_path.parent.mkdir(exist_ok=True)
    
    assignments = []
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                assignments = json.load(f)
            except:
                assignments = []
    
    file_id = context.user_data.get('file_id')
    file_name = context.user_data.get('file_name')
    
    assignment_data = {
        'type': item_type,
        'item_id': item_id,
        'title': title,
        'description': description,
        'file_id': file_id,
        'file_name': file_name,
        'deadline': deadline.isoformat(),
        'max_grade': max_grade,
        'created_at': datetime.now().isoformat()
    }
    
    # Check for duplicates - same title and item_id
    duplicate_found = False
    for existing_assignment in assignments:
        if (existing_assignment.get('title') == title and 
            existing_assignment.get('item_id') == item_id and
            existing_assignment.get('type') == item_type):
            duplicate_found = True
            # Update existing assignment instead of adding duplicate
            existing_assignment['description'] = description
            existing_assignment['file_id'] = file_id
            existing_assignment['file_name'] = file_name
            existing_assignment['deadline'] = deadline.isoformat()
            existing_assignment['max_grade'] = max_grade
            existing_assignment['created_at'] = datetime.now().isoformat()
            logger.warning(f"Updated existing assignment: {title}")
            break
    
    if not duplicate_found:
        assignments.append(assignment_data)
        logger.info(f"Added new assignment: {title}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, ensure_ascii=False, indent=2)
    
    # Get item name
    if item_type == 'courses':
        from config.courses_config import get_course
        item = get_course(item_id)
        item_name = item['name'] if item else item_id
    else:
        from config.materials_config import get_material
        item = get_material(item_id)
        item_name = item['name'] if item else item_id
    
    type_label = "الواجب" if assignment_type == "assignment" else "الاختبار"
    
    text = f"""
🎉 **تم إنشاء {type_label} بنجاح!**

📚 الدورة/المادة: {item_name}
📝 العنوان: {title}
📋 الوصف: {description}
📎 الملف: {file_name}
⏰ الموعد النهائي: {deadline.strftime('%Y-%m-%d %H:%M')}
🎯 الدرجة القصوى: {max_grade}

✅ {type_label} الآن متاح للطلاب المسجلين
    """
    
    await message_to_reply.reply_text(text)
    
    context.user_data.clear()
    logger.info(f"Admin created {assignment_type}: {title} for {item_id}")
    
    return ConversationHandler.END


async def cancel_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel assignment creation"""
    await update.message.reply_text("❌ تم الإلغاء")
    context.user_data.clear()
    return ConversationHandler.END
