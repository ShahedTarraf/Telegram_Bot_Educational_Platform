"""
User Dashboard Handlers
معالجات لوحة المستخدم
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from database.models.user import User
from utils.statistics import StatisticsManager
from utils.achievements import AchievementManager
from utils.reports import ReportGenerator


async def show_my_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's statistics"""
    user_id = update.effective_user.id
    
    try:
        stats = await StatisticsManager.get_student_stats(user_id)
        
        if not stats:
            await update.message.reply_text("❌ لم نتمكن من جلب الإحصائيات", parse_mode="Markdown")
            return
        
        text = f"""
📊 **إحصائياتي - {stats['full_name']}**

📚 **الدورات:**
• مسجل في: {stats['enrolled_courses']} دورة
• بانتظار الموافقة: {stats['pending_courses']} دورة

📝 **الواجبات:**
• المجموع: {stats['total_assignments']}
• المسلمة: {stats['submitted']}
• المصححة: {stats['graded']}
• بانتظار التصحيح: {stats['pending']}

📈 **الأداء الأكاديمي:**
• المعدل العام: {stats['average_grade']}/100
• أعلى درجة: {stats['highest_grade']}/100
• أقل درجة: {stats['lowest_grade']}/100

✅ **النجاح/الرسوب:**
• الناجح: {stats['passed']}
• الراسب: {stats['failed']}

📅 **النشاط:**
• منذ التسجيل: {stats['days_since_registration']} يوم
• آخر نشاط: منذ {stats['days_since_last_active']} يوم
{'🟢 نشط' if stats['is_active'] else '🔴 غير نشط'}

💪 استمر في التقدم الرائع!
        """
        
        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing statistics: {e}")
        await update.message.reply_text("❌ حدث خطأ في عرض الإحصائيات")


async def show_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's achievements and badges"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = update.effective_user.id
    else:
        user_id = update.effective_user.id
    
    try:
        achievements_data = await AchievementManager.get_user_achievements(user_id)
        
        text = f"""
🏆 **شاراتي**

⭐ **نقاطي:** {achievements_data['total_points']} نقطة
🎖️ **الشارات المفتوحة:** {achievements_data['unlocked_count']}/{achievements_data['total_count']}

"""
        
        # Show unlocked achievements
        if achievements_data['unlocked']:
            text += "✅ **الشارات التي حصلت عليها:**\n\n"
            for ach in achievements_data['unlocked']:
                text += f"{ach['emoji']} **{ach['name']}**\n"
                text += f"   {ach['description']}\n"
                text += f"   🏆 +{ach['points']} نقطة\n\n"
        
        # Show some locked achievements
        if achievements_data['locked']:
            text += "\n🔒 **شارات يمكنك الحصول عليها:**\n\n"
            for ach in achievements_data['locked'][:5]:  # Show first 5
                text += f"{ach['emoji']} **{ach['name']}**\n"
                text += f"   {ach['description']}\n"
                text += f"   🏆 {ach['points']} نقطة\n\n"
        
        text += "\n💪 واصل التقدم لفتح المزيد من الشارات!"
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back_stats")]]
        
        if query:
            await query.message.edit_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
    except Exception as e:
        logger.error(f"Error showing achievements: {e}")
        await update.message.reply_text("❌ حدث خطأ في عرض الشارات")


async def show_admin_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin dashboard statistics"""
    try:
        stats = await StatisticsManager.get_dashboard_stats()
        
        text = f"""
📊 **الإحصائيات العامة - لوحة التحكم**

👥 **المستخدمون:**
• المجموع: {stats['total_users']}
• النشطين (آخر 7 أيام): {stats['active_users']}
• جدد هذا الأسبوع: {stats['new_users_this_week']}
• معدل التفاعل: {stats['engagement_rate']}%

📚 **التسجيلات:**
• المجموع: {stats['total_enrollments']}
• الموافق عليها: {stats['approved_enrollments']}
• بانتظار الموافقة: {stats['pending_enrollments']}

