"""
Smart Notification System
نظام الإشعارات الذكي
"""
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import httpx
from loguru import logger

from database.models.user import User
from database.models.assignment import Assignment
from database.models.notification import Notification
from config.settings import settings


class SmartNotificationManager:
    """Smart notification manager with scheduling"""
    
    @staticmethod
    async def send_telegram_message(telegram_id: int, message: str, parse_mode: str = "Markdown"):
        """Send Telegram message"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": telegram_id,
                        "text": message,
                        "parse_mode": parse_mode
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {telegram_id}: {e}")
            return False
    
    @staticmethod
    async def create_and_send_notification(
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "info",
        related_id: Optional[str] = None
    ):
        """Create notification in DB and send via Telegram"""
        try:
            # Create in database
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                related_id=related_id
            )
            await notification.insert()
            
            # Format message
            emoji_map = {
                'info': 'ℹ️',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'assignment': '📝',
                'grade': '🎓',
                'approval': '✅',
                'deadline': '⏰'
            }
            
            emoji = emoji_map.get(notification_type, 'ℹ️')
            formatted_message = f"{emoji} **{title}**\n\n{message}"
            
            # Send via Telegram
            await SmartNotificationManager.send_telegram_message(
                user_id,
                formatted_message
            )
            
            logger.info(f"Notification sent to user {user_id}: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to create and send notification: {e}")
            return False
    
    @staticmethod
    async def send_deadline_reminders():
        """Send reminders for assignments due soon"""
        try:
            # Find assignments due in 24 hours
            tomorrow = datetime.utcnow() + timedelta(days=1)
            day_after = datetime.utcnow() + timedelta(days=2)
            
            assignments = await Assignment.find(
                Assignment.deadline > tomorrow,
                Assignment.deadline < day_after
            ).to_list()
            
            for assignment in assignments:
                # Get all students who haven't submitted
                users = await User.find().to_list()
                
                for user in users:
                    # Check if user has access and hasn't submitted
                    if user.has_approved_course(assignment.related_id):
                        submission = assignment.get_submission(str(user.telegram_id))
                        
                        if not submission:
                            # Send reminder
                            hours_left = int((assignment.deadline - datetime.utcnow()).total_seconds() / 3600)
                            
                            message = f"""
⏰ **تذكير بموعد نهائي قريب!**

📝 **الواجب:** {assignment.title}
⏱️ **الوقت المتبقي:** {hours_left} ساعة

لم تقم بتسليم هذا الواجب بعد!
يرجى التسليم قبل انتهاء الموعد.

🔔 لن نرسل المزيد من التذكيرات.
                            """
                            
                            await SmartNotificationManager.create_and_send_notification(
                                user.telegram_id,
                                "تذكير بموعد نهائي",
                                message.strip(),
                                "deadline",
                                str(assignment.id)
                            )
            
            logger.info(f"Deadline reminders sent for {len(assignments)} assignments")
        except Exception as e:
            logger.error(f"Error sending deadline reminders: {e}")
    
    @staticmethod
    async def send_new_content_notification(content_type: str, content_title: str, course_id: str):
        """Notify students about new content"""
        try:
            # Get all enrolled students
            users = await User.find().to_list()
            enrolled_users = [u for u in users if u.has_approved_course(course_id)]
            
            emoji_map = {
                'video': '🎥',
                'assignment': '📝',
                'exam': '📄',
                'lecture': '📖'
            }
            
            emoji = emoji_map.get(content_type, '📢')
            
            message = f"""
{emoji} **محتوى جديد متاح!**

تم إضافة: **{content_title}**
النوع: {content_type}

افتح البوت الآن للوصول إلى المحتوى الجديد! 🚀
            """
            
            for user in enrolled_users:
                await SmartNotificationManager.create_and_send_notification(
                    user.telegram_id,
                    "محتوى جديد",
                    message.strip(),
                    "info",
                    course_id
                )
            
            logger.info(f"New content notification sent to {len(enrolled_users)} users")
        except Exception as e:
            logger.error(f"Error sending new content notification: {e}")
    
    @staticmethod
    async def send_daily_admin_summary():
        """Send daily summary to admin"""
        try:
            # Calculate today's stats
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # New registrations
            new_users = await User.find(User.registered_at > today).count()
            
            # New submissions
            all_assignments = await Assignment.find().to_list()
            new_submissions = 0
            for assignment in all_assignments:
                for submission in assignment.submissions:
                    if submission.submitted_at > today:
                        new_submissions += 1
            
            # Pending grading
            pending_grading = 0
            for assignment in all_assignments:
                for submission in assignment.submissions:
                    if submission.status == "submitted":
                        pending_grading += 1
            
            # Pending approvals
            pending_approvals = await User.find(
                User.courses.approval_status == "pending"
            ).count()
            
            message = f"""
