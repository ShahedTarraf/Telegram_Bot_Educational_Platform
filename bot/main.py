"""Telegram Bot Main Entry Point"""
import asyncio
import traceback
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    TypeHandler,
    filters,
)
from loguru import logger

from config.settings import settings
from database.connection import init_db, close_db
from bot.keyboards.main_keyboards import get_main_menu_keyboard, get_admin_menu_keyboard
from bot.handlers.start import (
    start_command,
    asking_name,
    asking_phone,
    asking_email,
    cancel_registration,
    get_my_id,
    ASKING_NAME,
    ASKING_PHONE,
    ASKING_EMAIL
)
from bot.handlers.courses import (
    show_courses,
    show_course_details,
    process_payment,
    receive_payment_proof,
    cancel_payment,
)
from bot.handlers.materials import (
    show_materials,
    show_semesters,
    show_semester_materials,
    show_material_details
)
from bot.handlers.content import (
    show_lectures,
    show_videos,
    watch_video,
    show_assignments,
    view_assignment,
    show_exams,
    show_links,
    show_certificate
)
from bot.handlers.admin import (
    admin_start_upload,
    admin_select_type,
    admin_select_course,
    admin_receive_video,
    admin_enter_video_title,
    admin_cancel,
    admin_quick_video_upload,
    admin_show_videos,
    admin_help,
    SELECTING_COURSE,
    UPLOADING_VIDEO,
    ENTERING_VIDEO_TITLE
)
from bot.handlers.assignments import (
    create_assignment,
    select_assignment_type,
    select_assignment_item,
    enter_assignment_title,
    enter_assignment_description,
    upload_assignment_file,
    enter_assignment_deadline,
    enter_max_grade,
    cancel_assignment,
    SELECTING_ITEM,
    ENTERING_TITLE,
    ENTERING_DESCRIPTION,
    UPLOADING_FILE,
    ENTERING_DEADLINE,
    ENTERING_MAX_GRADE
)
from bot.handlers.submissions import (
    submit_assignment_file,
    cancel_submission
)
from bot.handlers.assignment_submission_json import (
    start_assignment_submission,
    receive_submission_file,
    view_submission_status_json,
    grade_assignment,
    WAITING_FOR_FILE
)
from bot.handlers.admin_grading import (
    start_grading_menu,
    select_assignment_for_grading,
    select_student_for_grading,
    enter_grade,
    enter_feedback_and_save,
    grade_more,
    cancel_grading,
    SELECTING_ASSIGNMENT,
    SELECTING_STUDENT,
    ENTERING_GRADE,
    ENTERING_FEEDBACK
)
from bot.handlers.admin_course_stats import (
    show_course_statistics,
    show_detailed_course_stats,
    back_to_course_stats
)
from bot.handlers.exam_grading import (
    start_exam_grading_menu,
    select_exam_for_grading,
    select_student_for_exam_grading,
    enter_exam_grade,
    enter_exam_feedback_and_save,
    grade_more_exam,
    cancel_exam_grading,
    SELECTING_EXAM,
    SELECTING_STUDENT_EXAM,
    ENTERING_EXAM_GRADE,
    ENTERING_EXAM_FEEDBACK
)
from bot.handlers.dashboard import (
    show_my_statistics,
    show_achievements,
    show_admin_statistics,
    show_top_students,
    export_user_report,
    show_admin_reports_menu,
    export_students_excel
)
from bot.handlers.chat import (
    start_chat_with_instructor,
    receive_chat_message,
    admin_reply_to_student,
    cancel_chat,
    WAITING_FOR_MESSAGE
)
from bot.handlers.quiz import (
    show_quizzes,
    view_quiz,
    start_quiz,
    answer_quiz_question,
    complete_quiz,
    review_quiz_answers
)
from bot.handlers.certificates import (
    request_certificate,
    export_certificate_menu,
    upload_certificate_pdf,
    send_certificate_to_student,
    cancel_certificate_export,
    show_admin_messages,
    process_certificate_request,
    start_reply_to_student,
    send_reply_to_student,
    CERT_UPLOAD_PDF,
    CERT_ENTER_STUDENT_ID
)
from bot.handlers.exam_creator import (
    start_create_exam,
    select_exam_type,
    select_exam_course,
    enter_exam_title,
    enter_exam_link,
    enter_exam_max_grade,
    back_to_type_selection,
    cancel_exam_creation,
    EXAM_SELECTING_TYPE,
    EXAM_SELECTING_COURSE,
    EXAM_ENTERING_TITLE,
    EXAM_ENTERING_LINK,
    EXAM_ENTERING_MAX_GRADE
)
from bot.handlers.send_message import (
    start_send_message,
    select_student,
    send_message_to_student,
    send_another_message,
    cancel_send_message,
    SELECTING_STUDENT,
    ENTERING_MESSAGE
)


