"""
Notification Model
"""
from datetime import datetime
from typing import Optional, Union
from beanie import Document
from pydantic import Field


class Notification(Document):
    """Notification model"""
    user_id: Union[str, int]  # telegram_id of recipient (can be str or int)
    
    # Content
    title: str
    message: str
    notification_type: str  # approval, new_video, new_assignment, new_exam, project_update, payment_approved, etc.
    
    # Related content
    related_to: Optional[str] = None  # course, material, assignment, exam, project
    related_id: Optional[str] = None
    
    # Action button (optional)
    action_text: Optional[str] = None
    action_callback: Optional[str] = None
    
    # Status
    sent: bool = False
    read: bool = False
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Priority
    priority: str = "normal"  # low, normal, high, urgent
    
    class Settings:
        name = "notifications"
        indexes = [
            "user_id",
            "read",
            "sent",
            ("user_id", "read"),
        ]
    
    async def mark_as_sent(self):
        """Mark notification as sent"""
        self.sent = True
        self.sent_at = datetime.utcnow()
        await self.save()
    
    async def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.utcnow()
        await self.save()
    
    def get_formatted_text(self) -> str:
        """Get formatted notification text"""
        emoji_map = {
            "approval": "✅",
            "new_video": "🎥",
            "new_assignment": "📝",
            "new_exam": "📋",
            "project_update": "💼",
            "payment_approved": "💰",
            "payment_rejected": "❌",
            "general": "📢"
        }
        
        emoji = emoji_map.get(self.notification_type, "📢")
        text = f"{emoji} **{self.title}**\n\n{self.message}"
        return text
