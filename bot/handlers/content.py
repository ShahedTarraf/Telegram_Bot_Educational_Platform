"""
Content Handlers - Videos, Lectures, Assignments
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from pathlib import Path
import json
from datetime import datetime

from database.models.user import User


async def show_lectures(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lectures for course"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("lectures_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    # If a group link is configured, show it instead of content
    link = None
    try:
        from config.courses_config import get_course
        course = get_course(course_id)
        if course and course.get('group_link'):
            link = course['group_link']
        else:
            gl_path = Path('data/group_links.json')
            if gl_path.exists():
                with open(gl_path, 'r', encoding='utf-8') as f:
                    gl = json.load(f)
                    link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
    except Exception as e:
        logger.error(f"Error loading course group link: {e}")
    if link:
        text = f"🔗 **رابط مجموعة الدورة**\n\nانضم عبر الزر التالي:"
        keyboard = [
            [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
            [InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]
        ]
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    text = """
📖 **المحاضرات النظرية**

سيتم إضافة المحاضرات قريباً...

للأدمن: لرفع المحاضرات:
1. أرسل ملفات PDF للبوت
2. أو أضف روابط Google Drive
    """
    
    keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
    
    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show videos for course"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("videos_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    # If a group link is configured, show it instead of content
    link = None
    try:
        from config.courses_config import get_course
        course = get_course(course_id)
        if course and course.get('group_link'):
            link = course['group_link']
        else:
            gl_path = Path('data/group_links.json')
            if gl_path.exists():
                with open(gl_path, 'r', encoding='utf-8') as f:
                    gl = json.load(f)
                    link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
    except Exception as e:
        logger.error(f"Error loading course group link: {e}")
    if link:
        text = f"🔗 **رابط مجموعة الدورة**\n\nانضم عبر الزر التالي:"
        keyboard = [
            [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
            [InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]
        ]
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    # Load videos from JSON
    import json
    from pathlib import Path
    
    videos_file = Path('data/videos.json')
    course_videos = []
    
    if videos_file.exists():
        try:
            with open(videos_file, 'r', encoding='utf-8') as f:
                all_videos = json.load(f)
                # Filter videos for this course
                course_videos = [v for v in all_videos if v.get('type') == 'courses' and v.get('item_id') == course_id]
        except Exception as e:
            logger.error(f"Error loading videos: {e}")
    
    if course_videos:
        text = f"🎥 **الفيديوهات المتاحة** ({len(course_videos)} فيديو)\n\n"
        
        keyboard = []
        # Remove duplicates by title
        seen_titles = set()
        unique_videos = []
        
        for video in course_videos:
            title = video.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_videos.append(video)
        
        for i, video in enumerate(unique_videos, 1):
            title = video.get('title', f'فيديو {i}')
            duration = video.get('duration', 0)
            minutes = duration // 60
            seconds = duration % 60
            
            text += f"{i}. **{title}**\n"
            text += f"   ⏱️ المدة: {minutes}:{seconds:02d}\n"
            if video.get('description'):
                desc = video.get('description')[:50]  # Limit description length
                text += f"   📝 {desc}...\n"
            text += "\n"
            
            # Add button to watch video
            keyboard.append([InlineKeyboardButton(
                f"▶️ مشاهدة: {title[:30]}", 
                callback_data=f"watch_{i-1}_{course_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")])
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Store videos in context for watching
        context.user_data[f'videos_{course_id}'] = unique_videos
    else:
        text = """
🎥 **الفيديوهات**

لا توجد فيديوهات متاحة حالياً...

