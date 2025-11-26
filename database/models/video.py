"""
Video Model
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field


class Video(Document):
    """Video model"""
    title: str
    description: Optional[str] = None
    file_id: str  # Telegram File ID
    file_unique_id: str  # Telegram unique file ID
    duration: Optional[int] = None  # Duration in seconds
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail_file_id: Optional[str] = None
    
    # Classification
    video_type: str  # lecture, assignment_solution, project_demo, etc.
    related_to: str  # course, material, project
    related_id: str  # course_id, material_id, project_id
    
    # Order and organization
    order: int = 0
    section: Optional[str] = None  # Section name
    
    # Access control
    is_public: bool = False
    downloadable: bool = False
    
    # Metadata
    uploaded_by: str  # admin telegram_id
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Statistics
    views_count: int = 0
    unique_viewers: List[str] = Field(default_factory=list)  # user_ids who watched
    
    # Status
    is_active: bool = True
    
    class Settings:
        name = "videos"
        indexes = [
            "file_id",
            "related_to",
            "related_id",
            ("related_to", "related_id"),
        ]
    
    async def increment_views(self, user_id: str):
        """Increment views count"""
        self.views_count += 1
        if user_id not in self.unique_viewers:
            self.unique_viewers.append(user_id)
        self.updated_at = datetime.utcnow()
        await self.save()
    
    def get_info_text(self) -> str:
        """Get formatted video info"""
        info = f"📹 **{self.title}**\n\n"
        if self.description:
            info += f"{self.description}\n\n"
        if self.duration:
            mins = self.duration // 60
            secs = self.duration % 60
            info += f"⏱️ المدة: {mins}:{secs:02d}\n"
        info += f"👁️ المشاهدات: {self.views_count}\n"
        return info