📊 **ملخص يومي - {datetime.utcnow().strftime('%Y-%m-%d')}**

👥 **مستخدمون جدد:** {new_users}
📝 **تسليمات جديدة:** {new_submissions}
⏳ **بانتظار التصحيح:** {pending_grading}
⏰ **طلبات انتظار الموافقة:** {pending_approvals}

{'✅ لا توجد مهام عاجلة!' if pending_grading == 0 and pending_approvals == 0 else '⚠️ لديك مهام تحتاج انتباهك!'}

🔗 افتح لوحة التحكم: http://localhost:8000
            """
            
            await SmartNotificationManager.send_telegram_message(
                settings.TELEGRAM_ADMIN_ID,
                message.strip()
            )
            
            logger.info("Daily admin summary sent")
        except Exception as e:
            logger.error(f"Error sending daily admin summary: {e}")
    
    @staticmethod
    async def send_welcome_message(telegram_id: int, full_name: str):
        """Send welcome message to new user"""
        message = f"""
🎉 **مرحباً {full_name}!**

نحن سعداء بانضمامك إلى المنصة التعليمية! 

📚 **ماذا يمكنك فعله الآن؟**

1️⃣ تصفح الدورات الاحترافية
2️⃣ الاطلاع على المواد الجامعية
3️⃣ التسجيل في الدورات
4️⃣ مشاهدة الفيديوهات التعليمية
5️⃣ حل الواجبات والاختبارات

💡 **نصيحة:** ابدأ بتصفح الدورات المتاحة واختر ما يناسبك!

🤝 **بحاجة لمساعدة؟**
استخدم زر "📞 التواصل" في أي وقت.

حظاً موفقاً في رحلتك التعليمية! 🚀
        """
        
        await SmartNotificationManager.create_and_send_notification(
            telegram_id,
            "مرحباً بك!",
            message.strip(),
            "success"
        )
    
    @staticmethod
    async def send_inactivity_reminder(telegram_id: int, full_name: str, days_inactive: int):
        """Send reminder to inactive users"""
        message = f"""
👋 **نفتقدك يا {full_name}!**

لم نرك منذ {days_inactive} أيام! 😢

📚 **هل تعلم؟**
تم إضافة محتوى جديد ومثير للاهتمام!

✨ **عد الآن واكتشف:**
• فيديوهات جديدة
• واجبات ممتعة
• اختبارات تفاعلية

⏰ لا تفوت الفرصة - بعض الدورات لها موعد نهائي قريب!

نحن بانتظارك! 💪
        """
        
        await SmartNotificationManager.create_and_send_notification(
            telegram_id,
            "نفتقدك!",
            message.strip(),
            "info"
        )
    
    @staticmethod
    async def send_achievement_notification(telegram_id: int, achievement_name: str, achievement_desc: str):
        """Send achievement/badge notification"""
        message = f"""
🏆 **إنجاز جديد!**

🎖️ **{achievement_name}**

{achievement_desc}

استمر في العمل الرائع! 💪
شاركنا إنجازك مع أصدقائك! 🎉
        """
        
        await SmartNotificationManager.create_and_send_notification(
            telegram_id,
            "إنجاز جديد!",
            message.strip(),
            "success"
        )


class NotificationScheduler:
    """Background task scheduler for notifications"""
    
    @staticmethod
    async def start_notification_scheduler():
        """Start background notification tasks"""
        logger.info("Starting notification scheduler...")
        
        while True:
            try:
                # Run deadline reminders every 6 hours
                await SmartNotificationManager.send_deadline_reminders()
                
                # Check for inactive users (daily at 10 AM)
                now = datetime.utcnow()
                if now.hour == 10:
                    await NotificationScheduler.send_inactivity_reminders()
                
                # Send daily admin summary (daily at 8 PM)
                if now.hour == 20:
                    await SmartNotificationManager.send_daily_admin_summary()
                
                # Wait 6 hours
                await asyncio.sleep(6 * 60 * 60)
                
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(60)
    
    @staticmethod
    async def send_inactivity_reminders():
        """Check and send inactivity reminders"""
        try:
            week_ago = datetime.utcnow() - timedelta(days=7)
            inactive_users = await User.find(User.last_active < week_ago).to_list()
            
            for user in inactive_users:
                days_inactive = (datetime.utcnow() - user.last_active).days
                await SmartNotificationManager.send_inactivity_reminder(
                    user.telegram_id,
                    user.full_name,
                    days_inactive
                )
            
            logger.info(f"Inactivity reminders sent to {len(inactive_users)} users")
        except Exception as e:
            logger.error(f"Error sending inactivity reminders: {e}")