async def main_menu_handler(update: Update, context):
    """Handle main menu buttons"""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Admin buttons
    if user_id == settings.TELEGRAM_ADMIN_ID:
        if text == "💬 الرسائل":
            await show_admin_messages(update, context)
            return
        elif text == "👤 حسابي":
            await show_admin_statistics(update, context)
            return
        elif text == "📈 إحصائيات الدورات":
            await show_course_statistics(update, context)
            return
        # Note: أزرار الأدمن الأخرى تُعالج بواسطة ConversationHandlers
    
    # Regular buttons
    if text == "📚 الدورات الاحترافية":
        await show_courses(update, context)
    elif text == "🎓 المواد الجامعية":
        await show_materials(update, context)
    elif text == "📞 التواصل":
        from bot.keyboards.main_keyboards import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [[InlineKeyboardButton("💬 تواصل الآن", callback_data="start_chat")]]
        await update.message.reply_text(
            "📞 **التواصل**\n\n"
            "للاستفسارات والدعم:\n"
            "📧 Email: shahode54g@gmail.com\n"
            "📱 Telegram: @Shahdtarraf44\n\n"
            "أو تواصل مباشرة مع المدرس:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def error_handler(update: Update, context):
    """Handle errors"""
    logger.error(f"Update {update} caused error: {context.error}")
    # Debug: log full update dict and traceback for easier debugging
    try:
        if isinstance(update, Update):
            logger.debug(f"error_handler update dict: {update.to_dict()}")
        else:
            logger.debug(f"error_handler received non-Update object: {update}")
    except Exception as serialize_error:
        logger.error(f"Failed to serialize update in error_handler: {serialize_error}")

    try:
        if context and context.error:
            tb = "".join(
                traceback.format_exception(
                    type(context.error), context.error, context.error.__traceback__
                )
            )
            logger.error(f"error_handler traceback for context.error:\n{tb}")
    except Exception as tb_error:
        logger.error(f"Failed to format traceback in error_handler: {tb_error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ حدث خطأ. يرجى المحاولة لاحقاً."
        )

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = get_admin_menu_keyboard() if update.effective_user.id == settings.TELEGRAM_ADMIN_ID else get_main_menu_keyboard()
    await query.message.reply_text("اختر من القائمة:", reply_markup=keyboard)


async def _post_init(application: Application):
    """Initialize resources after Application is built"""
    await init_db()


async def _post_shutdown(application: Application):
    """Cleanup resources before shutdown"""
    await close_db()


def create_application() -> Application:
    logger.info("Initializing Educational Platform Bot application...")
    
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
    )
    application = (
        Application
        .builder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .request(request)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    # Global debug handler to log every incoming Update without changing behavior
    async def debug_log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if isinstance(update, Update):
                logger.debug(f"Incoming update: {update.to_dict()}")
            else:
                logger.debug(f"Incoming non-Update object in debug_log_update: {update}")
        except Exception as e:
            logger.error(f"Failed to serialize update in debug_log_update: {e}")

    application.add_handler(TypeHandler(Update, debug_log_update), group=-1)
    
    # Registration conversation handler
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ASKING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_name)],
            ASKING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_phone)],
            ASKING_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, asking_email)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_registration),
            MessageHandler(filters.Regex("^❌ إلغاء$"), cancel_registration)
        ],
    )
    
    application.add_handler(registration_handler)
    
    # Admin video upload conversation handler
    admin_upload_handler = ConversationHandler(
        entry_points=[
            CommandHandler("upload", admin_start_upload),
            MessageHandler(filters.Regex("^📹 رفع فيديو$"), admin_start_upload)
        ],
        states={
            SELECTING_COURSE: [CallbackQueryHandler(admin_select_course)],
            UPLOADING_VIDEO: [MessageHandler(filters.VIDEO, admin_receive_video)],
            ENTERING_VIDEO_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_enter_video_title)],
        },
        fallbacks=[
            CommandHandler("cancel", admin_cancel),
            CallbackQueryHandler(admin_cancel, pattern="^admin_cancel$")
        ],
        allow_reentry=True,
    )
    
    
    
    # Assignment creation conversation handler (PDF upload)
    assignment_handler = ConversationHandler(
        entry_points=[
            CommandHandler("createassignment", create_assignment),
            MessageHandler(filters.Regex("^📝 إنشاء واجب$"), create_assignment)
        ],
        states={
            SELECTING_ITEM: [
                CallbackQueryHandler(select_assignment_type, pattern="^assign_type_"),
                CallbackQueryHandler(select_assignment_item, pattern="^assign_item_"),
                CallbackQueryHandler(cancel_assignment, pattern="^assign_cancel$")
            ],
            ENTERING_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_assignment_title)],
            ENTERING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_assignment_description)],
            UPLOADING_FILE: [MessageHandler(filters.Document.PDF | filters.Document.ALL, upload_assignment_file)],
            ENTERING_DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_assignment_deadline)],
            ENTERING_MAX_GRADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_max_grade),
                CallbackQueryHandler(enter_max_grade, pattern="^max_grade_")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_assignment),
            CallbackQueryHandler(cancel_assignment, pattern="^assign_cancel$")
        ],
        allow_reentry=True,
    )
    
    
    
    # Exam creation handler
    exam_handler = ConversationHandler(
        entry_points=[
            CommandHandler("createexam", start_create_exam),
            MessageHandler(filters.Regex("^📋 إنشاء اختبار$"), start_create_exam)
        ],
        states={
            EXAM_SELECTING_TYPE: [
                CallbackQueryHandler(select_exam_type, pattern="^exam_type_"),
                CallbackQueryHandler(cancel_exam_creation, pattern="^exam_cancel$")
            ],
            EXAM_SELECTING_COURSE: [
                CallbackQueryHandler(select_exam_course, pattern="^exam_course_"),
                CallbackQueryHandler(back_to_type_selection, pattern="^exam_back_type$"),
                CallbackQueryHandler(cancel_exam_creation, pattern="^exam_cancel$")
            ],
            EXAM_ENTERING_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exam_title)
            ],
            EXAM_ENTERING_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exam_link)
            ],
            EXAM_ENTERING_MAX_GRADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exam_max_grade),
                CallbackQueryHandler(enter_exam_max_grade, pattern="^exam_grade_")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_exam_creation),
            CallbackQueryHandler(cancel_exam_creation, pattern="^exam_cancel$")
        ],
        allow_reentry=True
    )
    
    
    
    # Certificate export handler
    certificate_export_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📜 تصدير شهادة$"), export_certificate_menu)
        ],
        states={
            CERT_UPLOAD_PDF: [
                MessageHandler(filters.Document.PDF | filters.Document.ALL, upload_certificate_pdf)
            ],
            CERT_ENTER_STUDENT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_certificate_to_student)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_certificate_export)
        ],
        allow_reentry=True
    )
    
    
    
    # Admin grading conversation handler
    grading_handler = ConversationHandler(
        entry_points=[
            CommandHandler("grade_assignments", start_grading_menu),
            MessageHandler(filters.Regex("^📊 تقييم الواجبات$"), start_grading_menu)
        ],
        states={
            SELECTING_ASSIGNMENT: [
                CallbackQueryHandler(select_assignment_for_grading, pattern="^grade_assign_"),
                CallbackQueryHandler(cancel_grading, pattern="^grade_cancel$")
            ],
            SELECTING_STUDENT: [
                CallbackQueryHandler(select_student_for_grading, pattern="^grade_student_"),
                CallbackQueryHandler(cancel_grading, pattern="^grade_back$")
            ],
            ENTERING_GRADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_grade)
            ],
            ENTERING_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_feedback_and_save)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_grading),
            CallbackQueryHandler(cancel_grading, pattern="^grade_cancel$")
        ],
        allow_reentry=True
    )
    
    
    
    # Handle "grade more" callback
    
    
    # Exam grading conversation handler
    exam_grading_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📊 تقييم الاختبارات$"), start_exam_grading_menu)
        ],
        states={
            SELECTING_EXAM: [
                CallbackQueryHandler(select_exam_for_grading, pattern="^grade_exam_"),
                CallbackQueryHandler(cancel_exam_grading, pattern="^cancel_exam_grading$")
            ],
            SELECTING_STUDENT_EXAM: [
                CallbackQueryHandler(select_student_for_exam_grading, pattern="^grade_exam_student_"),
                CallbackQueryHandler(start_exam_grading_menu, pattern="^back_exam_grading$"),
                CallbackQueryHandler(cancel_exam_grading, pattern="^cancel_exam_grading$")
            ],
            ENTERING_EXAM_GRADE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exam_grade),
                CallbackQueryHandler(cancel_exam_grading, pattern="^cancel_exam_grading$")
            ],
            ENTERING_EXAM_FEEDBACK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exam_feedback_and_save),
                CallbackQueryHandler(cancel_exam_grading, pattern="^cancel_exam_grading$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_exam_grading, pattern="^cancel_exam_grading$")
        ],
        allow_reentry=True
    )
    
    
    
    # Handle "grade more exam" callback
    
    
    # Course statistics callbacks
    application.add_handler(CallbackQueryHandler(show_detailed_course_stats, pattern="^course_stats_"))
    application.add_handler(CallbackQueryHandler(back_to_course_stats, pattern="^back_course_stats$"))
    
    # Chat conversation handler - MUST be before main_menu_handler
    chat_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_chat_with_instructor, pattern="^start_chat$"),
            MessageHandler(filters.Regex("^💬 الدردشة$"), start_chat_with_instructor)
        ],
        states={
            WAITING_FOR_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_chat_message)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_chat, pattern="^cancel_chat$")
        ],
        per_user=True,
        per_chat=True
    )
    application.add_handler(chat_handler)
    
    # Send message to student handler
    send_message_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📬 إرسال رسالة$"), start_send_message)
        ],
        states={
            SELECTING_STUDENT: [
                CallbackQueryHandler(select_student, pattern="^msg_student_"),
                CallbackQueryHandler(cancel_send_message, pattern="^msg_cancel$")
            ],
            ENTERING_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_to_student),
                CallbackQueryHandler(cancel_send_message, pattern="^msg_cancel$")
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_send_message, pattern="^msg_cancel$")
        ],
        allow_reentry=True
    )
    application.add_handler(send_message_handler)
    
    # Handle "send another message" callback
    application.add_handler(CallbackQueryHandler(send_another_message, pattern="^msg_send_another$"))
    application.add_handler(CallbackQueryHandler(cancel_send_message, pattern="^msg_done$"))
    
    # Admin commands
    application.add_handler(CommandHandler("videos", admin_show_videos))
    application.add_handler(CommandHandler("adminhelp", admin_help))
    application.add_handler(CommandHandler("myid", get_my_id))
    application.add_handler(CommandHandler("id", get_my_id))
    
    # Main menu handlers (only for non-conversation buttons)
    application.add_handler(MessageHandler(
        filters.Regex("^(📚 الدورات الاحترافية|🎓 المواد الجامعية|📞 التواصل|💬 الرسائل|👤 حسابي|📈 إحصائيات الدورات)$"),
        main_menu_handler
    ))
    
    # Callback query handlers - Courses
    application.add_handler(CallbackQueryHandler(show_courses, pattern="^back_courses$"))
    application.add_handler(CallbackQueryHandler(show_course_details, pattern="^course_"))
    application.add_handler(CallbackQueryHandler(process_payment, pattern="^pay_"))
    application.add_handler(CallbackQueryHandler(cancel_payment, pattern="^cancel_payment$"))
    
    # Callback query handlers - Materials
    application.add_handler(CallbackQueryHandler(show_materials, pattern="^back_materials$"))
    application.add_handler(CallbackQueryHandler(show_materials, pattern="^back_years$"))
    application.add_handler(CallbackQueryHandler(back_to_main_menu, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(show_semesters, pattern="^year_"))
    application.add_handler(CallbackQueryHandler(show_semester_materials, pattern="^semester_"))
    application.add_handler(CallbackQueryHandler(show_material_details, pattern="^material_"))
    
    # Callback query handlers - Content
    application.add_handler(CallbackQueryHandler(show_lectures, pattern="^lectures_"))
    application.add_handler(CallbackQueryHandler(show_videos, pattern="^videos_"))
    application.add_handler(CallbackQueryHandler(watch_video, pattern="^watch_"))
    application.add_handler(CallbackQueryHandler(show_assignments, pattern="^assignments_"))
    application.add_handler(CallbackQueryHandler(view_assignment, pattern="^view_assignment_"))
    application.add_handler(CallbackQueryHandler(show_exams, pattern="^exams_"))
    application.add_handler(CallbackQueryHandler(show_links, pattern="^links_"))
    application.add_handler(CallbackQueryHandler(show_certificate, pattern="^certificate_"))
    
    # Certificate handlers
    application.add_handler(CallbackQueryHandler(process_certificate_request, pattern="^cert_request_"))
    application.add_handler(CallbackQueryHandler(process_certificate_request, pattern="^cert_export_"))
    
    # Reply to student handlers
    application.add_handler(CallbackQueryHandler(start_reply_to_student, pattern="^reply_msg_"))
    
    # Admin reply message handler (when in reply mode)
    async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id == settings.TELEGRAM_ADMIN_ID and 'replying_to_student' in context.user_data:
            await send_reply_to_student(update, context)
    
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.User(settings.TELEGRAM_ADMIN_ID),
        handle_admin_reply
    ), group=1)  # Lower priority
    
    # Payment proof handler (photo) - must check context first
    async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads - either payment proof or assignment submission"""
        if context.user_data.get('submitting_assignment_index') is not None:
            await receive_submission_file(update, context)
        else:
            await receive_payment_proof(update, context)
    
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Document handler for assignment submissions
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads for assignment submissions"""
        if context.user_data.get('submitting_assignment_index') is not None:
            await receive_submission_file(update, context)
    
    application.add_handler(MessageHandler(filters.Document.PDF | filters.Document.ALL, handle_document))
    
    # Video handler for assignment submissions
    async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle video uploads for assignment submissions"""
        if context.user_data.get('submitting_assignment_index') is not None:
            await receive_submission_file(update, context)
    
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # Submission callback handlers (JSON-based)
    application.add_handler(CallbackQueryHandler(start_assignment_submission, pattern="^submit_solution_"))
    application.add_handler(CallbackQueryHandler(view_submission_status_json, pattern="^submission_status_"))
    
    # Admin grading command
    
    
    # Admin reply command
    application.add_handler(CommandHandler("reply", admin_reply_to_student))
    
    # Quiz handlers
    application.add_handler(CallbackQueryHandler(show_quizzes, pattern="^quizzes_"))
    application.add_handler(CallbackQueryHandler(view_quiz, pattern="^quiz_view_"))
    application.add_handler(CallbackQueryHandler(start_quiz, pattern="^quiz_start_"))
    application.add_handler(CallbackQueryHandler(answer_quiz_question, pattern="^quiz_answer_"))
    application.add_handler(CallbackQueryHandler(complete_quiz, pattern="^quiz_finish$"))
    application.add_handler(CallbackQueryHandler(review_quiz_answers, pattern="^quiz_review_"))
    
    # Dashboard and statistics handlers
    application.add_handler(CallbackQueryHandler(show_achievements, pattern="^show_achievements$"))
    application.add_handler(CallbackQueryHandler(show_top_students, pattern="^show_top_students$"))
    application.add_handler(CallbackQueryHandler(export_user_report, pattern="^export_pdf_"))
    application.add_handler(CallbackQueryHandler(show_admin_reports_menu, pattern="^admin_reports$"))
    application.add_handler(CallbackQueryHandler(export_students_excel, pattern="^export_students_excel$"))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    return application
