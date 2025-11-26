"""
Main Keyboards for Telegram Bot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [KeyboardButton("📚 الدورات الاحترافية"), KeyboardButton("🎓 المواد الجامعية")],
        [KeyboardButton("💬 الدردشة"), KeyboardButton("📞 التواصل")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_admin_menu_keyboard():
    """Get admin menu keyboard with extra admin commands"""
    keyboard = [
        [KeyboardButton("📚 الدورات الاحترافية"), KeyboardButton("🎓 المواد الجامعية")],
        [KeyboardButton("📬 إرسال رسالة"), KeyboardButton("💬 الرسائل")],
        [KeyboardButton("👤 حسابي")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_courses_keyboard():
    """Get courses selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🟢 مبتدئ", callback_data="course_nlp_beginner")],
        [InlineKeyboardButton("🟡 متوسط", callback_data="course_nlp_intermediate")],
        [InlineKeyboardButton("🔵 خبير", callback_data="course_nlp_expert")],
        [InlineKeyboardButton("« رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_years_keyboard():
    """Get university years keyboard"""
    keyboard = [
        [InlineKeyboardButton("السنة الثالثة", callback_data="year_3")],
        [InlineKeyboardButton("السنة الرابعة", callback_data="year_4")],
        [InlineKeyboardButton("السنة الخامسة", callback_data="year_5")],
        [InlineKeyboardButton("« رجوع", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_semesters_keyboard(year: int):
    """Get semesters keyboard for a year"""
    keyboard = [
        [InlineKeyboardButton("الفصل الأول", callback_data=f"semester_{year}_1")],
        [InlineKeyboardButton("الفصل الثاني", callback_data=f"semester_{year}_2")],
        [InlineKeyboardButton("« رجوع", callback_data="back_years")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_methods_keyboard(item_type: str, item_id: str):
    """Get payment methods keyboard"""
    keyboard = [
        [InlineKeyboardButton("💳 Sham Cash", callback_data=f"pay_sham_{item_type}_{item_id}")],
        [InlineKeyboardButton("💰 HARAM", callback_data=f"pay_haram_{item_type}_{item_id}")],
        [InlineKeyboardButton("« إلغاء", callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_course_content_keyboard(course_id: str):
    """Get course content keyboard"""
    keyboard = [
        [InlineKeyboardButton("🎥 الفيديوهات", callback_data=f"videos_{course_id}")],
        [InlineKeyboardButton("📝 الواجبات", callback_data=f"assignments_{course_id}")],
        [InlineKeyboardButton("📋 الاختبارات", callback_data=f"exams_{course_id}")],
        [InlineKeyboardButton("🔗 الروابط", callback_data=f"links_{course_id}")],
        [InlineKeyboardButton("« رجوع", callback_data="back_courses")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_material_content_keyboard(material_id: str):
    """Get material content keyboard"""
    keyboard = [
        [InlineKeyboardButton("📖 المحاضرات", callback_data=f"mat_lectures_{material_id}")],
        [InlineKeyboardButton("🎥 الفيديوهات", callback_data=f"mat_videos_{material_id}")],
        [InlineKeyboardButton("📝 الواجبات", callback_data=f"mat_assignments_{material_id}")],
        [InlineKeyboardButton("📋 الاختبارات", callback_data=f"mat_exams_{material_id}")],
        [InlineKeyboardButton("📄 الملخصات", callback_data=f"mat_summaries_{material_id}")],
        [InlineKeyboardButton("🔗 روابط مهمة", callback_data=f"mat_links_{material_id}")],
        [InlineKeyboardButton("« رجوع", callback_data="back_materials")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_button(callback_data: str = "back"):
    """Get simple back button"""
    keyboard = [[InlineKeyboardButton("« رجوع", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_button():
    """Get cancel button"""
    keyboard = [[KeyboardButton("❌ إلغاء")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