📹 سيتم إضافة الفيديوهات قريباً من قبل المدرس.
        """
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def watch_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send video to user"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: watch_{index}_{course_id}
    # Use maxsplit to handle course_id with underscores
    parts = query.data.split('_', 2)  # Split into max 3 parts: ['watch', 'index', 'course_id']
    video_index = int(parts[1])
    course_id = parts[2]
    
    # Get videos from context OR reload from JSON
    videos = context.user_data.get(f'videos_{course_id}', [])
    
    # If no videos in context, reload from JSON
    if not videos:
        import json
        from pathlib import Path
        
        videos_file = Path('data/videos.json')
        if videos_file.exists():
            try:
                with open(videos_file, 'r', encoding='utf-8') as f:
                    all_videos = json.load(f)
                    videos = [v for v in all_videos if v.get('type') == 'courses' and v.get('item_id') == course_id]
                    # Store back in context
                    context.user_data[f'videos_{course_id}'] = videos
            except Exception as e:
                logger.error(f"Error loading videos: {e}")
    
    if videos and video_index < len(videos):
        video = videos[video_index]
        file_id = video.get('file_id')
        title = video.get('title')
        description = video.get('description', '')
        
        if not file_id:
            await query.message.reply_text("❌ معرف الفيديو غير موجود")
            return
        
        caption = f"🎥 **{title}**\n\n"
        if description:
            caption += f"{description}\n\n"
        caption += "استمتع بالمشاهدة! 🍿"
        
        try:
            await query.message.reply_video(
                video=file_id,
                caption=caption
            )
            
            keyboard = [[InlineKeyboardButton("« رجوع للقائمة", callback_data=f"videos_{course_id}")]]
            await query.message.reply_text(
                "هل تريد مشاهدة فيديو آخر؟",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"User {update.effective_user.id} watched video: {title}")
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await query.message.reply_text(
                "❌ عذراً، حدث خطأ في إرسال الفيديو. يرجى المحاولة لاحقاً.\n\n"
                f"التفاصيل: {str(e)}"
            )
    else:
        await query.message.reply_text("❌ الفيديو غير موجود")


async def show_assignments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show assignments for course"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("assignments_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    # If a group link is configured, show it instead of content
    link = None
    try:
        from config.courses_config import get_course
        course = get_course(course_id)
        if course and course.get('group_link'):
            link = course['group_link']
        else:
            gl_path = Path('data/group_links.json')
            if gl_path.exists():
                with open(gl_path, 'r', encoding='utf-8') as f:
                    gl = json.load(f)
                    link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
    except Exception as e:
        logger.error(f"Error loading course group link: {e}")
    if link:
        text = f"🔗 **رابط مجموعة الدورة**\n\nانضم عبر الزر التالي:"
        keyboard = [
            [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
            [InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]
        ]
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    # Load assignments from JSON
    import json
    from pathlib import Path
    from datetime import datetime
    
    assignments_file = Path('data/assignments.json')
    course_assignments = []
    
    if assignments_file.exists():
        try:
            with open(assignments_file, 'r', encoding='utf-8') as f:
                all_assignments = json.load(f)
                # Filter assignments for this course
                course_assignments = [a for a in all_assignments if a.get('type') == 'courses' and a.get('item_id') == course_id]
        except Exception as e:
            logger.error(f"Error loading assignments: {e}")
    
    if course_assignments:
        # Remove duplicates by title
        seen_titles = {}
        unique_assignments = []
        
        for assignment in course_assignments:
            title = assignment.get('title', '')
            if title and title not in seen_titles:
                seen_titles[title] = True
                unique_assignments.append(assignment)
        
        text = f"📝 **الواجبات المتاحة** ({len(unique_assignments)} واجب)\n\n"
        
        keyboard = []
        for i, assignment in enumerate(unique_assignments, 1):
            title = assignment.get('title', f'واجب {i}')
            description = assignment.get('description', '')
            
            text += f"{i}. **{title}**\n"
            if description:
                desc_short = description[:50]
                text += f"   📝 {desc_short}{'...' if len(description) > 50 else ''}\n"
            text += "\n"
            
            # Add button to view assignment details
            keyboard.append([InlineKeyboardButton(
                f"📝 عرض: {title[:30]}", 
                callback_data=f"view_assignment_{i-1}_{course_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")])
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Store assignments in context for viewing
        context.user_data[f'assignments_{course_id}'] = unique_assignments
    else:
        text = """
📝 **الواجبات**

لا توجد واجبات متاحة حالياً...

