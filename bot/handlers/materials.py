"""
Materials Handler for University Subjects
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from pathlib import Path
import json

from database.models.user import User
from config.materials_config import get_all_years, get_materials_by_year_semester, get_material, calculate_materials_price
from bot.keyboards.main_keyboards import get_years_keyboard, get_semesters_keyboard, get_payment_methods_keyboard


async def show_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show university materials (years)"""
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message
    
    text = """
🎓 **المواد الجامعية**

اختر السنة الدراسية:
    """
    
    await message.reply_text(
        text,
        reply_markup=get_years_keyboard()
    )


async def show_semesters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show semesters for selected year"""
    query = update.callback_query
    await query.answer()
    
    # Extract year from callback_data
    year = int(query.data.replace("year_", ""))
    
    text = f"""
📚 **السنة {['الثالثة', 'الرابعة', 'الخامسة'][year-3]}**

اختر الفصل الدراسي:
    """
    
    await query.message.reply_text(
        text,
        reply_markup=get_semesters_keyboard(year)
    )


async def show_semester_materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show materials for selected semester"""
    query = update.callback_query
    await query.answer()
    
    # Extract year and semester from callback_data: semester_year_sem
    parts = query.data.split('_')
    year = int(parts[1])
    semester = int(parts[2])
    
    # Get materials
    materials = get_materials_by_year_semester(year, semester)
    
    if not materials:
        await query.message.reply_text("📚 لا توجد مواد متاحة حالياً")
        return
    
    text = f"""
📚 **السنة {['الثالثة', 'الرابعة', 'الخامسة'][year-3]} - الفصل {['الأول', 'الثاني'][semester-1]}**

المواد المتاحة:
"""
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = []
    
    for material in materials:
        text += f"\n• {material['name']}"
        keyboard.append([
            InlineKeyboardButton(
                material['name'],
                callback_data=f"material_{material['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("« رجوع", callback_data="back_materials")])
    
    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_material_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show material details and payment options"""
    query = update.callback_query
    await query.answer()
    
    material_id = query.data.replace("material_", "")
    material = get_material(material_id)
    
    if not material:
        await query.message.reply_text("❌ المادة غير موجودة")
        return
    
    # Get user
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        await query.message.reply_text("❌ يرجى التسجيل أولاً باستخدام /start")
        return
    
    # Check if already enrolled
    enrollment = user.get_material_enrollment(material_id)
    if enrollment:
        if enrollment.approval_status == "approved":
            link = None
            try:
                if material.get('group_link'):
                    link = material['group_link']
                else:
                    gl_path = Path('data/group_links.json')
                    if gl_path.exists():
                        with open(gl_path, 'r', encoding='utf-8') as f:
                            gl = json.load(f)
                            link = gl.get('materials', {}).get(material_id) or gl.get(material_id)
            except Exception as e:
                logger.error(f"Error loading material group link: {e}")
            if link:
                text = f"✅ **{material['name']}**\n\nانضم إلى مجموعة المادة:"
                keyboard = [
                    [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
                    [InlineKeyboardButton("« رجوع", callback_data="back_materials")]
                ]
            else:
                text = f"✅ **{material['name']}**\n\nرابط المجموعة غير متاح حالياً. سيتم مشاركته قريباً."
                keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back_materials")]]
            await query.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        elif enrollment.approval_status == "pending":
            await query.message.reply_text(
                f"⏳ **{material['name']}**\n\nطلبك قيد المراجعة."
            )
            return
    
    # Calculate price for single material (for display reference)
    material_price = calculate_materials_price([material_id])
    
    # Show material details using the new template
    text = f"""
⭐ **{material['name']}**
👩‍🏫 مع المهندسة: {material['instructor']}
━━━━━━━━━━━━━━━━━━━━
📖 **الوصف العام**
{material['description']}
━━━━━━━━━━━━━━━━━━━━
✨ **محتوى الكورس**
⭐ 1) متابعة تامة لمواد الجامعة
شرح نظري كامل ومنهجي
جلسات عملية لحل التمارين وتطبيق الأفكار مباشرة

⭐ 2) ملخصات احترافية
إعداد ملخص شامل بنهاية دراسة كل مقرر
يساعد على مراجعة أهم المفاهيم بسرعة وسهولة

⭐ 3) نظام اختبارات دوري
اختبار بعد كل محاضرة
يساعد على تثبيت المعلومات وقياس تقدّمك

⭐ 4) تدريب مكثف
حل أسئلة الدورات السابقة
ضمان فهم كامل لمختلف أنماط الأسئلة
━━━━━━━━━━━━━━━━━━━
💰 **الأسعار**
مادة واحدة: 75,000 ل.س
مادتان(خصم): 125,000 ل.س
━━━━━━━━━━━━━━━━━━━━
💳 **وسائل الدفع**
يرجى اختيار وسيلة الدفع المناسبة لإتمام التسجيل.
    """
    
    await query.message.reply_text(
        text,
        reply_markup=get_payment_methods_keyboard("material", material_id),
        parse_mode="Markdown"
    )
