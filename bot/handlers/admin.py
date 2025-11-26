"""
Admin Handlers - Upload Videos, Create Assignments, etc.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from loguru import logger

from config.settings import settings
from config.courses_config import get_all_courses

# Conversation states
SELECTING_COURSE, UPLOADING_VIDEO, ENTERING_VIDEO_TITLE = range(3)


async def admin_start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start video upload process for admin"""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return ConversationHandler.END
    
    # Show type selection (course or material)
    keyboard = [
        [InlineKeyboardButton("📚 الدورات", callback_data="admin_type_courses")],
        [InlineKeyboardButton("🎓 المواد", callback_data="admin_type_materials")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "📹 رفع فيديو جديد\n\nاختر النوع:"
    
    logger.info(f"Sending upload menu to admin {user_id}")
    logger.info(f"Keyboard has {len(keyboard)} rows")
    
    await update.message.reply_text(
        text=text,
        reply_markup=reply_markup
    )
    
    return SELECTING_COURSE


async def admin_start_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start upload from callback (for back button)"""
    query = update.callback_query
    
    keyboard = [
        [InlineKeyboardButton("📚 الدورات الاحترافية", callback_data="admin_type_courses")],
        [InlineKeyboardButton("🎓 المواد الجامعية", callback_data="admin_type_materials")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")]
    ]
    
    text = "📹 *رفع فيديو جديد*\n\nاختر النوع:"
    
    await query.message.edit_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_COURSE


async def admin_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin selects type (course or material)"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_cancel":
        await query.message.reply_text("❌ تم الإلغاء")
        context.user_data.clear()
        return ConversationHandler.END
    
    upload_type = query.data.replace("admin_type_", "")
    context.user_data['admin_upload_type'] = upload_type
    
    keyboard = []
    
    if upload_type == "courses":
        courses = get_all_courses()
        for course in courses:
            keyboard.append([InlineKeyboardButton(
                course['name'],
                callback_data=f"admin_item_{course['id']}"
            )])
        text = "📚 اختر الدورة:"
    else:
        from config.materials_config import get_all_materials
        materials = get_all_materials()
        for material in materials:
            keyboard.append([InlineKeyboardButton(
                f"{material['name']} - س{material['year']} ف{material['semester']}",
                callback_data=f"admin_item_{material['id']}"
            )])
        text = "🎓 اختر المادة:"
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data="admin_back")])
    
    logger.info(f"Showing {len(keyboard)-1} {upload_type} for selection")
    
    await query.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return SELECTING_COURSE


async def admin_select_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin selects course/material for video"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_cancel":
        await query.message.reply_text("❌ تم الإلغاء")
        context.user_data.clear()
        return ConversationHandler.END
    
    if query.data == "admin_back":
        # Go back to type selection
        return await admin_start_upload_callback(update, context)
    
    if query.data.startswith("admin_type_"):
        return await admin_select_type(update, context)
    
    item_id = query.data.replace("admin_item_", "")
    context.user_data['admin_upload_item'] = item_id
    
    upload_type = context.user_data.get('admin_upload_type', 'courses')
    
    if upload_type == 'courses':
        from config.courses_config import get_course
        item = get_course(item_id)
        item_name = item['name'] if item else item_id
    else:
        from config.materials_config import get_material
        item = get_material(item_id)
        item_name = item['name'] if item else item_id
    
    text = f"""
✅ تم اختيار: **{item_name}**

📹 الآن أرسل الفيديو الذي تريد رفعه
    """
    
    await query.message.reply_text(text)
    return UPLOADING_VIDEO


async def admin_receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin uploads video"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return ConversationHandler.END
    
    if not update.message.video:
        await update.message.reply_text("❌ يرجى إرسال فيديو")
        return UPLOADING_VIDEO
    
    # Get video info
    video = update.message.video
    file_id = video.file_id
    duration = video.duration
    caption = update.message.caption or ""
    
    item_id = context.user_data.get('admin_upload_item')
    upload_type = context.user_data.get('admin_upload_type', 'courses')
    
    # Save to context for title entry
    context.user_data['admin_video_file_id'] = file_id
    context.user_data['admin_video_duration'] = duration
    context.user_data['admin_video_caption'] = caption
    
    text = f"""
✅ تم استلام الفيديو!

📹 المدة: {duration // 60} دقيقة و {duration % 60} ثانية
📝 الوصف: {caption if caption else 'بدون وصف'}

الآن أدخل عنوان الفيديو:
    """
    
    await update.message.reply_text(text)
    return ENTERING_VIDEO_TITLE


async def admin_enter_video_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin enters video title"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return ConversationHandler.END
    
    title = update.message.text
    
    # Get saved data
    item_id = context.user_data.get('admin_upload_item')
    upload_type = context.user_data.get('admin_upload_type', 'courses')
    file_id = context.user_data.get('admin_video_file_id')
    duration = context.user_data.get('admin_video_duration')
    caption = context.user_data.get('admin_video_caption')
    
    # Save to temporary storage
    video_data = {
        'type': upload_type,
        'item_id': item_id,
        'title': title,
        'description': caption,
        'file_id': file_id,
        'duration': duration
    }
    
    # For now, save to a simple JSON file
    import json
    from pathlib import Path
    
    videos_file = Path('data/videos.json')
    videos_file.parent.mkdir(exist_ok=True)
    
    videos = []
    if videos_file.exists():
        with open(videos_file, 'r', encoding='utf-8') as f:
            try:
                videos = json.load(f)
            except:
                videos = []
    
    # Check for duplicates - same title and item_id
    duplicate_found = False
    for existing_video in videos:
        if (existing_video.get('title') == title and 
            existing_video.get('item_id') == item_id and
            existing_video.get('type') == upload_type):
            duplicate_found = True
            # Update existing video instead of adding duplicate
            existing_video['file_id'] = file_id
            existing_video['duration'] = duration
            existing_video['description'] = caption
            logger.warning(f"Updated existing video: {title}")
            break
    
    if not duplicate_found:
        videos.append(video_data)
        logger.info(f"Added new video: {title}")
    
    with open(videos_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    
    # Get item name
    if upload_type == 'courses':
        from config.courses_config import get_course
        item = get_course(item_id)
        item_name = item['name'] if item else item_id
        type_label = "الدورة"
    else:
        from config.materials_config import get_material
        item = get_material(item_id)
        item_name = item['name'] if item else item_id
        type_label = "المادة"
    
    text = f"""
🎉 **تم رفع الفيديو بنجاح!**

📚 {type_label}: {item_name}
📹 العنوان: {title}
📝 الوصف: {caption if caption else 'بدون وصف'}
⏱️ المدة: {duration // 60}:{duration % 60:02d}
🆔 File ID: `{file_id}`

✅ الفيديو الآن متاح للطلاب المسجلين
    """
    
    await update.message.reply_text(text)
    
    # Clear context
    context.user_data.clear()
    
    logger.info(f"Admin uploaded video: {title} for {upload_type} {item_id}")
    
    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel admin operation"""
    await update.message.reply_text("❌ تم الإلغاء")
    context.user_data.clear()
    return ConversationHandler.END


# Quick upload - for admins who send video directly
async def admin_quick_video_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick video upload when admin sends video directly"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return
    
    # Check if there's active payment session
    if 'payment' in context.user_data:
        # This is payment proof, not admin upload
        return
    
    video = update.message.video
    file_id = video.file_id
    caption = update.message.caption or "فيديو بدون عنوان"
    duration = video.duration
    
    text = f"""
📹 **فيديو مستلم!**

🆔 File ID: `{file_id}`
📝 الوصف: {caption}
⏱️ المدة: {duration // 60}:{duration % 60:02d}

لحفظ هذا الفيديو في دورة معينة:
1. استخدم الأمر /upload
2. أو أرسل الأمر /addvideo ثم اختر الدورة

أو احفظ الـ File ID أعلاه لاستخدامه لاحقاً.
    """
    
    await update.message.reply_text(text)


# Show all videos
async def admin_show_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all uploaded videos"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط")
        return
    
    import json
    from pathlib import Path
    
    videos_file = Path('data/videos.json')
    
    if not videos_file.exists():
        await update.message.reply_text("📹 لا توجد فيديوهات محفوظة بعد")
        return
    
    with open(videos_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    if not videos:
        await update.message.reply_text("📹 لا توجد فيديوهات محفوظة بعد")
        return
    
    from config.courses_config import get_course
    
    text = "📹 **قائمة الفيديوهات المحفوظة:**\n\n"
    
    for i, video in enumerate(videos, 1):
        course = get_course(video['course_id'])
        course_name = course['name'] if course else video['course_id']
        
        text += f"{i}. **{video['title']}**\n"
        text += f"   📚 الدورة: {course_name}\n"
        text += f"   ⏱️ المدة: {video['duration'] // 60}:{video['duration'] % 60:02d}\n"
        text += f"   🆔 File ID: `{video['file_id']}`\n\n"
    
    await update.message.reply_text(text)


# Admin help
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin commands"""
    user_id = update.effective_user.id
    
    if user_id != settings.TELEGRAM_ADMIN_ID:
        return
    
    text = """
🔑 **أوامر الأدمن:**

📹 **الفيديوهات:**
/upload - رفع فيديو جديد (مع اختيار الدورة)
/videos - عرض جميع الفيديوهات المحفوظة

📝 **الواجبات:**
/createassignment - إنشاء واجب جديد
/grade_assignments - تقييم واجبات الطلاب

📋 **الاختبارات:**
/createexam - إنشاء اختبار جديد (Google Forms)
- دعم جميع الدورات الثلاثة ✨
- روابط مباشرة للطلاب
- نظام تقييم متكامل

⚙️ **الإدارة:**
/adminhelp - عرض هذه القائمة

---

**💡 الأزرار السريعة:**
📹 رفع فيديو - رفع فيديو مباشرة
📝 إنشاء واجب - إنشاء واجب جديد
📋 إنشاء اختبار - إنشاء اختبار لأي دورة
📊 تقييم الواجبات - تقييم واجبات الطلاب
📊 تقييم الاختبارات - تقييم اختبارات الطلاب

**📖 للمزيد:**
راجع ملفات:
- `HOW_TO_UPLOAD_CONTENT.md`
- `EXAM_SYSTEM_UPDATE.md` ← جديد!
    """
    
    await update.message.reply_text(text)
