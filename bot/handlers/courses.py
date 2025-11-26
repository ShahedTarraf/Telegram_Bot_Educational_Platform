"""
Courses Handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from pathlib import Path
import json

from database.models.user import User
from config.courses_config import get_course, get_all_courses
from bot.keyboards.main_keyboards import (
    get_courses_keyboard,
    get_payment_methods_keyboard,
    get_course_content_keyboard
)


async def show_courses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available courses"""
    query = update.callback_query
    if query:
        await query.answer()
        
        text = """
📚 **الدورات الاحترافية المتاحة:**

اختر المستوى المناسب لك:
    """
        
        await query.edit_message_text(
            text,
            reply_markup=get_courses_keyboard(),
            parse_mode="Markdown"
        )
    else:
        text = """
📚 **الدورات الاحترافية المتاحة:**

اختر المستوى المناسب لك:
    """
        
        await update.message.reply_text(
            text,
            reply_markup=get_courses_keyboard(),
            parse_mode="Markdown"
        )


async def show_course_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show course details"""
    query = update.callback_query
    await query.answer()
    
    # Extract course_id from callback_data
    course_id = query.data.replace("course_", "")
    course = get_course(course_id)
    
    if not course:
        await query.edit_message_text("❌ الدورة غير موجودة")
        return
    
    # Get user
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    if not user:
        await query.edit_message_text("❌ يرجى التسجيل أولاً باستخدام /start")
        return
    
    # Check if already enrolled
    enrollment = user.get_course_enrollment(course_id)
    
    if enrollment:
        if enrollment.approval_status == "approved":
            link = None
            try:
                if course.get('group_link'):
                    link = course['group_link']
                else:
                    gl_path = Path('data/group_links.json')
                    if gl_path.exists():
                        with open(gl_path, 'r', encoding='utf-8') as f:
                            gl = json.load(f)
                            link = gl.get('courses', {}).get(course_id) or gl.get(course_id)
            except Exception as e:
                logger.error(f"Error loading group link: {e}")
            if link:
                text = f"✅ **{course['name']}**\n\nانضم إلى المجموعة الخاصة بالدورة:" 
                keyboard = [
                    [InlineKeyboardButton("🔗 الانضمام إلى المجموعة", url=link)],
                    [InlineKeyboardButton("🎥 الفيديوهات", callback_data=f"videos_{course_id}")],
                    [InlineKeyboardButton("📝 الواجبات", callback_data=f"assignments_{course_id}")],
                    [InlineKeyboardButton("📋 الاختبارات", callback_data=f"exams_{course_id}")],
                    [InlineKeyboardButton("🔗 الروابط", callback_data=f"links_{course_id}")],
                    [InlineKeyboardButton("« رجوع", callback_data="back_courses")]
                ]
            else:
                text = f"✅ **{course['name']}**\n\nرابط المجموعة غير متاح حالياً. سيتم مشاركته قريباً."
                keyboard = [
                    [InlineKeyboardButton("🎥 الفيديوهات", callback_data=f"videos_{course_id}")],
                    [InlineKeyboardButton("📝 الواجبات", callback_data=f"assignments_{course_id}")],
                    [InlineKeyboardButton("📋 الاختبارات", callback_data=f"exams_{course_id}")],
                    [InlineKeyboardButton("🔗 الروابط", callback_data=f"links_{course_id}")],
                    [InlineKeyboardButton("« رجوع", callback_data="back_courses")]
                ]
            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        elif enrollment.approval_status == "pending":
            await query.message.reply_text(
                f"⏳ **{course['name']}**\n\n"
                "طلبك قيد المراجعة. سيتم إشعارك فور الموافقة."
            )
            return
        elif enrollment.approval_status == "rejected":
            await query.message.reply_text(
                f"❌ **{course['name']}**\n\n"
                "تم رفض طلبك. يرجى التواصل مع الإدارة."
            )
            return
    
    # Show course details for enrollment
    text = f"""
📚 **{course['name']}**

━━━━━━━━━━━━━━━━━━━━

⏱️ **المدة:** {course['duration']}

💰 **السعر:**
• التسجيل: 100,000 ل.س