📝 **الواجبات:**
• المجموع: {stats['total_assignments']}
• التسليمات: {stats['total_submissions']}
• المصححة: {stats['graded_submissions']}
• بانتظار التصحيح: {stats['pending_grading']}

📈 **الأداء:**
• المعدل العام: {stats['average_grade']}/100
• معدل الإنجاز: {stats['completion_rate']}%

🎯 {'✅ الأداء ممتاز!' if stats['average_grade'] > 75 else '⚠️ يحتاج تحسين'}
        """
        
        keyboard = [
            [InlineKeyboardButton("📈 عرض الرسوم البيانية", callback_data="show_charts")],
            [InlineKeyboardButton("👥 أفضل 10 طلاب", callback_data="show_top_students")],
            [InlineKeyboardButton("📊 تقارير مفصلة", callback_data="admin_reports")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing admin statistics: {e}")
        await update.message.reply_text("❌ حدث خطأ في عرض الإحصائيات")


async def show_top_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top performing students"""
    query = update.callback_query
    await query.answer()
    
    try:
        top_students = await StatisticsManager.get_top_students(10)
        
        text = "🏆 **أفضل 10 طلاب**\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        
        for i, student in enumerate(top_students, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            text += f"{medal} **{student['full_name']}**\n"
            text += f"   📊 المعدل: {student['average_grade']}/100\n"
            text += f"   📝 الواجبات: {student['total_assignments']}\n\n"
        
        keyboard = [[InlineKeyboardButton("« رجوع", callback_data="back_admin_stats")]]
        
        await query.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Error showing top students: {e}")
        await query.message.edit_text("❌ حدث خطأ في عرض القائمة")


async def export_user_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export user report as PDF"""
    query = update.callback_query
    await query.answer("جاري تحضير التقرير...")
    
    user_id = int(query.data.split('_')[-1])
    
    try:
        pdf_buffer = await ReportGenerator.generate_student_report_pdf(user_id)
        
        if pdf_buffer:
            user = await User.find_one(User.telegram_id == user_id)
            filename = f"report_{user.full_name.replace(' ', '_')}.pdf"
            
            await context.bot.send_document(
                chat_id=user_id,
                document=pdf_buffer,
                filename=filename,
                caption="📊 تقريرك الأكاديمي"
            )
            
            await query.message.reply_text("✅ تم إرسال التقرير بنجاح!")
        else:
            await query.message.reply_text("❌ حدث خطأ في إنشاء التقرير")
            
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        await query.message.reply_text("❌ حدث خطأ في تصدير التقرير")


async def show_admin_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin reports menu"""
    query = update.callback_query
    await query.answer()
    
    text = """
📈 **التقارير**

اختر نوع التقرير الذي تريد تصديره:
    """
    
    keyboard = [
        [InlineKeyboardButton("👥 تقرير الطلاب (Excel)", callback_data="export_students_excel")],
        [InlineKeyboardButton("📊 تقرير الدرجات (Excel)", callback_data="export_grades_excel")],
        [InlineKeyboardButton("« رجوع", callback_data="back_admin_stats")]
    ]
    
    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def export_students_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export students report as Excel"""
    query = update.callback_query
    await query.answer("جاري تحضير التقرير...")
    
    try:
        excel_buffer = await ReportGenerator.generate_students_excel()
        
        if excel_buffer:
            await context.bot.send_document(
                chat_id=update.effective_user.id,
                document=excel_buffer,
                filename=f"students_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                caption="📊 تقرير الطلاب"
            )
            
            await query.message.reply_text("✅ تم إرسال التقرير بنجاح!")
        else:
            await query.message.reply_text("❌ حدث خطأ في إنشاء التقرير")
            
    except Exception as e:
        logger.error(f"Error exporting Excel: {e}")
        await query.message.reply_text("❌ حدث خطأ في تصدير التقرير")
