"""
Achievements and Badges System
نظام الشارات والمكافآت
"""
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger

from database.models.user import User
from database.models.assignment import Assignment
from database.models.quiz import Quiz
from utils.notifications import SmartNotificationManager


class Achievement:
    """Achievement definition"""
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        emoji: str,
        points: int,
        check_function
    ):
        self.id = id
        self.name = name
        self.description = description
        self.emoji = emoji
        self.points = points
        self.check_function = check_function


class AchievementManager:
    """Manage user achievements"""
    
    ACHIEVEMENTS = []
    
    @classmethod
    def initialize(cls):
        """Initialize all achievements"""
        cls.ACHIEVEMENTS = [
            # First steps
            Achievement(
                "first_login",
                "أول تسجيل دخول",
                "قمت بتسجيل الدخول لأول مرة!",
                "👋",
                10,
                cls.check_first_login
            ),
            Achievement(
                "first_enrollment",
                "أول تسجيل في دورة",
                "سجلت في أول دورة لك!",
                "📚",
                20,
                cls.check_first_enrollment
            ),
            Achievement(
                "first_submission",
                "أول تسليم",
                "سلمت أول واجب لك!",
                "📝",
                30,
                cls.check_first_submission
            ),
            
            # Academic achievements
            Achievement(
                "perfect_score",
                "الدرجة الكاملة",
                "حصلت على 100/100 في واجب!",
                "💯",
                50,
                cls.check_perfect_score
            ),
            Achievement(
                "high_achiever",
                "متفوق",
                "معدلك أعلى من 90%",
                "⭐",
                100,
                cls.check_high_achiever
            ),
            Achievement(
                "dedicated_student",
                "طالب ملتزم",
                "سلمت 5 واجبات متتالية في الوقت المحدد",
                "🎯",
                80,
                cls.check_dedicated_student
            ),
            
            # Streaks
            Achievement(
                "weekly_active",
                "نشيط أسبوعياً",
                "دخلت كل يوم لمدة أسبوع",
                "🔥",
                40,
                cls.check_weekly_active
            ),
            Achievement(
                "quiz_master",
                "خبير الاختبارات",
                "نجحت في 5 اختبارات",
                "🎓",
                70,
                cls.check_quiz_master
            ),
            
            # Special achievements
            Achievement(
                "early_bird",
                "الطائر المبكر",
                "أول من يسلم الواجب",
                "🌅",
                60,
                cls.check_early_bird
            ),
            Achievement(
                "course_completer",
                "منهي الدورات",
                "أنهيت دورة كاملة بنجاح",
                "🏆",
                150,
                cls.check_course_completer
            ),
            Achievement(
                "helping_hand",
                "يد المساعدة",
                "ساعدت 3 زملاء عبر الدردشة",
                "🤝",
                90,
                cls.check_helping_hand
            )
        ]
    
    @staticmethod
    async def check_first_login(user: User) -> bool:
        """Check if this is user's first login"""
        return user.registered_at is not None
    
    @staticmethod
    async def check_first_enrollment(user: User) -> bool:
        """Check if user has enrolled in a course"""
        return len(user.courses) > 0
    
    @staticmethod
    async def check_first_submission(user: User) -> bool:
        """Check if user has submitted an assignment"""
        assignments = await Assignment.find().to_list()
        for assignment in assignments:
            if assignment.has_submitted(str(user.telegram_id)):
                return True
        return False
    
    @staticmethod
    async def check_perfect_score(user: User) -> bool:
        """Check if user got 100/100"""
        assignments = await Assignment.find().to_list()
        for assignment in assignments:
            submission = assignment.get_submission(str(user.telegram_id))
            if submission and submission.grade == assignment.max_grade:
                return True
        return False
    
    @staticmethod
    async def check_high_achiever(user: User) -> bool:
        """Check if average grade is above 90%"""
        assignments = await Assignment.find().to_list()
        grades = []
        
        for assignment in assignments:
            submission = assignment.get_submission(str(user.telegram_id))
            if submission and submission.grade is not None:
                percentage = (submission.grade / assignment.max_grade) * 100
                grades.append(percentage)
        
        if grades:
            avg = sum(grades) / len(grades)
            return avg >= 90
        return False
    
    @staticmethod
    async def check_dedicated_student(user: User) -> bool:
        """Check if submitted 5 assignments on time"""
        assignments = await Assignment.find().to_list()
        on_time_count = 0
        
        for assignment in assignments:
            submission = assignment.get_submission(str(user.telegram_id))
            if submission and assignment.deadline:
                if submission.submitted_at <= assignment.deadline:
                    on_time_count += 1
        
        return on_time_count >= 5
    
    @staticmethod
    async def check_weekly_active(user: User) -> bool:
        """Check if active every day for a week"""
        # This would require tracking daily activity
        # For now, simplified check
        week_ago = datetime.utcnow() - timedelta(days=7)
        return user.last_active > week_ago
    
    @staticmethod
    async def check_quiz_master(user: User) -> bool:
        """Check if passed 5 quizzes"""
        quizzes = await Quiz.find().to_list()
        passed_count = 0
        
        for quiz in quizzes:
            best = quiz.get_best_attempt(str(user.telegram_id))
            if best and best.passed:
                passed_count += 1
        
        return passed_count >= 5
    
    @staticmethod
    async def check_early_bird(user: User) -> bool:
        """Check if first to submit"""
        assignments = await Assignment.find().to_list()
        for assignment in assignments:
            if len(assignment.submissions) > 0:
                first_submission = min(assignment.submissions, key=lambda s: s.submitted_at)
                if first_submission.user_id == str(user.telegram_id):
                    return True
        return False
    
    @staticmethod
    async def check_course_completer(user: User) -> bool:
        """Check if completed a course"""
        # This would require course completion tracking
        # Simplified: check if passed all assignments in a course
        return False  # Implement based on course structure
    
    @staticmethod
    async def check_helping_hand(user: User) -> bool:
        """Check if helped others via chat"""
        # This would require chat message tracking
        return False  # Implement based on chat system
    
    @classmethod
    async def check_all_achievements(cls, user: User) -> List[Achievement]:
        """Check all achievements for a user"""
        if not cls.ACHIEVEMENTS:
            cls.initialize()
        
        unlocked = []
        
        for achievement in cls.ACHIEVEMENTS:
            try:
                if await achievement.check_function(user):
                    # Check if user already has this achievement
                    if not hasattr(user, 'achievements'):
                        user.achievements = []
                    
                    if achievement.id not in user.achievements:
                        unlocked.append(achievement)
            except Exception as e:
                logger.error(f"Error checking achievement {achievement.id}: {e}")
        
        return unlocked
    
    @classmethod
    async def award_achievement(cls, user: User, achievement: Achievement):
        """Award achievement to user"""
        try:
            # Add to user's achievements
            if not hasattr(user, 'achievements'):
                user.achievements = []
            
            if achievement.id not in user.achievements:
                user.achievements.append(achievement.id)
                
                # Add points
                if not hasattr(user, 'achievement_points'):
                    user.achievement_points = 0
                user.achievement_points += achievement.points
                
                await user.save()
                
                # Send notification
                await SmartNotificationManager.send_achievement_notification(
                    user.telegram_id,
                    f"{achievement.emoji} {achievement.name}",
                    f"{achievement.description}\n\n🏆 +{achievement.points} نقطة!"
                )
                
                logger.info(f"Achievement {achievement.id} awarded to user {user.telegram_id}")
                return True
        except Exception as e:
            logger.error(f"Error awarding achievement: {e}")
        
        return False
    
    @classmethod
    async def check_and_award_achievements(cls, user: User):
        """Check and award new achievements"""
        unlocked = await cls.check_all_achievements(user)
        
        for achievement in unlocked:
            await cls.award_achievement(user, achievement)
    
    @classmethod
    async def get_user_achievements(cls, telegram_id: int) -> Dict:
        """Get user's achievement statistics"""
        if not cls.ACHIEVEMENTS:
            cls.initialize()
        
        user = await User.find_one(User.telegram_id == telegram_id)
        if not user:
            return {}
        
        if not hasattr(user, 'achievements'):
            user.achievements = []
        
        unlocked_achievements = []
        locked_achievements = []
        
        for achievement in cls.ACHIEVEMENTS:
            if achievement.id in user.achievements:
                unlocked_achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'emoji': achievement.emoji,
                    'points': achievement.points
                })
            else:
                locked_achievements.append({
                    'id': achievement.id,
                    'name': achievement.name,
                    'description': achievement.description,
                    'emoji': '🔒',
                    'points': achievement.points
                })
        
        total_points = getattr(user, 'achievement_points', 0)
        
        return {
            'total_points': total_points,
            'unlocked_count': len(unlocked_achievements),
            'total_count': len(cls.ACHIEVEMENTS),
            'unlocked': unlocked_achievements,
            'locked': locked_achievements
        }


# Initialize on import
AchievementManager.initialize()