📖 **محتوى الدورة:**
"""
    
    for i, item in enumerate(course['syllabus'], 1):
        text += f"{i}. {item}\n"
    
    text += "\n🎯 **المشاريع العملية:**\n"
    for proj in course['projects']:
        text += f"• {proj['name']}\n"
    
    text += "\n━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "💳 **اختر وسيلة الدفع للتسجيل:**"
    
    await query.edit_message_text(
        text,
        reply_markup=get_payment_methods_keyboard("course", course_id),
        parse_mode="Markdown"
    )


async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process payment - ask for proof"""
    query = update.callback_query
    await query.answer()
    
    # Parse callback_data: pay_method_type_id
    parts = query.data.split('_')
    payment_method = parts[1]  # shap or herm
    item_type = parts[2]  # course or material
    item_id = '_'.join(parts[3:])  # rest is the ID
    
    # Get payment info
    from config.settings import settings
    
    if payment_method == "shap" or payment_method == "sham":
        payment_number = settings.SHAP_CASH_NUMBER
        payment_name = "Sham Cash"
    else:
        payment_number = settings.HARAM_NUMBER
        payment_name = "HARAM"
    
    # Get item info
    if item_type == "course":
        course = get_course(item_id)
        item_name = course['name']
        amount = course['price']
    else:
        from config.materials_config import get_material, calculate_materials_price
        material = get_material(item_id)
        item_name = material['name']
        # Calculate price for single material
        amount = calculate_materials_price([item_id])
    
    # Store in context for next step
    context.user_data['payment'] = {
        'method': payment_method,
        'type': item_type,
        'id': item_id,
        'amount': amount
    }
    
    text = f"""
💳 **الدفع عبر {payment_name}**

📦 العنصر: {item_name}
💰 المبلغ: {amount:,} ل.س

📱 **رقم الحساب:**
`{payment_number}`

━━━━━━━━━━━━━━━━━━━━

**خطوات الدفع:**
1. قم بالتحويل إلى الرقم أعلاه
2. التقط صورة لإثبات الدفع (Screenshot)
3. أرسل الصورة هنا

⏳ في انتظار إثبات الدفع...
    """
    
    await query.edit_message_text(text, parse_mode="Markdown")


async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive payment proof photo"""
    if 'payment' not in context.user_data:
        await update.message.reply_text("❌ لا يوجد عملية دفع نشطة")
        return
    
    if not update.message.photo:
        await update.message.reply_text("❌ يرجى إرسال صورة لإثبات الدفع")
        return
    
    # Get largest photo
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    payment_data = context.user_data['payment']
    user = await User.find_one(User.telegram_id == update.effective_user.id)
    
    try:
        if payment_data['type'] == 'course':
            # Add course enrollment
            await user.add_course_enrollment(
                course_id=payment_data['id'],
                payment_amount=payment_data['amount'],
                payment_method=payment_data['method'].upper(),
                payment_proof_file_id=file_id
            )
            
            logger.info(f"Course enrollment payment received: {user.full_name} -> {payment_data['id']}")
            
        else:
            # Add material enrollment
            from config.materials_config import get_material
            material = get_material(payment_data['id'])
            await user.add_material_enrollment(
                material_id=payment_data['id'],
                year=material['year'],
                semester=material['semester'],
                payment_amount=payment_data['amount'],
                payment_method=payment_data['method'].upper(),
                payment_proof_file_id=file_id
            )
            
            logger.info(f"Material enrollment payment received: {user.full_name} -> {payment_data['id']}")
        
        # Send notification to admin
        from config.settings import settings
        admin_text = f"""
🔔 **طلب تسجيل جديد**

👤 الطالب: {user.full_name}
📱 الهاتف: {user.phone}
📧 البريد: {user.email}

📦 النوع: {'دورة' if payment_data['type'] == 'course' else 'مادة'}
💰 المبلغ: {payment_data['amount']:,} ل.س
💳 الوسيلة: {payment_data['method'].upper()}

⏳ في انتظار الموافقة
        """
        
        try:
            await context.bot.send_photo(
                chat_id=settings.TELEGRAM_ADMIN_ID,
                photo=file_id,
                caption=admin_text
            )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
        
        # Confirm to user
        await update.message.reply_text(
            "✅ **تم استلام إثبات الدفع!**\n\n"
            "⏳ طلبك قيد المراجعة من الإدارة\n"
            "سيتم إشعارك فور الموافقة على طلبك\n\n"
            "شكراً لثقتك 🙏"
        )
        
        # Clear payment data
        context.user_data.pop('payment', None)
        
    except Exception as e:
        import traceback
        logger.error(f"Payment processing error: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        await update.message.reply_text(
            "❌ حدث خطأ أثناء معالجة الدفع. يرجى المحاولة لاحقاً."
        )


async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current payment flow"""
    query = update.callback_query
    await query.answer()
    # Remove any stored payment context
    context.user_data.pop('payment', None)
    
    # Inform user and suggest using menus again
    await query.edit_message_text(
        "❌ تم إلغاء عملية الدفع.\n\n"
        "يمكنك اختيار دورة أو مادة أخرى من القوائم من جديد."
    )
