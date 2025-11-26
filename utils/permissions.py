"""
Advanced Permissions System
نظام الأذونات المتقدم
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from database.models.user import User
from config.settings import settings


class Permission(str, Enum):
    """Permission types"""
    # Content management
    CREATE_VIDEO = "create_video"
    DELETE_VIDEO = "delete_video"
    CREATE_ASSIGNMENT = "create_assignment"
    DELETE_ASSIGNMENT = "delete_assignment"
    CREATE_QUIZ = "create_quiz"
    DELETE_QUIZ = "delete_quiz"
    
    # Grading
    GRADE_ASSIGNMENTS = "grade_assignments"
    GRADE_QUIZZES = "grade_quizzes"
    
    # User management
    VIEW_ALL_STUDENTS = "view_all_students"
    APPROVE_ENROLLMENTS = "approve_enrollments"
    EDIT_USER = "edit_user"
    DELETE_USER = "delete_user"
    
    # Communication
    SEND_ANNOUNCEMENTS = "send_announcements"
    ACCESS_CHAT = "access_chat"
    
    # Reports
    EXPORT_REPORTS = "export_reports"
    VIEW_ANALYTICS = "view_analytics"
    
    # System
    MANAGE_ROLES = "manage_roles"
    SYSTEM_SETTINGS = "system_settings"


class Role(str, Enum):
    """User roles"""
    SUPER_ADMIN = "super_admin"
    INSTRUCTOR = "instructor"
    ASSISTANT = "assistant"
    STUDENT = "student"
    GUEST = "guest"


class RolePermissions(BaseModel):
    """Role with its permissions"""
    role: Role
    permissions: List[Permission]
    description: str


class PermissionManager:
    """Manage user permissions"""
    
    # Define role permissions
    ROLE_PERMISSIONS = {
        Role.SUPER_ADMIN: [
            # Has all permissions
            Permission.CREATE_VIDEO,
            Permission.DELETE_VIDEO,
            Permission.CREATE_ASSIGNMENT,
            Permission.DELETE_ASSIGNMENT,
            Permission.CREATE_QUIZ,
            Permission.DELETE_QUIZ,
            Permission.GRADE_ASSIGNMENTS,
            Permission.GRADE_QUIZZES,
            Permission.VIEW_ALL_STUDENTS,
            Permission.APPROVE_ENROLLMENTS,
            Permission.EDIT_USER,
            Permission.DELETE_USER,
            Permission.SEND_ANNOUNCEMENTS,
            Permission.ACCESS_CHAT,
            Permission.EXPORT_REPORTS,
            Permission.VIEW_ANALYTICS,
            Permission.MANAGE_ROLES,
            Permission.SYSTEM_SETTINGS
        ],
        
        Role.INSTRUCTOR: [
            Permission.CREATE_VIDEO,
            Permission.CREATE_ASSIGNMENT,
            Permission.CREATE_QUIZ,
            Permission.GRADE_ASSIGNMENTS,
            Permission.GRADE_QUIZZES,
            Permission.VIEW_ALL_STUDENTS,
            Permission.APPROVE_ENROLLMENTS,
            Permission.SEND_ANNOUNCEMENTS,
            Permission.ACCESS_CHAT,
            Permission.EXPORT_REPORTS,
            Permission.VIEW_ANALYTICS
        ],
        
        Role.ASSISTANT: [
            Permission.GRADE_ASSIGNMENTS,
            Permission.GRADE_QUIZZES,
            Permission.VIEW_ALL_STUDENTS,
            Permission.ACCESS_CHAT,
            Permission.VIEW_ANALYTICS
        ],
        
        Role.STUDENT: [
            Permission.ACCESS_CHAT
        ],
        
        Role.GUEST: []
    }
    
    @classmethod
    def get_role_permissions(cls, role: Role) -> List[Permission]:
        """Get permissions for a role"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    async def get_user_role(cls, telegram_id: int) -> Role:
        """Get user's role"""
        # Check if super admin
        if telegram_id == settings.TELEGRAM_ADMIN_ID:
            return Role.SUPER_ADMIN
        
        # Get from database
        user = await User.find_one(User.telegram_id == telegram_id)
        if not user:
            return Role.GUEST
        
        # Check if user has role attribute
        if hasattr(user, 'role') and user.role:
            try:
                return Role(user.role)
            except ValueError:
                pass
        
        # Default to student if registered
        return Role.STUDENT
    
    @classmethod
    async def has_permission(cls, telegram_id: int, permission: Permission) -> bool:
        """Check if user has specific permission"""
        role = await cls.get_user_role(telegram_id)
        role_permissions = cls.get_role_permissions(role)
        return permission in role_permissions
    
    @classmethod
    async def has_any_permission(cls, telegram_id: int, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions"""
        role = await cls.get_user_role(telegram_id)
        role_permissions = cls.get_role_permissions(role)
        return any(p in role_permissions for p in permissions)
    
    @classmethod
    async def has_all_permissions(cls, telegram_id: int, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions"""
        role = await cls.get_user_role(telegram_id)
        role_permissions = cls.get_role_permissions(role)
        return all(p in role_permissions for p in permissions)
    
    @classmethod
    async def assign_role(cls, telegram_id: int, role: Role) -> bool:
        """Assign role to user"""
        try:
            user = await User.find_one(User.telegram_id == telegram_id)
            if not user:
                return False
            
            user.role = role.value
            await user.save()
            return True
        except Exception:
            return False
    
    @classmethod
    def get_role_description(cls, role: Role) -> str:
        """Get role description"""
        descriptions = {
            Role.SUPER_ADMIN: "مدير النظام - صلاحيات كاملة",
            Role.INSTRUCTOR: "مدرس - يمكنه إنشاء المحتوى والتقييم",
            Role.ASSISTANT: "مساعد تدريس - يمكنه التقييم والمساعدة",
            Role.STUDENT: "طالب - يمكنه الوصول للمحتوى والتسليم",
            Role.GUEST: "ضيف - صلاحيات محدودة"
        }
        return descriptions.get(role, "غير معروف")
    
    @classmethod
    async def get_user_permissions_list(cls, telegram_id: int) -> List[str]:
        """Get list of user's permissions"""
        role = await cls.get_user_role(telegram_id)
        permissions = cls.get_role_permissions(role)
        return [p.value for p in permissions]


# Decorator for permission checking
def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            
            if not await PermissionManager.has_permission(user_id, permission):
                await update.message.reply_text(
                    "❌ ليس لديك صلاحية للقيام بهذا الإجراء."
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(update, context, *args, **kwargs):
            user_id = update.effective_user.id
            user_role = await PermissionManager.get_user_role(user_id)
            
            if user_role != role:
                await update.message.reply_text(
                    f"❌ هذه الميزة متاحة فقط لـ {PermissionManager.get_role_description(role)}"
                )
                return
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