📝 سيتم إضافة الواجبات قريباً من قبل المدرس.
        """
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def view_assignment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View assignment details"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback data: view_assignment_{index}_{course_id}
    # Use maxsplit to handle course_id with underscores
    parts = query.data.split('_', 3)  # Split into max 4 parts: ['view', 'assignment', 'index', 'course_id']
    assignment_index = int(parts[2])
    course_id = parts[3]
    
    # Get assignments from context OR reload from JSON
    assignments = context.user_data.get(f'assignments_{course_id}', [])
    
    # If no assignments in context, reload from JSON
    if not assignments:
        import json
        from pathlib import Path
        
        assignments_file = Path('data/assignments.json')
        if assignments_file.exists():
            try:
                with open(assignments_file, 'r', encoding='utf-8') as f:
                    all_assignments = json.load(f)
                    assignments = [a for a in all_assignments if a.get('type') == 'courses' and a.get('item_id') == course_id]
                    # Store back in context
                    context.user_data[f'assignments_{course_id}'] = assignments
            except Exception as e:
                logger.error(f"Error loading assignments: {e}")
    
    if assignments and assignment_index < len(assignments):
        from datetime import datetime
        assignment = assignments[assignment_index]
        title = assignment.get('title')
        description = assignment.get('description', '')
        questions = assignment.get('questions', [])
        deadline_str = assignment.get('deadline', '')
        
        text = f"📝 **{title}**\n\n"
        
        if description:
            text += f"📋 **الوصف:**\n{description}\n\n"
        
        if questions:
            text += "❓ **الأسئلة:**\n"
            for i, q in enumerate(questions, 1):
                text += f"{i}. {q}\n"
            text += "\n"
        
        # Parse deadline
        try:
            deadline = datetime.fromisoformat(deadline_str)
            text += f"⏰ **الموعد النهائي:** {deadline.strftime('%Y-%m-%d %H:%M')}\n"
            
            # Check if overdue
            if datetime.now() > deadline:
                text += "❌ **انتهى الموعد النهائي**\n"
            else:
                days_left = (deadline - datetime.now()).days
                hours_left = ((deadline - datetime.now()).seconds // 3600)
                text += f"⌛ **متبقي:** {days_left} يوم و {hours_left} ساعة\n"
        except:
            pass
        
        text += "\n📎 **لتسليم الحل:**\n"
        text += "اضغط على زر \"تسليم الحل\" بالأسفل\n"
        
        keyboard = [
            [InlineKeyboardButton("📤 تسليم الحل", callback_data=f"submit_solution_{assignment_index}_{course_id}")],
            [InlineKeyboardButton("📊 حالة التسليم", callback_data=f"submission_status_{assignment_index}_{course_id}")],
            [InlineKeyboardButton("« رجوع للواجبات", callback_data=f"assignments_{course_id}")]
        ]
        
        # Send PDF file if available
        file_id = assignment.get('file_id')
        file_name = assignment.get('file_name', 'الواجب.pdf')
        
        if file_id:
            try:
                # Send the PDF file
                await context.bot.send_document(
                    chat_id=update.effective_user.id,
                    document=file_id,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown",
                    filename=file_name
                )
                # Delete the query message to avoid clutter
                await query.message.delete()
            except Exception as e:
                logger.error(f"Error sending assignment file: {e}")
                # Fall back to text only
                await query.message.edit_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        else:
            # No file, just send text
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    else:
        await query.message.reply_text("❌ الواجب غير موجود")


async def show_exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show exams for course"""
    query = update.callback_query
    await query.answer()
    
    try:
        course_id = query.data.replace("exams_", "")
        logger.info(f"Show exams for course: {course_id}")
        
        # Verify user has access
        user = await User.find_one(User.telegram_id == update.effective_user.id)
        if not user or not user.has_approved_course(course_id):
            await query.edit_message_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
            return
        # If a group link is configured, show it instead of content
        link = None
        try:
            from config.courses_config import get_course
            course = get_course(course_id)
            if course and course.get('group_link'):
                link = course['group_link']
            else:
                gl_path = Path('data/group_links.json')
                if gl_path.exists():
                    with open(gl_path, 'r', encoding='utf-8') as f:
                        gl = json.load(f)
                        link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
        except Exception as e:
            logger.error(f"Error loading course group link: {e}")
        if link:
            text = f"🔗 **رابط مجموعة الدورة**\n\nانضم عبر الزر التالي:"
            keyboard = [
                [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
                [InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]
            ]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        
        # Load exams from JSON
        exams_path = Path("data/exams.json")
        exams = []
        
        if exams_path.exists():
            try:
                with open(exams_path, 'r', encoding='utf-8') as f:
                    all_exams = json.load(f)
                    exams = [e for e in all_exams if e.get('course_id') == course_id]
                    logger.info(f"Found {len(exams)} exams for course {course_id}")
            except Exception as e:
                logger.error(f"Error loading exams file: {e}")
                await query.edit_message_text(
                    "❌ حدث خطأ في تحميل الاختبارات\n\n"
                    "يرجى المحاولة لاحقاً أو التواصل مع الإدارة."
                )
                return
        
        if not exams:
            text = "📋 **الاختبارات**\n\n❌ لا توجد اختبارات متاحة حالياً."
            keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
            await query.edit_message_text(
                text, 
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        
        text = f"📋 **الاختبارات المتاحة** ({len(exams)} اختبار)\n\n"
        keyboard = []
        
        for i, exam in enumerate(exams, 1):
            title = exam.get('title', f'اختبار {i}')
            max_grade = exam.get('max_grade', 100)
            exam_link = exam.get('link', '')
            
            # Validate exam link
            if not exam_link or not exam_link.startswith('http'):
                logger.warning(f"Invalid exam link for: {title}")
                continue
            
            # Truncate title if too long (max 30 chars for display)
            display_title = title[:30] + "..." if len(title) > 30 else title
            button_title = title[:35] + "..." if len(title) > 35 else title
            
            text += f"{i}. **{display_title}**\n"
            text += f"   🎯 الدرجة القصوى: {max_grade}\n"
            if exam.get('description'):
                desc_short = exam['description'][:60]
                text += f"   📝 {desc_short}{'...' if len(exam['description']) > 60 else ''}\n"
            text += "\n"
            
            keyboard.append([
                InlineKeyboardButton(
                    f"🔗 فتح: {button_title}", 
                    url=exam_link
                )
            ])
        
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")])
        
        text += "\n━━━━━━━━━━━━━━━━━━━━\n"
        text += "💡 **تعليمات مهمة:**\n"
        text += "1. اضغط على زر الاختبار للانتقال إلى Google Forms\n"
        text += "2. أكمل الاختبار وسجّل إجاباتك\n"
        text += "3. يمكنك العودة للبوت في أي وقت\n"
        text += "4. سيتم تقييم إجاباتك من قبل المدرس\n\n"
        text += "📱 بعد الانتهاء، ارجع للبوت لمتابعة الدروس"
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error in show_exams: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await query.edit_message_text(
                "❌ حدث خطأ في عرض الاختبارات\n\n"
                "يرجى المحاولة لاحقاً أو التواصل مع الإدارة.\n\n"
                f"الخطأ: {str(e)[:100]}"
            )
        except Exception as edit_error:
            logger.error(f"Failed to send error message: {edit_error}")
            pass


async def show_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show important links"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("links_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    
    # Try to load links from data/links.json
    links = []
    try:
        links_path = Path('data/links.json')
        if links_path.exists():
            with open(links_path, 'r', encoding='utf-8') as f:
                import json
                all_links = json.load(f)
                # Support both nested and flat structures
                course_links = (
                    all_links.get('courses', {}).get(course_id)
                    if isinstance(all_links, dict) else None
                )
                if course_links and isinstance(course_links, list):
                    links = [l for l in course_links if isinstance(l, dict) and l.get('url')]
                elif isinstance(all_links, dict) and all_links.get(course_id):
                    # Flat mapping
                    raw = all_links.get(course_id)
                    if isinstance(raw, list):
                        links = [l for l in raw if isinstance(l, dict) and l.get('url')]
    except Exception as e:
        logger.error(f"Error loading course links: {e}")
    
    # Fallback to single group link from group_links.json
    group_link = None
    if not links:
        try:
            gl_path = Path('data/group_links.json')
            if gl_path.exists():
                with open(gl_path, 'r', encoding='utf-8') as f:
                    gl = json.load(f)
                    group_link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
        except Exception as e:
            logger.error(f"Error loading course group link (fallback): {e}")
    
    if links:
        text = "🔗 **روابط مهمة**\n\nاختر ما تريد فتحه:"
        keyboard = []
        for item in links:
            title = item.get('title') or item.get('name') or 'رابط'
            url = item.get('url')
            if url and url.startswith('http'):
                keyboard.append([InlineKeyboardButton(title[:40], url=url)])
        keyboard.append([InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")])
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    elif group_link:
        text = "🔗 **رابط المجموعة**\n\nانضم عبر الزر التالي:"
        keyboard = [
            [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=group_link)],
            [InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]
        ]
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        text = "🔗 **روابط مهمة**\n\nلا توجد روابط حالياً."
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def show_certificate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show certificate"""
    query = update.callback_query
    await query.answer()
    
    course_id = query.data.replace("certificate_", "")
    
    # Verify user has access
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user or not user.has_approved_course(course_id):
        await query.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا المحتوى")
        return
    
    # Check if course is completed
    enrollment = user.get_course_enrollment(course_id)
    if enrollment and enrollment.completed:
        text = "🎓 **الشهادة**\n\n✅ تهانينا! أكملت الدورة بنجاح!\nستحصل على الشهادة قريباً..."
    else:
        text = "🎓 **الشهادة**\n\n⏳ أكمل الدورة أولاً للحصول على الشهادة"
    
    keyboard = [[InlineKeyboardButton("« رجوع", callback_data=f"course_{course_id}")]]
    
    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
