"""
Advanced Statistics System
نظام الإحصائيات المتقدم
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database.models.user import User
from database.models.assignment import Assignment
from database.models.notification import Notification
from loguru import logger


class StatisticsManager:
    """Advanced statistics manager"""
    
    @staticmethod
    async def get_dashboard_stats() -> Dict:
        """Get comprehensive dashboard statistics"""
        try:
            # User statistics
            logger.debug("get_dashboard_stats: counting total users")
            total_users = await User.find().count()
            logger.debug(f"get_dashboard_stats: total_users={total_users}")
            active_users = await User.find(
                User.last_active > datetime.utcnow() - timedelta(days=7)
            ).count()
            logger.debug(f"get_dashboard_stats: active_users_last_7_days={active_users}")
            new_users_this_week = await User.find(
                User.registered_at > datetime.utcnow() - timedelta(days=7)
            ).count()
            logger.debug(f"get_dashboard_stats: new_users_this_week={new_users_this_week}")
            
            # Course enrollment stats
            logger.debug("get_dashboard_stats: loading all users for enrollment stats")
            users = await User.find().to_list()
            logger.debug(f"get_dashboard_stats: loaded {len(users)} users for enrollment stats")
            total_enrollments = sum(len(user.courses) for user in users)
            approved_enrollments = sum(
                len([c for c in user.courses if c.approval_status == "approved"])
                for user in users
            )
            pending_enrollments = sum(
                len([c for c in user.courses if c.approval_status == "pending"])
                for user in users
            )
            
            # Assignment stats
            logger.debug("get_dashboard_stats: loading all assignments")
            all_assignments = await Assignment.find().to_list()
            logger.debug(f"get_dashboard_stats: loaded {len(all_assignments)} assignments")
            total_assignments = len(all_assignments)
            total_submissions = sum(len(a.submissions) for a in all_assignments)
            graded_submissions = sum(
                len([s for s in a.submissions if s.status == "graded"])
                for a in all_assignments
            )
            
            # Calculate average grade
            all_grades = []
            for assignment in all_assignments:
                for submission in assignment.submissions:
                    if submission.grade is not None:
                        all_grades.append(submission.grade)
            
            average_grade = sum(all_grades) / len(all_grades) if all_grades else 0
            
            # Engagement rate
            engagement_rate = (active_users / total_users * 100) if total_users > 0 else 0
            
            # Completion rate
            completion_rate = (
                graded_submissions / total_submissions * 100
            ) if total_submissions > 0 else 0
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'new_users_this_week': new_users_this_week,
                'total_enrollments': total_enrollments,
                'approved_enrollments': approved_enrollments,
                'pending_enrollments': pending_enrollments,
                'total_assignments': total_assignments,
                'total_submissions': total_submissions,
                'graded_submissions': graded_submissions,
                'pending_grading': total_submissions - graded_submissions,
                'average_grade': round(average_grade, 2),
                'engagement_rate': round(engagement_rate, 2),
                'completion_rate': round(completion_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}
    
    @staticmethod
    async def get_student_stats(telegram_id: int) -> Dict:
        """Get individual student statistics"""
        try:
            logger.debug(f"get_student_stats: loading user by telegram_id={telegram_id}")
            user = await User.find_one(User.telegram_id == telegram_id)
            if not user:
                return {}
            
            # Get all assignments with this student's submissions
            logger.debug("get_student_stats: loading all assignments")
            all_assignments = await Assignment.find().to_list()
            logger.debug(f"get_student_stats: loaded {len(all_assignments)} assignments")
            student_assignments = []
            
            for assignment in all_assignments:
                submission = assignment.get_submission(str(telegram_id))
                if submission:
                    student_assignments.append({
                        'assignment': assignment,
                        'submission': submission
                    })
            
            # Calculate stats
            total_assignments = len(student_assignments)
            submitted = len([a for a in student_assignments if a['submission'].submitted_at])
            graded = len([a for a in student_assignments if a['submission'].status == 'graded'])
            
            grades = [
                a['submission'].grade
                for a in student_assignments
                if a['submission'].grade is not None
            ]
            
            average_grade = sum(grades) / len(grades) if grades else 0
            highest_grade = max(grades) if grades else 0
            lowest_grade = min(grades) if grades else 0
            
            passed = len([g for g in grades if g >= 60])
            failed = len([g for g in grades if g < 60])
            
            # Enrollment stats
            enrolled_courses = len([c for c in user.courses if c.approval_status == 'approved'])
            pending_courses = len([c for c in user.courses if c.approval_status == 'pending'])
            
            # Activity
            days_since_registration = (datetime.utcnow() - user.registered_at).days
            days_since_last_active = (datetime.utcnow() - user.last_active).days
            
            return {
                'full_name': user.full_name,
                'enrolled_courses': enrolled_courses,
                'pending_courses': pending_courses,
                'total_assignments': total_assignments,
                'submitted': submitted,
                'graded': graded,
                'pending': submitted - graded,
                'average_grade': round(average_grade, 2),
                'highest_grade': highest_grade,
                'lowest_grade': lowest_grade,
                'passed': passed,
                'failed': failed,
                'days_since_registration': days_since_registration,
                'days_since_last_active': days_since_last_active,
                'is_active': days_since_last_active < 7
            }
        except Exception as e:
            logger.error(f"Error getting student stats: {e}")
            return {}
    
    @staticmethod
    async def get_assignment_stats(assignment_id: str) -> Dict:
        """Get assignment-specific statistics"""
        try:
            logger.debug(f"get_assignment_stats: loading assignment by id={assignment_id}")
            assignment = await Assignment.find_one(Assignment.id == assignment_id)
            if not assignment:
                return {}
            
            total_submissions = len(assignment.submissions)
            graded = len([s for s in assignment.submissions if s.status == 'graded'])
            pending = total_submissions - graded
            
            grades = [s.grade for s in assignment.submissions if s.grade is not None]
            
            if grades:
                average_grade = sum(grades) / len(grades)
                highest_grade = max(grades)
                lowest_grade = min(grades)
                passed = len([g for g in grades if g >= assignment.pass_grade])
                failed = len([g for g in grades if g < assignment.pass_grade])
            else:
                average_grade = 0
                highest_grade = 0
                lowest_grade = 0
                passed = 0
                failed = 0
            
            # Submission timeliness
            on_time = 0
            late = 0
            
            for submission in assignment.submissions:
                if assignment.deadline:
                    if submission.submitted_at <= assignment.deadline:
                        on_time += 1
                    else:
                        late += 1
            
            return {
                'title': assignment.title,
                'total_submissions': total_submissions,
                'graded': graded,
                'pending': pending,
                'average_grade': round(average_grade, 2),
                'highest_grade': highest_grade,
                'lowest_grade': lowest_grade,
                'passed': passed,
                'failed': failed,
                'pass_rate': round(passed / graded * 100, 2) if graded > 0 else 0,
                'on_time': on_time,
                'late': late
            }
        except Exception as e:
            logger.error(f"Error getting assignment stats: {e}")
            return {}
    
    @staticmethod
    async def get_top_students(limit: int = 10) -> List[Dict]:
        """Get top performing students"""
        try:
            logger.debug("get_top_students: loading all users")
            users = await User.find().to_list()
            logger.debug(f"get_top_students: loaded {len(users)} users")
            logger.debug("get_top_students: loading all assignments")
            all_assignments = await Assignment.find().to_list()
            logger.debug(f"get_top_students: loaded {len(all_assignments)} assignments")
            
            student_performances = []
            
            for user in users:
                grades = []
                for assignment in all_assignments:
                    submission = assignment.get_submission(str(user.telegram_id))
                    if submission and submission.grade is not None:
                        grades.append(submission.grade)
                
                if grades:
                    avg_grade = sum(grades) / len(grades)
                    student_performances.append({
                        'telegram_id': user.telegram_id,
                        'full_name': user.full_name,
                        'email': user.email,
                        'average_grade': round(avg_grade, 2),
                        'total_assignments': len(grades)
                    })
            
            # Sort by average grade
            student_performances.sort(key=lambda x: x['average_grade'], reverse=True)
            
            return student_performances[:limit]
        except Exception as e:
            logger.error(f"Error getting top students: {e}")
            return []
    
    @staticmethod
    async def get_activity_chart_data(days: int = 30) -> Dict:
        """Get activity data for charts"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get daily registrations
            logger.debug(f"get_activity_chart_data: loading users registered after {start_date}")
            users = await User.find(User.registered_at > start_date).to_list()
            logger.debug(f"get_activity_chart_data: loaded {len(users)} users for registrations chart")
            
            daily_registrations = {}
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_key = date.strftime('%Y-%m-%d')
                daily_registrations[date_key] = 0
            
            for user in users:
                date_key = user.registered_at.strftime('%Y-%m-%d')
                if date_key in daily_registrations:
                    daily_registrations[date_key] += 1
            
            # Get daily submissions
            logger.debug("get_activity_chart_data: loading all assignments for submissions chart")
            all_assignments = await Assignment.find().to_list()
            logger.debug(f"get_activity_chart_data: loaded {len(all_assignments)} assignments for submissions chart")
            daily_submissions = {}
            
            for i in range(days):
                date = start_date + timedelta(days=i)
                date_key = date.strftime('%Y-%m-%d')
                daily_submissions[date_key] = 0
            
            for assignment in all_assignments:
                for submission in assignment.submissions:
                    date_key = submission.submitted_at.strftime('%Y-%m-%d')
                    if date_key in daily_submissions:
                        daily_submissions[date_key] += 1
            
            return {
                'labels': list(daily_registrations.keys()),
                'registrations': list(daily_registrations.values()),
                'submissions': list(daily_submissions.values())
            }
        except Exception as e:
            logger.error(f"Error getting activity chart data: {e}")
            return {}
