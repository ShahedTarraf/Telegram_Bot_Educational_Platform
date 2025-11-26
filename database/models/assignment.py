"""
Assignment Model
"""
from datetime import datetime
from typing import Optional, List
from beanie import Document
from pydantic import Field


class AssignmentSubmission(Document):
    """Assignment submission sub-document"""
    user_id: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    file_id: Optional[str] = None  # Telegram file ID
    text_answer: Optional[str] = None
    grade: Optional[int] = None  # 0-100
    feedback: Optional[str] = None
    graded_by: Optional[str] = None  # admin telegram_id
    graded_at: Optional[datetime] = None
    status: str = "submitted"  # submitted, graded, returned


class Assignment(Document):
    """Assignment model"""
    title: str
    description: str
    instructions: Optional[str] = None
    
    # Classification
    related_to: str  # course, material
    related_id: str
    
    # Content
    attachment_file_id: Optional[str] = None
    attachment_type: Optional[str] = None  # pdf, image, video
    
    # Deadline
    deadline: Optional[datetime] = None
    allow_late_submission: bool = True
    
    # Grading
    max_grade: int = 100
    pass_grade: int = 60
    
    # Submissions
    submissions: List[AssignmentSubmission] = Field(default_factory=list)
    
    # Metadata
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    is_active: bool = True
    order: int = 0
    
    class Settings:
        name = "assignments"
        indexes = [
            "related_to",
            "related_id",
            ("related_to", "related_id"),
        ]
    
    def get_submission(self, user_id: str) -> Optional[AssignmentSubmission]:
        """Get user's submission"""
        for submission in self.submissions:
            if submission.user_id == user_id:
                return submission
        return None
    
    def has_submitted(self, user_id: str) -> bool:
        """Check if user has submitted"""
        return self.get_submission(user_id) is not None
    
    async def add_submission(
        self,
        user_id: str,
        file_id: Optional[str] = None,
        text_answer: Optional[str] = None
    ):
        """Add new submission"""
        # Remove old submission if exists
        self.submissions = [s for s in self.submissions if s.user_id != user_id]
        
        submission = AssignmentSubmission(
            user_id=user_id,
            file_id=file_id,
            text_answer=text_answer
        )
        self.submissions.append(submission)
        self.updated_at = datetime.utcnow()
        await self.save()
    
    async def grade_submission(
        self,
        user_id: str,
        grade: int,
        feedback: str,
        graded_by: str
    ):
        """Grade a submission"""
        submission = self.get_submission(user_id)
        if submission:
            submission.grade = grade
            submission.feedback = feedback
            submission.graded_by = graded_by
            submission.graded_at = datetime.utcnow()
            submission.status = "graded"
            self.updated_at = datetime.utcnow()
            await self.save()
    
    def is_past_deadline(self) -> bool:
        """Check if past deadline"""
        if not self.deadline:
            return False
        return datetime.utcnow() > self.deadline
    
    def get_info_text(self) -> str:
        """Get formatted assignment info"""
        info = f"📝 **{self.title}**\n\n"
        info += f"{self.description}\n\n"
        if self.instructions:
            info += f"📋 التعليمات:\n{self.instructions}\n\n"
        if self.deadline:
            info += f"📅 الموعد النهائي: {self.deadline.strftime('%Y-%m-%d %H:%M')}\n"
        info += f"🎯 الدرجة القصوى: {self.max_grade}\n"
        info += f"✅ درجة النجاح: {self.pass_grade}\n"
        return info
